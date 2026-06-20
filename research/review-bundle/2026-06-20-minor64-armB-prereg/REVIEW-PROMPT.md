# Cold review — Minor 64 Arm B pre-reg (order → pulse/act), pre-build (2026-06-20)

**What this round is:** the **pre-build design review** of the pre-registration for Minor 64's Arm B —
the one arm of that experiment that would cost LLM burn. Arm A (deterministic, no burn) is already
complete; this round rules on whether Arm B's design is sound enough to LOCK and then build/run its
cheap first stage. There are no `research/runs/` for this; nothing has been built yet. The build is
gated on this review.

**READ THIS FIRST — what you are ruling on (not just "find everything").** The design is staged
cheap-first: a deterministic **Stage B0** (no LLM) that measures whether surprise *order* even survives
into the pulse prompt, and which can *falsify the whole premise before a dollar is spent*; and a gated
**Stage B1** (real burn) that measures pulse/act divergence against a same-prompt-resample noise floor.
Your job is to rule on run-readiness of **B0**, and on whether **B1** is worth any burn at all or is
underpowered theater. For each issue you raise, classify it:
- **INVALIDATING** — it makes a verdict *wrong* (a positive would be an artifact; a null is unreachable;
  the premise is false in a way the design doesn't catch). These block the lock.
- **IMPERFECT-BUT-RUNNABLE** — it caveats a result, not falsifies it. These belong in §11, not the gate.

**Read (this clone):**
- `research/preregistrations/2026-06-20-minor64-armB-order-vs-pulse-DRAFT.md` — the design under review.
- `src/runtime/salience.py` (~480–540) — **verify the premise in the bytes**: the igniting-trace
  assembly, `contribution = magnitude * 0.5^(age/AROUSAL_HALF_LIFE_SECONDS)` (~497, 505), and the
  `traces.sort(key=lambda item: -contribution)` (~513). The draft's §1 claims this sort is the *only*
  thing standing between raw chronology and the prompt. Confirm or break that.
- `src/runtime/pulse_engine.py` (~459–520) — the `for trace in traces[:6]` truncation (~500) and
  `render_prompt_for_debug` (~621). Check whether anything ELSE in `_build_prompt` carries chronological
  order into the prompt that the draft's §1 missed (recalled memories, `perception.recent_events`, the
  felt-node projection, observed_ts ordering anywhere).
- `research/harness/teacher_forced_replay.py` — run `python3 research/harness/teacher_forced_replay.py
  --selftest` (no burn). Confirm the `pen_fn`/MockLLM seam (~104–118, 176–185, 428), `parity_gate`,
  `c4_signal`/`c4_shifted`, `score_arm`, and `DELTA = 0.15` are what the draft reuses for Arm B, and
  that reusing the spine's `verdict` for a *between-order* (not between-model) comparison is sound.
- `research/analysis/affect_order_sensitivity.py` — Arm A. **Caveat: the real ledgers it reads
  (`familiar/*/memory/runtime_ledger.jsonl`) are gitignored runtime and are NOT in this clone, so Arm
  A's numbers are not reproducible here.** Read the schedule-construction logic (`_ev`, `load_windows`,
  the matched escalating/de-escalating pairing in `probe1`/`probe5`); take Arm A's reported result as
  given context (the draft's §0 summarizes it).
- Context (read-only): the `worldweaver` parent program.

**The premise (§1), stated so you can attack it directly.** Chronological surprise order reaches the LLM
*only* through (a) permutation of the contribution-ranking and (b) the top-6 truncation deciding which
traces survive — because traces are contribution-sorted, then the prompt renders them in passed order,
top 6. If that is true, B0 can pre-answer the experiment: if the rendered trace block is byte-identical
across escalating/de-escalating in ≥80% of real windows, order is erased before the LLM and **no burn is
justified** (a real offline finding, not a non-finding).

**The six questions this round must answer (classify each residual INVALIDATING vs IMPERFECT-BUT-RUNNABLE):**
1. **Premise completeness (§1).** Is the contribution-sort + top-6 truncation genuinely the ONLY path
   order takes to the LLM? Find any leak in `_build_prompt` the draft missed. A missed order-channel is
   INVALIDATING (the premise falsifier in §1 would then be wrong).
2. **The noise floor (§3).** Is same-prompt resample the right floor? Is the between-order vs
   within-prompt comparison sound? Is naming it "the Minor 50 principle" honest, or a stretch the draft
   should drop?
3. **Top-6 truncation confound (§1.2, §2.4).** Membership change is a qualitatively different cause than
   reordering. Should B1 separate rank-only windows from membership-change windows, or is pooling them
   as "what order does" defensible?
4. **Power (§8).** With ~17 real windows, is B1 worth any burn, or do B0 + Arm A already exhaust the
   recoverable signal? Are K=20, min-qualifying-windows=8, δ=0.15 defensible, or underpowered theater
   that B0 should be allowed to terminate?
5. **Verdict reachability (§5, §7).** Is ORDER-INERT (the null) genuinely reachable with a pre-committed
   acceptance region, or is this a design that can only confirm?
6. **Scope creep.** Does anything smuggle in the gated trend-term / afterimage recovery build that §9
   says stays gated?

Hold to the standing brief's locked falsifiers and the anti-spiral commitment (is this design itself a
rescue spiral, or a genuinely cheap-first test that lets B0 kill the burn?). Claims and raw evidence
only; cite `file:line` for every code-grounded claim; no verdict language without a fresh adversarial
check.

**End with a one-line verdict, exactly one of:**
- `LOCKABLE-AND-RUN-B0` (with limitations X, Y) — build and run B0 as written.
- `NEEDS-ONE-AMENDMENT: <the single most important fix>`
- `REJECT: <the premise or design is broken; why>`
