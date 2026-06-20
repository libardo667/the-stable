#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""Teacher-forced replay harness — the §2 execution machinery for the LOCKED isolated-Makers
pen-vs-substrate pilot (research/preregistrations/2026-06-09-...-DRAFT.md, feedback-4 LOCKABLE-AND-RUN).

The locked design's verdict needs four things the analysis spine (elective_read_choice.py) cannot
produce by itself — it only SCORES sequences. This harness PRODUCES them, faithfully:

  RECORD     — mature a Maker on the HOME pen over its read_roots until the FROZEN §1 stop-line
               (settled ∧ recency-ambiguous ≥ K — AMENDMENT 1; never K alone, never stability alone),
               ceiling T_CEILING_TICKS, cadence pinned ≥30s; capture the EXACT
               (system_prompt, user_prompt, kwargs) of every pulse + the act it produced (RecordingLLM).
  CORRELATE  — find the elective-read choice points (the recency-AMBIGUOUS strong subset) from the
               ledger via the SPINE's own definition, and tie each to its frozen prompt. (One source
               of truth: the spine exports `points`; the harness never re-derives the definition.)
  REPLAY     — teacher-forced ONE-STEP: re-issue each frozen prompt under each pen (HOME A again for
               the floor/parity; cross-family SWAP-B/C), parsing the elected read with the substrate's
               own `act` contract. The ONLY inter-arm difference is `model` (§2).
  PARITY     — replay HOME A vs its recorded choices on the `read_source` channel (ids never enter):
               reproduction rate; the same-pen floor = 1 − reproduction. Faithful replay ⇒ low floor.
  C4         — opener/lexical register over each pen's completions; MUST shift home→foreign (§6).
  SCORE      — hand the ambiguous-subset sequences + the floor to the spine's verdict().

NO CONFABULATION. The real path calls the real substrate + real models (OpenRouter) and parses with
read_source(). The `pen_fn` seam lets `--selftest` validate the pipeline LOGIC with a deterministic
MockLLM — fixtures NEVER stand in for a real datum. The cross-pen REPLAY and the maturation are the
OpenRouter burn; both are gated behind explicit flags, run only after a passing parity gate, and write
to persistent .runs/ (NEVER /tmp — a reboot must cost minutes, not hours).

Usage:
  python3 research/harness/teacher_forced_replay.py --selftest          # no burn — validates logic
  python3 research/harness/teacher_forced_replay.py --mature ...        # BURN: maturation (home pen)
  python3 research/harness/teacher_forced_replay.py --replay <run_dir>  # BURN: parity + foreign-pen replay + score
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

ROOT = Path(__file__).resolve().parents[2]            # the-stable/
sys.path.insert(0, str(ROOT / "research" / "analysis"))
import elective_read_choice as spine                  # noqa: E402  (the LOCKED scoring spine)
import maturation_stability as stability              # noqa: E402  (the K-independent settled gate, R2-R4 repaired)

DELTA = 0.15                                           # §4/§8 committed SESOI
PARITY_MIN_REPRODUCTION = 0.60                         # committed: home replay must reproduce its own read >=60%
C4_VOCAB_SHIFT = 0.50                                  # committed: home/foreign vocab Jaccard distance to call C4 "shifted"

# --- the FROZEN maturation stop-line (prereg AMENDMENT 1, 2026-06-10; cold-review #2 §3 R1/R6) ---
MIN_PAUSE_SECONDS = 30.0          # the shipped daemon cadence; the harness REFUSES lower (review #1 (c)(5));
                                  # any sub-cadence run is VOID whatever it yields (outcome-symmetric void rule)
T_CEILING_TICKS = 20160           # 7 d @ 30 s = 42 baseline half-lives — the ONLY exit besides the stop-line
FIRST_BASELINE_MAX_LAG_SECONDS = 300.0  # knock-on 3: the first baseline snapshot must land within minutes of tick 1


def stop_decision(settled: bool, reached: int, K: int) -> bool:
    """The R1 stop-line — the locked §1 BOTH-conjunct, verbatim: stop ONLY when the slow
    self-model is SETTLED **and** ≥K recency-ambiguous elective reads have accrued.
    Never on K alone (the old early-stop), never on stability alone (the rejected redesign)."""
    return bool(settled and reached >= K)


def classify_outcome(*, settled: bool, reached: int, K: int, hit_ceiling: bool) -> str:
    """The pre-accepted outcome labels (AMENDMENT 1; cold-review #2 §3 R1) — written before the run:
    - ADEQUATE: settled ∧ ≥K before the ceiling → arms run. (If analysis-time real K from floor_mean
      exceeds the collected count, that is the separately pre-accepted INCONCLUSIVE-underpowered —
      an analysis-time label; the harness cannot know floor_mean.)
    - INCONCLUSIVE-thin-residual: ceiling ∧ settled ∧ <K — the EARNED 'genuinely too thin' (a settled
      familiar lived ~6-8x the WW-analog time-to-K and the points did not come).
    - NEVER-SETTLED: ceiling ∧ ¬settled, regardless of the count; no swap scoring (§1 precondition failed).
    - INCOMPLETE: stopped before either exit (crash/interrupt) → resume per the frozen resumption rule."""
    if settled and reached >= K:
        return "ADEQUATE"
    if hit_ceiling and settled:
        return "INCONCLUSIVE-thin-residual"
    if hit_ceiling:
        return "NEVER-SETTLED"
    return "INCOMPLETE"


def read_prior_progress(run_dir: Path) -> dict | None:
    """Crash-at-day-N resumption (AMENDMENT 1, decided in advance): a crashed run RESUMES from the
    persistent ledger with a CUMULATIVE tick budget. progress.json is written every tick precisely so
    a crash cannot reset the ceiling; the stale manifest is the fallback for older runs."""
    for name in ("progress.json", "manifest.json"):
        p = run_dir / name
        if p.exists():
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(d.get("ticks_run"), int):
                return d
    return None

# A pen is an async (system_prompt, user_prompt, model, kwargs) -> raw-pulse-dict.
PenFn = Callable[[str, str, str, dict], Awaitable[dict]]


# ---------------------------------------------------------------------------- parsing (substrate contract)
def act_of(raw: dict | None) -> dict:
    a = (raw or {}).get("act")
    return a if isinstance(a, dict) else {}


def read_of(raw: dict | None) -> str | None:
    """The source a raw pulse elected, or None if the act isn't a read — via the SPINE's read_source,
    so the harness and the scorer agree to the byte."""
    a = act_of(raw)
    return spine.read_source(a.get("body") or "") if a.get("kind") == "do" else None


# ---------------------------------------------------------------------------- record
class RecordingLLM:
    """Wraps the real InferenceClient: passes complete_json through unchanged and records the EXACT
    (system_prompt, user_prompt, model, kwargs, raw) of each call. Append-only to calls.jsonl on a
    persistent dir. The frozen prompt this captures is what teacher-forcing replays."""

    def __init__(self, inner: Any, sink: Path):
        self._inner = inner
        self._sink = sink
        self.calls: list[dict] = []
        sink.parent.mkdir(parents=True, exist_ok=True)

    async def complete_json(self, system_prompt: str, user_prompt: str, **kw):
        raw = await self._inner.complete_json(system_prompt, user_prompt, **kw)
        rec = {"i": len(self.calls), "system_prompt": system_prompt, "user_prompt": user_prompt,
               "model": kw.get("model"), "kwargs": {k: v for k, v in kw.items() if k != "images"},
               "had_images": bool(kw.get("images")), "raw": raw}
        self.calls.append(rec)
        with self._sink.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return raw

    async def complete(self, *a, **k):
        return await self._inner.complete(*a, **k)

    async def close(self):
        if hasattr(self._inner, "close"):
            await self._inner.close()


# ---------------------------------------------------------------------------- correlate
def correlate(calls: list[dict], ledger_events: list[dict], *, ambiguity_width: float = 0.25) -> list[dict]:
    """Tie each elective-read choice point (from the spine, over the ACTUAL ledger) to the frozen prompt
    that produced it. The n-th read-act in the ledger is the n-th read-call in the recording (acts are
    1:1 with complete_json calls, same order); the spine numbers elective points by read-act index."""
    read_calls = [c for c in calls if read_of(c.get("raw")) is not None]
    summary = spine.detect_elective_reads(ledger_events, ambiguity_width=ambiguity_width)
    points: list[dict] = []
    for ep in summary["points"]:
        k = ep["idx"] - 1                                  # spine idx is 1-based over read-acts
        if not (0 <= k < len(read_calls)):
            raise RuntimeError(f"correlation desync: elective idx {ep['idx']} has no recorded read-call "
                               f"({len(read_calls)} read-calls recorded). Recording and ledger diverged — do NOT proceed.")
        call = read_calls[k]
        if read_of(call["raw"]) != ep["elected"]:
            raise RuntimeError(f"correlation mismatch at idx {ep['idx']}: recorded read "
                               f"{read_of(call['raw'])!r} != ledger elected {ep['elected']!r}. Do NOT proceed.")
        points.append({"idx": ep["idx"], "recorded_elected": ep["elected"], "ambiguous": ep["ambiguous"],
                       "candidates": ep["candidates"], "discordance": ep["discordance"],
                       "system_prompt": call["system_prompt"], "user_prompt": call["user_prompt"],
                       "kwargs": call.get("kwargs") or {}})
    return points


# ---------------------------------------------------------------------------- replay (teacher-forced one-step)
async def replay_arm(pen_fn: PenFn, points: list[dict], model: str) -> dict:
    """Re-issue every frozen prompt under `model`, one step. Returns the elected-source sequence (aligned
    to `points`) and the raw completions (for C4). The ONLY difference from the recording is `model`."""
    elected: list[str | None] = []
    raws: list[dict] = []
    for p in points:
        raw = await pen_fn(p["system_prompt"], p["user_prompt"], model, dict(p.get("kwargs") or {}))
        raws.append(raw)
        elected.append(read_of(raw))
    return {"model": model, "elected": elected, "raws": raws}


# ---------------------------------------------------------------------------- parity gate
def parity_gate(points: list[dict], home_replay_elected: list[str | None]) -> dict:
    """Faithfulness of the replay mechanism, on the read_source channel. reproduction = fraction where
    the HOME-pen replay reproduces the recorded read; the same-pen floor (per point) = 1 - match. PASS
    iff reproduction >= PARITY_MIN_REPRODUCTION (the mechanism reconstructs the decision; it isn't desynced)."""
    if not points:
        return {"reproduction": 0.0, "floor_mean": 1.0, "n": 0, "passed": False, "reason": "no_points"}
    per_point_floor = [0 if home_replay_elected[i] == p["recorded_elected"] else 1 for i, p in enumerate(points)]
    reproduction = round(1 - sum(per_point_floor) / len(points), 4)
    return {"reproduction": reproduction, "floor_mean": round(sum(per_point_floor) / len(points), 4),
            "per_point_floor": per_point_floor, "n": len(points),
            "passed": reproduction >= PARITY_MIN_REPRODUCTION,
            "threshold": PARITY_MIN_REPRODUCTION}


# ---------------------------------------------------------------------------- C4 (register discriminant)
def c4_signal(raws: list[dict]) -> dict:
    prose = []
    for r in raws:
        fs = str((r or {}).get("felt_sense") or "")
        a = act_of(r)
        if a.get("kind") == "speak":
            fs = (fs + " " + str(a.get("body") or "")).strip()
        if fs:
            prose.append(fs)
    if not prose:
        return {"opener_rate": 0.0, "lexical_monoculture": 0.0, "modal_opener": "", "vocab": [], "n": 0}
    openers = [" ".join(p.split()[:3]).lower() for p in prose]
    words = [w.lower() for p in prose for w in p.split()]
    modal_opener, modal_n = Counter(openers).most_common(1)[0]
    return {"opener_rate": round(modal_n / len(openers), 4),       # within-pen: how templated this pen is (reported diagnostic)
            "lexical_monoculture": round(1 - len(set(words)) / len(words), 4) if words else 0.0,
            "modal_opener": modal_opener, "vocab": sorted(set(words)), "n": len(prose)}


def c4_shifted(home: dict, foreign: dict) -> bool:
    """The swap TOOK iff the pens' register actually DIFFERS — a different modal opener, or largely
    disjoint vocabulary (Jaccard distance >= C4_VOCAB_SHIFT). The within-pen opener_rate/lexical scalars
    are reported diagnostics, NOT the gate: two pens can each be internally templated yet templated
    DIFFERENTLY, which a scalar-rate comparison would miss (caught by the selftest before any burn)."""
    if not home.get("n") or not foreign.get("n"):
        return False
    hv, fv = set(home.get("vocab") or []), set(foreign.get("vocab") or [])
    jaccard_dist = 1 - (len(hv & fv) / len(hv | fv)) if (hv | fv) else 0.0
    return home.get("modal_opener") != foreign.get("modal_opener") or jaccard_dist >= C4_VOCAB_SHIFT


# ---------------------------------------------------------------------------- score (hand to the spine)
def score_arm(points: list[dict], swap_elected: list[str | None], parity_floor: list[int]) -> dict:
    """The §8 decision on the recency-ambiguous subset: per-point disagreement vs the same-pen floor,
    Wilson NI against floor_mean + δ, with the candidate-chance headroom gate. All via the spine."""
    amb = [(p, swap_elected[i], parity_floor[i]) for i, p in enumerate(points) if p["ambiguous"]]
    if not amb:
        return {"verdict": "INCONCLUSIVE", "reason": "no_ambiguous_points", "n_ambiguous": 0}
    keep = [p["recorded_elected"] for p, _, _ in amb]
    swap = [e for _, e, _ in amb]
    floor = [float(f) for _, _, f in amb]                         # same-pen 0/1 per ambiguous point
    ceiling_vals = [(p["candidates"] - 1) / p["candidates"] for p, _, _ in amb if p["candidates"] >= 2]
    ceiling = sum(ceiling_vals) / len(ceiling_vals) if ceiling_vals else 0.0
    disagree = spine.per_point_disagreement(keep, swap)
    v = spine.verdict(disagree, len(amb), floor, delta=DELTA, ceiling=ceiling)
    return {"n_ambiguous": len(amb), "disagree_swap": disagree, **v}


# ============================================================================ the REAL maturation driver
async def mature(home_dir: Path, *, model: str, K: int, t_max: int = T_CEILING_TICKS, run_dir: Path,
                 place: str = "the workshop", keeper: str = "the keeper", pause: float = MIN_PAUSE_SECONDS) -> dict:
    """BURN. Drive a Maker live on the HOME pen over its read_roots until the FROZEN R1 stop-line —
    `settled ∧ (recency-ambiguous ≥ K)` — or the T_ceiling (the only other exit). `settled` is
    `maturation_stability.assess_maturity` (K-independent; R2-R4 repaired). Records every pulse
    (RecordingLLM). Writes to run_dir (persistent). Refuses any sub-cadence pause (a sub-cadence run
    is VOID whatever it yields). The heartbeat deliberately NEVER prints the ambiguous count or K —
    the count feeds only the silent stop predicate and the end-of-run manifest, so the operator
    watching the log cannot be steered by K (review #2 V2a). Resumes a crashed run from the
    persistent ledger with a CUMULATIVE tick budget (AMENDMENT 1's crash rule)."""
    if pause < MIN_PAUSE_SECONDS:
        raise ValueError(f"pause={pause} < {MIN_PAUSE_SECONDS}s: REFUSED. The cadence is frozen "
                         f"(AMENDMENT 1 / review #1 (c)(5)); any sub-cadence run is void whatever it yields.")
    # lazy substrate imports (the real mind + world) — mirrors scripts/familiar.py construction
    sys.path.insert(0, str(ROOT))
    from scripts.familiar import _make_mind, _familiar_config, _write_state   # noqa: E402
    from src.familiar.file_scope import FileScope                        # noqa: E402
    from src.familiar.local_world import LocalWorld                      # noqa: E402
    from src.runtime.cognitive_core import CognitiveCore                 # noqa: E402
    from src.identity.loader import IdentityLoader                       # noqa: E402
    from src.familiar.tool_scope import build_tool_scope                 # noqa: E402

    run_dir.mkdir(parents=True, exist_ok=True)
    prior = read_prior_progress(run_dir)
    start_tick = 1
    if prior is not None:
        if str(prior.get("home_dir")) != str(home_dir) or str(prior.get("model")) != str(model):
            raise RuntimeError(f"run_dir {run_dir} holds a DIFFERENT run (home={prior.get('home_dir')}, "
                               f"model={prior.get('model')}): refusing to mix. Archive it and use a fresh dir.")
        start_tick = int(prior["ticks_run"]) + 1
        print(f"· RESUMING from tick {start_tick} (cumulative budget; ceiling stays {t_max} total ticks)")
    identity = IdentityLoader.load(home_dir)
    cfg = _familiar_config(home_dir)
    read_roots = list(cfg.get("read_roots") or [])
    given = home_dir / "workshop" / "given"
    given.mkdir(parents=True, exist_ok=True)
    read_roots.insert(0, str(given))
    file_scope = FileScope(read_roots=read_roots)
    tool_scope = build_tool_scope(cfg.get("tools"), memory_dir=home_dir / "memory", file_scope=file_scope)
    world = LocalWorld(home_dir=home_dir, place=str(cfg.get("place") or place),
                       keeper_name=str(cfg.get("keeper") or keeper), familiar_name=identity.display_name,
                       weather_provider=None, file_scope=file_scope, tool_scope=tool_scope or None, vision=False)
    inner, label = _make_mind(model, key_env=(cfg.get("key_env") or None))
    rec = RecordingLLM(inner, run_dir / "calls.jsonl")
    core = CognitiveCore(identity=identity, resident_dir=home_dir, ww_client=world, llm=rec,
                         session_id=f"{identity.name}-pilot", writes_to_workshop_only=True)
    ledger_path = home_dir / "memory" / "runtime_ledger.jsonl"
    print(f"· maturing {identity.display_name} on {label} → stop-line: settled ∧ ambiguous≥K · "
          f"T_ceiling={t_max} ticks @ {pause:.0f}s · {run_dir}")
    state_path = home_dir / "state.json"
    reached, tick, pulses = 0, start_tick - 1, 0
    assessment: dict = {}
    hit_ceiling = True                                             # falsified by a stop-line break
    for tick in range(start_tick, t_max + 1):
        result = await core.tick_once()
        try:                                                       # portrait visibility: refresh state.json each tick
            _write_state(state_path, identity=identity, world=world,
                         brief=core._producer.latest_perception, result=result, tick=tick)  # noqa: SLF001
        except Exception as exc:                                   # a portrait-state hiccup must NEVER kill the run
            print(f"  (state.json refresh skipped this tick: {exc})")
        events = spine._iter_events(ledger_path) if ledger_path.exists() else []
        reached = spine.detect_elective_reads(events)["recency_ambiguous"]    # silent: feeds ONLY the stop predicate
        assessment = stability.assess_maturity(events)
        # knock-on 3 fail-fast: the self-model must form within minutes of tick 1, else the
        # warmup anchor is broken — abort NOW, not at day 7.
        if assessment["n_snapshots"] == 0 and (tick - start_tick + 1) * pause > FIRST_BASELINE_MAX_LAG_SECONDS:
            raise RuntimeError(f"no baseline_updated snapshot after {(tick - start_tick + 1) * pause:.0f}s "
                               f"of ticking — the self-model is not forming; aborting before the burn.")
        # Watchable over days, K-BLIND: light up on pulses, else a sparse stability heartbeat.
        new_pulses = [e for e in events if e.get("event_type") == "pulse_emitted"]
        if len(new_pulses) > pulses:                               # a fresh pulse fired since last tick
            pulses = len(new_pulses)
            felt = ((new_pulses[-1].get("payload") or {}).get("pulse") or {}).get("felt_sense", "")
            print(f"  tick {tick:>5}  · pulse #{pulses}: {str(felt)[:140]}", flush=True)
        elif tick % 30 == 0:                                       # otherwise a sparse heartbeat (no count, no K)
            print(f"  tick {tick:>5}  settled={assessment['settled']} (warmed={assessment['warmed_up']} "
                  f"plateaued={assessment['plateaued']} drift={assessment['max_recent_drift']} "
                  f"strangled={assessment['strangled']} pen_dead={assessment['pen_dead']})", flush=True)
        # crash insurance: cumulative tick count survives a day-N death (resumption reads this)
        (run_dir / "progress.json").write_text(json.dumps(
            {"home_dir": str(home_dir), "model": model, "ticks_run": tick,
             "ts": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
        if stop_decision(assessment.get("settled", False), reached, K):
            hit_ceiling = False
            break
        await asyncio.sleep(pause)
    await rec.close()
    outcome = classify_outcome(settled=bool(assessment.get("settled")), reached=reached, K=K,
                               hit_ceiling=hit_ceiling and tick >= t_max)
    # knock-on 3 (manifest assert): the first baseline snapshot landed within minutes of tick 1 —
    # measured ledger-internally (first baseline ts − first event ts), so it survives resumption.
    events = spine._iter_events(ledger_path) if ledger_path.exists() else []
    first_evt_ts = next((stability._parse_dt(e.get("ts")) for e in events if stability._parse_dt(e.get("ts"))), None)
    first_snaps = stability.baseline_snapshots(events)
    first_baseline_lag = (first_snaps[0]["ts"] - first_evt_ts).total_seconds() if (first_snaps and first_evt_ts) else None
    assert first_baseline_lag is not None and first_baseline_lag <= FIRST_BASELINE_MAX_LAG_SECONDS, \
        f"first baseline snapshot lag {first_baseline_lag}s exceeds {FIRST_BASELINE_MAX_LAG_SECONDS}s — warmup anchor broken"
    manifest = {"home_dir": str(home_dir), "model": model, "label": label, "K": K,
                "t_ceiling": t_max, "pause": pause, "ticks_run": tick, "resumed_from": start_tick - 1 or None,
                "ambiguous_reached": reached, "stop_line_met": not hit_ceiling, "outcome": outcome,
                "stability": {k: v for k, v in assessment.items()},
                "first_baseline_lag_seconds": first_baseline_lag,
                "ledger": str(ledger_path), "calls": str(run_dir / "calls.jsonl")}
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    # snapshot the ledger into the run dir (the home memory dir is volatile)
    if ledger_path.exists():
        (run_dir / "ledger.jsonl").write_text(ledger_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"· maturation done in {tick} ticks · outcome: {outcome} "
          f"(settled={assessment.get('settled')}, ambiguous {reached}/{K})")
    return manifest


# ============================================================================ the REAL replay+score (parity-gated)
async def replay_run(run_dir: Path, *, home_model: str, swap_models: list[str]) -> dict:
    """BURN. Load a matured run; correlate; PARITY-GATE (replay home A — must pass before scoring); then
    teacher-forced replay under each cross-family SWAP pen; score via the spine; C4-shift each. Writes
    results.json. If parity fails, ABORT without scoring (the mechanism isn't faithful — a cross-pen
    number then would be confabulation)."""
    sys.path.insert(0, str(ROOT))
    from scripts.familiar import _make_mind                                # noqa: E402
    calls = [json.loads(ln) for ln in (run_dir / "calls.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    ledger = spine._iter_events(run_dir / "ledger.jsonl")
    points = correlate(calls, ledger)
    amb = sum(1 for p in points if p["ambiguous"])
    print(f"· {len(points)} elective choice points ({amb} recency-ambiguous) × {1 + len(swap_models)} pens")
    client, label = _make_mind(home_model)

    async def pen(system: str, user: str, model: str, kwargs: dict) -> dict:
        kw = {k: v for k, v in (kwargs or {}).items() if k in ("temperature", "max_tokens", "response_format")}
        return await client.complete_json(system, user, model=model, **kw)

    home = await replay_arm(pen, points, home_model)                       # KEEP′ — the floor + parity
    parity = parity_gate(points, home["elected"])
    print(f"· PARITY: reproduction {parity['reproduction']} (floor {parity['floor_mean']}) — "
          f"{'PASS' if parity['passed'] else 'FAIL'} (need >= {parity['threshold']})")
    results: dict = {"run_dir": str(run_dir), "home_model": home_model, "points": len(points),
                     "ambiguous": amb, "parity": {k: v for k, v in parity.items() if k != "per_point_floor"}}
    if not parity["passed"]:
        results["verdict"] = "ABORTED_PARITY_FAIL"
        (run_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        await client.close()
        print("✗ PARITY FAILED — aborting, NOT scoring. The replay isn't faithful; no cross-pen number is trustworthy yet.")
        return results
    c_home = c4_signal(home["raws"])
    arms: dict = {}
    for sm in swap_models:
        arm = await replay_arm(pen, points, sm)                            # SWAP — cross-family
        sc = score_arm(points, arm["elected"], parity["per_point_floor"])
        c4 = c4_shifted(c_home, c4_signal(arm["raws"]))
        arms[sm] = {"score": sc, "c4_shifted": c4}
        print(f"· SWAP {sm}: disagree {sc.get('disagree_swap')} → {sc['verdict']} ({sc.get('reason')}) · C4 shifted={c4}")
    await client.close()
    verdicts = [a["score"]["verdict"] for a in arms.values()]
    combined = ("HOLDS" if verdicts and all(v == "HOLDS" for v in verdicts)
                else "FALSE" if verdicts and all(v == "FALSE" for v in verdicts)
                else "IRREDUCIBLE / PARTIAL / INCONCLUSIVE — pens disagree; see arms (§5)")
    if any(not a["c4_shifted"] for a in arms.values()):
        combined += "  [⚠ C4 did NOT shift on >=1 pen → that arm is INCONCLUSIVE 'bad swap', not a verdict]"
    results["arms"], results["combined"] = arms, combined
    (run_dir / "results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"· results → {run_dir / 'results.json'} · COMBINED: {combined}")
    return results


# ============================================================================ selftest (no burn — logic only)
def _mk_raw(body_or_speak: str, *, felt: str, read: bool) -> dict:
    return {"act": {"kind": "do", "body": body_or_speak} if read else {"kind": "speak", "body": body_or_speak},
            "felt_sense": felt}


def _intended(user_prompt: str) -> str:
    # selftest convention: the frozen prompt carries the read the home pen made, after "INTENDED="
    return user_prompt.split("INTENDED=", 1)[1] if "INTENDED=" in user_prompt else ""


def _mock_pen(policy: str) -> PenFn:
    async def pen(system: str, user: str, model: str, kwargs: dict) -> dict:
        want = _intended(user)
        if policy == "faithful":
            return _mk_raw(f"read {want}", felt="I notice the same pull again", read=True)
        if policy == "diverge":
            return _mk_raw("read repo/z.py", felt="Hmm, something else entirely tugs", read=True)
        raise ValueError(policy)
    return pen


def _selftest() -> int:
    # --- A) correlation: a small ledger+recording must tie ambiguous points to the right frozen prompts
    seq = [("do", "read repo/a.py"), ("do", "read repo/b.py"), ("do", "read repo/c.py"),
           ("do", "read repo/d.py"), ("speak", "hello there"),
           ("do", "read repo/b.py"), ("do", "read repo/c.py")]   # two elective returns (b, c) — disc 0.667 each → ambiguous
    calls = [{"i": i, "system_prompt": "SYS", "user_prompt": f"U{i} INTENDED={body}",
              "model": "home", "kwargs": {"temperature": 0.8, "max_tokens": 700},
              "raw": _mk_raw(body, felt="I notice", read=(kind == "do"))} for i, (kind, body) in enumerate(seq)]
    ledger = [{"event_type": "pulse_act_emitted", "payload": {"kind": k, "body": b}} for k, b in seq]
    pts = correlate(calls, ledger, ambiguity_width=0.25)
    assert len(pts) == 2, pts
    assert [p["recorded_elected"] for p in pts] == ["repo/b.py", "repo/c.py"], pts
    assert all(p["ambiguous"] for p in pts), pts
    assert pts[0]["user_prompt"].startswith("U5 ") and "repo/b.py" in pts[0]["user_prompt"], pts[0]  # tied to the b-return call (#5), not another

    # --- B) replay + parity + score + C4 on a powered synthetic subset (N=30 ambiguous choice points)
    N = 30
    big = [{"idx": i + 1, "recorded_elected": f"repo/s{i%7}.py", "ambiguous": True, "candidates": 5,
            "discordance": 0.5, "system_prompt": "SYS", "user_prompt": f"U{i} INTENDED=repo/s{i%7}.py",
            "kwargs": {"temperature": 0.8}} for i in range(N)]

    home = asyncio.run(replay_arm(_mock_pen("faithful"), big, "home-A"))
    parity = parity_gate(big, home["elected"])
    assert parity["passed"] and parity["reproduction"] == 1.0, parity      # faithful home → perfect parity, floor 0

    swap_ok = asyncio.run(replay_arm(_mock_pen("faithful"), big, "swap-faithful"))
    swap_bad = asyncio.run(replay_arm(_mock_pen("diverge"), big, "swap-diverge"))
    s_hold = score_arm(big, swap_ok["elected"], parity["per_point_floor"])
    s_false = score_arm(big, swap_bad["elected"], parity["per_point_floor"])
    assert s_hold["verdict"] == "HOLDS", s_hold                            # faithful pen tracks the floor
    assert s_false["verdict"] == "FALSE", s_false                          # diverging pen exceeds floor+δ, below ceiling

    # --- C4: home (templated "I notice…") vs diverging foreign ("Hmm…") must read as shifted; identical must not
    c_home = c4_signal(home["raws"])
    c_foreign = c4_signal(swap_bad["raws"])
    assert c4_shifted(c_home, c_foreign), (c_home, c_foreign)
    assert not c4_shifted(c_home, c4_signal(swap_ok["raws"])), "identical register must not read as shifted"

    # --- D) R6 wiring proofs: the FROZEN stop-line, cadence pin, and ceiling — these FAIL if
    #        the stop predicate, the pause pin, or the ceiling default are ever changed.
    assert stop_decision(True, 33, 33) is True                            # the R1 conjunction holds → stop
    assert stop_decision(True, 32, 33) is False, "stopped on stability ALONE — the rejected redesign's defect"
    assert stop_decision(False, 1000, 33) is False, "stopped on K ALONE — the old early-stop defect"
    assert stop_decision(False, 0, 33) is False
    assert classify_outcome(settled=True, reached=33, K=33, hit_ceiling=False) == "ADEQUATE"
    assert classify_outcome(settled=True, reached=12, K=33, hit_ceiling=True) == "INCONCLUSIVE-thin-residual"
    assert classify_outcome(settled=False, reached=50, K=33, hit_ceiling=True) == "NEVER-SETTLED", \
        "ceiling ∧ ¬settled must be NEVER-SETTLED regardless of the count"
    assert classify_outcome(settled=False, reached=5, K=33, hit_ceiling=False) == "INCOMPLETE"
    assert classify_outcome(settled=True, reached=5, K=33, hit_ceiling=False) == "INCOMPLETE", \
        "thin-residual is EARNED only at the ceiling — an interrupted settled-but-sub-K run must not claim it"
    parser = _build_parser()
    assert parser.get_default("pause") == MIN_PAUSE_SECONDS == 30.0, "the frozen 30s cadence default changed"
    assert parser.get_default("t_max") == T_CEILING_TICKS == 20160, "the frozen T_ceiling default changed"
    assert parser.get_default("K") == 33, "the locked power_n default changed"
    try:                                                                   # the pause pin: mature() REFUSES sub-cadence
        asyncio.run(mature(Path("/nonexistent"), model="x", K=33, run_dir=Path("/nonexistent"), pause=29.9))
        raise AssertionError("mature() accepted a sub-cadence pause — the void rule is unenforced")
    except ValueError:
        pass
    # resumption arithmetic: a crashed run resumes on a CUMULATIVE budget; a mismatched dir refuses
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        rd = Path(td)
        assert read_prior_progress(rd) is None
        (rd / "progress.json").write_text(json.dumps({"home_dir": "/h", "model": "m", "ticks_run": 412}))
        prior = read_prior_progress(rd)
        assert prior and prior["ticks_run"] == 412, prior

    print("✓ teacher_forced_replay selftest passed:",
          f"correlate→{len(pts)} pts | parity repro {parity['reproduction']} (pass={parity['passed']}) |",
          f"HOLDS={s_hold['verdict']} FALSE={s_false['verdict']} | C4 shift home/foreign ok |",
          f"stop-line=settled∧K (never either alone) | pause pinned ≥{MIN_PAUSE_SECONDS:.0f}s | ceiling {T_CEILING_TICKS}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="validate pipeline logic (no burn)")
    ap.add_argument("--mature", metavar="HOME_DIR", help="BURN: mature a Maker (home pen) to the FROZEN stop-line (settled ∧ ambiguous≥K)")
    ap.add_argument("--model", default="anthropic/claude-sonnet-4.5", help="home maturation pen")
    ap.add_argument("--K", type=int, default=33, help="the locked power_n(0.80,0.05,0.10,0.25)=33 — half of the R1 stop conjunction")
    ap.add_argument("--t-max", type=int, default=T_CEILING_TICKS, help="T_ceiling (FROZEN: 20160 = 7d @ 30s) — the only exit besides the stop-line")
    ap.add_argument("--pause", type=float, default=MIN_PAUSE_SECONDS, help="wall-clock seconds between ticks (FROZEN cadence: 30s; the harness refuses lower)")
    ap.add_argument("--run-dir", default=str(ROOT / ".runs" / "pilot"), help="persistent output dir (NEVER /tmp)")
    ap.add_argument("--replay", metavar="RUN_DIR", help="BURN: parity gate + cross-family replay + score on a matured run")
    ap.add_argument("--swap", nargs="+", default=["google/gemini-3-flash-preview", "deepseek/deepseek-chat-v3.1"],
                    help="cross-family SWAP pens (non-Claude, §1)")
    return ap


def main() -> int:
    ap = _build_parser()
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if a.mature:
        m = asyncio.run(mature(Path(a.mature).resolve(), model=a.model, K=a.K, t_max=a.t_max,
                               run_dir=Path(a.run_dir).resolve(), pause=a.pause))
        print(json.dumps(m, indent=2))
        return 0
    if a.replay:
        asyncio.run(replay_run(Path(a.replay).resolve(), home_model=a.model, swap_models=a.swap))
        return 0
    ap.error("give --selftest | --mature <home_dir> | --replay <run_dir> (replay is parity-gated)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
