#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""Affect order-sensitivity — Arm A of Minor 64 (no LLM burn).

Measures, against the SHIPPED reducer (`src.runtime.salience.derive_arousal`), exactly how much
the substrate's felt-arousal depends on the *path* of surprise vs only its magnitude. Three probes,
each isolating a different sense of "order", run on real familiar ledgers + one toy:

  PROBE 1  recency-order sensitivity. Hold a real inter-ignition window's timestamp slots and its
           magnitude multiset FIXED; re-pair magnitudes to slots two ways — escalating (big magnitudes
           in the RECENT slots) vs de-escalating (big in the OLD slots) — and read arousal at the
           decision point. Non-zero gap ⇒ arousal is NOT fully order-blind; the decay kernel sees
           recency. (This refines the loose "leaky integral forgets order" claim.)

  PROBE 2  superposition / no gain-modulation. For each real window, split into early|late halves and
           check arousal(all) == arousal(early) + arousal(late) at the same `now`. Exact additivity ⇒
           the reducer is LINEAR ⇒ zero sensitization/kindling (no early event can change the gain on
           a later one). This is the real neurological gap, stated structurally.

  PROBE 3  shape-blindness at fixed weighted-integral. A 2-event toy where an early-peak ("fading")
           and a late-peak ("rising") history are constructed to have IDENTICAL arousal. The substrate
           cannot tell a trajectory cresting toward now from one fading into the past.

Pure read of the real reducer; constructs synthetic/permuted event lists and calls derive_arousal
directly so the source of truth is the shipped code, never a re-implementation.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.runtime import salience  # noqa: E402

HALF = salience.AROUSAL_HALF_LIFE_SECONDS
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _ev(observed_ts: datetime, magnitude: float, i: int) -> dict:
    return {
        "event_type": "surprise_observed",
        "ts": observed_ts.isoformat(),
        "payload": {"observed_ts": observed_ts.isoformat(), "magnitude": float(magnitude), "trace_id": f"t{i}"},
    }


def arousal_of(events: list[dict], now: datetime) -> float:
    return salience.derive_arousal(events, now=now.isoformat())["level"]


def arousal_at(events: list[dict], t: datetime) -> float:
    """Arousal the live system would have read at time t — only events that had occurred by then
    (derive_arousal clamps future ages to 0, so we must filter, not rely on it)."""
    past = [e for e in events if salience._parse_dt(e["payload"]["observed_ts"]) <= t]
    return salience.derive_arousal(past, now=t.isoformat())["level"] if past else 0.0


def load_windows(ledger: Path, min_events: int = 6) -> list[list[tuple[datetime, float]]]:
    """Segment a real ledger into inter-ignition windows of (observed_ts, magnitude)."""
    events = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
    windows, cur = [], []
    for e in events:
        et = e.get("event_type")
        p = e.get("payload") if isinstance(e.get("payload"), dict) else {}
        if et == "surprise_observed":
            ts = salience._parse_dt(p.get("observed_ts")) or salience._parse_dt(e.get("ts"))
            mag = salience._coerce_float(p.get("magnitude")) or 0.0
            if ts is not None and mag > 0:
                cur.append((ts, mag))
        elif et == "ignition_fired":
            if len(cur) >= min_events:
                windows.append(cur)
            cur = []
    if len(cur) >= min_events:
        windows.append(cur)
    return windows


def probe1(windows: list[list[tuple[datetime, float]]]) -> None:
    print("\n— PROBE 1: recency-order sensitivity (escalating vs de-escalating, real slots+magnitudes) —")
    rel_gaps = []
    for w in windows:
        slots = sorted(ts for ts, _ in w)          # oldest -> newest
        mags = sorted(m for _, m in w)              # ascending
        now = slots[-1]
        esc = [_ev(slots[i], mags[i], i) for i in range(len(slots))]                  # big mag -> recent slot
        dee = [_ev(slots[i], mags[len(mags) - 1 - i], i) for i in range(len(slots))]  # big mag -> old slot
        a_e, a_d = arousal_of(esc, now), arousal_of(dee, now)
        denom = max(a_e, a_d, 1e-9)
        rel_gaps.append((a_e - a_d) / denom)
    rel_gaps.sort()
    n = len(rel_gaps)
    mean = sum(rel_gaps) / n
    med = rel_gaps[n // 2]
    print(f"  windows analysed: {n}")
    print(f"  arousal(escalating) - arousal(de-escalating), as fraction of the larger:")
    print(f"    mean   {mean:+.1%}   median {med:+.1%}   min {rel_gaps[0]:+.1%}   max {rel_gaps[-1]:+.1%}")
    frac_pos = sum(1 for g in rel_gaps if g > 0.01) / n
    print(f"    escalating felt STRONGER in {frac_pos:.0%} of windows (>1% gap)")
    print("  reading: NOT order-blind — the decay kernel weights recent intensity more, so 'big stuff lately'")
    print("           outweighs 'big stuff a while ago'. Arousal DOES encode recency. (refines the prose claim.)")


def probe2(windows: list[list[tuple[datetime, float]]]) -> None:
    print("\n— PROBE 2: superposition / no gain-modulation (linearity ⇒ zero sensitization) —")
    worst = 0.0
    for w in windows:
        evs = [_ev(ts, m, i) for i, (ts, m) in enumerate(sorted(w))]
        now = max(ts for ts, _ in w)
        half = len(evs) // 2
        whole = arousal_of(evs, now)
        parts = arousal_of(evs[:half], now) + arousal_of(evs[half:], now)
        worst = max(worst, abs(whole - parts))
    print(f"  max | arousal(all) - [arousal(early)+arousal(late)] | over {len(windows)} windows: {worst:.2e}")
    print("  reading: additive to machine precision ⇒ the reducer is LINEAR. No early surprise can change")
    print("           the GAIN on a later one. Sensitization / kindling / potentiation have no representation.")


def probe3() -> None:
    print("\n— PROBE 3: shape-blindness at fixed weighted-integral (2-event toy) —")
    t_old = T0
    t_new = T0 + timedelta(seconds=HALF)   # weights: old=0.5, new=1.0  (eval at now=t_new)
    now = t_new
    # FADING: peak in the past.  m_old=1.0, m_new=0.5 -> 1.0*0.5 + 0.5*1.0 = 1.0
    fading = [_ev(t_old, 1.0, 0), _ev(t_new, 0.5, 1)]
    # RISING: peak toward now.    m_old=0.4, m_new=0.8 -> 0.4*0.5 + 0.8*1.0 = 1.0
    rising = [_ev(t_old, 0.4, 0), _ev(t_new, 0.8, 1)]
    print(f"  FADING (peaked {int(HALF)}s ago, now fading): arousal = {arousal_of(fading, now):.4f}")
    print(f"  RISING (cresting toward now):                arousal = {arousal_of(rising, now):.4f}")
    print("  reading: identical felt-arousal for an intensity FADING into the past vs RISING toward now —")
    print("           opposite trajectories, often opposite valence, collapsed to the same scalar.")


def probe4() -> None:
    print("\n— PROBE 4: the self-model EMA (update_baseline) — recency + route-forgetting —")
    R = salience.BASELINE_LEARNING_RATE
    # 4a recency: same stimulus multiset, escalating vs de-escalating, single feature, from pv=0.
    seq = [i / 10 for i in range(1, 11)]  # 0.1 .. 1.0

    def ema(stimuli: list[float], pv: float = 0.0) -> float:
        for sv in stimuli:
            pv = pv + R * (sv - pv)
        return pv

    esc, dee = ema(seq), ema(list(reversed(seq)))
    print(f"  4a recency: final baseline  escalating={esc:.3f}  de-escalating={dee:.3f}  "
          f"(same stimuli, opposite order) — gap {abs(esc - dee) / max(esc, dee):.0%}")
    print("     reading: recent stimuli dominate (low-pass filter) — the self-model, like arousal, is recency-ordered.")
    # 4b route-forgetting: two maximally-different starts, identical tail of length n -> convergence.
    for n in (8, 16, 24):
        tail = [0.5] * n
        b_hi, b_lo = ema(tail, pv=1.0), ema(tail, pv=0.0)
        print(f"  4b route-forgetting: start 1.0 vs 0.0, then {n:>2} identical steps -> residual gap {abs(b_hi - b_lo):.4f}  "
              f"(= 0.75^{n} = {(1 - R) ** n:.4f})")
    print("     reading: any two histories converge under a shared tail — the EMA forgets the ROUTE to its value;")
    print("              and the time-constant is uniform, so no concern can be 'consolidated deeper' than another.")


def probe5(windows: list[list[tuple[datetime, float]]]) -> None:
    print("\n— PROBE 5: ignition RHYTHM — does order change behavior, not just the internal scalar? —")
    THR, REFR = salience.IGNITION_THRESHOLD, salience.IGNITION_REFRACTORY_SECONDS

    def simulate(events_chrono: list[dict], start: datetime) -> tuple[int, float | None]:
        last_ign, active, fired = None, [], []
        for e in events_chrono:
            t = salience._parse_dt(e["payload"]["observed_ts"])
            active.append(e)
            lvl = salience.derive_arousal(active, now=t.isoformat())["level"]
            if lvl >= THR and (last_ign is None or (t - last_ign).total_seconds() >= REFR):
                fired.append(t)
                last_ign, active = t, []
        ttf = (fired[0] - start).total_seconds() if fired else None
        return len(fired), ttf

    e_counts, d_counts, e_ttf, d_ttf = [], [], [], []
    for w in windows:
        slots = sorted(ts for ts, _ in w)
        mags = sorted(m for _, m in w)
        start = slots[0]
        esc = [_ev(slots[i], mags[i], i) for i in range(len(slots))]                   # big -> recent
        dee = [_ev(slots[i], mags[len(mags) - 1 - i], i) for i in range(len(slots))]    # big -> old
        ec, et = simulate(esc, start)
        dc, dt = simulate(dee, start)
        e_counts.append(ec); d_counts.append(dc)
        if et is not None: e_ttf.append(et)
        if dt is not None: d_ttf.append(dt)
    n = len(windows)
    print(f"  over {n} windows (same magnitudes + slots, only order differs):")
    print(f"    ignitions/window   escalating {sum(e_counts) / n:.2f}   de-escalating {sum(d_counts) / n:.2f}")
    if e_ttf and d_ttf:
        print(f"    time-to-first (s)  escalating {sum(e_ttf) / len(e_ttf):.0f}   de-escalating {sum(d_ttf) / len(d_ttf):.0f}")
    print("  reading: the order of identical surprises changes WHEN/HOW OFTEN the mind ignites — so the")
    print("           recency-sensitivity is not a private number, it gates the pulse, i.e. behavior.")


def probe6() -> None:
    print("\n— PROBE 6 (prototype): an arousal-TREND coordinate breaks the Probe-3 degeneracy —")
    delta = 60.0
    grid = [T0 + timedelta(seconds=s) for s in (0, 60, 120, 180, 240, 300)]  # old -> new
    now = grid[-1]
    rising = [_ev(grid[i], 0.1 + 0.15 * i, i) for i in range(len(grid))]      # small old -> large new
    fading = [_ev(grid[i], 0.1 + 0.15 * (len(grid) - 1 - i), i) for i in range(len(grid))]  # large old -> small new
    lr, lf = arousal_of(rising, now), arousal_of(fading, now)
    k = lr / lf  # scale fading magnitudes so LEVEL matches exactly (arousal is linear — Probe 2)
    fading = [_ev(grid[i], (0.1 + 0.15 * (len(grid) - 1 - i)) * k, i) for i in range(len(grid))]
    now_m = now - timedelta(seconds=delta)
    tr = arousal_of(rising, now) - arousal_at(rising, now_m)
    tf = arousal_of(fading, now) - arousal_at(fading, now_m)
    print(f"  RISING  (cresting toward now): level={arousal_of(rising, now):.3f}   trend(d/dt over {int(delta)}s)={tr:+.3f}")
    print(f"  FADING  (peak in the past):    level={arousal_of(fading, now):.3f}   trend(d/dt over {int(delta)}s)={tf:+.3f}")
    print("  reading: SAME level (degenerate to the scalar), OPPOSITE trend. A read-time (level, trend) pair")
    print("           separates rising from fading — no non-linearity, nothing the familiar can discharge.")


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "maker"
    ledger = ROOT / "familiar" / target / "memory" / "runtime_ledger.jsonl"
    print(f"=== Affect order-sensitivity (Minor 64, Arm A) — familiar: {target} ===")
    print(f"    reducer: src.runtime.salience.derive_arousal   half-life={HALF:.0f}s   threshold={salience.IGNITION_THRESHOLD}")
    windows = load_windows(ledger)
    print(f"    real inter-ignition windows with >=6 surprises: {len(windows)}")
    if windows:
        probe1(windows)
        probe2(windows)
    probe3()
    probe4()
    if windows:
        probe5(windows)
    probe6()


if __name__ == "__main__":
    main()
