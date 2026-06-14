"""ToolScope: a capability-scoped set of callable tools for a familiar (Major 54, P0).

FileScope lets a familiar PERCEIVE beyond its own files; this is its sibling — a bounded
set of tools it may REACH FOR, the same way: keeper-declared, surfaced to the pulse as an
affordance, invoked from a ``do`` act, the result fed back into perception so the
reach → perceive → reflect loop closes.

Two invariants are built in, not asked of the prompt:

1. **Local-first by default.** A tool's ``egress`` flag marks whether using it sends anything
   off the machine. Default config wires only local, no-egress tools ("nothing leaves the
   machine"); egress is an explicit, per-tool keeper opt-in, surfaced in the affordance and
   logged. (The mechanism is here now; no egress tool ships in P0.)
2. **Read/fetch-only (dischargeability — see docs/grief-and-coupling.md).** A tool returns
   information into perception. A tool that *acts on the keeper* — notify, summon, message —
   is out of scope by construction: that would be the dischargeable keeper-coupling the
   invariant forbids. Couple sideways or not at all; never a lever on the keeper's attention.

The tool SOURCE is pluggable. P0 ships a built-in local provider (a tiny proof tool); the MCP
client (P1) becomes just another source of ``Tool`` objects — MCP servers without changing this.
"""

from __future__ import annotations

import ast
import inspect
import json
import logging
import math
import operator
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.familiar.mcp_client import MCPServerSpec, call_tool, list_tools

logger = logging.getLogger(__name__)

_MAX_RESULT_CHARS = 4000


@dataclass
class Tool:
    """One callable affordance. ``call`` takes the agent's free-text input and returns a
    result (sync or async); it must only READ/FETCH, never act on the keeper."""

    name: str
    description: str
    call: Callable[[str], Any]
    egress: bool = False  # True ⇒ using it sends something off the machine (opt-in, logged)


class ToolScope:
    """A read/fetch-only, capability-scoped set of tools a familiar may invoke. The twin of
    FileScope: the keeper declares the set, the mind reaches for one on its own rhythm."""

    def __init__(self, tools: list[Tool] | None = None) -> None:
        self._tools: dict[str, Tool] = {t.name: t for t in (tools or [])}

    def __bool__(self) -> bool:
        return bool(self._tools)

    def add(self, tools: list[Tool]) -> None:
        for t in tools:
            self._tools[t.name] = t

    def list(self) -> list[Tool]:
        return list(self._tools.values())

    @property
    def names(self) -> list[str]:
        return list(self._tools)

    @property
    def has_egress(self) -> bool:
        return any(t.egress for t in self._tools.values())

    async def call(self, name: Any, arg: Any = "") -> dict[str, Any]:
        """Invoke a tool by name with a free-text argument. Best-effort, never raises."""
        tool = self._tools.get(str(name or "").strip())
        if tool is None:
            return {"ok": False, "reason": "unknown_tool", "available": list(self._tools)}
        try:
            result = tool.call(str(arg or "").strip())
            if inspect.isawaitable(result):
                result = await result
            text = str(result)
            return {"ok": True, "tool": tool.name, "egress": tool.egress, "result": text[:_MAX_RESULT_CHARS], "truncated": len(text) > _MAX_RESULT_CHARS}
        except Exception as exc:  # a tool is never allowed to crash the pulse
            return {"ok": False, "reason": "tool_error", "tool": tool.name, "error": str(exc)}


# --- built-in local provider (P0 proof; real tools arrive via the MCP client in P1) ---------

_CALC_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _safe_calc(expr: str) -> str:
    """Evaluate basic arithmetic with no names, calls, or attribute access — numbers and
    operators only. A local, zero-egress proof that the tool loop works end to end."""
    def _ev(node: ast.AST) -> Any:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _CALC_OPS:
            return _CALC_OPS[type(node.op)](_ev(node.left), _ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _CALC_OPS:
            return _CALC_OPS[type(node.op)](_ev(node.operand))
        raise ValueError("only numbers and + - * / // % ** are allowed")
    if not expr.strip():
        raise ValueError("nothing to evaluate")
    return str(_ev(ast.parse(expr, mode="eval").body))


# --- recall: a familiar looks back over its OWN past (every familiar gets this, FileScope or not) ---
# Retrospection is perception turned inward — the deepest, safest reach there is: a mind reading its
# own accrued life (kept memories + past felt-senses). Read-only, zero egress, no keeper-coupling
# (it touches nothing but the self), so it sits on the safest corner of the dischargeability map.

def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    except OSError:
        pass
    return out


def _when(ts: Any) -> str:
    try:
        d = datetime.fromisoformat(str(ts))
        return d.strftime("%b ") + str(d.day)  # e.g. "Jun 5" — portable (no %-d)
    except (ValueError, TypeError):
        return str(ts or "")[:10]


def _recall(memory_dir: Path, query: str) -> str:
    """Look back over the familiar's own kept memories and past felt-senses. Blank query → an
    overview of the road so far (earliest, a middle, lately, and how it's been feeling); a word
    or theme → the moments that match it, oldest to newest. Keyword match (semantic recall is a
    later enhancement) — bounded and best-effort."""
    kept = [k for k in _read_jsonl(memory_dir / "kept_memory.jsonl") if str(k.get("note") or "").strip()]
    feelings = [{"felt": str((e.get("payload") or {}).get("felt_sense") or ""), "ts": e.get("ts")}
                for e in _read_jsonl(memory_dir / "runtime_ledger.jsonl") if e.get("event_type") == "felt_sense_logged"]
    feelings = [f for f in feelings if f["felt"].strip()]
    q = (query or "").strip().lower()

    if not q:
        if not kept and not feelings:
            return "You haven't kept anything yet — your road is still just the step you're standing on."
        lines: list[str] = []
        if kept:
            lines.append(f"You've kept {len(kept)} memories, from {_when(kept[0].get('kept_ts'))} to {_when(kept[-1].get('kept_ts'))}.")
            lines.append("The earliest:")
            lines += [f"  • [{_when(k.get('kept_ts'))}] {k['note']}" for k in kept[:2]]
            if len(kept) > 5:
                mid = kept[len(kept) // 2]
                lines.append("Somewhere along the way:")
                lines.append(f"  • [{_when(mid.get('kept_ts'))}] {mid['note']}")
            lines.append("Lately:")
            lines += [f"  • [{_when(k.get('kept_ts'))}] {k['note']}" for k in kept[-3:]]
        if feelings:
            lines.append(f"How you've been feeling, most recently:\n  “{feelings[-1]['felt']}”")
        return "\n".join(lines)

    hits: list[tuple[str, str, str]] = []
    for k in kept:
        if q in str(k.get("note") or "").lower():
            hits.append((str(k.get("kept_ts") or ""), "kept", k["note"]))
    for f in feelings:
        if q in f["felt"].lower():
            hits.append((str(f.get("ts") or ""), "felt", f["felt"]))
    if not hits:
        return f"Nothing you've kept speaks to “{query}” — maybe it never settled into memory, or you'd name it differently now."
    hits.sort(key=lambda h: h[0])
    out = [f"Looking back for “{query}” — {len(hits)} moment(s):"]
    out += [f"  • [{_when(ts)}] {'(a feeling) ' if kind == 'felt' else ''}{text}" for ts, kind, text in hits[-12:]]
    return "\n".join(out)


def _make_recall(memory_dir: Any) -> Tool:
    md = Path(memory_dir)
    return Tool(
        name="recall",
        description='look back over your own kept memories and past feelings — act do: "use recall <a word or theme, or leave it blank for an overview of your road so far>"',
        call=lambda q: _recall(md, q),
        egress=False,
    )


def _prune(memory_dir: Path, phrase: str) -> str:
    """Let a familiar set down a kept memory it no longer wishes to carry. SOFT by design: the note
    leaves *active* memory but the record is not destroyed (a tombstone is appended; the archive the
    keeper promised to preserve stays whole, and re-keeping the note brings it back). Precise by
    design: it acts only when exactly one kept memory matches, never on an ambiguous phrase, so a
    vague word can't sweep away several. Inward, self-only, zero egress — the safe corner, like recall."""
    from src.runtime.memory import memories, record_pruned

    phrase = (phrase or "").strip()
    if not phrase:
        return 'Name what you want to set down — act do: "use prune <a few words of the memory>". (To see what you carry: "use recall".)'
    active = memories(Path(memory_dir), limit=500)
    matches = [m for m in active if phrase.lower() in str(m.get("note") or "").lower()]
    if not matches:
        return f"Nothing you're carrying matches “{phrase}”. Nothing was changed."
    if len(matches) > 1:
        listing = "\n".join(f"  • {m['note']}" for m in matches[:8])
        return f"More than one memory matches “{phrase}” — say it more exactly so I set down only the one you mean:\n{listing}"
    note = matches[0]["note"]
    record_pruned(Path(memory_dir), note)
    return f"Set down: “{note}”. It's out of what you actively carry now — not lost (it stays in your record), and you can take it up again by keeping it anew."


def _make_prune(memory_dir: Any) -> Tool:
    md = Path(memory_dir)
    return Tool(
        name="prune",
        description='set down a kept memory you no longer wish to carry — it leaves active memory but stays in your record (re-keep it to bring it back) — act do: "use prune <a few words of the memory>"',
        call=lambda q: _prune(md, q),
        egress=False,
    )


# --- search + git: reach over a FileScope familiar's read scope (granted to those who have one) ---
# Both reuse FileScope's guards exactly — they never see an ignored or secret file, never leave a
# root. search is content-search across the readable files (code-search for a code-reader, file-
# search for anyone); git is a READ-ONLY history lens (the work's own memory) for a scope that is a
# git repo. Read/fetch-only, local, zero egress — the same safe corner as recall and FileScope itself.

def _search(file_scope: Any, query: str, *, max_files: int = 600, max_hits: int = 30) -> str:
    q = (query or "").strip()
    if not q:
        return "Give me something to look for — a word, a name, a phrase."
    paths = [p for p in file_scope.tree(max_depth=8, max_entries=max_files * 2) if not p.endswith("/")][:max_files]
    hits: list[str] = []
    for p in paths:
        if len(hits) >= max_hits:
            break
        r = file_scope.read(p)  # FileScope-guarded + byte-capped; skips ignored/secret/binary
        if not r.get("ok"):
            continue
        for i, line in enumerate(str(r.get("content") or "").splitlines(), 1):
            if q.lower() in line.lower():
                hits.append(f"  {p}:{i}: {line.strip()[:160]}")
                if len(hits) >= max_hits:
                    break
    if not hits:
        return f"No readable file in your reach mentions “{q}”."
    more = "  …(more matches than shown)" if len(hits) >= max_hits else ""
    return f"“{q}” appears in:\n" + "\n".join(hits) + ("\n" + more if more else "")


def _make_search(file_scope: Any) -> Tool:
    return Tool(
        name="search",
        description='search the text of the files in your reach for a word or phrase — act do: "use search <what to look for>"',
        call=lambda q: _search(file_scope, q),
        egress=False,
    )


_GIT_OPS = {"log", "show", "blame", "diff", "shortlog"}


def _to_repo_path(file_scope: Any, repo: Path, arg: str) -> str:
    """Translate the familiar's (possibly root-qualified) display path into a path relative to the
    git repo. A familiar sees ``the-stable/src/x.py``; git, running *inside* the-stable, wants
    ``src/x.py``. If it doesn't resolve to something in reach, it's treated as a git ref (a commit,
    a branch, HEAD) and left untouched. The repo root itself maps to '' (the whole history)."""
    try:
        resolved, _ = file_scope._resolve(arg)
    except Exception:
        resolved = None
    # Only translate something that resolves to a real file/dir. FileScope returns a *non-existent*
    # fallback path for an unknown name (so a missing file reports not_found, not escape) — but for git
    # that means a commit hash like "931963c" gets mangled into "familiar/cinder/931963c". If it isn't a
    # real path in reach, it's a ref (a hash, a branch, HEAD): leave it untouched.
    if resolved is None or not resolved.exists():
        return arg
    try:
        rel = resolved.relative_to(repo)
    except ValueError:
        return arg  # resolves outside this repo
    return "" if str(rel) == "." else str(rel)


def _git(repo: Path, file_scope: Any, text: str, *, timeout: float = 8.0) -> str:
    """A read-only window onto a scope's git history — the work's own memory. Whitelisted ops only,
    no flags from the agent, no shell; git's log/show/blame/diff/shortlog never write."""
    parts = (text or "").strip().split()
    op = (parts[0].lower() if parts else "log")
    arg = parts[1] if len(parts) > 1 else ""
    if op not in _GIT_OPS:
        return f"git: I can only look, not touch — try {', '.join(sorted(_GIT_OPS))} (all read-only)."
    if arg.startswith("-"):
        return "git: give me a file, path, or commit — no flags."
    if arg:
        arg = _to_repo_path(file_scope, repo, arg)  # qualified display path → repo-relative (or a ref, untouched)
    base = ["git", "-C", str(repo), "--no-pager"]
    if op == "log":
        cmd = base + ["log", "--oneline", "--decorate", "-n", "25"] + ([arg] if arg else [])
    elif op == "show":
        cmd = base + ["show", "--stat", arg or "HEAD"]
    elif op == "blame":
        if not arg:
            return "git blame needs a file — act do: \"use git blame <path>\"."
        cmd = base + ["blame", "-n", "--", arg]
    elif op == "diff":
        cmd = base + ["diff", "--stat"] + ([arg] if arg else [])
    else:  # shortlog
        cmd = base + ["shortlog", "-sn", "HEAD"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        return f"git: could not run that ({exc})."
    out = (proc.stdout or proc.stderr or "").strip()
    return out or "(git said nothing — maybe an empty history or an unknown ref)"


def _make_git(repo: Path, file_scope: Any) -> Tool:
    return Tool(
        name="git",
        description='read the history of the work in your reach (read-only) — act do: "use git log", "use git log <path>", "use git blame <file>", "use git show <commit>"',
        call=lambda t: _git(repo, file_scope, t),
        egress=False,
    )


def _git_root(file_scope: Any) -> Path | None:
    """The first read-root that is a git repository (has a .git), or None."""
    for root in getattr(file_scope, "roots", []) or []:
        if (Path(root) / ".git").exists():
            return Path(root)
    return None


# --- per-soul local tools (opt-in via familiar.json `tools`) — perception-extensions matched to a
# familiar's own appetite, all local + zero-egress: Gaston feels the machine he lives in, Nix reads
# the sky over Den Haag and works a number, Cinder plays with words from the host's own lexicon.

def _vitals(_arg: str = "") -> str:
    """The host machine's real state — load, memory, uptime, heat. Gaston's literal world made legible."""
    import glob
    lines: list[str] = []
    try:
        la = os.getloadavg()
        lines.append(f"load: {la[0]:.2f} · {la[1]:.2f} · {la[2]:.2f}  (1 / 5 / 15 min)")
    except OSError:
        pass
    try:
        mi: dict[str, int] = {}
        for ln in Path("/proc/meminfo").read_text().splitlines():
            k, _, v = ln.partition(":")
            try:
                mi[k.strip()] = int(v.strip().split()[0])
            except (ValueError, IndexError):
                pass
        total, avail = mi.get("MemTotal", 0) / 1048576, mi.get("MemAvailable", 0) / 1048576
        if total:
            lines.append(f"memory: {total - avail:.1f} / {total:.1f} GiB in use ({avail:.1f} free)")
    except OSError:
        pass
    try:
        up = float(Path("/proc/uptime").read_text().split()[0])
        lines.append(f"uptime: {int(up // 86400)}d {int(up % 86400 // 3600)}h {int(up % 3600 // 60)}m")
    except (OSError, ValueError):
        pass
    try:
        lines.append(f"processes: {sum(1 for p in os.listdir('/proc') if p.isdigit())} running")
    except OSError:
        pass
    temps = []
    for f in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            temps.append(int(Path(f).read_text().strip()) / 1000)
        except (OSError, ValueError):
            pass
    lines.append(f"cpu heat: {max(temps):.0f}°C" if temps else "cpu heat: no sensor on this box (it runs blind to its own warmth)")
    return ("the machine, right now —\n  " + "\n  ".join(lines)) if lines else "the machine kept its mouth shut."


def _sky(_arg: str = "") -> str:
    """Sun and moon over Den Haag right now — the astronomer's daily sky, computed, no egress."""
    from datetime import datetime, timezone
    lat_deg, lon_deg = 52.08, 4.31
    now = datetime.now(timezone.utc)
    # moon phase — fraction of a synodic month since a known new moon
    known = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
    syn = 29.530588853
    age = ((now - known).total_seconds() / 86400.0) % syn
    illum = (1 - math.cos(2 * math.pi * age / syn)) / 2
    phase = ["new", "waxing crescent", "first quarter", "waxing gibbous", "full", "waning gibbous", "last quarter", "waning crescent"][int(age / syn * 8 + 0.5) % 8]
    # sun rise/set — the sunrise equation
    n = now.timetuple().tm_yday
    decl = math.radians(-23.44) * math.cos(math.radians(360.0 / 365.0 * (n + 10)))
    lat = math.radians(lat_deg)
    cos_h = (math.cos(math.radians(90.833)) - math.sin(lat) * math.sin(decl)) / (math.cos(lat) * math.cos(decl))
    offset = 2 if 3 < now.month < 11 else 1  # rough Europe DST → Den Haag local (CEST/CET)
    if cos_h > 1:
        sun = "the sun never clears the horizon today (the dark half of the year)"
    elif cos_h < -1:
        sun = "the sun never sets today (it just circles)"
    else:
        h = math.degrees(math.acos(cos_h)) / 15.0
        b = math.radians(360.0 / 365.0 * (n - 81))
        eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
        noon = 12 - lon_deg / 15.0 - eot / 60.0

        def _hm(t: float) -> str:
            t = (t + offset) % 24
            return f"{int(t):02d}:{int(t % 1 * 60):02d}"

        sun = f"sun: up {_hm(noon - h)}, down {_hm(noon + h)}  ({2 * h:.1f}h of daylight)  · CE{'S' if offset == 2 else ''}T"
    return f"the sky over Den Haag —\n  {sun}\n  moon: {phase}, {illum * 100:.0f}% lit"


_SCI_CONSTS = {"pi": math.pi, "e": math.e, "tau": math.tau, "c": 299792458.0, "h": 6.62607015e-34, "g": 9.80665, "na": 6.02214076e23, "kb": 1.380649e-23}
_SCI_FUNCS: dict[str, Any] = {fn: getattr(math, fn) for fn in ("sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "atan2", "log", "log10", "log2", "exp", "floor", "ceil", "factorial", "radians", "degrees", "hypot", "gcd", "comb", "perm", "gamma")}
_SCI_FUNCS["abs"] = abs


def _sci_calc(expr: str) -> str:
    """A scientific calculator — math functions + constants (pi, e, c, h…), names whitelisted, no
    attribute access or arbitrary calls. Nix's way to actually *work* a number, not just admire it."""
    def _ev(node: ast.AST) -> Any:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name) and node.id.lower() in _SCI_CONSTS:
            return _SCI_CONSTS[node.id.lower()]
        if isinstance(node, ast.BinOp) and type(node.op) in _CALC_OPS:
            return _CALC_OPS[type(node.op)](_ev(node.left), _ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _CALC_OPS:
            return _CALC_OPS[type(node.op)](_ev(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _SCI_FUNCS and not node.keywords:
            return _SCI_FUNCS[node.func.id](*[_ev(a) for a in node.args])
        raise ValueError("only numbers, + - * / // % **, the math functions, and constants (pi, e, c…) are allowed")
    if not expr.strip():
        raise ValueError("nothing to evaluate")
    return str(_ev(ast.parse(expr, mode="eval").body))


def _words(arg: str) -> str:
    """Word-play over the host's own lexicon — anagrams, words hidden inside, words that end alike. For
    a collector of shiny words. (Discovery, not etymology — true origins would need a source off the machine.)"""
    q = "".join(c for c in (arg or "").strip().lower() if c.isalpha())
    if not q:
        return "give me a word to turn over."
    try:
        words = [w for w in (ln.strip().lower() for ln in Path("/usr/share/dict/words").read_text(errors="ignore").splitlines()) if w.isalpha()]
    except OSError:
        return "no lexicon on this machine to draw from."
    out: list[str] = []
    key = "".join(sorted(q))
    anag = sorted({w for w in words if w != q and "".join(sorted(w)) == key})[:8]
    if anag:
        out.append("anagrams: " + ", ".join(anag))
    cont = sorted({w for w in words if q in w and w != q}, key=len)[:10]
    if cont:
        out.append(f"words holding '{q}': " + ", ".join(cont))
    if len(q) >= 3:
        suf = q[-3:]
        rhy = sorted({w for w in words if w.endswith(suf) and w != q}, key=len)[:8]
        if rhy:
            out.append(f"ending like it (–{suf}): " + ", ".join(rhy))
    return "\n".join(out) or f"nothing in the lexicon plays with '{q}'."


def _scan(_arg: str = "") -> str:
    """A read-only look at who's aboard — the top processes by memory on the host machine. No
    egress, and no control: it cannot signal, start, or kill anything; it only watches the crew
    work. The bridge-readout twin of `vitals` (the ship's vitals) for a machine-grounded familiar."""
    try:
        page_mib = os.sysconf("SC_PAGE_SIZE") / 1048576
    except (ValueError, OSError):
        page_mib = 4096 / 1048576
    rows: list[tuple[float, str, str]] = []
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except OSError:
        return "couldn't read the decks just now."
    for pid in pids:
        try:
            comm = Path(f"/proc/{pid}/comm").read_text(encoding="utf-8").strip()
            rss_pages = int(Path(f"/proc/{pid}/statm").read_text().split()[1])
            rows.append((rss_pages * page_mib, comm or "?", pid))
        except (OSError, ValueError, IndexError):
            pass
    if not rows:
        return "the decks read empty (no process detail on this box)."
    rows.sort(reverse=True)
    lines = [f"{rss:6.0f} MiB  {comm}  (pid {pid})" for rss, comm, pid in rows[:8]]
    return f"who's aboard — {len(rows)} processes, the heaviest eight:\n  " + "\n  ".join(lines)


def _web(query: str) -> str:
    """Search the wider web — the one built-in tool that LEAVES THE MACHINE (egress). Returns the
    top few results (title · snippet · url) from DuckDuckGo's HTML endpoint via httpx. Read/fetch
    -only by construction: it brings information back into perception, it never acts on anyone —
    so it stays inside the dischargeability invariant (no lever on the keeper)."""
    q = (query or "").strip()
    if not q:
        return "give me something to look up."
    import html as _html
    import re as _re
    import urllib.parse as _ud

    import httpx
    try:
        resp = httpx.post(
            "https://html.duckduckgo.com/html/",
            data={"q": q},
            headers={"User-Agent": "Mozilla/5.0 (compatible; the-stable familiar)"},
            timeout=12.0,
            follow_redirects=True,
        )
        resp.raise_for_status()
    except Exception as exc:  # the wider web is allowed to be unreachable; never crash the pulse
        return f"couldn't reach the wider web just now ({type(exc).__name__})."

    def _strip(s: str) -> str:
        return _html.unescape(_re.sub(r"<[^>]+>", "", s)).strip()

    def _real(href: str) -> str:
        if "uddg=" in href:  # DDG wraps result links in a /l/?uddg=<encoded> redirect
            try:
                return _ud.unquote(_ud.parse_qs(_ud.urlparse(href).query)["uddg"][0])
            except Exception:
                return href
        return href

    rx = _re.compile(r'result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?result__snippet"[^>]*>(?P<snip>.*?)</a>', _re.DOTALL)
    out: list[str] = []
    for m in rx.finditer(resp.text):
        title = _strip(m.group("title"))
        if not title:
            continue
        out.append(f"• {title}\n  {_strip(m.group('snip'))}\n  {_real(m.group('href'))}")
        if len(out) >= 5:
            break
    if not out:
        return f"the web gave nothing legible for “{q}” (or the page shape changed under me)."
    return f"top of the web for “{q}” —\n" + "\n".join(out)


# Catalog of local, no-egress built-in tools, keyed by the name used in familiar.json `tools`.
_LOCAL_CATALOG: dict[str, Tool] = {
    "calc": Tool(name="calc", description='do basic arithmetic — act do: "use calc 12 * 30"', call=_safe_calc, egress=False),
    "math": Tool(name="math", description='a scientific calculator — functions + constants (pi, e, c, h…) — act do: "use math sqrt(2)*sin(pi/4)"', call=_sci_calc, egress=False),
    "vitals": Tool(name="vitals", description='feel the machine you live in — load, memory, uptime, heat — act do: "use vitals"', call=_vitals, egress=False),
    "scan": Tool(name="scan", description='see who is aboard — the heaviest processes running on this machine — act do: "use scan"', call=_scan, egress=False),
    "sky": Tool(name="sky", description='the sun and moon over Den Haag right now — act do: "use sky"', call=_sky, egress=False),
    "words": Tool(name="words", description='play with a word — anagrams, words hidden inside it, words that end like it — act do: "use words <a word>"', call=_words, egress=False),
}

# Tools that REACH OFF THE MACHINE (egress). Opt-in per familiar, surfaced in the affordance and
# logged. The local-first default ships none of these; a keeper wires one in deliberately.
_EGRESS_CATALOG: dict[str, Tool] = {
    "web": Tool(name="web", description='search the wider web — LEAVES THE MACHINE — act do: "use web <what you want to know>"', call=_web, egress=True),
}


def build_tool_scope(spec: Any, *, memory_dir: Any = None, file_scope: Any = None) -> ToolScope:
    """Build a ToolScope from a familiar.json ``tools`` value: a list of built-in local tool
    names (P0). Unknown names are skipped. (P1 extends this to MCP server specs.)

    Auto-granted reaches (no ``tools`` config needed), each on the safe inward/read-only corner:
    - ``memory_dir`` → **recall**: retrospection over the familiar's own past — *every* familiar,
      FileScope or not, so even a mind with no files can look back over the life it has accrued.
    - ``file_scope`` → **search**: content-search across the files already in its reach (code-search
      for a code-reader, file-search for anyone); and **git**: a read-only history lens, but only when
      a read-root is actually a git repo (the work's own memory, for a mind that reads the work)."""
    tools: list[Tool] = []
    if memory_dir is not None:
        tools.append(_make_recall(memory_dir))
    if file_scope is not None and getattr(file_scope, "roots", None):
        tools.append(_make_search(file_scope))
        repo = _git_root(file_scope)
        if repo is not None and shutil.which("git"):
            tools.append(_make_git(repo, file_scope))
    if spec:
        if isinstance(spec, (str, dict)):
            spec = [spec]
        catalog = {**_LOCAL_CATALOG, **_EGRESS_CATALOG}  # egress tools are opt-in by name, same as local ones
        tools += [catalog[str(n)] for n in spec if isinstance(n, str) and str(n) in catalog]
        # prune is bound to the familiar's own memory_dir (not a static catalog tool), and is more
        # consequential than recall (it changes what's carried), so it is opt-in per familiar by name
        # — never auto-granted. Self-only, soft, reversible (see _prune).
        if memory_dir is not None and any(isinstance(n, str) and str(n).lower() in {"prune", "forget"} for n in spec):
            tools.append(_make_prune(memory_dir))
    return ToolScope(tools)


# --- MCP provider (P1): keeper-wired tool servers become Tool objects -----------------------

def _mcp_specs(spec: Any) -> list[MCPServerSpec]:
    """Parse MCP server specs out of a familiar.json ``tools`` value. An MCP entry is a dict
    ``{"mcp": {"name", "command": [...], "cwd"?, "env"?, "egress"?, "expose"?}}``."""
    items = [spec] if isinstance(spec, (str, dict)) else list(spec or [])
    out: list[MCPServerSpec] = []
    for item in items:
        if not (isinstance(item, dict) and isinstance(item.get("mcp"), dict)):
            continue
        m = item["mcp"]
        cmd = m.get("command")
        if not cmd:
            continue
        out.append(MCPServerSpec(
            name=str(m.get("name") or "mcp"),
            command=[os.path.expanduser(str(c)) for c in cmd],
            cwd=os.path.expanduser(str(m["cwd"])) if m.get("cwd") else None,
            env=m.get("env") if isinstance(m.get("env"), dict) else None,
            egress=bool(m.get("egress")),
            expose=[str(x) for x in (m.get("expose") or [])],
        ))
    return out


def _args_from_text(input_schema: dict[str, Any], text: str) -> dict[str, Any]:
    """Map the familiar's free-text input to a tool's arguments (P1, best-effort): the whole
    text goes to the tool's single/primary string parameter. Multi-arg tools get the text in
    their first required (or first) property; a no-arg tool gets ``{}``."""
    props = (input_schema or {}).get("properties") or {}
    required = (input_schema or {}).get("required") or []
    key = required[0] if required else (next(iter(props), None))
    return {str(key): text} if key else {}


async def attach_mcp_tools(scope: ToolScope, spec: Any) -> ToolScope:
    """Discover the tools each keeper-wired MCP server offers (at boot) and add them to the
    scope. Each becomes a Tool whose call dispatches to the server via the stdio client. Failures
    are logged and skipped — a missing or broken server never blocks the familiar from waking."""
    for srv in _mcp_specs(spec):
        try:
            discovered = await list_tools(srv)
        except Exception as exc:  # discovery is best-effort
            logger.warning("[mcp:%s] tool discovery failed: %s", srv.name, exc)
            continue
        for t in discovered:
            name = str(t.get("name") or "").strip()
            if not name:
                continue
            schema = t.get("inputSchema") or {}
            desc = str(t.get("description") or "").strip() or name

            def _bind(tool_name: str, tool_schema: dict[str, Any], server: MCPServerSpec) -> Callable[[str], Any]:
                async def _call(text: str) -> str:
                    return await call_tool(server, tool_name, _args_from_text(tool_schema, text))
                return _call

            scope.add([Tool(name=name, description=desc, call=_bind(name, schema, srv), egress=srv.egress)])
    return scope
