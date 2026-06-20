# Cold re-review (v3) — isolated-Makers pre-reg, after the feedback-2 punch-list (2026-06-09)

**What this round is:** the **third pre-launch design review**, after the pre-registration and extractor
were revised against your feedback-2 (`research/mr-review-history/2026-06-09-mr-review-feedback-2.md`, in
this clone — read it, and feedback-1 before it). Still NO `research/runs/`: judge the *revised design* +
the extractor *primitives*. The teacher-forced replay harness is still gated on THIS review. Your job:
confirm feedback-2's three blockers are resolved, **stress the new statistical framing** (it changed
substantially), hunt for flaws the reframe introduced, and say whether it is now **lockable**.

**Read (this clone):**
- `research/preregistrations/2026-06-09-isolated-makers-pen-vs-substrate-DRAFT.md` — revised; note the new
  References section grounding each statistical choice.
- `research/analysis/elective_read_choice.py` — run `--selftest`; **hand-trace `verdict()`,
  `_recency_discordance`, and `shuffle_null` independently of the asserts.**
- `research/mr-review-history/2026-06-09-mr-review-feedback-2.md` and `-feedback-1.md` — check the
  punch-list against them.
- Context (read-only, do not review): the `worldweaver` parent program.

**Feedback-2's three blockers — verify each is resolved, and that the fix didn't break something:**
1. **Blocker §3 — the `D` ratio divided by ~0 in the strong-concern HOLDS regime.** Fixed by **dropping
   the ratio**: `verdict()` is now an **equivalence / non-inferiority decision** of `disagree(SWAP, KEEP′)`
   against the **same-pen KEEP/KEEP′ floor** within a committed margin δ (Schuirmann 1987; Lakens 2017);
   the shuffle (Gini-Simpson `1 − Σf²`) is the FALSE-side **ceiling, reported not divided by**; the
   permutation p uses the +1 correction (Phipson & Smyth 2010). **Questions for you:** Is the same-pen
   floor the right HOLDS reference (you argued it is in feedback-2 §2)? Is the one-proportion-CI
   non-inferiority logic correct, and is the CI level it uses defensible (it uses a 95% two-sided CI —
   should equivalence use a 90% CI / one-sided α)? The selftest's concentrated-KEEP case now returns
   HOLDS via the floor — is that the *right* answer when the chance ceiling is 0, or is single-source
   concentration still fundamentally uninformative and should it be flagged INCONCLUSIVE?
2. **Blocker §4 — the salience band was a monotone loosener (recency-follower scored 100% at every band).**
   Fixed by **recency-discordance**: the strong subset is choices where the elected source's
   discordance (fraction of established candidates MORE recent that the pen skipped) is `≥ τ=0.5`. The
   selftest proves a recency-follower now scores **0** discordant. Grounded as recency-as-an-
   alternative-specific-covariate (McFadden 1974). **Questions:** Does discordance actually neutralize
   recency, or is there a residual recency artifact (e.g. is `last_seen`-based recency the right rank, and
   does the τ=0.5 cut admit a subtler recency policy)? Is the prose/code direction now aligned (the
   recurring feedback-1/-2 bug)?
3. **Blocker §5 — δ unfilled, θ-forms unwritten ("pre-committed input list," not function).** Fixed:
   **δ = 0.15** committed as a number (the SESOI); `θ_hold = floor_mean + δ` as an explicit form;
   `HOLDS ⟺ CI_upper ≤ θ_hold`, `FALSE ⟺ CI_lower > θ_hold`. **Questions:** Is δ = 0.15
   (per-point disagreement-rate units) defensible as a SESOI, or arbitrary? Is the K power-formula now
   fully determined by `floor_mean` alone, with no operator latitude left after the pilot?

**Must-fix items (feedback-2 §6/§9) — check they landed:** baseline-variance calibration made MANDATORY
(§2); parity gate redefined on the **`read_source` channel, ids excluded** (the "byte-identical" claim
was false — uuid4 ids differ; §9); C4 opener/lexical extractor flagged **to-build with a committed
threshold**, with the borrowed 0.0%/33.8% speak-cohort evidence acknowledged (§9); §10 states the
load-bearing assumption (a thin *isolated* slice is non-decisive for the city port, never
channel-universal).

**On the literature:** I grounded the reframe in TOST/equivalence testing, permutation inference, the
Gini-Simpson index, conditional logit, and the forking-paths/preregistration literature (see the prereg's
References). **Check I represented these correctly** — especially that equivalence testing is the right
frame for a HOLDS-is-no-difference claim, and that I haven't misapplied the non-inferiority logic.

Hold us to the standing brief's locked falsifiers. Claims and raw evidence only; no verdict language
without a fresh adversarial check. If it's lockable, say so and on what; if not, the remaining blockers.
