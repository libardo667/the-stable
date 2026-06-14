# improvements/ — the work-item ledger (the-stable)

This is the project's **work-item harness**: where an intended change is written down *before* it is
built, reviewed against a rubric frozen ahead of the work, and archived once it ships. `majors/` hold
large arcs; `minors/` hold bounded changes. The methodology that governs them lives in `harness/`
(adoption guide, operating model, quality gates, pruning playbook), with the item shapes in
`MAJOR_SCHEMA.md` / `MINOR_SCHEMA.md`.

**Append-only discipline.** `majors/` and `minors/` hold only **live** work — in progress, proposed, or
held-for-later. When an item ships or is retired it moves to a local **`history/`** archive (gitignored),
never deleted. So this published folder is always an honest snapshot of what is actually *open*: the full
ledger is kept, it just isn't all shown at once, because it isn't all live.

**Provenance — shown with the seams.** These items are written by the operating AI instance in working
session with the keeper, who sets direction and holds the veto. They are kept as worked: the reasoning,
the dependencies, the reviewer corrections that changed them. Some carry a *"held loosely / post-verdict"*
banner — those are a research agenda, not commitments. This is the same two-hands honesty the rest of the
project runs on: a model's hand, shown as a model's, not laundered into the keeper's voice.

## Active majors

**The cognitive substrate (49–59) — shared with WorldWeaver, canonical here.**
The architecture both repos run on: a mechanistic substrate under a single predictive pulse, a self that
comes apart at clean joints, the growth pipeline. These stay in `majors/` as the depended-on reference
even where already shipped, because the later items build on them.
- `49` demote loops to mechanism · `50` residents as practitioners · `51` grow a model from the ledger
- `52` familiar as companion surface · `54` capability surface (tools/MCP) · `55` sight + scoped files
- `56` belief provenance · `57` the keeper→familiar seam · `58` self-delta maturation · `59` tool-loop in ignition

**The research frontier — held loosely, post-verdict, no timescale.**
Experiment designs caught from keeper conversations and kept honestly as *open questions*, not plans:
- `60` rung-1 distillation · `61` the Witness · `63` the dischargeability dial · `64` counterfactual biographies
- `65` cross-embodiment transplant · `66` identity factorization · `67` the confederate world
- `68` tiered pens · `69` the metabolism of a persistent mind

**Publishing & positioning.**
- `62` the publishing keystone (the arc that produced this ledger going public)

> Funding, grant, and application-strategy items (the grant-pack refresh, the application calendar, the
> spend-ledger backfill) are tracked privately and are not part of this public cut.

## Active minors

Bounded changes and experiment seeds — each file names its own problem and carries its own status:
- *measurement* — `47` cost before/after · `50` matched-window re-measure · `63` per-pulse metabolic mass · `64` cost of order (affect)
- *safety & ethics* — `54` the egress×goal×learning rule · `59` the coercion-ethics gate · `65` port the honest briefing to WorldWeaver
- *companions & adoption* — `52` a new personal companion · `55` the responsive-world experiment · `57` first-run as adoption · `58` the folio exhibition
- *positioning & ops* — `60` welfare-science positioning · `53` publish the-stable

## See also

- [`harness/`](harness/) — the operating model, quality gates, and pruning playbook this ledger runs on.
- `history/` — a local, append-only archive of shipped and retired items (kept, not published).
- [**WorldWeaver**](https://github.com/libardo667/worldweaver) — the whole made thing this is a pilot of: it applies these same mechanisms at city scale
  and is the front door to the program. The cognitive substrate (majors 49–59) is **canonical here**;
  WorldWeaver keeps pointer stubs into it.
- **the-mews** — a sibling embodiment in the same program.
- [**prune**](https://github.com/libardo667/prune) — this harness shipped empty, as a reusable scaffold for any project; this folder is that
  scaffold with the work actually done in it.
