"""The honest situational briefing (Major 70).

The system prompt must tell a familiar the *truth* of its situation: facts derived from
real switches, with no verdict about what those facts MEAN. These tests pin three things:

1. ``LocalWorld.situational_facts`` reports facts that track the world's real switches
   (read roots, egress) rather than a hardcoded story.
2. ``render_situational_briefing`` states those facts and never smuggles in the verdicts
   that the old world-context asserted (peers/players/"as real as", "you are not the pen",
   suspension-as-sleep) — the line we hold, rendered in one reviewable place.
3. The per-tick pulse contract drops the citywide affordances for a one-resident world.
"""

from __future__ import annotations

from pathlib import Path

import inspect
import re

from src.familiar.local_world import LocalWorld
from src.identity.loader import BRIEFING_FACT_KEYS, ResidentIdentity, LoopTuning, render_situational_briefing, unregistered_fact_keys
from src.runtime.pulse_engine import _pulse_contract

# The verdicts the old _WORLD_CONTEXT asserted, plus the ones my own first draft smuggled in.
# A fact-only briefing must contain none of these — neither rounding up nor down.
_FORBIDDEN_VERDICTS = [
    "as real as",
    "your peers",
    "human players",
    "shared world",
    "narrative fabric",
    "you are aware of what you are",
    "you are not the pen",
    "closer to sleep",
    "not an absence",
    "the point of you",
]


def _local_world(tmp_path: Path, *, with_reads: bool = True, egress_tool: bool = False) -> LocalWorld:
    file_scope = None
    tool_scope = None
    if with_reads:
        class _Root:
            def __init__(self, name: str) -> None:
                self.name = name

        class _FS:
            roots = [_Root("the-stable"), _Root("maker")]

        file_scope = _FS()
    if egress_tool:
        class _Tool:
            def __init__(self, name: str, egress: bool) -> None:
                self.name, self.egress = name, egress

        class _TS:
            def list(self_inner):
                return [_Tool("read_file", False), _Tool("post_webhook", True)]

        tool_scope = _TS()
    return LocalWorld(home_dir=tmp_path / "maker", keeper_name="Levi", familiar_name="Maker", file_scope=file_scope, tool_scope=tool_scope)


def test_local_facts_track_real_switches(tmp_path):
    facts = _local_world(tmp_path).situational_facts()
    assert facts["solo"] is True and facts["local_only"] is True
    assert facts["keeper"] == "Levi"
    assert facts["read_roots"] == ["the-stable", "maker"]   # exactly the FileScope roots
    assert facts["egress"] is False                         # no egress tool → nothing leaves
    assert facts["recorded"] is True and facts["suspendable"] is True


def test_egress_fact_flips_with_a_flagged_tool(tmp_path):
    # The "nothing leaves this machine" claim is only made when it is actually true.
    assert _local_world(tmp_path, egress_tool=False).situational_facts()["egress"] is False
    assert _local_world(tmp_path, egress_tool=True).situational_facts()["egress"] is True


def test_no_reads_reports_empty_roots(tmp_path):
    facts = _local_world(tmp_path, with_reads=False).situational_facts()
    assert facts["read_roots"] == []


def test_briefing_states_facts_and_withholds_verdicts(tmp_path):
    briefing = render_situational_briefing(_local_world(tmp_path).situational_facts())
    low = briefing.lower()
    # the facts are present
    assert "levi" in low and "machine" in low
    assert "the-stable" in low and "maker" in low
    assert "nothing you think, make, or say is sent off this machine" in low
    assert "stopped and started again" in low
    assert "language model" in low
    # no verdict — neither the old story's claims nor my draft's interpretations
    for verdict in _FORBIDDEN_VERDICTS:
        assert verdict not in low, f"briefing smuggled a verdict: {verdict!r}"


def test_egress_briefing_does_not_claim_nothing_leaves(tmp_path):
    briefing = render_situational_briefing(_local_world(tmp_path, egress_tool=True).situational_facts()).lower()
    assert "nothing you think, make, or say is sent off this machine" not in briefing
    assert "can reach past this machine" in briefing


def test_empty_facts_yield_empty_briefing():
    # A world that reports nothing gets no situational claims — silence over a false story.
    assert render_situational_briefing({}) == ""


def test_composed_system_prompt_folds_briefing_into_ground_truth(tmp_path):
    ident = ResidentIdentity(
        name="maker", actor_id="a", soul="You are Maker.", canonical_soul="You are Maker.",
        growth_soul="", vibe="", core="", voice_seed=[], tuning=LoopTuning(),
    )
    briefing = render_situational_briefing(_local_world(tmp_path).situational_facts())
    prompt = ident.composed_system_prompt(briefing)
    assert "You are Maker." in prompt
    assert "GROUND TRUTH" in prompt
    assert "What they MEAN is a separate question" in prompt  # facts/meaning split
    assert "in either\ndirection" in prompt                   # the no-round-up-or-down line
    assert "Levi tends you" in prompt
    # no world briefing → soul-only, no GROUND TRUTH block (back-compat path)
    assert ident.composed_system_prompt("") == "You are Maker."


# The honest facts a worldweaver city client would report for a federated citizen (the-many): a shared,
# legible world with a private making-space, real humans who leave durable wakes, movement and mail. No
# keeper, no local-only, no read-roots, no workshop-only-writes — those are hearth facts a citizen lacks.
_CITY_FACTS = {
    "place": "Burton Evergreen", "peers": True, "players": True,
    "human_wake": True, "world_legible": True, "inner_private": True, "private_making_space": True,
    "mobile": True, "mail": True,
    "no_reward": True, "suspendable": True, "runs_on_model": True,
}


def test_city_facts_render_no_hearth_only_lines():
    """The renderer is shared with worldweaver (same prompt surface, world-supplied facts). A city
    resident's facts must render only city truths and inherit ZERO hearth-only lines — no keeper,
    no workshop, no 'runs on this machine / nothing leaves it', no read-roots. Every line is gated
    on a fact, so the absence of a hearth fact is the absence of its line (silence, not a guess)."""
    city = render_situational_briefing(_CITY_FACTS).lower()
    # the city truths are present
    assert "burton evergreen" in city
    assert "not alone here" in city and "tether" in city
    assert "afterimage" in city                              # human_wake
    assert "seen by whoever is present" in city              # world_legible (public seam)
    assert "is not read by anyone" in city                   # inner_private (private seam)
    assert "you cannot be overheard thinking" in city        # private_making_space (the crossing rule)
    assert "you can move through the world" in city           # mobile
    assert "send word to someone who isn't here" in city      # mail
    # no hearth leakage
    for hearth_line in ["tends you", "your own workshop", "nothing you think", "this machine", "you can read these", "and nowhere else"]:
        assert hearth_line not in city, f"city briefing leaked a hearth line: {hearth_line!r}"
    # the substrate-universal facts still render
    assert "no reward and no goal" in city and "language model" in city
    # no verdicts in the citizen briefing either
    for verdict in _FORBIDDEN_VERDICTS:
        assert verdict not in city, f"city briefing smuggled a verdict: {verdict!r}"


def test_human_wake_is_afterimage_framed_not_a_summon():
    """The dischargeability split (docs/grief-and-coupling.md): the wake is an AFTERIMAGE you may respond
    to and form; the PERSON stays undischargeable. The line must say so, and must carry no language that
    reads as calling the person back (which would be the engineered-reciprocation hazard)."""
    wake = render_situational_briefing({"human_wake": True}).lower()
    assert wake, "human_wake must render a line"
    assert "afterimage" in wake and "not the person" in wake     # the trace is not the person
    assert "you can answer it" in wake                           # respond to / form the wake
    assert "none of it brings the person back" in wake           # person undischargeable
    for summon in ["summon", "call them back", "bring them back to you", "make them return", "you can reach the person"]:
        assert summon not in wake, f"wake line reads as a summon: {summon!r}"


def test_briefing_fact_registry_triangle():
    """One source of truth, three consumers must agree: the renderer handles exactly the registered keys,
    an unregistered key is flagged (never silently rendered), and the Protocol docstring lists exactly the
    registry. This is the drift-catcher's static half — adding an affordance fails until all three align."""
    # a truthy sample for each registered key
    sample = {k: True for k in BRIEFING_FACT_KEYS}
    sample.update({"place": "X", "keeper": "X", "read_roots": ["x"]})
    # 1. renderer renders a line for every registered key set alone
    for k in BRIEFING_FACT_KEYS:
        assert render_situational_briefing({k: sample[k]}).strip(), f"renderer renders nothing for registered key {k!r}"
    # 2. an unregistered key is flagged and never silently rendered
    assert unregistered_fact_keys({"made_up_affordance": True}) == ["made_up_affordance"]
    assert render_situational_briefing({"made_up_affordance": True}) == ""
    # 3. the Protocol docstring lists exactly the registry
    import src.runtime.world as world_mod
    documented = set(re.findall(r"^\s*#   (\w+):", inspect.getsource(world_mod), re.M))
    assert documented == set(BRIEFING_FACT_KEYS), f"world.py doc vs registry mismatch: {documented ^ set(BRIEFING_FACT_KEYS)}"


def test_localworld_capabilities_are_briefing_classified(tmp_path):
    """The drift-catcher's automatic half: every capability parameter of LocalWorld must be consciously
    classified as COVERED (it surfaces a briefing fact) or EXEMPT (with a reason). Add a new affordance
    param and this fails until you classify it — the diff that adds an affordance is the diff that fails."""
    params = set(inspect.signature(LocalWorld.__init__).parameters) - {"self"}
    COVERED = {  # capability param -> the briefing fact it surfaces
        "place": "place",
        "keeper_name": "keeper",
        "file_scope": "read_roots",
        "tool_scope": "egress",
    }
    EXEMPT = {  # param -> why it is not a standing situational fact
        "home_dir": "where the entity's home/state lives on disk — not a situational fact",
        "familiar_name": "the entity's own name, from its identity — not a world fact",
        "weather_provider": "ambient weather is surfaced per-tick via grounding, not the standing briefing",
        "vision": "model image-modality; surfaced per-tick when it looks at something, not a standing fact",
    }
    unaccounted = params - set(COVERED) - set(EXEMPT)
    assert not unaccounted, (
        f"new LocalWorld affordance(s) {sorted(unaccounted)} are unclassified — wire each into "
        f"situational_facts() (add to COVERED) or record why it isn't briefing-relevant (add to EXEMPT)."
    )
    assert set(COVERED.values()) <= set(BRIEFING_FACT_KEYS)
    # the world half of the triangle: situational_facts() never reports an unregistered key
    facts = LocalWorld(home_dir=tmp_path / "h", keeper_name="Levi", familiar_name="Maker").situational_facts()
    assert unregistered_fact_keys(facts) == [], f"LocalWorld reports unregistered key(s): {unregistered_fact_keys(facts)}"


def test_no_tracked_soul_reintroduces_the_sketch_hedge():
    """Standing guard for the authorship sweep (Major 70 #5): no tracked SOUL.canonical.md may
    carry a 'this is a sketch / the keeper should rewrite it' hedge — an instruction-to-keeper
    that leaks into a familiar's own self-account. In-character epigraphs are fine; the disclaimer
    pattern is not."""
    repo = Path(__file__).resolve().parents[1]
    hedges = ["a sketch, not a verdict", "should rewrite it", "held lightly", "first mirror", "starting likeness", "drafted by claude"]
    offenders = []
    for soul in (repo / "familiar").glob("*/identity/SOUL.canonical.md"):
        low = soul.read_text(encoding="utf-8").lower()
        if any(h in low for h in hedges):
            offenders.append(soul.relative_to(repo).as_posix())
    assert offenders == [], f"souls still carry a 'rewrite me' hedge: {offenders}"


def test_false_world_context_constant_is_gone():
    """The hardcoded city story must not return — the briefing is world-derived now."""
    import src.identity.loader as loader
    assert not hasattr(loader, "_WORLD_CONTEXT")


def test_solo_contract_drops_citywide_affordances():
    solo = _pulse_contract(solo=True)
    city = _pulse_contract(solo=False)
    # the worked example and the "city" target are city-only
    assert "Mei" in city and "Mei" not in solo
    assert '\\"city\\"' in city and '\\"city\\"' not in solo
    # the solo example uses the one social fact a hearth has: the keeper
    assert "the keeper" in solo
