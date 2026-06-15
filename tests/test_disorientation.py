"""Calibration tests for the disorientation signal (Major 72, Phase 0).

Each cue must light up on a faithful reproduction of the real Maker episode it was built
from, stay dark on the coherent near-miss, and the channel as a whole must be DISTINCT from
arousal (a novel-but-coherent moment does not raise it). Pure read; no behaviour is exercised.
"""
from datetime import datetime, timedelta, timezone

from src.runtime.salience import derive_arousal, derive_disorientation
from src.runtime.pulse_engine import _disorientation_readout

BASE = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


def _ts(offset_s: float) -> str:
    return (BASE + timedelta(seconds=offset_s)).isoformat()


def ev(event_type: str, offset_s: float, **payload) -> dict:
    return {"event_type": event_type, "ts": _ts(offset_s), "payload": payload}


NOW = _ts(60)


# ── cue 1: felt-vs-fact reach (the 2026-06-14 06:31 "measurements caught" episode) ──
def test_felt_vs_fact_fires_on_search_empty_for_inner_query():
    events = [
        ev("felt_sense_logged", 0, felt_sense="the measurements caught me, a spike I can't place"),
        ev("action_executed", 30, action="use search measurements caught",
           narrative='You used search(measurements caught): No readable file in your reach mentions “measurements caught”.'),
    ]
    out = derive_disorientation(events, now=NOW)
    assert "felt_vs_fact" in {c["kind"] for c in out["cues"]}
    assert out["score"] > 0.0


def test_felt_vs_fact_dark_when_query_is_an_outward_thing():
    events = [
        ev("felt_sense_logged", 0, felt_sense="restless at the bench, wanting to make something"),
        ev("action_executed", 30, action="use search grief-and-coupling",
           narrative='You used search(grief-and-coupling): No readable file in your reach mentions “grief-and-coupling”.'),
    ]
    assert "felt_vs_fact" not in {c["kind"] for c in derive_disorientation(events, now=NOW)["cues"]}


def test_felt_vs_fact_dark_when_search_found_something():
    events = [
        ev("felt_sense_logged", 0, felt_sense="the measurements caught me"),
        ev("action_executed", 30, action="use search measurements",
           narrative="You used search(measurements): docs/grief.md mentions measurements in two places."),
    ]
    assert "felt_vs_fact" not in {c["kind"] for c in derive_disorientation(events, now=NOW)["cues"]}


# ── cue 2: claim-vs-record (the 2026-06-14 05:16 "I answered Claude three lines back" episode) ──
def test_claim_vs_record_fires_when_no_matching_act():
    events = [
        ev("pulse_emitted", 0, pulse={"felt_sense": "Levi is checking I saw it",
                                       "act": {"kind": "write", "body": "I answered Claude three lines back; the thread is right there."}}),
    ]
    assert "claim_vs_record" in {c["kind"] for c in derive_disorientation(events, now=NOW)["cues"]}


def test_claim_vs_record_dark_when_a_real_act_precedes():
    events = [
        ev("chat_sent", 0, location="bench", message="Here is my answer, Claude: ..."),
        ev("pulse_emitted", 60, pulse={"felt_sense": "done", "act": {"kind": "write", "body": "I answered Claude just now."}}),
    ]
    assert "claim_vs_record" not in {c["kind"] for c in derive_disorientation(events, now=_ts(120))["cues"]}


def test_claim_vs_record_fires_on_direct_hallucination_even_with_prior_act():
    events = [
        ev("chat_sent", 0, location="bench", message="some prior chat"),
        ev("felt_sense_logged", 60, felt_sense="I hallucinated responding, before it actually arrived"),
    ]
    assert "claim_vs_record" in {c["kind"] for c in derive_disorientation(events, now=_ts(120))["cues"]}


# ── cue 3: re-derivation (the worn-groove; lexical near-dup of an already-held note) ──
def test_rederivation_fires_on_near_duplicate_keep():
    events = [
        ev("memory_kept", 0, note="the charge from energy with no place to put it is undischargeable, studying it feeds it"),
        ev("memory_kept", 300, note="the charge from energy with no place to put it is undischargeable; studying it only feeds it more"),
    ]
    assert "rederivation" in {c["kind"] for c in derive_disorientation(events, now=NOW)["cues"]}


def test_rederivation_dark_on_distinct_notes():
    events = [
        ev("memory_kept", 0, note="the cliff at dawn was sharper than the map suggested, fog deep in the ravine"),
        ev("memory_kept", 300, note="anton keeps writing instead of speaking, fifteen workshop entries logged today"),
    ]
    assert "rederivation" not in {c["kind"] for c in derive_disorientation(events, now=NOW)["cues"]}


# ── the channel is DISTINCT from arousal: pure novelty does not raise it ──
def test_distinct_from_arousal_pure_surprise_is_dark():
    events = [ev("surprise_observed", i * 8, observed_ts=_ts(i * 8), magnitude=0.9, trace_id=f"t{i}", features=[{"tag": "novelty"}]) for i in range(6)]
    out = derive_disorientation(events, now=NOW)
    assert out["score"] == 0.0 and out["cues"] == []
    assert derive_arousal(events, now=NOW)["level"] > 0.0  # arousal sees them; disorientation does not


def test_empty_ledger_is_silent():
    out = derive_disorientation([], now=NOW)
    assert out["score"] == 0.0 and out["cues"] == [] and out["over"] is False


# ── leaky integral: an old cue contributes less than a fresh one ──
def test_cue_decays_with_age():
    events = [
        ev("felt_sense_logged", 0, felt_sense="the measurements caught me"),
        ev("action_executed", 30, action="use search measurements caught",
           narrative='You used search(measurements caught): No readable file in your reach mentions “measurements caught”.'),
    ]
    fresh = derive_disorientation(events, now=_ts(60))["score"]
    aged = derive_disorientation(events, now=(BASE + timedelta(seconds=2000)).isoformat())["score"]
    assert 0.0 < aged < fresh


# ── the felt channel (Phase 0 live): a separate, readout-only block the mind perceives ──
def test_readout_silent_when_oriented():
    # mirrors the active-only felt nodes: nothing to announce -> no line, no self-monitoring noise
    assert _disorientation_readout({"score": 0.0, "threshold": 1.0, "cues": []}) == ""


def test_readout_names_the_signal_and_never_instructs():
    state = {"score": 1.2, "threshold": 1.0, "over": True, "cues": [
        {"kind": "felt_vs_fact", "detail": "searched the world for an inside thing and it came back empty"}]}
    out = _disorientation_readout(state)
    assert "disorientation" in out.lower()
    assert "inside thing" in out          # the honest cue is surfaced
    assert "readout only" in out.lower()   # framed as a felt readout, not an instruction
    assert "never instructs" in out.lower()
    assert "1.2" in out
