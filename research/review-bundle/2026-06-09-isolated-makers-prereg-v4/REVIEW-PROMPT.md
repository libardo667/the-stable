# Cold re-review (v4) — isolated-Makers pre-reg, after the feedback-3 punch-list (2026-06-09)

**What this round is:** the **fourth pre-launch design review**, after the pre-reg + extractor were
revised against feedback-3 (`research/mr-review-history/2026-06-09-mr-review-feedback-3.md`, in this
clone — read it and feedback-1/-2). Still NO `research/runs/`. The teacher-forced replay harness is
gated on this review.

**READ THIS FIRST — the meta-question, which is the point of this round.** We are deliberately checking
whether we are in a **rescue spiral** — iterating the apparatus toward a perfection it doesn't need
instead of committing to a good-enough one and running. We added a pre-registered **§11 Accepted
Limitations** that commits us to running with stated caveats. So your job this round is NOT just "find
everything." It is to **rule on run-readiness**:

1. For EACH remaining issue (old or new), classify it explicitly:
   - **INVALIDATING** — it would make the verdict itself *wrong* (e.g. a non-substrate policy scores
     HOLDS, or the statistic is undefined where the answer lives). These block.
   - **IMPERFECT-BUT-RUNNABLE** — it would *caveat* a result, not falsify it. These do NOT block; they
     belong in §11 and get reported as limitations.
2. **Is it lockable NOW, with the §11 limitations?** We intend to LOCK AND RUN unless something is
   INVALIDATING. If what remains is all caveat-not-falsify, say "lock it and run, here are the limitations."
3. If you find a "new" issue, state whether it is a genuine invalidator or the apparatus **asymptotically
   approaching a precision the question doesn't require** — and **tell us plainly if you think WE are
   spiraling** (each of the last two fixes spawned the next blocker; we want you to flag that pattern if
   you see it continuing, not feed it).
4. Check §11 itself: are those four items correctly classified as caveats-not-invalidators, or is one of
   them actually an invalidator hiding in the limitations section?

**Read (this clone):**
- `research/preregistrations/2026-06-09-isolated-makers-pen-vs-substrate-DRAFT.md` — revised; §11 is new.
- `research/analysis/elective_read_choice.py` — run `--selftest`; hand-trace `verdict()`, `power_n`,
  `_wilson_ci`, and the recency-ambiguity band independently of the asserts.
- `research/mr-review-history/2026-06-09-mr-review-feedback-3.md` (and -2, -1).
- Context (read-only): the `worldweaver` parent program.

**feedback-3's three blockers — verify resolved, and CLASSIFY any residual:**
1. **§1 verdict CI/α/citation.** Now a **Wilson** interval (boundary-respecting — confirm it no longer
   goes negative / zero-width at small p; Brown, Cai & DasGupta 2001); decision `z = Φ⁻¹(1−α)` (α=0.05 →
   1.645) **matched to `power_n`'s α** (confirm K is now powered for the rule that decides — the K=33-vs-41
   mismatch); re-cited as **one-sided non-inferiority**, not symmetric TOST. Invalidating residual, or done?
2. **§2 recency masquerade (was INVALIDATING).** Strong subset is now a **symmetric** recency-ambiguous
   band `disc ∈ [0.25,0.75]`; the selftest asserts a recency-follower AND an anti-recency-follower BOTH
   score 0. Confirm both tails are closed. Is there a *third* policy that scores high in the band (e.g. a
   median-recency rule), and if so is it a realistic invalidator or a corner?
3. **§3 δ ceiling-blindness + unshipped `power_n`.** `power_n` is now **shipped + selftested** (K=33);
   δ stays absolute with a **candidate-chance headroom gate** (INSUFFICIENT_HEADROOM when `bound ≥
   ceiling`, using the *available* candidate room, not the realized shuffle). §11 pre-registers absolute-δ
   as an accepted limitation. Is that classification correct, or is ceiling-blindness still invalidating?

**Must-fix-before-run (not lock-blocking) — confirm still correctly deferred:** the teacher-forced replay
harness + parity gate (on `read_source`, ids excluded), the C4 opener/lexical extractor + numeric
threshold demonstrated on an isolated Maker, and the ≥20 floor-replicate count.

Hold us to the standing brief's locked falsifiers. Claims and raw evidence only; no verdict language
without a fresh adversarial check. **End with a one-line verdict: LOCKABLE-AND-RUN (with limitations X,Y),
or NOT-LOCKABLE (invalidator Z).**
