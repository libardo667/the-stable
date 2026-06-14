"""A minimal MCP (Model Context Protocol) stdio client (Major 54, P1).

Just enough of MCP to let a familiar use keeper-wired tool servers — no SDK, stdlib only,
in the spirit of a httpx + pathspec runtime. The transport is JSON-RPC 2.0 over a server
subprocess's stdin/stdout, newline-delimited (the MCP stdio transport).

A session is short-lived and stateless: for each operation (discover the server's tools, or
call one) we spawn the server, do the ``initialize`` handshake, run the op, and close. Tool
use is occasional, so the spawn cost is a fair trade for not holding a subprocess and its
lifecycle across every tick. Everything is best-effort and time-bounded — a tool server can
be slow, crash, or speak nonsense, and it must never take the pulse down with it.

Local-first: a stdio server runs ON the machine, so by default a familiar's MCP tools are
no-egress. A server that itself reaches out (an API proxy) is the keeper's explicit choice,
declared with ``egress: true`` in familiar.json.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_PROTOCOL_VERSION = "2024-11-05"
_DEFAULT_TIMEOUT = 20.0


@dataclass
class MCPServerSpec:
    """A keeper-declared MCP server: how to launch it and how to treat it."""

    name: str
    command: list[str]
    cwd: str | None = None
    env: dict[str, str] | None = None
    egress: bool = False           # True ⇒ this server reaches off the machine (keeper opt-in)
    expose: list[str] = field(default_factory=list)  # if set, only these tool names are surfaced
    timeout: float = _DEFAULT_TIMEOUT


async def _readline_json(stream: asyncio.StreamReader, timeout: float) -> dict[str, Any] | None:
    line = await asyncio.wait_for(stream.readline(), timeout)
    if not line:
        return None
    try:
        return json.loads(line.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        return {}


async def _run_ops(spec: MCPServerSpec, ops: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    """Spawn the server, initialize, run each (method, params) in order, return their JSON-RPC
    results (or {} on trouble). Stateless: the subprocess is closed before returning."""
    env = {**os.environ, **(spec.env or {})} if spec.env else None
    try:
        proc = await asyncio.create_subprocess_exec(
            *spec.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            cwd=spec.cwd,
            env=env,
        )
    except (OSError, ValueError) as exc:
        logger.warning("[mcp:%s] could not launch %r: %s", spec.name, spec.command, exc)
        return [{} for _ in ops]

    async def _send(msg: dict[str, Any]) -> None:
        assert proc.stdin is not None
        proc.stdin.write((json.dumps(msg) + "\n").encode("utf-8"))
        await proc.stdin.drain()

    async def _await_id(want: int) -> dict[str, Any]:
        assert proc.stdout is not None
        # skip notifications / log lines / id-mismatches until our response arrives
        for _ in range(64):
            msg = await _readline_json(proc.stdout, spec.timeout)
            if msg is None:
                return {}
            if msg.get("id") == want:
                return msg
        return {}

    results: list[dict[str, Any]] = []
    try:
        await _send({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {
            "protocolVersion": _PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "familiar", "version": "0"}}})
        await _await_id(0)
        await _send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        for i, (method, params) in enumerate(ops, start=1):
            await _send({"jsonrpc": "2.0", "id": i, "method": method, "params": params})
            results.append(await _await_id(i))
    except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError) as exc:
        logger.warning("[mcp:%s] op failed: %s", spec.name, exc)
        results += [{} for _ in range(len(ops) - len(results))]
    finally:
        try:
            if proc.stdin is not None:
                proc.stdin.close()
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=3.0)
        except (ProcessLookupError, asyncio.TimeoutError, OSError):
            pass
    return results


async def list_tools(spec: MCPServerSpec) -> list[dict[str, Any]]:
    """Discover the server's tools: a list of ``{name, description, inputSchema}``."""
    (resp,) = await _run_ops(spec, [("tools/list", {})])
    tools = (resp.get("result") or {}).get("tools") or []
    if spec.expose:
        allow = set(spec.expose)
        tools = [t for t in tools if t.get("name") in allow]
    return tools


async def call_tool(spec: MCPServerSpec, name: str, arguments: dict[str, Any]) -> str:
    """Call one tool, return its text result. Best-effort — returns an error string, never raises."""
    (resp,) = await _run_ops(spec, [("tools/call", {"name": name, "arguments": arguments})])
    if not resp:
        return f"(the '{spec.name}' tool server did not respond)"
    if resp.get("error"):
        return f"(tool error: {resp['error'].get('message', resp['error'])})"
    content = (resp.get("result") or {}).get("content") or []
    parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
    text = "\n".join(p for p in parts if p).strip()
    return text or "(the tool returned nothing)"
