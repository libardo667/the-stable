# Cold re-review — isolated-Makers pre-reg v2, after the feedback-1 punch-list (2026-06-09)

**What this round is:** a **second pre-launch design review**, after the pre-registration was revised in
response to your prior cold read (`research/mr-review-history/2026-06-09-mr-review-feedback-1.md`, in
this clone — read it). Still NO `research/runs/` numbers: judge the *revised design* and the extractor
*primitives*, not a result. The full teacher-forced replay harness is deliberately NOT built yet — its
build is gated on THIS review. Your job: confirm the fixes actually resolve the blocking flaws, hunt for
new flaws the fixes introduced, and say whether the design is now **lockable**.

**Read (this clone):**
- `research/preregistrations/2026-06-09-isolated-makers-pen-vs-substrate-DRAFT.md` — the revised design.
- `research/analysis/elective_read_choice.py` — run `--selftest`; hand-trace `shuffle_null` and
  `per_point_disagreement` independently of the asserts.
- `research/mr-review-history/2026-06-09-mr-review-feedback-1.md` — your prior review (check the punch-list against it).
- Context (read-only, do not review): the `worldweaver` parent program.

**What changed in response to feedback-1 — verify each landed, and that it didn't break something:**
1. **§2 the killer (alignment):** statistic is now **teacher-forced one-step replay** — per-point
   disagreement over KEEP's *recorded* frozen choice points; the positional-sequence comparison is gone.
   Does teacher-forcing actually restore arm-invariance, and is the choice-point *set* (KEEP's recorded
   points) the right conditioning, or does scoring only KEEP's points bias against SWAP-only divergences?
2. **§4 the null:** the degenerate different-repo null is dropped; replaced by a **within-Maker
   frequency-preserving shuffle** (`shuffle_null`). Is the shuffle self-distance a valid denominator for
   the teacher-forced numerator, or a category mismatch (within-arm permutation spread vs cross-arm
   disagreement)?
3. **§3 salience:** symmetric fraction now reported across `band ∈ {0,0.25,0.5}`, HOLDS strong only if it
   survives a recency-neutralizing band. Sound, or still gameable?
4. **§6 C4:** pinned to **templated-opener/lexical** (the arm-C-visible signal), not the at-chance
   register embedder. Is the opener/lexical signal actually present and measurable on isolated Makers?
5. **§4/§8 stop-rule:** K is a pre-committed power **formula** (not a fill-in number); a **hard
   maturation cap** makes "below K at T_max" an INCONCLUSIVE result, not "grow longer"; θ are
   pre-committed **functions** with a **peeking firewall**. Does this actually close the rescue-spiral
   you flagged, or did it move the soft spot?
6. **§7 / §8.7:** the recall-bound caveat is stated (candidate set is recall-shaped → pen authors the
   *selection*, not the menu); a **the-stable parity gate** is required before cross-pen scoring. Enough?
7. **§0/§1 bug:** `salience_symmetric` is now asserted in the selftest; the inverted fixture comment is fixed.

**Plus the cross-seam correction (§10):** your §7 "city first" assumed a read affordance the city lacks
— verified in code (worldweaver city residents are CityWorld/no-FileScope; `grep FileScope(|read_roots
ww_agent/src/` is empty). The sequencing is inverted: the-stable first (only venue with the affordance),
city contingent on a powered slice + porting the affordance. **Does the inverted sequencing hold, and is
the-stable's frontier claim ("only venue testable now") legitimate or a rationalization?**

Hold us to the standing brief's locked falsifiers. Claims and raw evidence only; no verdict language
without a fresh adversarial check. If it's lockable, say so and on what; if not, the remaining blockers.
