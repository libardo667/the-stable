#!/usr/bin/env python3
"""A tiny example MCP stdio server (Major 54, P1 demo) — stdlib only.

A handful of local, no-egress, no-data tools, to prove the MCP path end to end and to give a
familiar something with variety to reach for. The keeper would wire their own servers the same
way (a `{"mcp": {...}}` entry in familiar.json); this one is the worked example.

Protocol: JSON-RPC 2.0 over stdin/stdout, one message per line (the MCP stdio transport).
Nothing here leaves the machine.
"""

import json
import random
import re
import sys

_UNITS = {("km", "mi"): 0.621371, ("mi", "km"): 1.60934, ("m", "ft"): 3.28084,
          ("ft", "m"): 0.3048, ("kg", "lb"): 2.20462, ("lb", "kg"): 0.453592}


def _text_stats(args):
    t = str(args.get("text", ""))
    words = len(t.split())
    return f"words: {words}, characters: {len(t)}, lines: {t.count(chr(10)) + 1 if t else 0}, ~reading time: {round(words / 3.3)}s"


def _dice(args):
    spec = str(args.get("spec", "")).strip()
    m = re.fullmatch(r"(\d*)d(\d+)", spec, re.I)
    if m:
        n, sides = int(m.group(1) or 1), int(m.group(2))
        if not (1 <= n <= 100 and 2 <= sides <= 1000):
            return "dice out of range (1-100 dice, 2-1000 sides)"
        rolls = [random.randint(1, sides) for _ in range(n)]
        return f"rolled {spec}: {rolls} (sum {sum(rolls)})"
    if "," in spec:
        opts = [o.strip() for o in spec.split(",") if o.strip()]
        return f"picked: {random.choice(opts)}" if opts else "nothing to pick from"
    return 'give NdM (e.g. "2d6") or a comma-list to pick from'


def _units(args):
    q = str(args.get("query", "")).strip().lower()
    m = re.fullmatch(r"([-\d.]+)\s*([a-z]+)\s*(?:to|in|->)\s*([a-z]+)", q)
    if not m:
        return 'try "100 km to mi" — known: km/mi, m/ft, kg/lb, c/f'
    val, frm, to = float(m.group(1)), m.group(2), m.group(3)
    if (frm, to) == ("c", "f"):
        return f"{val}°C = {round(val * 9 / 5 + 32, 2)}°F"
    if (frm, to) == ("f", "c"):
        return f"{val}°F = {round((val - 32) * 5 / 9, 2)}°C"
    factor = _UNITS.get((frm, to))
    return f"{val} {frm} = {round(val * factor, 4)} {to}" if factor else f"don't know {frm}→{to}; try km/mi, m/ft, kg/lb, c/f"


TOOLS = [
    {"name": "text_stats", "description": "word / character / line count and reading-time estimate for some text",
     "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, "_fn": _text_stats},
    {"name": "dice", "description": 'roll dice ("2d6") or pick from a comma-list ("tea, coffee, nothing")',
     "inputSchema": {"type": "object", "properties": {"spec": {"type": "string"}}, "required": ["spec"]}, "_fn": _dice},
    {"name": "units", "description": 'convert units, e.g. "100 km to mi" (km/mi, m/ft, kg/lb, c/f)',
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}, "_fn": _units},
]
_FN = {t["name"]: t["_fn"] for t in TOOLS}
_PUBLIC = [{k: v for k, v in t.items() if not k.startswith("_")} for t in TOOLS]


def _handle(msg):
    mid, method = msg.get("id"), msg.get("method")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {"protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}}, "serverInfo": {"name": "familiar-demo", "version": "0.1"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": _PUBLIC}}
    if method == "tools/call":
        p = msg.get("params") or {}
        fn = _FN.get(p.get("name"))
        if fn is None:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"no tool {p.get('name')}"}}
        try:
            text = fn(p.get("arguments") or {})
        except Exception as exc:
            text = f"error: {exc}"
        return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": str(text)}]}}
    if mid is None:
        return None  # a notification (e.g. initialized) — no response
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "unknown method"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
