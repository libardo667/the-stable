# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""Maturation stability gate — the §1 stop-line, operationalized (K-INDEPENDENT).

The locked §1 stop-line grows each Maker until BOTH hold: ≥K recency-ambiguous
elective reads AND *"a stable drive/concern profile (the slow self-model settled;
not still climbing)."* The harness historically checked only K. This module
supplies the second, K-independent half: it reads the **baseline** — the
substrate's slow self-model (``substrate.derive_baseline``) — and reports when it
has SETTLED. It never looks at the elective-read count; K is applied later, at
analysis. So "matured" and "reached K" are measured by disjoint instruments, and
no stability threshold can be tuned toward the verdict.

Every threshold is anchored to the substrate's OWN habituation constants, never to
K or to the ambiguous-read yield:

- **settle window = ``BASELINE_DECAY_HALF_LIFE`` (4 h).** The self-model's own
  timescale. "Settled over a rolling window" means *at least one habituation
  half-life*, not an arbitrary tick count.
- **drift floor = ``BASELINE_EPSILON`` (0.02).** The per-tag value below which a
  feature does not even survive into the self-model — so drift under it is, by the
  substrate's own definition, noise rather than climbing.
- **strangled guard = ``IGNITION_THRESHOLD`` (1.0).** Distinguishes settled-quiet
  from strangled-quiet (worldweaver feedback-2: a mind that WANTS to fire but
  cannot reads from the ledger as serene; that silence is not maturity).

Adapted from worldweaver's principled maturation stop (``mr-review 2026-06-07``):
stop when the instrument PLATEAUS over a rolling window past a warmup it cannot
fire inside of; keep a generous ceiling as a backstop and treat "never stabilized"
as itself a result. The WW lesson — the coarse EXTENT curve froze while the SCORED
DEPTH curve still climbed — is why ``drift`` is the **max** over tags (every
dimension must be flat), never the mean: a single still-climbing concern must veto
"settled", never be averaged away by settled ones.

Cold-review #2 (2026-06-10, REJECT-with-repair) drove three false-positive
"settled" states through the gate as first coded; the repairs are R2–R4 of its §3,
all K-blind, all on the same pre-existing constants:

- **R2 net-window drift.** Per-step drift at the 60 s snapshot cadence misses any
  climb slower than 0.02/min (a full 0→1 ramp over 12 h read settled at 14× under
  the floor). ``plateaued`` now ALSO requires the NET drift across the window —
  ``drift(window[0], window[-1])`` — to be under the floor.
- **R3 non-degeneracy.** An empty/contentless self-model (dead embedder, starved
  ``read_roots``) drifts 0.0 and read trivially settled. ``settled`` now requires
  the terminal in-window snapshot to carry ≥1 tag ≥ ``BASELINE_EPSILON``.
- **R4 pen-dead.** ``record_ignition`` fires "regardless of producer success"
  (integrator.py), so a dead pen keeps resetting arousal and the raw-arousal
  strangled guard goes blind. In-window ignitions > 0 with zero pulses → not
  settled, flagged ``pen_dead`` (distinct from ``strangled``).
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so `src` resolves standalone

from src.runtime.salience import IGNITION_THRESHOLD, derive_arousal
from src.runtime.substrate import BASELINE_DECAY_HALF_LIFE, BASELINE_EPSILON

SETTLE_WINDOW_SECONDS = BASELINE_DECAY_HALF_LIFE  # 4 h — one habituation half-life
DRIFT_FLOOR = BASELINE_EPSILON                    # 0.02 — the substrate's own per-tag noise floor


def _parse_dt(s: Any) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _flatten(by_scope: dict[str, Any]) -> dict[str, float]:
    """``{scope: {tag: v}}`` → flat ``{"scope.tag": v}`` so drift is one vector."""
    flat: dict[str, float] = {}
    for scope, tags in (by_scope or {}).items():
        if isinstance(tags, dict):
            for tag, v in tags.items():
                try:
                    flat[f"{scope}.{tag}"] = float(v)
                except (TypeError, ValueError):
                    continue
    return flat


def baseline_snapshots(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ordered self-model snapshots from ``baseline_updated`` events: ``{ts, vec}``."""
    snaps: list[dict[str, Any]] = []
    for e in events:
        if str(e.get("event_type") or "").strip() != "baseline_updated":
            continue
        payload = e.get("payload") if isinstance(e.get("payload"), dict) else {}
        ts = _parse_dt(payload.get("updated_ts")) or _parse_dt(e.get("ts"))
        if ts is None:
            continue
        snaps.append({"ts": ts, "vec": _flatten(payload.get("by_scope") or {})})
    snaps.sort(key=lambda s: s["ts"])
    return snaps


def drift(a: dict[str, float], b: dict[str, float]) -> float:
    """MAX absolute per-tag change over the union of tags (a vanished tag drifts
    from its value to 0). Max, not mean: one still-climbing concern vetoes settled."""
    keys = set(a) | set(b)
    if not keys:
        return 0.0
    return max(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys)


def drift_argmax(a: dict[str, float], b: dict[str, float]) -> tuple[float, str | None]:
    """``drift`` plus WHICH tag carried it (diagnostic only — V4a′: a churny tag
    that forever blocks the plateau is undiagnosable without its name)."""
    keys = set(a) | set(b)
    if not keys:
        return 0.0, None
    tag = max(keys, key=lambda k: abs(a.get(k, 0.0) - b.get(k, 0.0)))
    return abs(a.get(tag, 0.0) - b.get(tag, 0.0)), tag


def assess_maturity(
    events: list[dict[str, Any]],
    *,
    now: Any = None,
    settle_window_seconds: float = SETTLE_WINDOW_SECONDS,
    drift_floor: float = DRIFT_FLOOR,
) -> dict[str, Any]:
    """Is the slow self-model SETTLED? Reads only the baseline + arousal/ignition/
    pulse waveform — never the elective-read count. Returns the verdict and its parts.

    ``settled`` ⇔ ``warmed_up`` ∧ ``plateaued`` ∧ ``non_degenerate`` ∧ ¬``strangled`` ∧ ¬``pen_dead``:
    - **warmed_up** — at least one habituation half-life has elapsed since the
      self-model first formed (the gate *cannot* fire inside cold-start warmup,
      which WW warned dominates the early hours).
    - **plateaued** — across the trailing settle window there are ≥2 snapshots,
      EVERY consecutive-snapshot drift is below the floor, AND the NET drift from
      the window's first to last snapshot is below the floor (R2: per-step drift
      at the 60 s snapshot cadence cannot see a slow ramp; the net conjunct can).
    - **non_degenerate** — the terminal in-window snapshot carries ≥1 tag at/above
      ``BASELINE_EPSILON`` (R3: an empty self-model — dead embedder, starved scope
      — must not read as trivially settled).
    - **strangled** — terminal arousal is at/over ignition threshold yet no pulse
      discharged in the trailing window: charge with no falling edge. Plateaued
      perception over a strangled mind is not maturity.
    - **pen_dead** — ignitions fired in the window but zero pulses discharged
      (R4: ``record_ignition`` resets arousal regardless of producer success, so
      a dead pen is invisible to the raw-arousal strangled guard; the
      ignition-vs-pulse mismatch sees it).
    """
    now_dt = _parse_dt(now) or datetime.now(timezone.utc)
    snaps = baseline_snapshots(events)

    warmed_up = bool(snaps) and (now_dt - snaps[0]["ts"]).total_seconds() >= settle_window_seconds

    window_start = now_dt.timestamp() - settle_window_seconds
    window = [s for s in snaps if s["ts"].timestamp() >= window_start]
    step_drifts = [drift_argmax(window[i - 1]["vec"], window[i]["vec"]) for i in range(1, len(window))]
    max_recent_drift, max_drift_tag = max(step_drifts, key=lambda dv: dv[0]) if step_drifts else (None, None)
    net_window_drift = drift(window[0]["vec"], window[-1]["vec"]) if len(window) >= 2 else None
    net_ok = net_window_drift is not None and net_window_drift < drift_floor
    plateaued = len(window) >= 2 and all(d < drift_floor for d, _ in step_drifts) and net_ok

    # R3 non-degeneracy: the terminal in-window self-model must have CONTENT.
    non_degenerate = bool(window) and any(v >= BASELINE_EPSILON for v in window[-1]["vec"].values())

    # Strangled-quiet guard (WW feedback-2): high arousal, no discharge.
    arousal = derive_arousal(events, now=now_dt)
    recent_pulses = sum(
        1
        for e in events
        if str(e.get("event_type") or "") == "pulse_emitted"
        and (_parse_dt((e.get("payload") or {}).get("cast_ts")) or _parse_dt(e.get("ts")) or now_dt).timestamp()
        >= window_start
    )
    strangled = bool(arousal.get("level", 0.0) >= IGNITION_THRESHOLD and recent_pulses == 0)

    # R4 pen-dead guard: igniting but never emitting (arousal resets on ignition
    # regardless of producer success, so the strangled guard cannot see this).
    recent_ignitions = sum(
        1
        for e in events
        if str(e.get("event_type") or "") == "ignition_fired"
        and (_parse_dt((e.get("payload") or {}).get("fired_ts")) or _parse_dt(e.get("ts")) or now_dt).timestamp()
        >= window_start
    )
    pen_dead = bool(recent_ignitions > 0 and recent_pulses == 0)

    settled = bool(warmed_up and plateaued and non_degenerate and not strangled and not pen_dead)
    return {
        "settled": settled,
        "warmed_up": warmed_up,
        "plateaued": plateaued,
        "non_degenerate": non_degenerate,
        "strangled": strangled,
        "pen_dead": pen_dead,
        "max_recent_drift": max_recent_drift,
        "max_drift_tag": max_drift_tag,
        "net_window_drift": net_window_drift,
        "drift_floor": drift_floor,
        "n_snapshots": len(snaps),
        "n_in_window": len(window),
        "arousal_level": arousal.get("level"),
        "recent_pulses": recent_pulses,
        "recent_ignitions": recent_ignitions,
        "settle_window_seconds": settle_window_seconds,
    }


# ----------------------------------------------------------------------------- #
# selftest — the code must PROVE the prose: each predicate FAILS if it is false.
# ----------------------------------------------------------------------------- #
def _ev(event_type: str, ts: datetime, payload: dict[str, Any]) -> dict[str, Any]:
    return {"event_type": event_type, "ts": ts.isoformat(), "payload": payload}


def _baseline(ts: datetime, rest: float, mob: float = 0.0) -> dict[str, Any]:
    scope = {"rest_drive": rest}
    if mob:
        scope["mobility_drive"] = mob
    return _ev("baseline_updated", ts, {"by_scope": {"self": scope}, "updated_ts": ts.isoformat()})


def _selftest() -> int:
    from datetime import timedelta

    base = datetime(2026, 6, 10, 0, 0, tzinfo=timezone.utc)
    hl = SETTLE_WINDOW_SECONDS
    now = base + timedelta(seconds=hl * 3)  # 3 half-lives elapsed → past warmup

    def at(frac: float) -> datetime:  # frac of a half-life from base
        return base + timedelta(seconds=hl * frac)

    # 1) PLATEAUED + warmed + healthy → settled True. Snapshots flat within floor
    #    across the trailing window (last half-life: frac 2.0..3.0).
    flat = [_baseline(at(f), rest=0.50 + 0.005 * i) for i, f in enumerate([2.0, 2.3, 2.6, 2.9])]
    flat = [_baseline(at(0.0), rest=0.10)] + flat  # an early snapshot anchors warmup
    a = assess_maturity(flat, now=now)
    assert a["settled"] is True, a
    assert a["plateaued"] and a["warmed_up"] and not a["strangled"], a

    # 2) STILL CLIMBING (drift > floor each step) → plateaued False → not settled.
    climb = [_baseline(at(0.0), rest=0.10)] + [
        _baseline(at(f), rest=0.10 + 0.10 * i) for i, f in enumerate([2.0, 2.3, 2.6, 2.9], start=1)
    ]
    c = assess_maturity(climb, now=now)
    assert c["plateaued"] is False and c["settled"] is False, c
    assert (c["max_recent_drift"] or 0) >= DRIFT_FLOOR, c

    # 2b) SPIKE-AND-RETURN (churny-but-stationary): a tag jumps 0.50→0.90→0.50 inside the
    #     window, so NET drift is 0.0 — only the PER-STEP max can veto this. (Without this
    #     case, the R2 net conjunct shadows the per-step test on monotone climbs and the
    #     per-step predicate would have no failing test behind it.)
    spike = [_baseline(at(0.0), rest=0.50)] + [
        _baseline(at(f), rest=v) for f, v in [(2.0, 0.50), (2.3, 0.90), (2.6, 0.50), (2.9, 0.50)]
    ]
    sp = assess_maturity(spike, now=now)
    assert (sp["net_window_drift"] or 0.0) < DRIFT_FLOOR, sp      # net is blind to this by construction
    assert (sp["max_recent_drift"] or 0.0) >= DRIFT_FLOOR, sp
    assert sp["max_drift_tag"] == "self.rest_drive", sp            # V4a′: the churny tag is NAMED
    assert sp["plateaued"] is False and sp["settled"] is False, \
        f"per-step plateau FAILED: a spiking tag with zero net drift read as settled: {sp}"

    # 3) COLD-START (first baseline < one half-life ago) → warmed_up False.
    young_now = at(0.5)
    young = [_baseline(at(0.0), rest=0.5), _baseline(at(0.2), rest=0.5), _baseline(at(0.4), rest=0.5)]
    y = assess_maturity(young, now=young_now)
    assert y["warmed_up"] is False and y["settled"] is False, y

    # 4) STRANGLED (flat baseline, but arousal ≥ threshold and zero pulses) → not settled.
    #    The forged surprise must ACTUALLY clear IGNITION_THRESHOLD at `now` — cold-review #2
    #    caught the prior draft forging one that decayed to 0.947, leaving the assert behind an
    #    `if` that never ran (dead code). Surprise sits 144 s before `now` — well inside one
    #    arousal half-life (AROUSAL_HALF_LIFE_SECONDS = 300 s) — so 5.0·0.5^(144/300) ≈ 3.59.
    #    The guard is now a HARD assert, preceded by a hard assert that the forge is real.
    strangle = list(flat) + [
        _ev("surprise_observed", at(2.99), {"magnitude": 5.0}),
    ]
    s = assess_maturity(strangle, now=now)
    assert s["arousal_level"] is not None and s["arousal_level"] >= IGNITION_THRESHOLD, \
        f"forged arousal did not clear ignition threshold — the strangled test would be dead code again: {s}"
    assert s["strangled"] is True and s["settled"] is False, s
    # and the same high-arousal window WITH a pulse is NOT strangled:
    unstrangled = list(strangle) + [_ev("pulse_emitted", at(2.995), {"cast_ts": at(2.995).isoformat()})]
    u = assess_maturity(unstrangled, now=now)
    assert u["strangled"] is False, u

    # 5) drift() is MAX not mean: one climbing tag vetoes even if others are flat.
    assert drift({"a": 0.5, "b": 0.5}, {"a": 0.5, "b": 0.9}) == 0.4
    assert drift_argmax({"a": 0.5, "b": 0.5}, {"a": 0.5, "b": 0.9}) == (0.4, "b")

    # 6) R2 — the cold-review #2 driven false positive, replayed VERBATIM as a failing test:
    #    a tag climbing 0→1 over 12 h at the live 60 s snapshot cadence. Per-step drift
    #    (~0.0014) sits 14× UNDER the floor — the per-step test alone called this settled.
    #    The net-window conjunct must catch it.
    ramp_now = base + timedelta(hours=12)
    ramp = [_baseline(base + timedelta(seconds=60 * i), rest=round(i / 720.0, 6)) for i in range(721)]
    r = assess_maturity(ramp, now=ramp_now)
    assert r["warmed_up"] is True, r
    assert (r["max_recent_drift"] or 0.0) < DRIFT_FLOOR, \
        f"ramp per-step drift unexpectedly >= floor — this test no longer exercises the R2 hole: {r}"
    assert r["net_window_drift"] is not None and r["net_window_drift"] >= DRIFT_FLOOR, r
    assert r["plateaued"] is False and r["settled"] is False, \
        f"R2 FAILED: a full 0→1 climb over 12 h at 60 s cadence read as settled: {r}"

    # 7) R3 — degenerate (contentless) self-model: warmed + zero-drift, but EMPTY vectors →
    #    must NOT read settled (the dead-embedder / starved-read_roots silent killer).
    empty = [_ev("baseline_updated", at(f), {"by_scope": {}, "updated_ts": at(f).isoformat()})
             for f in [0.0, 2.0, 2.3, 2.6, 2.9]]
    e = assess_maturity(empty, now=now)
    assert e["warmed_up"] is True and e["plateaued"] is True, e   # the other legs pass — only R3 stands between this and "settled"
    assert e["non_degenerate"] is False and e["settled"] is False, \
        f"R3 FAILED: a contentless self-model read as settled: {e}"

    # 8) R4 — pen-dead: ignitions fired in the window, ZERO pulses discharged → not settled,
    #    flagged pen_dead (distinct from strangled — ignition resets arousal, so the strangled
    #    guard is blind here by construction).
    dead = list(flat) + [_ev("ignition_fired", at(f), {"fired_ts": at(f).isoformat()}) for f in (2.5, 2.7)]
    d = assess_maturity(dead, now=now)
    assert d["recent_ignitions"] == 2 and d["recent_pulses"] == 0, d
    assert d["strangled"] is False, d                              # the old guard cannot see this failure mode
    assert d["pen_dead"] is True and d["settled"] is False, \
        f"R4 FAILED: a pen-dead familiar (igniting, never emitting) read as settled: {d}"
    # and the same window with a pulse discharged is NOT pen-dead (and is settled):
    alive = list(dead) + [_ev("pulse_emitted", at(2.8), {"cast_ts": at(2.8).isoformat()})]
    al = assess_maturity(alive, now=now)
    assert al["pen_dead"] is False and al["settled"] is True, al

    print(
        "✓ maturation_stability selftest passed: "
        f"settled={a['settled']} | climbing→not-settled | cold-start→not-warmed | "
        f"strangled-guard(arousal {s['arousal_level']:.2f}≥{IGNITION_THRESHOLD}) | "
        f"R2 12h-ramp→not-settled (net {r['net_window_drift']:.3f}≥{DRIFT_FLOOR}) | "
        f"R3 empty-vec→not-settled | R4 pen-dead→not-settled | "
        f"drift=max(window={SETTLE_WINDOW_SECONDS/3600:.0f}h, floor={DRIFT_FLOOR})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
