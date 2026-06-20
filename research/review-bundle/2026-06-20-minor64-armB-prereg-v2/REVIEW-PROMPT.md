# Cold re-review (v2) — Minor 64 Arm B pre-reg (order → pulse/act), after feedback-5 (2026-06-20)

**What this round is:** the **second** pre-build design review of Minor 64 Arm B. v1 (cold review #5,
`research/mr-review-history/2026-06-20-mr-review-feedback-5.md`, in this clone — READ IT FIRST) returned
**NEEDS-ONE-AMENDMENT** and cold-recomputed two INVALIDATING B0 bugs plus power caveats. The pre-reg was
revised (v2; see its top changelog). Your job is **run-readiness of B0**, not "find everything":

- Classify each remaining issue **INVALIDATING** (a verdict would be *wrong*) vs **IMPERFECT-BUT-RUNNABLE**
  (it caveats, not falsifies). We intend to LOCK AND RUN B0 unless something is INVALIDATING.
- Verify the v1 fixes actually landed in the bytes; do not take the changelog on testimony.
- Flag a rescue spiral if you see one (each fix spawning the next blocker).

**Read (this clone):**
- `research/mr-review-history/2026-06-20-mr-review-feedback-5.md` — the v1 review you are checking against.
- `research/preregistrations/2026-06-20-minor64-armB-order-vs-pulse-DRAFT.md` — the v2 design (changelog at top).
- `src/runtime/salience.py` (~480–531) and `src/runtime/pulse_engine.py` (~459–587, esp. the trace loop
  `:500–503`, the **arousal-scalar opener `:583`**, and `render_prompt_for_debug :621`). **Re-verify in the
  bytes** that v2's §1 now names every order channel (contribution-rank, top-6 membership, the rendered
  arousal scalar, the stable-sort tiebreak). Re-recompute the arousal-scalar delta on a matched pair if you
  wish (feedback-5 got escalating 5.11 vs de-escalating 1.62 on `{1.0, 5.0}`).
- `research/harness/teacher_forced_replay.py` — confirm v2's §3 correctly RETRACTS v1's "reuse the spine,
  no new machinery": `per_point_disagreement` is teacher-forced-aligned-only (its docstring), and Arm B's
  two-prompt/resample design needs a re-specified two-sample statistic. Is v2's replacement sound?
- `research/analysis/affect_order_sensitivity.py` — confirm v2's B0 no longer reuses `_ev`/`load_windows`
  (the bug feedback-5 proved collapses the trace block to the empty fallback), and instead preserves full
  surprise payloads. (The real ledgers it reads are gitignored runtime, NOT in this clone — Arm A's numbers
  are not reproducible here; take them as given context.)
- Context (read-only): the `worldweaver` parent program.

**The six questions for this round are in the v2 draft's "Brief to the cold reviewer — v2" section** (did
the B0 fix land; is the differential-probe design with a fixed memory_dir sound or does it bias PREMISE-DEAD;
is the §3 B1 statistic re-spec right and what estimator would you require selftested; is the power honesty
adequate; is the one new instrument a spiral or required; any scope creep). Answer each, cite `file:line`
for every code-grounded claim, hold to the standing brief's falsifiers and anti-spiral commitment.

**End with a one-line verdict, exactly one of:**
- `LOCKABLE-AND-RUN-B0` (with limitations X, Y) — build and run B0 as written.
- `NEEDS-ONE-AMENDMENT: <the single most important fix>`
- `REJECT: <the premise or design is broken; why>`
