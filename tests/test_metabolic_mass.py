# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""Per-pulse metabolic mass in the ledger (Minor 63).

The substrate already captures token usage on every inference call and threw it away. These tests
pin that a pulse now records its own cost — model, prompt/completion tokens, latency, local-vs-cloud
pen — into its ``pulse_emitted`` ledger event, and that a usage-less (stub) mind is byte-identically
unchanged: no metabolic field, no behavior difference.
"""

from __future__ import annotations

import asyncio
import json

from src.identity.loader import LoopTuning, ResidentIdentity
from src.runtime.ledger import load_runtime_events
from src.runtime.pulse import route_pulse
from src.runtime.pulse_engine import LLMPulseProducer


def _identity() -> ResidentIdentity:
    return ResidentIdentity(
        name="sun_li", actor_id="actor-123",
        soul="You are Sun Li.", canonical_soul="You are Sun Li.", growth_soul="",
        vibe="watchful", core="Keeps a small tea stall.", voice_seed=["Tea?"], tuning=LoopTuning(),
    )


class _UsageLLM:
    """A live-like client: returns a pulse AND exposes the per-call accounting an InferenceClient does."""

    def __init__(self, *, local: bool = False):
        self.last_usage = {"prompt_tokens": 412, "completion_tokens": 88, "total_tokens": 500}
        self.last_model = "anthropic/claude-haiku-4.5"
        self.is_local = local

    async def complete(self, system_prompt, user_prompt, **kwargs):
        return json.dumps({"felt_sense": "the stall is quiet", "act": {"kind": "write", "body": "A note on the fog."}})


class _StubLLM:
    """The offline stub: no usage accounting at all (mirrors test_cognitive_core's stub)."""

    async def complete(self, system_prompt, user_prompt, **kwargs):
        return json.dumps({"felt_sense": "quiet", "act": None})


def _pulse_emitted(memory_dir) -> dict:
    events = [e for e in load_runtime_events(memory_dir) if str(e.get("event_type") or "") == "pulse_emitted"]
    assert len(events) == 1, f"expected exactly one pulse_emitted, got {len(events)}"
    return events[0].get("payload") or {}


def test_live_pulse_records_metabolic_mass(tmp_path):
    producer = LLMPulseProducer(llm=_UsageLLM(local=False), identity=_identity(), memory_dir=tmp_path)
    pulse = asyncio.run(producer(traces=[], stimulus={}, arousal=1.2))
    assert pulse is not None and pulse.metabolic is not None
    route_pulse(tmp_path, pulse)

    metabolic = _pulse_emitted(tmp_path).get("metabolic")
    assert metabolic is not None, "pulse_emitted must carry a metabolic payload for a live pulse"
    assert metabolic["model"] == "anthropic/claude-haiku-4.5"
    assert metabolic["prompt_tokens"] == 412
    assert metabolic["completion_tokens"] == 88
    assert metabolic["pen_local"] is False
    assert isinstance(metabolic["latency_ms"], int) and metabolic["latency_ms"] >= 0


def test_pen_local_flips_with_a_local_pen(tmp_path):
    producer = LLMPulseProducer(llm=_UsageLLM(local=True), identity=_identity(), memory_dir=tmp_path)
    pulse = asyncio.run(producer(traces=[], stimulus={}, arousal=1.2))
    route_pulse(tmp_path, pulse)
    assert _pulse_emitted(tmp_path)["metabolic"]["pen_local"] is True


def test_stub_pulse_omits_metabolic_and_is_unchanged(tmp_path):
    # A usage-less mind: no metabolic field on the pulse, none in the ledger event, behavior identical.
    producer = LLMPulseProducer(llm=_StubLLM(), identity=_identity(), memory_dir=tmp_path)
    pulse = asyncio.run(producer(traces=[], stimulus={}, arousal=1.2))
    assert pulse is not None and pulse.metabolic is None
    route_pulse(tmp_path, pulse)

    payload = _pulse_emitted(tmp_path)
    assert "metabolic" not in payload, "a usage-less pulse must not write a metabolic field"
    # the rest of the event is untouched
    assert payload["pulse"]["felt_sense"] == "quiet"


def test_summed_ledger_mass_reconciles_with_a_simple_analysis(tmp_path):
    # Acceptance #3/#4: a tiny analysis over the ledger can report total tokens / mean mass / the
    # local-vs-cloud split — and the summed per-pulse figures are exactly the per-call usage.
    for _ in range(3):
        producer = LLMPulseProducer(llm=_UsageLLM(local=False), identity=_identity(), memory_dir=tmp_path)
        route_pulse(tmp_path, asyncio.run(producer(traces=[], stimulus={}, arousal=1.2)))

    masses = [(e.get("payload") or {}).get("metabolic") for e in load_runtime_events(tmp_path) if str(e.get("event_type") or "") == "pulse_emitted"]
    masses = [m for m in masses if m]
    assert len(masses) == 3
    total_prompt = sum(m["prompt_tokens"] for m in masses)
    total_completion = sum(m["completion_tokens"] for m in masses)
    assert total_prompt == 412 * 3 and total_completion == 88 * 3
    assert all(m["pen_local"] is False for m in masses)  # the local/cloud split is recoverable
