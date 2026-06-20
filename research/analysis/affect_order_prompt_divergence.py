#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""Affect order → prompt divergence — Minor 64 Arm B, Stage B0 (no LLM burn).

LOCKED design: research/preregistrations/2026-06-20-minor64-armB-order-vs-pulse-DRAFT.md
(cold reviews #5 + #6). B0 asks, with ZERO burn: does the ORDER of a matched surprise history change the
*pulse prompt the LLM would read*? If not (the full prompt is byte-identical for escalating vs
de-escalating in >=80% of real windows), order does not reach the LLM through the channels B0 varies and
the gated B1 burn is not justified — a real offline finding (PREMISE-DEAD), SCOPED to channels (a)-(d).

How order reaches the LLM (verified in code; §1 of the pre-reg), and B0 exercises all four:
  (a) contribution-rank permutation of the trace block  (salience.py:513 sorts by contribution desc)
  (b) top-6 truncation membership                       (pulse_engine.py:500  `traces[:6]`)
  (c) the rendered arousal SCALAR, OUTSIDE the block     (pulse_engine.py:583  "Your arousal (X.XX)...")
  (d) the stable-sort chronological tiebreak             (list.sort stable, traces appended in order)

Method (the matched DIFFERENTIAL probe). For each real inter-ignition window, hold the slot-time SET and
the (magnitude+content) bundle MULTISET fixed; build escalating (big magnitude -> recent slot) and
de-escalating (big -> old) histories that differ ONLY in which slot each bundle lands on. Each surprise's
FULL payload (features, trace_id, valence) travels with its magnitude — NOT stripped (that was the v1 bug
cold review #5 caught: reusing affect_order_sensitivity._ev/load_windows drops features, so the trace
block collapses to the empty fallback and PREMISE-DEAD fires as an artifact). Render the REAL full prompt
for each order via the shipped reducer + LLMPulseProducer.render_prompt_for_debug, holding one real memory_dir
FIXED so every memory-derived block (felt projection, afterimage, grief, baseline) is identical across
orders and cancels in the diff — leaving the byte-diff to isolate channels (a)-(d).

PREMISE-DEAD is SCOPED (cold review #6, binding limitation 1): a byte-identical result means order does
not reach the LLM through (a)-(d) — NOT "order does not reach the LLM" writ large. The memory-derived
channels are deliberately held fixed and remain an un-foreclosed route for a future ledger-injection probe.

    python3 research/analysis/affect_order_prompt_divergence.py --selftest        # no familiar, no burn
    python3 research/analysis/affect_order_prompt_divergence.py --familiar maker   # B0 run on a real ledger
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.runtime import salience  # noqa: E402
from src.runtime.pulse_engine import LLMPulseProducer  # noqa: E402

TOP_K = 6  # pulse_engine.py:500 renders traces[:6]
PREMISE_DEAD_FRACTION = 0.80  # §1/§4: >=80% byte-identical full prompts ⇒ PREMISE-DEAD (scoped to a-d)


def _eff_mag(payload: dict) -> float:
    """The magnitude that actually drives arousal: arousal_magnitude if present (post-minor-66), else
    magnitude (behaviour-preserving) — matches salience.derive_arousal's own choice (salience.py:494-495)."""
    am = salience._coerce_float(payload.get("arousal_magnitude"))
    return am if am is not None else (salience._coerce_float(payload.get("magnitude")) or 0.0)


def load_payload_windows(ledger: Path, min_events: int = 6) -> list[list[dict]]:
    """Segment a real ledger into inter-ignition windows, each a list of FULL surprise payloads
    (features/trace_id/valence kept — unlike Arm A's load_windows, which dropped them)."""
    events = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    windows: list[list[dict]] = []
    cur: list[dict] = []
    for e in events:
        et = e.get("event_type")
        p = e.get("payload") if isinstance(e.get("payload"), dict) else {}
        if et == "surprise_observed":
            ts = salience._parse_dt(p.get("observed_ts")) or salience._parse_dt(e.get("ts"))
            if ts is not None and _eff_mag(p) > 0:
                payload = deepcopy(p)
                payload.setdefault("observed_ts", ts.isoformat())
                cur.append(payload)
        elif et == "ignition_fired":
            if len(cur) >= min_events:
                windows.append(cur)
            cur = []
    if len(cur) >= min_events:
        windows.append(cur)
    return windows


def _event(payload: dict, slot_iso: str) -> dict:
    p = deepcopy(payload)
    p["observed_ts"] = slot_iso
    return {"event_type": "surprise_observed", "ts": slot_iso, "payload": p}


def order_events(payloads: list[dict], *, escalating: bool) -> list[dict]:
    """Assign (magnitude+content) bundles to slot times by magnitude order. Slots sorted oldest->newest;
    bundles sorted by magnitude ascending for escalating (big magnitude -> newest slot), reversed for
    de-escalating (big -> oldest). Only the assignment differs; the slot-set and bundle-multiset are fixed."""
    slots = sorted(salience._parse_dt(p["observed_ts"]) for p in payloads)  # oldest -> newest
    by_mag = sorted(payloads, key=_eff_mag)  # ascending magnitude
    bundles = by_mag if escalating else list(reversed(by_mag))
    return [_event(bundles[i], slots[i].isoformat()) for i in range(len(slots))]


def _bundle_key(payload: dict) -> str:
    return json.dumps(
        {"trace_id": payload.get("trace_id"), "mag": round(_eff_mag(payload), 6), "valence": payload.get("valence"), "features": payload.get("features")},
        sort_keys=True,
        default=str,
    )


def assert_matched(esc: list[dict], dee: list[dict]) -> None:
    """HARD precondition (§2.2): identical slot-time SET and identical bundle MULTISET across the two
    orders — so any prompt difference is order, never a mismatched input."""
    slots_e = sorted(e["payload"]["observed_ts"] for e in esc)
    slots_d = sorted(e["payload"]["observed_ts"] for e in dee)
    assert slots_e == slots_d, "matched precondition broken: slot-time sets differ"
    keys_e = sorted(_bundle_key(e["payload"]) for e in esc)
    keys_d = sorted(_bundle_key(e["payload"]) for e in dee)
    assert keys_e == keys_d, "matched precondition broken: bundle multisets differ"


def build_engine(familiar_dir: Path | None) -> LLMPulseProducer:
    """A LLMPulseProducer whose render_prompt_for_debug builds the real user prompt. _build_prompt is
    identity- and llm-free (verified), so the selftest uses a stub identity + an empty memory_dir; the
    real run loads the familiar's identity and holds its real memory_dir fixed across both orders."""
    if familiar_dir is not None:
        from src.identity.loader import IdentityLoader  # noqa: E402

        identity = IdentityLoader.load(familiar_dir)
        memory_dir = familiar_dir / "memory"
    else:
        identity = SimpleNamespace(name="probe", display_name="Probe")
        memory_dir = Path(tempfile.mkdtemp(prefix="armb_b0_"))  # empty ⇒ memory blocks constant
    return LLMPulseProducer(llm=SimpleNamespace(), identity=identity, memory_dir=memory_dir)


def render_order(engine: LLMPulseProducer, payloads: list[dict], *, escalating: bool) -> tuple[str, float, list[dict]]:
    events = order_events(payloads, escalating=escalating)
    now = max(salience._parse_dt(e["payload"]["observed_ts"]) for e in events)
    state = salience.derive_arousal(events, now=now.isoformat())
    prompt = engine.render_prompt_for_debug(traces=state["traces"], stimulus={}, arousal=state["level"])
    return prompt, state["level"], state["traces"]


def _top_ids(traces: list[dict]) -> list[str]:
    return [str(t.get("trace_id")) for t in traces[:TOP_K]]


def compare_window(engine: LLMPulseProducer, payloads: list[dict]) -> dict:
    p_esc, lvl_esc, tr_esc = render_order(engine, payloads, escalating=True)
    p_dee, lvl_dee, tr_dee = render_order(engine, payloads, escalating=False)
    assert_matched(order_events(payloads, escalating=True), order_events(payloads, escalating=False))
    ids_e, ids_d = _top_ids(tr_esc), _top_ids(tr_dee)
    set_e, set_d = set(ids_e), set(ids_d)
    union = set_e | set_d
    membership_jaccard = round(1 - len(set_e & set_d) / len(union), 4) if union else 0.0
    shared = set_e & set_d
    rank_disp = sum(abs(ids_e.index(i) - ids_d.index(i)) for i in shared)
    membership_change = set_e != set_d
    return {
        "byte_identical": p_esc == p_dee,
        "arousal_delta": round(abs(lvl_esc - lvl_dee), 4),
        "arousal_esc": lvl_esc,
        "arousal_dee": lvl_dee,
        "membership_jaccard": membership_jaccard,
        "membership_change": membership_change,
        "rank_displacement": rank_disp,
        "rank_only": (not membership_change) and (not (p_esc == p_dee)),
        "n_surprises": len(payloads),
    }


def run(familiar: str) -> int:
    familiar_dir = ROOT / "familiar" / familiar
    ledger = familiar_dir / "memory" / "runtime_ledger.jsonl"
    if not ledger.exists():
        print(f"no ledger at {ledger} — nothing to measure", file=sys.stderr)
        return 1
    engine = build_engine(familiar_dir)
    windows = load_payload_windows(ledger)
    print(f"=== Minor 64 Arm B / Stage B0 — full-prompt order divergence — familiar: {familiar} ===")
    print(f"    reducer salience.derive_arousal · render LLMPulseProducer._build_prompt(react) · half-life {salience.AROUSAL_HALF_LIFE_SECONDS:.0f}s")
    print(f"    inter-ignition windows with >={6} surprises: {len(windows)}")
    if not windows:
        print("    (no qualifying windows — INCONCLUSIVE, no B1)")
        return 0
    results = [compare_window(engine, w) for w in windows]
    n = len(results)
    identical = [r for r in results if r["byte_identical"]]
    differ = [r for r in results if not r["byte_identical"]]
    membership = [r for r in differ if r["membership_change"]]
    rank_only = [r for r in differ if r["rank_only"]]
    frac_identical = len(identical) / n
    print("\n— per-window —")
    for i, r in enumerate(results):
        kind = "IDENTICAL" if r["byte_identical"] else ("membership" if r["membership_change"] else "rank-only")
        print(f"  w{i:>2} [{r['n_surprises']:>2} surprises]  {kind:<10}  arousalΔ {r['arousal_delta']:+.3f}  " f"membJaccard {r['membership_jaccard']:.2f}  rankDisp {r['rank_displacement']}")
    print("\n— pooled —")
    print(f"  full-prompt byte-identical: {len(identical)}/{n}  ({frac_identical:.0%})")
    print(f"  differ: {len(differ)}/{n}   of which membership-change {len(membership)} · rank-only {len(rank_only)}")
    amax = max((r["arousal_delta"] for r in results), default=0.0)
    print(f"  arousal-scalar Δ (channel c): max {amax:+.3f}  (nonzero ⇒ order reaches the opener even when the block matches)")
    print("\n— verdict (SCOPED to channels a-d; cold review #6 limitation 1) —")
    if frac_identical >= PREMISE_DEAD_FRACTION:
        print(f"  PREMISE-DEAD: order does NOT reach the LLM through (a)-(d) in >={PREMISE_DEAD_FRACTION:.0%} of windows.")
        print("  Order does not reach the LLM via contribution-rank / top-6 membership / the arousal scalar /")
        print("  the sort tiebreak. NOT a claim about memory-derived channels (felt/afterimage/grief, held fixed).")
        print("  ⇒ The B1 burn is not justified on these channels. Arm B closes here.")
    elif len(membership) == 0:
        print("  WEAK: order reaches the prompt only via arousal-scalar / rank, no membership change.")
        print("  ⇒ B1 only if the differing subset clears the read-act-rate gate AND the §8 count (>=8).")
    else:
        print("  STRONG: order changes top-6 membership (what the mind is shown) in some windows.")
        print(f"  ⇒ B1 candidate subset = the {len(differ)} differing windows ({len(membership)} membership-change).")
    print(f"  §8 gate: differing windows = {len(differ)} (need >=8 to power B1; else INCONCLUSIVE-underpowered).")
    return 0


# ---------------------------------------------------------------------------- selftest (no burn, no familiar)
def _payload(trace_id: str, mag: float, observed_ts: str) -> dict:
    return {
        "trace_id": trace_id,
        "magnitude": mag,
        "observed_ts": observed_ts,
        "valence": "neutral",
        "features": [{"scope": "self", "tag": trace_id, "delta": 0.5, "stimulus": f"now-{trace_id}", "predicted": f"exp-{trace_id}"}],
    }


def _selftest() -> int:
    from datetime import datetime, timedelta, timezone

    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    half = salience.AROUSAL_HALF_LIFE_SECONDS
    engine = build_engine(None)

    # POSITIVE CONTROL (cold review #6 limitation 1): an order that genuinely changes the trace BLOCK must
    # render NON-byte-identical — the falsifier can DETECT divergence, not merely report identity. Slots are
    # spaced one half-life apart so DECAY overtakes magnitude: a big surprise parked at an old slot ranks
    # BELOW a small recent one, so escalating vs de-escalating drop DIFFERENT traces from the top-6 (a real
    # membership change), not merely reorder. (At sub-half-life spacing magnitude dominates and only the
    # arousal scalar (channel c) moves — a weaker probe; here we force the block itself to differ.)
    payloads = [_payload(f"t{i}", float(i + 1), (t0 + timedelta(seconds=half * i)).isoformat()) for i in range(7)]
    esc, dee = order_events(payloads, escalating=True), order_events(payloads, escalating=False)
    # (i) matched precondition: the two orders share slot-set + bundle-multiset, yet genuinely permute.
    assert_matched(esc, dee)  # raises if broken
    assert esc[-1]["payload"]["trace_id"] != dee[-1]["payload"]["trace_id"], "orders did not actually permute"
    # (ii) the positive control proper.
    pos = compare_window(engine, payloads)
    assert not pos["byte_identical"], "positive control FAILED: divergent order rendered identical prompt"
    assert pos["membership_change"], "positive control should change top-6 membership (7 surprises, top-6)"
    assert pos["arousal_delta"] > 0, "channel (c): arousal scalar should differ across orders"

    # (iii) IDENTITY control: a one-surprise window has no order to permute ⇒ the falsifier must report
    # identity (it is not a stuck always-divergent bug either).
    one = [_payload("solo", 4.0, t0.isoformat())]
    assert compare_window(engine, one)["byte_identical"], "identity control FAILED: a 1-surprise window must render identically"

    print("✓ affect_order_prompt_divergence selftest passed:", f"matched precondition holds | positive control divergent (membership-change, arousalΔ {pos['arousal_delta']:+.3f}) |", "identity control identical | falsifier can both DETECT divergence and REPORT identity")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Minor 64 Arm B / Stage B0 — full-prompt order divergence (no burn).")
    ap.add_argument("--selftest", action="store_true", help="validate the apparatus (no familiar, no burn)")
    ap.add_argument("--familiar", default=None, help="familiar name under familiar/ to run B0 against (real ledger)")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if a.familiar:
        return run(a.familiar)
    ap.error("give --selftest or --familiar <name>")
    return 2


if __name__ == "__main__":
    sys.exit(main())
