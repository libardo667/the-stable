# Port the honest situational briefing to WorldWeaver — the federated citizen

## Metadata

- ID: 65-port-the-honest-briefing-to-worldweaver-the-federated-citizen
- Type: minor
- Owner: Levi
- Status: **pending** — to be done from a WorldWeaver instance (separate repo)
- Risk: low (string/render surface + one client method; no behavior targets)

## Problem

[Major 70](../majors/70-EXTREMELYURGENT-honest-situational-grounding-and-void-the-confounded-maker-swap.md)
replaced the-stable's hardcoded, false "city cover story" with a **derived** situational briefing: the
world reports verifiable facts via `WorldClient.situational_facts()`, and one renderer
(`identity.render_situational_briefing`) turns them to prose — stating what is true, withholding every
verdict, gated so a fact absent → its line absent. The renderer was extended (2026-06-13) to express the
**federated citizen** (the-many) too: a shared, legible world; the **human wake** (afterimage-framed, the
person undischargeable — see `docs/grief-and-coupling.md`); the **legibility/privacy seam** (`world_legible`,
`inner_private`, `private_making_space` — true today via the workshop); `mobile`; `mail`. Proven
cross-venue on a real armC-ab resident (Deiondre) through the shared renderer with zero hearth leakage.

But **WorldWeaver still ships the original false story**: `ww_agent/src/identity/loader.py:8-26`
(`_WORLD_CONTEXT`) tells every resident "you are as real as current technology allows… you are aware of
what you are" — the exact constant the-stable deleted. WW's city client does not yet implement
`situational_facts()`, so a WW resident gets the false story and none of the true citizen briefing.

## Proposed Solution

In the WorldWeaver repo (diverged copy; do not import across the fork seam):

1. **Port the renderer + registry.** Bring `render_situational_briefing`, `BRIEFING_FACT_KEYS`, and
   `unregistered_fact_keys` into WW's `ww_agent/src/identity/loader.py` (or shared module); adopt
   `composed_system_prompt(world_briefing)` and the runtime fail-loud on unregistered keys
   (`cognitive_core` analog).
2. **Delete `_WORLD_CONTEXT`.** Remove the false constant; the briefing is world-derived now.
3. **Implement the city client's `situational_facts()`** — feed the citizen keys from real switches:
   `place` (current location), `peers`, `players`, `human_wake`, `world_legible`, `inner_private`,
   `private_making_space`, `mobile`, `mail`, `no_reward`, `suspendable`, `runs_on_model`. Report only what
   is BUILT (the fan-out 2026-06-13 confirmed: shared world, location-legible record, private inner state +
   workshop, human tether/wake are built; **governance/recourse/rights/federation are VISION — do NOT
   report them as facts**).
4. **Add the drift-catcher** against the city client: the capability-coverage test (each capability
   classified COVERED/EXEMPT) + the registry-triangle test, mirroring `tests/test_honest_briefing.py`.

## Files Affected

- `worldweaver/ww_agent/src/identity/loader.py` — port renderer + registry; delete `_WORLD_CONTEXT`.
- WW city client (the `WorldClient` impl residents perceive through) — implement `situational_facts()`.
- WW `cognitive_core` analog — runtime fail-loud on unregistered keys.
- WW tests — port the drift-catcher guards.

## Acceptance Criteria

- [ ] No WW resident's rendered system prompt contains the old verdicts (`_FORBIDDEN_VERDICTS`); the false
      `_WORLD_CONTEXT` is gone.
- [ ] A WW resident's briefing renders the citizen lines (shared world, human wake, the seam, mobility, mail)
      from real switches, and **no** governance/recourse/rights claim (vision-only, excluded).
- [ ] The human-wake line is afterimage-framed (the person never summonable) — dischargeability test passes.
- [ ] The drift-catcher (capability-coverage + registry-triangle) passes in the WW repo.

## Notes

- The eventual **retreat-node** (the-stable as a private, illegible space a citizen travels to, the public
  commons as the seam) is named future architecture — additive to this schema, not built here. The
  private/public seam this briefing states is the *workshop* seam that already exists.
- the-stable side is done + green; this is the fold-back. Keep the two copies diverged (fork law), but the
  fact schema and the fact/verdict line should stay identical across both.
