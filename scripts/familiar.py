#!/usr/bin/env python3
"""Run a WorldWeaver resident as a local desktop familiar.

The same CognitiveCore that lives in the city — substrate, predictive pulse,
habituation, the slow self-model, circadian rhythm, the workshop — but grounded
in *this* machine's clock and kept company by one keeper. Each tick it writes a
small ``state.json`` (its felt sense, mood, what it's making, whether it's awake)
for a portrait UI to read, and it hears whatever the keeper appends to
``whispers.jsonl``.

Usage (from ww_agent/):

    # offline smoke test (deterministic stub mind, a few ticks):
    ../worldweaver_engine/.venv/bin/python scripts/familiar.py --ticks 4 --pause 0.2

    # live, against a local Ollama, as a daemon:
    export WW_INFERENCE_URL=http://localhost:11434/v1 WW_INFERENCE_KEY=ollama \
           WW_INFERENCE_MODEL=qwen2.5:7b-instruct
    ../worldweaver_engine/.venv/bin/python scripts/familiar.py --tick 30

Whisper to it from anywhere:
    echo '{"ts":"'$(date -Iseconds)'","text":"Cinder, are you there?"}' \
        >> familiar/cinder/whispers.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.familiar.file_scope import FileScope  # noqa: E402
from src.familiar.local_world import LocalWorld  # noqa: E402
from src.familiar.tool_scope import attach_mcp_tools, build_tool_scope  # noqa: E402
from src.familiar.weather import WeatherProvider  # noqa: E402
from src.identity.loader import IdentityLoader  # noqa: E402
from src.inference.client import model_accepts_images  # noqa: E402
from src.runtime.circadian import chronotype, circadian_state  # noqa: E402
from src.runtime.cognitive_core import CognitiveCore  # noqa: E402
from src.runtime.ledger import load_runtime_events  # noqa: E402
from src.runtime.memory import memories as kept_memories  # noqa: E402
from src.runtime.workshop import Workshop  # noqa: E402


# --------------------------------------------------------------------------
# A deterministic offline mind, so the familiar runs with no creds at all.
# --------------------------------------------------------------------------
import re  # noqa: E402

_FELT_LINE = re.compile(r"^\s*(\w+): \w[\w ]*\(([0-9.]+)\)\s*$", re.MULTILINE)


class _StubMind:
    """Not intelligent — echoes the felt substrate so the rhythm visibly runs,
    answers a whisper, and potters a journal line when settling."""

    async def complete_json(self, system_prompt, user_prompt, **kwargs):
        feats = {tag: min(float(val), 1.0) for tag, val in _FELT_LINE.findall(user_prompt)} or {"rest_drive": 0.4}
        top = max(feats, key=feats.get)
        act = None
        if "(to you)" in user_prompt or "spoke to you" in user_prompt:
            act = {"kind": "speak", "body": "Mm. I'm here — by the warm part of the machine.", "target": None}
        elif "this still moment is yours" in user_prompt:
            act = {"kind": "write", "body": "Quiet hour. The light's gone the colour of dishwater. Banked the embers; noted the hush.", "target": "journal"}
        return {"felt_sense": f"[stub] {top} sits closest to the surface", "act": act, "expectations": [{"features": feats, "scope": "self", "confidence": 0.9, "half_life": 600}]}

    async def complete(self, *a, **k):
        return "{}"

    async def close(self):
        return None


def _familiar_config(home_dir: Path) -> dict:
    """Per-familiar settings (familiar.json): its own model, place, keeper. Lets a
    stable of familiars each run on a different mind from one launcher."""
    path = home_dir / "familiar.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _make_mind(model_override: str | None = None, key_env: str | None = None):
    # A familiar may name its own key env var ("key_env" in familiar.json) so a group of them
    # (e.g. the book ecology) can bill to a separate key; falls back to the shared WW_INFERENCE_KEY.
    key = (os.environ.get(key_env, "").strip() if key_env else "") or os.environ.get("WW_INFERENCE_KEY", "").strip()
    model = (model_override or os.environ.get("WW_INFERENCE_MODEL", "qwen2.5:7b-instruct")).strip()
    if not key:
        want = key_env or "WW_INFERENCE_KEY"
        return _StubMind(), f"stub (offline — set {want} for the real mind; wanted {model})"
    from src.inference.client import InferenceClient

    url = os.environ.get("WW_INFERENCE_URL", "http://localhost:11434/v1")
    timeout = float(os.environ.get("WW_INFERENCE_TIMEOUT", "200"))
    return InferenceClient(base_url=url, api_key=key, default_model=model, timeout=timeout), f"{model} @ {url}"


# --------------------------------------------------------------------------


def _last_pulse(memory_dir: Path) -> dict | None:
    latest = None
    for event in load_runtime_events(memory_dir):
        if str(event.get("event_type") or "").strip() == "pulse_emitted":
            latest = (event.get("payload") or {}).get("pulse")
    return latest


def _journal_tail(home_dir: Path) -> str:
    candidates = list((home_dir / "workshop").glob("*.md"))
    if not candidates:
        return ""
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    try:
        body = newest.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    section = body.split("## ")[-1].strip()
    # drop the timestamp heading line if present
    lines = [ln for ln in section.splitlines() if ln.strip()]
    if lines and lines[0].count(":") >= 2 and lines[0].replace(":", "").replace("-", "").replace("T", "").replace("+", "").replace(".", "").strip().isdigit():
        lines = lines[1:]
    return " ".join(lines).strip()[:1200]


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _recent_exchange(home_dir: Path, n: int = 40) -> list[dict]:
    """The persistent back-and-forth: the keeper's whispers and her spoken replies — PLUS the
    familiar's own actions (tool calls, reads) tagged ``kind: "do"`` so the portrait can fold the
    process into a collapsible between the conversation, instead of flooding the thread with it.
    Merged in time order; the UI groups consecutive ``do`` items into one expandable artifact."""
    turns: list[dict] = []
    for w in _read_jsonl(home_dir / "whispers.jsonl"):
        if w.get("text"):
            turns.append({"who": "you", "kind": "whisper", "text": str(w["text"]).strip(), "ts": str(w.get("ts") or "")})
    for v in _read_jsonl(home_dir / "voice.jsonl"):
        kind = v.get("kind")
        if kind in ("speak", "do") and v.get("text"):
            turns.append({"who": "her", "kind": kind, "text": str(v["text"]).strip(), "ts": str(v.get("ts") or "")})

    def _key(t):
        try:
            return datetime.fromisoformat(t["ts"]).timestamp()
        except (ValueError, TypeError):
            return 0.0

    turns.sort(key=_key)
    return turns[-n:]


def _mood(*, awake: bool, ignited: bool, settled: bool, fervor: bool, arousal: float, rest: float) -> str:
    if fervor:
        return "in a fervor"
    if settled:
        return "at rest" if rest > 0.5 else "pottering"
    if ignited:
        return "stirred"
    if not awake:
        return "drowsing"
    if arousal >= 0.6:
        return "watchful"
    if arousal >= 0.25:
        return "attentive"
    return "quiet"


_FILESCOPE_CACHE: dict[str, tuple[float, dict]] = {}


def _filescope_summary(world: LocalWorld) -> dict | None:
    """What this familiar may read, for the portrait's FileScope viewer: each root
    and a shallow tree of its non-ignored entries (secrets & .gitignore already
    hidden by FileScope itself). Recomputed at most once a minute — the filesystem
    walk is bounded, but not worth doing every tick."""
    fs = getattr(world, "_file_scope", None)
    if fs is None or not getattr(fs, "roots", None):
        return None
    key = str(world.home_dir)
    nowt = datetime.now(timezone.utc).timestamp()
    cached = _FILESCOPE_CACHE.get(key)
    if cached and nowt - cached[0] < 60.0:
        return cached[1]
    roots = []
    for root in fs.roots:
        try:
            entries = fs.tree(str(root), max_depth=2, max_entries=80)
        except Exception:
            entries = []
        roots.append({"name": root.name, "path": str(root), "entries": entries})
    summary = {"roots": roots, "note": "read-only · secrets & .gitignore hidden"}
    _FILESCOPE_CACHE[key] = (nowt, summary)
    return summary


def _toolscope_summary(world: LocalWorld) -> dict | None:
    """What this familiar may USE, for the portrait's tools viewer — the read/fetch-only tools
    it can reach for, each marked whether it leaves the machine (egress). The human twin of the
    FileScope viewer: see at a glance what reach the keeper has given a familiar."""
    ts = getattr(world, "_tool_scope", None)
    if not ts:
        return None
    tools = [{"name": t.name, "description": t.description, "egress": bool(t.egress)} for t in ts.list()]
    return {"tools": tools, "any_egress": any(t["egress"] for t in tools), "note": "read/fetch-only · local unless marked egress"}


def _write_state(state_path: Path, *, identity, world: LocalWorld, brief: dict, result: dict, tick: int) -> dict:
    g = brief.get("grounding") or {}
    wake = float(brief.get("wakefulness") if brief.get("wakefulness") is not None else 1.0)
    ct = chronotype(identity.name, explicit=_familiar_config(world.home_dir).get("chronotype"))
    rest = float((g.get("rest_pressure") if isinstance(g, dict) else None) or 0.0)
    pulse = _last_pulse(world.home_dir / "memory") or {}
    awake = wake >= 0.4
    spoken = world.spoken[-1]["text"] if world.spoken else None
    shop = Workshop(world.home_dir / "workshop")
    state = {
        "name": identity.display_name,
        "place": world.place,
        "tick": tick,
        "ts": datetime.now(timezone.utc).isoformat(),
        "local_time": datetime.now().astimezone().strftime("%H:%M"),
        "time_of_day": g.get("time_of_day"),
        "day_of_week": g.get("day_of_week"),
        "weather": g.get("weather") or "",
        "chronotype": round(ct, 2),
        "chronotype_kind": "lark" if ct < -0.5 else "owl" if ct > 0.5 else "even",
        "wakefulness": round(wake, 3),
        "awake": awake,
        "arousal": round(float(result.get("arousal_level") or 0.0), 3),
        "ignited": bool(result.get("ignited")),
        "settled": bool(result.get("settled")),
        "fervor": bool(result.get("fervor")),
        "mood": _mood(awake=awake, ignited=bool(result.get("ignited")), settled=bool(result.get("settled")), fervor=bool(result.get("fervor")), arousal=float(result.get("arousal_level") or 0.0), rest=rest),
        "felt_sense": pulse.get("felt_sense") or "",
        "act": pulse.get("act"),
        "last_spoken": spoken,
        "journal_tail": _journal_tail(world.home_dir),
        "workshop": shop.summary(),
        "drawings": shop.drawings(limit=6),
        "memories": [{"note": m["note"], "ts": m.get("kept_ts")} for m in kept_memories(world.home_dir / "memory", limit=200)],
        "exchange": _recent_exchange(world.home_dir),
        "filescope": _filescope_summary(world),
        "toolscope": _toolscope_summary(world),
        "anchor_gating": bool(_familiar_config(world.home_dir).get("anchor_gating")),
    }
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return state


async def _run(args) -> None:
    # Legible logs (timestamps + the pulse warnings — dropped/salvaged/inference) rather than silence.
    # wake-all.sh sends stdout+stderr to a per-familiar daemon.log; here we just set the level/format.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # one INFO line per HTTP call is noise — keep ours + warnings
    home_dir = Path(args.home).resolve()
    if not home_dir.is_absolute():
        home_dir = Path(__file__).resolve().parent.parent / args.home
    if not (home_dir / "identity").exists():
        print(f"no familiar at {home_dir} (need identity/SOUL.canonical.md)")
        return

    identity = IdentityLoader.load(home_dir)
    cfg = _familiar_config(home_dir)
    place = str(cfg.get("place") or args.place)
    keeper = str(cfg.get("keeper") or args.keeper)
    weather = None if args.no_weather else WeatherProvider()
    read_roots = list(cfg.get("read_roots") or [])
    # Every familiar can revisit gifts the keeper has left it: workshop/given/ is always a read
    # root, even if the familiar has no broader file scope. Gift *delivery* reads given/ directly
    # (the given channel works regardless), but re-opening a gift by path later needs FileScope.
    given_dir = home_dir / "workshop" / "given"
    given_dir.mkdir(parents=True, exist_ok=True)
    # Prepend (not append): a gift lives under workshop/, which a broad workspace read-root
    # would otherwise claim first and hide via the repo's `workshop/` gitignore.
    read_roots.insert(0, str(given_dir))
    file_scope = FileScope(read_roots=read_roots)
    tool_scope = build_tool_scope(cfg.get("tools"), memory_dir=home_dir / "memory", file_scope=file_scope)  # recall for all; search + git lens for FileScope-havers
    await attach_mcp_tools(tool_scope, cfg.get("tools"))  # discover keeper-wired MCP servers' tools
    # Sight (Major 55): can this familiar see images? An explicit "vision" in familiar.json wins;
    # otherwise infer from the model id (conservative — unknown models are text-only).
    resolved_model = (args.model or "").strip() or cfg.get("model") or ""
    vision = bool(cfg["vision"]) if cfg.get("vision") is not None else model_accepts_images(resolved_model)
    world = LocalWorld(home_dir=home_dir, place=place, keeper_name=keeper, familiar_name=identity.display_name, weather_provider=weather, file_scope=file_scope, tool_scope=tool_scope or None, vision=vision)
    mind, label = _make_mind(resolved_model or None, key_env=(cfg.get("key_env") or None))
    if file_scope is not None:
        print(f"· read scope: {', '.join(str(r) for r in file_scope.roots)} (read-only; secrets & .gitignore hidden)")
        print(f"· sight: {'ON — can see images & rendered PDF pages' if vision else 'text-only — PDFs read as text, images noted but unseen'}")
    if tool_scope:
        print(f"· tools: {', '.join(tool_scope.names)}{'  (includes EGRESS)' if tool_scope.has_egress else '  (local, no egress)'}")
    ct = chronotype(identity.name, explicit=cfg.get("chronotype"))
    kind = "lark" if ct < -0.5 else "owl" if ct > 0.5 else "even-keeled"
    print(f"· waking {identity.display_name} at {world.place}  ·  mind: {label}")
    print(f"· chronotype {ct:+.1f}h ({kind})  ·  it is {datetime.now().astimezone().strftime('%H:%M')} — wakefulness {circadian_state(datetime.now().hour, ct)['wakefulness']:.2f}")
    print(f"· whisper to it:  echo '{{\"ts\":\"...\",\"text\":\"...\"}}' >> {home_dir / 'whispers.jsonl'}")

    anchor_gating = bool(cfg.get("anchor_gating"))
    if anchor_gating:
        print("· anchor-gating ON (experimental): drive-resonant concrete anchors may drive arousal")
    clean_drive_nudges = bool(cfg.get("clean_drive_nudges"))
    if clean_drive_nudges:
        print("· clean drive_nudges ON: the phantom 'curiosity' example is dropped from the pulse schema")
    core = CognitiveCore(
        identity=identity,
        resident_dir=home_dir,
        ww_client=world,
        llm=mind,
        session_id=f"{identity.name}-hearth",
        tick_seconds=args.tick,
        writes_to_workshop_only=True,  # a solo familiar has no mail; all writes are its own work
        anchor_gating=anchor_gating,
        clean_drive_nudges=clean_drive_nudges,
        ignition_refractory_seconds=cfg.get("refractory_seconds"),
        pulse_vision=vision,
    )
    state_path = home_dir / "state.json"

    stop = asyncio.Event()
    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop.set)
    except (NotImplementedError, RuntimeError):
        pass

    def _latest_whisper_ts() -> str:
        whispers = _read_jsonl(home_dir / "whispers.jsonl")
        return str(whispers[-1].get("ts") or "") if whispers else ""

    # Don't answer whispers from before she woke; only new ones since boot.
    last_whisper_ts = _latest_whisper_ts()

    tick = 0
    try:
        while not stop.is_set():
            tick += 1
            cur_whisper_ts = _latest_whisper_ts()
            addressed = bool(cur_whisper_ts) and cur_whisper_ts != last_whisper_ts
            last_whisper_ts = cur_whisper_ts
            result = await core.tick_once(force_ignite=addressed)
            brief = core._producer.latest_perception  # noqa: SLF001
            state = _write_state(state_path, identity=identity, world=world, brief=brief, result=result, tick=tick)
            mark = " ▲" if state["ignited"] else " ✦" if state.get("fervor") else " ❍" if state["settled"] else ""
            line = f"  {state['local_time']} {state['mood']:<10} arousal {state['arousal']:.2f}{mark}"
            if state["felt_sense"]:
                line += f"  — {state['felt_sense'][:70]}"
            print(line)
            if state.get("last_spoken"):
                print(f'             “{state["last_spoken"]}”')
            if args.ticks and tick >= args.ticks:
                break
            try:
                await asyncio.wait_for(stop.wait(), timeout=args.tick if not args.ticks else args.pause)
            except asyncio.TimeoutError:
                pass
    finally:
        # Growth distillation: promote mature self-delta proposals before shutdown.
        try:
            from src.runtime.growth import distill
            gr = await distill(home_dir, embedder=getattr(core, "_embedder", None))
            if gr.get("promoted"):
                print(f"· growth: {gr['promoted']} line(s) promoted to identity/soul_growth.md")
            elif gr.get("candidates"):
                print(f"· growth: {gr['candidates']} candidate(s), none mature yet ({gr.get('note', '')})")
        except Exception as exc:
            logger.warning("growth distillation failed at shutdown: %s", exc)
        if hasattr(mind, "close"):
            await mind.close()
        await world.close()
        print(f"· {identity.display_name} banks the embers. (state at {state_path})")


def main() -> None:
    p = argparse.ArgumentParser(description="Run a WorldWeaver resident as a local desktop familiar.")
    p.add_argument("--home", default="familiar/cinder", help="the familiar's home dir (holds identity/, memory/, workshop/)")
    p.add_argument("--place", default="the hearth")
    p.add_argument("--keeper", default="Levi")
    p.add_argument("--no-weather", action="store_true", help="don't fetch real local weather (blank sky)")
    p.add_argument("--model", default="", help="override the model in familiar.json (e.g. run a local familiar on a cloud slug)")
    p.add_argument("--tick", type=float, default=30.0, help="seconds between ticks (daemon cadence)")
    p.add_argument("--ticks", type=int, default=0, help="stop after N ticks (0 = run forever); uses --pause between them")
    p.add_argument("--pause", type=float, default=0.5, help="seconds between ticks when --ticks is set")
    asyncio.run(_run(p.parse_args()))


if __name__ == "__main__":
    main()
