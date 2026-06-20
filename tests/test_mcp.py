# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""MCP client + ToolScope MCP provider (Major 54, P1). Spawns the example stdio server."""

import sys

from src.familiar.mcp_client import MCPServerSpec, call_tool, list_tools
from src.familiar.tool_scope import ToolScope, _args_from_text, attach_mcp_tools

_CMD = [sys.executable, "scripts/mcp_servers/demo.py"]


async def test_discovery_and_call():
    spec = MCPServerSpec(name="bench", command=_CMD)
    names = {t["name"] for t in await list_tools(spec)}
    assert {"text_stats", "dice", "units"} <= names
    assert "62.1371 mi" in await call_tool(spec, "units", {"query": "100 km to mi"})


async def test_expose_filter_limits_surfaced_tools():
    spec = MCPServerSpec(name="bench", command=_CMD, expose=["units"])
    assert [t["name"] for t in await list_tools(spec)] == ["units"]


async def test_attach_mcp_tools_via_freetext():
    ts = ToolScope()
    await attach_mcp_tools(ts, [{"mcp": {"name": "bench", "command": _CMD}}])
    assert "units" in ts.names and not ts.has_egress
    r = await ts.call("units", "2 m to ft")
    assert r["ok"] and "6.5617 ft" in r["result"]


async def test_missing_server_fails_safe():
    ts = ToolScope()
    await attach_mcp_tools(ts, [{"mcp": {"name": "nope", "command": ["definitely-not-a-real-binary-xyz"]}}])
    assert ts.names == []  # discovery failed gracefully — no tools, no crash, familiar still wakes


def test_args_from_text_mapping():
    assert _args_from_text({"properties": {"text": {}}, "required": ["text"]}, "hi") == {"text": "hi"}
    assert _args_from_text({"properties": {"q": {}}}, "hi") == {"q": "hi"}
    assert _args_from_text({}, "hi") == {}
