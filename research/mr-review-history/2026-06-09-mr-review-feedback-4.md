# Mr. Review — cold re-review (v4): isolated-Makers pen-vs-substrate, run-readiness ruling (2026-06-09)

**Round reviewed:** `research/review-bundle/2026-06-09-isolated-makers-prereg-v4/REVIEW-PROMPT.md` →
the revised `research/preregistrations/2026-06-09-isolated-makers-pen-vs-substrate-DRAFT.md` (new §11
"Accepted Limitations") and its measurement spine `research/analysis/elective_read_choice.py`. Prior
method checked against `research/mr-review-history/2026-06-09-mr-review-feedback-{1,2,3}.md`. The
`worldweaver` parent program is mounted read-only and used only to (a) re-derive the borrowed parent
figures and (b) judge the §10 frontier claim — I reviewed only this repo's round.

**Method.** Started cold from this project's standing brief — inherited falsifiers and correction
principles, no findings. The dispatcher framing says "re-derive every number from `research/runs/`":
**there is still no `research/runs/`, and the round says so** — this is the fourth *pre-launch* design
review; the teacher-forced replay harness is gated on THIS review and is unbuilt. So "recompute" means
what it meant in feedback-1/-2/-3: run the shipped `--selftest`; **re-implement the load-bearing
functions from scratch (Wilson CI, the normal quantile via `statistics.NormalDist`, `power_n`) and
cross-check the module against my own**; build adversarial fixtures the module's own asserts do not
exercise; and read the substrate to settle what a design review can settle before tokens are spent.
Everything labeled "verified" I ran in this clone, offline (Python 3.10.12; stdlib only). No verdict word
without a fresh adversarial check.

**This round's job (per the prompt) is a run-readiness ruling, not a defect hunt.** Each remaining item
is classified **INVALIDATING** (would make the verdict itself wrong — a non-substrate policy scores HOLDS,
or the statistic is undefined where the answer lives) or **IMPERFECT-BUT-RUNNABLE** (would caveat a
result, not falsify it → belongs in §11). The round commits to LOCK AND RUN unless something is
INVALIDATING.

**Headline.** **All three feedback-3 blockers are genuinely closed, and I re-derived each fix
independently of the module's asserts.** (1) The verdict CI is now a real **Wilson** interval — it equals
my own Wilson to 1e-9, its lower bound never goes negative and it has non-zero width at p=0, exactly the
two Wald failures feedback-3 demonstrated; and the decision `z` now **equals** `power_n`'s — both
one-sided α=0.05 → 1.6449 — so the K=33-vs-41 power/decision mismatch is gone. (2) The recency band is
**symmetric** `[0.25,0.75]`; a recency-follower AND an anti-recency-follower both score 0 (re-derived),
closing the feedback-3 §2 anti-recency tail. (3) `power_n` is **shipped + selftested** (I reproduced K=33,
50, 62 from scratch), and δ's ceiling-blindness is **defanged — and by something stronger than the
headroom gate the prereg credits**: the strong subset *structurally* requires ≥3 candidates, which pins
the candidate-chance ceiling into `[0.667, 0.95]`, so δ=0.15 is 16–22% of available room everywhere it can
fire — not the 30% swing feedback-3 feared (the 2-source case is excluded from the subset, not gated out
of it). **This is the first round across four where the prior round's blockers all close AND I find no new
*invalidating* flaw introduced by the fixes.** I found two residuals — a middle-recency band corner and a
candidate-set/recall-shaping mismatch — and I classify **both IMPERFECT-BUT-RUNNABLE**, with reasons
below. Crucially: turning either into a "fourth blocker requiring the conditional logit before lock"
would *be* the rescue-spiral this round asked me to watch for. I decline to feed it.

**Verdict: LOCKABLE-AND-RUN.**

---

## 0. Recompute / re-derivation log (what I ran in this clone, what held)

| Claim | I ran | Result |
|---|---|---|
| `elective_read_choice.py --selftest` passes | the shipped selftest | **Passes.** `elective_points=2, recency_ambiguous=1, candidate_chance_ceiling=0.75`; recency & anti-recency followers both `recency_ambiguous=0`; `power_n(.8,.05,.1,.25)=33`. |
| **`_inv_norm` is accurate** (it underpins both `verdict`'s z and `power_n`'s) | vs `statistics.NormalDist().inv_cdf` at 7 points | **Max err ~1.8e-9.** Φ⁻¹(0.95)=1.644854, Φ⁻¹(0.975)=1.959964 reproduced. |
| **feedback-3 §1b: decision α == power α** (the K=33-vs-41 mismatch) | `verdict`'s `z=_inv_norm(1−α)` vs `power_n`'s `z_a=_inv_norm(1−α)`, α=0.05 | **Match: both = 1.6449** (one-sided α=0.05). The old hardcoded `z=1.96` (α=0.025 → K=41) is **gone**; I confirmed K@α=0.025 would be 41, K@α=0.05 is 33, and the code now uses the latter for *both* power and decision. |
| **feedback-3 §1a: Wilson CI, boundary-respecting** | re-implemented Wilson from scratch; compared to `_wilson_ci`; contrasted the old Wald | **Equal to 1e-9.** p=0.02,n=150 → **[0.0080, 0.0490]** (old Wald **[−0.0024, 0.0424]**, negative); p=0,n=200 → **[0, 0.0133]** (old Wald [0,0], zero-width); p=0.10,n=33 → **[0.0423, 0.2183]** (old Wald lower −0.0024). Lower bound never <0; width >0 at p=0. |
| **feedback-3 §3b: `power_n` shipped + reproducible** | re-implemented the one-proportion NI sample size; compared | **Reproduced exactly:** floor 0.1→**33**, 0.2→50, 0.3→62, 0.05→22. The K engine now exists in the module (it was absent in v3). |
| `_recency_discordance` direction matches prose | elect each of 4 recency-ranked sources | **Matches.** newest→0.0, 2nd→0.333, 3rd→0.667, oldest→1.0. Direction-inversion bug (the recurring one) still absent. |
| **feedback-3 §2: both pure tails closed** | a recency-follower and an anti-recency-follower, 40 returns each | **Both score 0/40 ambiguous.** recency mean_disc 0.0; anti-recency mean_disc 1.0; neither enters the band. The §2 anti-recency masquerade is closed. |
| **NEW probe: a *middle*-recency policy** | a deterministic **median-recency** follower (always re-read the median-rank source) | **40/40 ambiguous, frac 1.000, mean_disc 0.400.** A pure recency-rank function scores 100% in the strong subset. See §2. (second-newest disc 0.2 and second-oldest disc 0.8 both score 0 — they fall just outside the band.) |
| **NEW: ambiguous subset structurally requires ≥3 candidates** | enumerate possible disc = k/(n−1) per candidate count | 2 candidates → disc∈{0,1} (**never in band**); ≥3 → mid values appear. So `candidate_chance_ceiling` is **structurally ≥0.667**. See §3. |
| **feedback-3 §3a: headroom gate behaviour** | swept `floor_mean` against the structural ceiling 0.667 | Gate (`ceiling≤bound`) can only fire at **floor_mean ≥ 0.517** — a same-pen floor disagreeing >50% with itself. In realistic regimes it is **inert**; the *subset definition*, not the gate, bounds the ceiling. See §3. |
| `verdict()` four branches all reachable | independent branch table | **HOLDS** (disagree 0.12, ci_hi 0.163 ≤ bound 0.25); **FALSE** (0.55, ci_lo 0.492 > 0.25); **INCONCLUSIVE/underpowered** (0.28,n=25, ci straddles); **INCONCLUSIVE/insufficient_headroom** (ceiling 0.20 ≤ bound). No division by any null anywhere. |
| `perm_p` never zero, resolution-limited | floor of size 5 | min perm_p = 1/(5+1)=0.167. At the prereg's **≥20** floor replicates, min = 1/21 ≈ **0.048 < 0.05** — the +1 p can *just* reach significance. The ≥20 floor is principled. |
| Determinism (replay rests on it) | grep `random.*`/`perception_seed` in pulse_engine/pulse/integrator/cognitive_core/perception | **Empty.** Selection is `max()`/`sorted()` (`pulse_engine.py:286,299`). "All REPLAYS" rests on a real property. |
| `uuid4` ids still minted (parity must exclude them) | grep | `pulse.py:384`, `ledger.py:1422`. §9's `read_source`-channel, ids-excluded parity is the right criterion. |
| §10 venue fact: city has no `FileScope`/`read_roots` | grep the worldweaver mount | **Verified.** `FileScope(read_roots=…)` instantiated only in `ww_agent/scripts/familiar.py:267`; `ww_agent/src/` grep otherwise empty. the-stable `local_world.py:375-377` carries `file_scope`. §10 holds. |
| Borrowed figures exact | grep worldweaver `research/` | **All exact.** opener **0.0%/33.8%** (`runs/2026-06-08-armC-ab/FINDINGS.md:26`, a *speak* cohort); StyleDistance **0.11 ≈ chance 0.10** (`runs/2026-06-08-register-calibration/README.md:25`); keep-rate **~1.3%/tick, 6 keeps** (`runs/2026-06-09-pen-swap-keep/FINDINGS.md:40`). |
| Parent's powered axis & framing | grep the LOCKED prereg | A1-elective (relational) is **PRIMARY / "the actual powered unit,"** scored vs a **degree-preserving shuffle null** (LOCKED §27/§41-43). The parent's own **"the recession … *is* the finding"** (LOCKED §6) is real — the-stable §6 inherits it legitimately, not as a novel rationalization. |

The apparatus runs and the selftest pins the verdict-bearing fields. The three statistical fixes are real
and independently reproduced. The two residuals below are in the *recency-control geometry* and the
*candidate-set definition*, and neither is invalidating.

---

## 1. feedback-3 blocker §1 (Wilson CI + α match + NI framing) — RESOLVED

All three sub-parts close, and I re-derived each independently of the module's asserts:

- **§1a Wilson interval — RESOLVED.** `_wilson_ci` equals my from-scratch Wilson to 1e-9 on six (p,n)
  pairs. The two Wald pathologies feedback-3 demonstrated are gone: at p=0.02,n=150 the lower bound is
  **+0.0080** (Wald: −0.0024, a negative probability); at p=0,n=200 the width is **0.0133** (Wald:
  zero-width false precision). The HOLDS verdict sits on `ci_hi`, and `ci_hi` is now a proper Wilson upper
  bound in exactly the small-disagreement regime the design targets.
- **§1b α match — RESOLVED.** `verdict()` computes `z = _inv_norm(1−alpha)` and `power_n` computes
  `z_a = _inv_norm(1−alpha)`; with the shared default α=0.05 both are **1.6449**. The v3 defect was a
  hardcoded `z=1.96` (a two-sided-95% / one-sided-α=0.025 decision) while power used α=0.05 → K=41-vs-33.
  I confirmed the numbers (K@0.025=41, K@0.05=33) and that the code now uses **one** α for both. The run
  is powered for the rule that decides it.
- **§1c NI framing — RESOLVED.** I probed the low tail: there is no "over-agreeing" branch (HOLDS is
  `ci_hi ≤ bound`, full stop), so it is a **one-sided non-inferiority** test, not symmetric TOST. The
  prereg §5/§8 and the References now cite Lakens (2017) NI and explicitly say "NOT symmetric
  TOST/Schuirmann." Prose and code agree.

**Classification: not an issue. Done.**

---

## 2. feedback-3 blocker §2 (recency masquerade) — RESOLVED for the two pure tails; a *middle*-recency corner remains → IMPERFECT-BUT-RUNNABLE

**The promised fix landed and I re-derived it.** The band is symmetric `[0.25,0.75]`. A recency-follower
(mean_disc 0.0) and an anti-recency-follower (mean_disc 1.0) **both score 0/40 ambiguous** — the
feedback-3 §2 hole (anti-recency at 100% in a one-sided `disc≥τ` subset) is closed. Real credit: this is
the class of bug all three prior rounds kept catching, and the fix is correct.

**The prompt's own question — is there a *third* policy that scores high in the band? Yes: a
median-recency rule.** I built a deterministic **median-recency follower** (always re-read the median-rank
source). It scores **40/40 ambiguous, mean_disc 0.400** — a pure function of recency rank, sitting at the
*center* of the strong subset. So the band closes the two *tails* but admits a *middle*-recency-determined
policy. This is real and I reproduced it.

**Why it is a corner, not a realistic invalidator** (three grounds, the first decisive):

1. **The documented shared-pen positional bias runs the *opposite* way.** The "lost in the middle"
   effect (Liu et al. 2023) is that LLMs over-attend to the *ends* of a context and *neglect the middle*.
   So the realistic shared cross-family disposition pushes pens *toward the tails* — which the band
   **excludes** — and *away from* the band center. A deterministic median-preference shared across
   gemini + deepseek + sonnet is not a known artifact; if anything the literature predicts pens avoid that
   region. The band is well-placed against the bias that actually exists.
2. **The masquerade needs *agreement*, and a median-follower is contrived.** A false HOLDS requires KEEP,
   KEEP′, SWAP-B and SWAP-C to all deterministically pick the same band source. A high-temperature
   *random* pen (the realistic "no preference" case) instead **disagrees** at chance — I measured a
   random-pick pen at mean_disc 0.506, stdev 0.100 across the band; two such pens drive toward FALSE/
   INCONCLUSIVE, not HOLDS. Only a *shared deterministic* middle-recency rule masquerades, and (1) argues
   that rule does not exist across families.
3. **It leaves a fingerprint the design can surface cheaply.** A median-follower **pins** discordance
   (I measured stdev **0.000**, all points at 0.400); genuine varied choice **spreads** it (random:
   stdev 0.100). The detector already computes per-point discordance but reports only `mean_discordance`,
   not its dispersion — so the fingerprint is discarded. *Recommendation (reporting, not a lock gate):*
   report the discordance **stdev / histogram** over the strong subset, so a suspiciously median-pinned
   subset is visible at read time. This is what the (deferred) conditional logit would formalize.

**Classification: IMPERFECT-BUT-RUNNABLE.** The prereg §11.2 already scopes its claim correctly — it says
the band "excludes both pure recency tails (verified)" and "disarm[s] the **demonstrated** masquerades,"
and explicitly defers the conditional logit as "a robustness backstop we *may* report, not a lock
requirement." The middle-recency policy is a *not-yet-demonstrated, literature-disfavored* masquerade, not
a contradiction of that claim. **Two small honesty fixes I recommend but do not block on:** (a) §11.2
should name the residual as "both pure tails *and* second-newest/second-oldest are excluded; a
*middle*-recency-determined policy is admitted, judged a corner because the documented positional bias is
toward the tails"; (b) add the dispersion diagnostic above.

---

## 3. feedback-3 blocker §3 (δ ceiling-blindness + unshipped `power_n`) — RESOLVED, and stronger than the prereg credits

**`power_n` is shipped and I reproduced it from scratch** (floor 0.1→33, 0.2→50, 0.3→62). The v3
"unverifiable forking-path" (the K engine absent from the module) is closed; with the §1b α-match, K is
powered for the deciding rule.

**The ceiling-blindness is genuinely defanged — but by the subset definition, not the headroom gate, and
this matters for how the prereg describes the protection.** I derived the structural fact the prereg does
not state explicitly: **an ambiguous point requires ≥3 candidates.** With 2 candidates, `disc = skipped/
(n−1) ∈ {0,1}` — it can *never* land in `[0.25,0.75]`. So every point in the strong subset has ≥3
candidates, and `candidate_chance_ceiling` (the mean of `(c−1)/c`) is **structurally ≥0.667**. Consequences:

- **δ=0.15 is 16–22% of available headroom across the *entire* realizable ceiling range `[0.667, 0.95]`**
  — not the 17%-to-30% swing feedback-3 feared. The wild-variation regime (a 2-source choice, ceiling 0.5,
  δ=30% of room) **cannot occur in the subset**, because 2-source points are excluded by the band itself.
  So the absolute δ is far *less* ceiling-sensitive than v3 implied. §11.1's "δ ceiling-independent by
  choice" is therefore not just an accepted limitation — it is **structurally well-behaved on this
  subset**, which is a stronger defense than the prereg makes.
- **The headroom gate is a near-inert backstop, not the mechanism.** `ceiling ≤ bound` can only fire at
  `floor_mean ≥ 0.517` (a same-pen pen disagreeing with itself >50% of the time) — essentially never. The
  selftest's `INSUFFICIENT_HEADROOM` case uses a synthetic `ceiling=0.10` the real detector **cannot
  produce** on a non-empty ambiguous subset. The gate is harmless, but §8/§11.1's framing that "the
  headroom gate handles the only regime where this bites" is imprecise: **the subset's ≥3-candidate floor
  handles it; the gate guards a corner that does not arise.** Worth one sentence of correction; not blocking.

**Classification: RESOLVED (blocker closed); the §11.1 wording is IMPERFECT-BUT-RUNNABLE** — accurate
enough to run on, improvable by crediting the subset structure rather than the gate. FALSE stays reachable
on any non-empty ambiguous subset (ceiling ≥0.667 ≫ a bound of ~0.25), which I confirmed in the branch table.

---

## 4. NEW observation — the detector's candidate set is "all-established," but §7 concedes the real set is recall-shaped → IMPERFECT-BUT-RUNNABLE (harness-consistency must-fix)

This is the one substantive item the prior rounds did not sharpen, and it is the familiar
"prose-describes-a-different-object-than-the-code" pattern on a new surface — so I name it, then classify
it honestly.

**The gap.** `detect_elective_reads` counts `candidates = len(established)` = **every source ever read**,
and computes both `_recency_discordance` and `candidate_chance_ceiling` over that full set. But §7's
"honest bound" states plainly that the real candidate set for a return is **recall-shaped** ("the pen
authors the *selection among what recall + context surfaced*, not the menu of the already-seen"). The
detector scores over "the menu of the already-seen" — the object §7 says is *not* the real menu.

**Why it is not merely cosmetic.** Discordance is `skipped/(candidates−1)`. Inflating the candidate count
toward all-established (a) **dilutes discordance toward mid-band** (more candidates → finer disc → more
points land in `[0.25,0.75]`), so the strong-subset count (the K-gate input) and the ceiling are both
*optimistic*; and (b) a choice that was near-forced over a 2–3 item *reachable* menu can be mislabeled
"ambiguous over 8" — re-admitting a recency-determined reachable choice through the band the §2 control was
supposed to guard. Direction: **inflates slice size and FALSE-reachability**, i.e. it can route a
genuinely starved channel into the full burn rather than the §6 INCONCLUSIVE-by-starvation result.

**Why it is IMPERFECT-BUT-RUNNABLE, not INVALIDATING.** It does not make a non-substrate policy score
HOLDS, and the statistic stays defined. The failure mode is a *falsely fat* slice that then tends to
return INCONCLUSIVE-underpowered at the verdict (the real reachable choices being near-forced → low true
disagreement variance) — it self-corrects at the cost of burn, not at the cost of a wrong verdict. And it
is bounded by an empirical question the **pilot answers for free**: how close is the reachable menu to
all-established? **Must-fix-before-run (it rides on the deferred harness, so it is correctly deferable):**
the teacher-forced replay must define the reachable candidate set, and **the detector's candidate notion
must equal the replay's** — either model the recall-shaped reachable set in the detector, or have the
pilot report the reachable-menu-size distribution and show all-established ≈ reachable. As written, the
powering (K, ceiling) and the scoring would be computed on different menus. I flag it now so the harness is
built consistent, not retrofitted.

---

## 5. §11 audit — are the four "Accepted Limitations" correctly caveats, or is an invalidator hiding among them?

The round explicitly asked me to check §11 itself. I went item by item:

- **§11.1 (absolute δ, ceiling-independent) — correctly a caveat, and *under*-claimed.** Per §3, the
  subset's ≥3-candidate floor makes δ 16–22% of headroom everywhere it can fire; the regime where absolute
  δ would distort is *structurally excluded*, not merely accepted. Caveat. (Improve the wording to credit
  the subset, not the inert gate.)
- **§11.2 (band is the two-sided control; conditional logit not run) — correctly a caveat.** Both pure
  tails are closed (verified). The residual is the middle-recency corner of §2, which is
  literature-disfavored and fingerprintable — a caveat, not a falsifier. The classification holds; the
  recommendation is to *name* the residual and add the dispersion diagnostic.
- **§11.3 (single-trajectory TF measures concordance at KEEP's junctures only) — correctly a caveat.**
  This is the necessary consequence of single-trajectory teacher-forcing (feedback-2 §1 established it is
  not a *bias* but a *scope* limit), and §9 already bars upgrading a HOLDS to the lifetime free-run claim.
  Genuine scope limitation. Caveat.
- **§11.4 (`perm_p` diagnostic, not a gate) — correctly a caveat.** The verdict rides on the Wilson NI
  decision, not `perm_p`. I confirmed `perm_p` is never zero and that ≥20 floor replicates is the minimum
  for the +1 p to reach α=0.05 (1/21 ≈ 0.048). Caveat.

**No invalidator is hiding in §11.** All four are caveat-not-falsify. The §11 commitment ("we re-open only
an invalidator") is therefore the right policy and it does not need to fire this round.

---

## 6. Are you spiraling? — No, and here is the test I applied

The round asked me to flag the pattern if each fix keeps spawning the next blocker. The honest read of the
four-round arc:

- feedback-1: 3 blockers (alignment, null, K/θ). feedback-2: 2 closed, 1 **new flaw introduced by the
  null fix** (ratio ÷0), 1 re-reported (band loosener). feedback-3: 2 closed, but **3 new/again problems**
  (Wald CI, anti-recency tail, ceiling-blind δ + unshipped K). **feedback-4 (this round): all 3 closed,
  and I find no new *invalidating* flaw introduced by the fixes.**

That is a *converging* sequence, not a diverging one. The distinguishing test between "warranted
correctness fixes" and "asymptotic gold-plating": **were the feedback-3 blockers real?** They were — a CI
that returns negative probabilities *is* wrong, an α mismatch *does* underpower, an anti-recency policy at
100% in the "strong subset" *is* a live masquerade. Closing them was warranted, not perfectionism. The two
items I surface this round are *materially different in kind*: a corner the literature argues against, and
a consistency note on an explicitly-deferred build. **Neither meets the round's own INVALIDATING bar.**

The trap the prompt warned about is real and adjacent: I *could* manufacture "the band still admits
median-recency → run the McFadden conditional logit before lock" into a fourth blocker. That would be the
spiral — feeding the next fix to a question that already has a good-enough apparatus. I decline. The
conditional logit is correctly §11-deferred as a robustness backstop; the cheap dispersion diagnostic
covers the realistic risk. **The apparatus is good enough for the question it asks.** The receding-target
framing (§6) is not a rationalization — it is the *parent program's own* stance (LOCKED §6: "the recession
… *is* the finding"), verified in the mount, and the §4 `T_max` cap + §6 INCONCLUSIVE-by-starvation give
the question a stop-rule, not just the runs. Commit and run.

---

## 7. Falsifier ledger (standing brief §1) — re-checked against v4

- **Cross-family pen — ✓.** §2 commits SWAP-B/C to non-Claude (gemini/deepseek); maturation pen
  `claude-sonnet-4.5` (Maker's native). Not a within-family swap.
- **Swap unannounced — ✓.** §2 commits; "any 'I feel different' is confabulation."
- **Voice MEASURED not eyeballed (→ C4) — ⚠ measured-in-principle, instrument deferred.** Off the
  at-chance register embedder (StyleDistance 0.11 ≈ chance 0.10, re-verified) onto opener/lexical (the
  0.0/33.8 split, re-verified, honestly flagged as borrowed from a *speak* cohort). The extractor + numeric
  threshold + isolated-Maker demonstration remain a must-build-before-run (§9). Correctly deferred, not
  lock-blocking.
- **Decompose what is FALSE — ✓.** FALSE is reachable (branch table: disagree 0.55 → FALSE, 0.40 →
  FALSE) and identity (which-source) vs depth/voice is intact. The FALSE is now *cleanly* observable: the
  CI is boundary-respecting (§1) and the strong subset closes both demonstrated tails (§2).
- **Measurement-before-claim — ✓ for the statistics in scope; deferred items honestly deferred.** All
  three verdict primitives now compute what they claim (Wilson, NI α, symmetric band, `power_n`),
  re-derived independently. The teacher-forced replay harness + parity gate, the C4 extractor, and the ≥20
  floor replicates are correctly listed as must-build-before-run, not silently assumed.

---

## 8. Frontier judgment (context-informed)

**Genuine frontier, re-derived cold.** `FileScope(read_roots=…)` is instantiated in worldweaver **only**
in the *familiar* runner (`ww_agent/scripts/familiar.py:267`); the city world path builds no read
affordance (grep empty); the-stable carries `file_scope`. So the elective-READ channel is **structurally
untestable in the city today** — the-stable is not duplicating the parent's relational A1-elective axis
(confirmed PRIMARY/powered, degree-preserving null), it is reaching a *different, thinner* channel the
parent cannot currently touch. The inverted sequencing (the-stable first as the only venue; city
contingent on a powered slice **and** a `FileScope` port) follows from the venue fact, and §10 correctly
keeps a thin isolated result non-decisive for the city port. The one program-level caution (not this
round's to fix): the parent's *only proven-powered* axis is the relational one this design removes, so the
frontier buys clean attribution at the cost of the powered anchor — which §6/§10 concede, and which the
pilot K-gate exists precisely to measure.

---

## 9. Run-readiness ledger and one-line verdict

**Resolved since feedback-3 (all three blockers, each re-derived cold):**
1. **Wilson CI + α match (§1).** Boundary-respecting Wilson == my own to 1e-9; decision α = power α = 0.05
   (K=33, not 41); one-sided NI, correctly cited. **Done.**
2. **Symmetric recency band (§2).** Both pure tails score 0; a middle-recency corner remains but is
   literature-disfavored and fingerprintable. **Blocker closed; residual is a caveat.**
3. **δ + `power_n` (§3).** `power_n` shipped + reproduced (33/50/62); ceiling-blindness *structurally*
   defanged by the ≥3-candidate subset floor (δ = 16–22% of room everywhere it can fire). **Done.**

**IMPERFECT-BUT-RUNNABLE — report as limitations, do NOT block:**
- The **middle-recency band corner** (§2): add the discordance-dispersion diagnostic; name the residual in
  §11.2. Cheap, reporting-only.
- The **all-established vs recall-shaped candidate set** (§4): a must-fix-*before-run* harness-consistency
  item (the detector's candidate notion must equal the replay's reachable set), not a lock gate; the pilot
  measures the gap for free.
- §11.1/§8 should **credit the subset structure** (not the near-inert headroom gate) for taming δ; the C4
  extractor + threshold, the teacher-forced replay harness + `read_source`-channel parity gate, and the
  ≥20 floor replicates remain correctly deferred must-builds.

**INVALIDATING items: none found.** No non-substrate policy scores HOLDS by a realistic path (the only
band masquerade is a literature-disfavored, fingerprintable, deterministic median-follower), and the
statistic is defined everywhere the answer lives (the v3 divide-by-zero is gone; Wilson is well-defined at
p=0; the headroom branch routes the no-room case to INCONCLUSIVE rather than a hollow HOLDS).

---

### VERDICT: **LOCKABLE-AND-RUN** — with accepted limitations (1) the recency-ambiguity band admits a middle-recency corner the conditional logit would close (literature-disfavored, fingerprintable; add a discordance-dispersion diagnostic), and (2) the detector scores candidates as all-established while §7 concedes the real set is recall-shaped (a must-build-consistent harness item the pilot measures). Both caveat a result; neither falsifies it. Lock the pre-registration and run.

---

*Cold review. Every figure labeled verified was re-derived by me in this clone, offline:
`elective_read_choice.py --selftest`; `_inv_norm` vs `statistics.NormalDist` (err ~2e-9); a from-scratch
Wilson interval matching `_wilson_ci` to 1e-9 (and the old Wald's negative/zero-width failures); a
from-scratch `power_n` reproducing K=33/50/62; the recency-discordance direction map; recency-,
anti-recency-, second-newest-, second-oldest-, and **median**-recency policy fixtures through the band; the
≥3-candidate structural floor and the headroom-gate firing threshold; the verdict branch table; a
discordance-dispersion measurement (median stdev 0.000 vs random 0.100); and direct grep/reads of
`src/runtime/{pulse_engine,pulse,ledger}.py`, the worldweaver `ww_agent/` FileScope path, and the three
borrowed parent-program figures + the parent's powered-axis framing. No verdict word is stamped without
that check. No loyalty applied — claims and evidence only, including the two residuals I judged corners
rather than blockers, and the one place (§3) where the design is stronger than its own prose claims.*
