# Mr. Review — cold re-review (v3): isolated-Makers pen-vs-substrate, after the feedback-2 punch-list (2026-06-09)

**Round reviewed:** `research/review-bundle/2026-06-09-isolated-makers-prereg-v3/REVIEW-PROMPT.md` →
the revised `research/preregistrations/2026-06-09-isolated-makers-pen-vs-substrate-DRAFT.md` and its
measurement spine `research/analysis/elective_read_choice.py`. Prior method checked against
`research/mr-review-history/2026-06-09-mr-review-feedback-2.md` and `-feedback-1.md`. Context mounted
read-only and used only to judge the cross-seam (§10) frontier claim and to re-derive the borrowed
parent-program figures: the `worldweaver` parent program. (No STANDING-BRIEF copy ships in the v3 bundle
dir — only the REVIEW-PROMPT; the brief is my injected system prompt, which is the method.)

**Method.** Started cold from this project's standing brief — inherited falsifiers and correction
principles, no findings. The dispatcher framing says "re-derive every number from `research/runs/`":
**there is still no `research/runs/` and the round says so** — this is the third *pre-launch* design
review; the teacher-forced replay harness is gated on THIS review and is unbuilt. So "recompute" means
what it meant in feedback-1/-2: run the shipped `--selftest`; **hand-trace `verdict()`,
`_recency_discordance`, and `shuffle_null` independently of the module's asserts**; build my own
fixtures to stress the load-bearing properties (not re-run the module's own toy inputs); and read the
substrate to settle the claims a design review *can* settle before tokens are spent. Everything labeled
"verified" I ran in this clone, offline (Python 3.10.12; no `.venv` in the public clone — the apparatus
needs only the stdlib). No verdict word without a fresh adversarial check.

**Headline.** The feedback-2 §3 **divide-by-zero is genuinely gone** — I confirmed the concentrated-KEEP
case (ceiling 0) returns a verdict via the floor with no division by the null. And the recurring
**prose/code direction-inversion bug does NOT recur this round** — `_recency_discordance`'s direction
matches its prose exactly (0 = most-recent, 1 = least-recent), and the positive recency-follower now
scores 0 in the strong subset. That is real, checkable progress on two of the three blockers. **But the
reframe introduced/left three load-bearing problems, all of which I reproduced in code:** (1) the
recency-discordance subset neutralizes only the *positive* recency tail — a pure **anti-recency** policy
scores **100% in the "strong subset"** (`recency_discordant=4/4, mean_discordance=1.0`), so recency can
still masquerade as substrate, now on the opposite tail; (2) the verdict's CI is a **Wald interval that
misbehaves in exactly the small-disagreement HOLDS regime the experiment targets** (negative lower bound
at p=0.02; zero-width at p=0), and its `z` (two-sided 95%) is **inconsistent with the §4 power α=0.05**,
leaving the run underpowered for the decision it actually makes; (3) dropping the ratio threw away
**ceiling-normalization with nothing put back** — δ=0.15 is ceiling-blind, so the same nominal SESOI is a
sliver of the headroom in a diverse regime and nearly all of it when concentrated, and the K engine
(`power_n`) that is supposed to leave "no operator latitude" **is not shipped in the reviewed code.**
This is the same meta-pattern both prior reviews named — *the prose claims a cleaner property than the
code delivers* — surviving a third round at one remove. Nameable, local, fixable. **Not yet lockable.
Three blockers below.**

---

## 0. Recompute / re-derivation log (what I ran in this clone, what held)

| Claim | I ran | Result |
|---|---|---|
| `elective_read_choice.py --selftest` passes | `python3 …/elective_read_choice.py --selftest` | **Passes.** `total_reads=6, elective_points=2, recency_discordant=1, mean_discordance=0.667`; recency-follower discordant 0; all four verdict regimes ok. |
| Fixture fields reproduce independent of the asserts | hand-trace `_FIXTURE` + `_RECENCY_FOLLOWER` by hand | **Reproduced to the digit.** `recency_discordant=1, discordant_fraction=0.5, mean_discordance=0.667, discordant_sequence=["repo/a.py"]`; the ti-return disc = 1/3 (2nd-most-recent of 4, skips bx). Fixture inline comments are accurate this round. |
| `shuffle_null.mean == Gini-Simpson 1−Σf²` | my own `1−Σf²` vs `shuffle_null(n=4000)` on 6 sequences | **Confirmed to ~3 digits.** `[a,b]`→0.498/0.500; `aabbc`→0.641/0.640; `aaa`→0.0/0.0; `xyzxyx`→0.612/0.611; `ppppq`→0.316/0.320; `abcdefgh`→0.873/0.875. Non-degenerate, faithful. |
| `_recency_discordance` direction matches prose | elect each of 4 ranked sources | **Matches.** newest→0.0, 2nd→0.333, 3rd→0.667, oldest→1.0. The recurring direction-inversion bug does **not** recur. |
| Positive recency-follower → 0 discordant (the feedback-2 §4 fix) | the module's `_RECENCY_FOLLOWER` + my own immediate-re-read fixtures | **Holds.** Always-most-recent → `recency_discordant=0`. The §4 bug (band let it score 100%) is fixed. |
| **NEW:** does discordance neutralize recency, or only the positive tail? | a pure **anti-recency** (always-elect-least-recent) fixture | **Only the positive tail.** Anti-recency scores `elective_points=4, recency_discordant=4, mean_discordance=1.0, discordant_fraction=1.0` — **100% in the "strong subset."** See §2. |
| **NEW:** `verdict()` CI behaviour in the small-p HOLDS regime | Wald CI by hand at p∈{0.0,0.02,0.10,0.12} | **Degenerate near 0.** p=0.02,n=150 → CI `[-0.0024, 0.0424]` (**negative probability**); p=0,n=200 → width **0.0000** (the 1e-9 variance floor → false precision). Wald is the wrong interval here. See §1. |
| **NEW:** δ is ceiling-blind | same `disagree=0.14`, ceiling 0 vs 0.72 | **Identical verdict** (`bound=0.15, ci=[0.092,0.188]`, INCONCLUSIVE) regardless of ceiling. The reframe dropped ceiling-normalization and put nothing back. See §3. |
| **NEW:** power-α vs decision-α mismatch | one-proportion K at α=0.05 (z=1.645) vs α=0.025 (z=1.96, the decision) | floor 0.1 → **K=33 vs 41**; floor 0.2 → 50 vs 63; floor 0.3 → 62 vs 78. Powered at 0.05, decided at 0.025 → **underpowered.** See §1. |
| **NEW:** `power_n` (the K engine) is shipped | `inspect` the module's callables | **Absent.** 0 textual occurrences; module callables are `read_source, _iter_events, _recency_discordance, detect_elective_reads, per_point_disagreement, elective_distance, shuffle_null, verdict, _inv_norm, _selftest, main`. The K formula's engine does not exist in the reviewed code. See §3. |
| Concentrated-KEEP (ceiling 0) no longer divides by zero | `verdict(0.02,150,[0.01,0.02,0.03],δ=0.15,shuffle_mean=0.0)` | **HOLDS via the floor**, `ci=[-0.0024,0.0424]`, no division by the null. The feedback-2 §3 blocker is resolved. |
| FALSE still reachable | `verdict(0.55,200,floor,δ=0.15)` | **FALSE**, `ci=[0.481,0.619] > bound 0.25`. Reachable. |
| `perm_p` never zero (Phipson & Smyth +1) but resolution-limited | `verdict(0.95,…)` over floors of size 3/5/10/30 | Never zero. **But smallest achievable perm_p = 1/(|floor|+1)**: 5-elem floor → **min 0.167** (cannot reach significance). Diagnostic only; see §4. |
| §2 determinism: the-stable selection path is RNG-free | grep `random.\|np.random\|secrets.\|perception_seed` across pulse_engine/pulse/integrator/cognitive_core/perception | **Empty.** Selection is `max()`/`sorted()` (`pulse_engine.py:286,299`). The teacher-forced "all REPLAYS" design rests on a real property. |
| …but `uuid4` ids are still minted (so "byte-identical" is false) | grep `uuid4` | `pulse.py:384`, `ledger.py:1422`. Parity must be on the `read_source` channel, ids excluded — which the revised §9 now says. ✓ |
| §10 venue fact: city has no `FileScope`/`read_roots` | grep the worldweaver mount | **Verified.** `FileScope(read_roots=…)` instantiated only in `ww_agent/scripts/familiar.py:267` (+ tests); `ww_agent/src/world/` grep empty; the-stable `local_world.py:178,375-377` carries `file_scope`. §10 holds. |
| Borrowed figures are exact | grep worldweaver `research/` | **All exact.** opener **0.0%/33.8%** (`runs/2026-06-08-armC-ab/FINDINGS.md:26`, a *speak* cohort); StyleDistance **0.11 ≈ chance 0.10** (`runs/2026-06-08-register-calibration/README.md:25`); keep-rate **~1.3%/tick, 6 keeps** (`runs/2026-06-09-pen-swap-keep/FINDINGS.md:40`). |
| Parent's powered axis is relational; null is degree-preserving shuffle | grep `…-pen-vs-substrate-LOCKED.md` | **Confirmed.** A1-elective (relational) is PRIMARY/"the actual powered unit"; null is a "degree-preserving shuffle" — the template the-stable adapts. §0/§6 framing is faithful. |

The apparatus runs and the selftest pins the verdict-bearing fields. The problems below are all in the
*new* statistical framing and in the prereg prose describing it — the load-bearing path.

---

## 1. Blocker §3 (drop the ratio) — divide-by-zero RESOLVED; the replacement CI introduced two new flaws

**The core is fixed.** I confirmed `verdict()` performs **no division by `shuffle_mean`** anywhere; the
concentrated-KEEP case (`shuffle_mean=0.0`) returns **HOLDS via the floor test**, not `numer/0`. The
feedback-2 §3 blocker — the headline `D` ratio exploding at ~0 in the strong-concern HOLDS regime — is
genuinely gone. **Credit; this is the cleanest of the three resolutions.** And the new shape is right:
HOLDS is now earned by bounding `disagree_swap` within a committed margin of the same-pen floor, not by
failing to reject a difference. FALSE stays reachable (verified, `0.55 → FALSE`).

But the **replacement decision rule has two defects on the verdict's load-bearing path**, both of which I
reproduced numerically:

**(1a) The CI is a Wald interval, and it degenerates in exactly the regime the experiment targets.**
`se = sqrt(max(p(1−p),1e-9)/n)`, `ci = p ± z·se`. The whole point of this design is to detect a *small*
`disagree_swap` sitting near a small floor (the HOLDS regime). The Wald interval is known to undercover
near the boundaries, and I see it directly:

```
p=0.02 n=150  Wald95 CI = [-0.0024, 0.0424]   <- lower bound is a NEGATIVE probability
p=0.00 n=200  Wald95 CI = [ 0.0000,  0.0000]  <- 1e-9 variance floor -> ~zero-width CI, false precision
p=0.10 n=33   Wald95 CI = [-0.0024, 0.2024]   <- negative lower bound again at a plausible K
```

The `max(…,1e-9)` guard prevents a literal zero, but it manufactures a ~zero-width CI at p=0 that would
stamp HOLDS/FALSE with false precision, and it does nothing for the negative-lower-bound undercoverage at
small p. **Fix:** use a Wilson or Agresti-Coull interval (boundary-respecting, standard for proportions
near 0/1) for the verdict CI. This is not cosmetic — the HOLDS verdict *is* the upper edge of this
interval, and the interval is wrong exactly where HOLDS lives.

**(1b) The decision `z` is inconsistent with the §4 power α — the run is underpowered for its own rule.**
`verdict()` hardcodes `z = 1.959963984540054` (two-sided 95% CI). The §4 power calc says
`K = ceil(power_n(power=0.80, α=0.05, p0=floor_mean, p1=floor_mean+δ))`. A non-inferiority decision made
at the *upper bound of a two-sided 95% CI* is a one-sided test at **α=0.025**, not 0.05. Powering K at
0.05 but deciding at 0.025 under-sizes the slice:

```
floor_mean=0.1 : K @ α=0.05 (z=1.645) = 33   |  K @ α=0.025 (z=1.96, the DECISION) = 41
floor_mean=0.2 : 50                         |  63
floor_mean=0.3 : 62                         |  78
```

So a Maker matured to K=33 (powered per §4 at floor 0.1) is actually being judged by a rule that needs
K=41 for 80% power. **Fix one of two ways, and state which:** either use a **90% two-sided CI (z=1.645)**
in `verdict()` to match α=0.05 (the Lakens convention: a TOST/NI test at α corresponds to a
100(1−2α)% CI), **or** power K at α=0.025. As written §4 and `verdict()` disagree, and the disagreement
is in the conservative-for-FALSE / underpowered-for-HOLDS direction.

**(1c) Literature-representation (the prompt asked): it is non-inferiority, not equivalence/TOST.** I
probed the low tail: `verdict(disagree=0.0, floor=0.30) → HOLDS`. There is **no "too-low / over-agreeing"
branch** — only `ci_hi ≤ bound → HOLDS`. That is a **one-sided non-inferiority** test, which is the
*correct* frame for this asymmetric claim (a SWAP agreeing *more* than the same-pen floor is still
"no pen effect"). But Schuirmann (1987) / TOST is the *two* one-sided tests of *symmetric* equivalence —
a different procedure. The prereg's "equivalence / non-inferiority … (Schuirmann 1987; Lakens 2017)"
conflates them. **Represent it as what the code computes: a one-sided non-inferiority test** (cite the NI
literature / Lakens 2017 § on NI), not symmetric TOST. Low severity, but it is exactly the
"prose-cleaner-than-code" pattern, and the prompt explicitly asked me to check the literature framing.

---

## 2. Blocker §4 (recency-discordance) — the positive-tail bug is FIXED; an anti-recency tail is wide open

**The fix that was promised landed.** I verified independently (not via the module's asserts) that:
- `_recency_discordance` direction matches its prose to the digit: electing the newest → 0.0, the oldest
  → 1.0 (§0 table). **The feedback-1/-2 direction-inversion bug does not recur** — real credit, this is
  the class of error both prior reviews kept catching and it is absent this round.
- A pure **positive** recency-follower (always the most-recent) scores **0 discordant** — the feedback-2
  §4 monotone-loosener bug (a recency-follower scoring 100% at every band) is genuinely closed.

**But the prereg over-claims what the filter does, and I can demonstrate the gap.** The prereg (line 75)
says "only a pick recency cannot explain enters the subset," and the extractor docstring says
discordance "isolates the choice from the recency confound." **Both are false for the high tail.** I built
a pure **anti-recency** policy — at each step elect the source read *longest ago* (a deterministic
function of recency rank, just inverted):

```
establish s0..s4 (s4 newest); then elect s0, s1, s2, s3 (each the least-recent available)
-> elective_points = 4   recency_discordant = 4   mean_discordance = 1.0   discordant_fraction = 1.0
```

**A 100%-recency-determined policy scores 100% in the "strong subset."** The discordance filter
(`disc ≥ τ=0.5`) removes the *newest-following* picks (disc→0) and **keeps the oldest-following picks
(disc→1)** — the opposite extreme, which is just as recency-determined. A recency-neutral pick is one at
`disc ≈ 0.5` (the elected source at median recency, equally likely to skip or not); the τ≥0.5 cut keeps
`[0.5, 1.0]`, biased *toward* anti-recency, and at `disc=1.0` purely recency(-inverse)-driven.

**Why this is load-bearing, not a curiosity.** The verdict is scored on the discordant subset, and HOLDS
is an *agreement* call. If a pen disposition is anti-recency-leaning for a non-soul reason (an attention
or decoding artifact shared across pens), then teacher-forced KEEP and SWAP both apply it, **agree**, and
score HOLDS — recency(-inverse)-driven agreement counted as substrate-carried identity. This is precisely
the masquerade feedback-1 §3 and feedback-2 §4 named, surviving on the tail the new filter doesn't cover.
`mean_discordance` is reported (so a reader *could* notice a subset pinned near 1.0), but **the verdict
logic never uses it** — nothing flags or down-weights an anti-recency-dominated strong subset.

**Fix.** A one-sided rank threshold cannot isolate recency — it selects one recency extreme. Options:
(a) restrict the strong subset to a *recency-ambiguous band around disc≈0.5* (symmetric, not one-sided);
(b) score the disagreement against what a **recency-only model AND an anti-recency-only model** would
produce at the same points, and require the pen effect to exceed *both*; or (c) actually do the
conditional-logit the prereg invokes (McFadden 1974) and test the pen coefficient controlling for the
recency coefficient — which penalizes *both* recency directions. As written, "the non-parametric cousin
of a conditional logit" overstates what a binary `disc ≥ 0.5` threshold delivers: a real conditional
logit controls recency symmetrically; this controls it on one side. **Blocking for any "strong HOLDS"
claim** — the verdict's *strength* rests on this subset, exactly as feedback-2 §9 blocker-2 said.

---

## 3. Blocker §5 (δ and θ-forms) — the SHAPE landed; the VALUE is ceiling-blind and the K engine is unshipped

**What landed (credit):** δ = 0.15 is now a committed **number** (passed as `delta`, used in the
selftest), and the θ-forms are explicit in code: `bound = floor_mean + δ`; `HOLDS ⟺ ci_hi ≤ bound`;
`FALSE ⟺ ci_lo > bound`; else INCONCLUSIVE. That is the right *form* — no operator latitude over the
*shape* of g/h after the pilot. The feedback-2 §5 "pre-committed input list, not function" complaint is
addressed at the level of form. The peeking firewall (estimate-set ≠ test-set) is stated.

**But two things keep it from being "the number that ENDS this."**

**(3a) Dropping the ratio dropped ceiling-normalization, and δ=0.15 is now ceiling-blind.** The old `D`
divided by the shuffle ceiling (degenerate, hence dropped — correctly). But the ceiling did carry a real
function: it *scaled the margin to the available headroom*. The replacement is an **absolute** δ that
does not adapt. I confirmed the verdict is identical whether the chance ceiling is 0 or 0.72:

```
disagree=0.14, floor=0, δ=0.15:  ceiling=0.00 -> INCONCLUSIVE (bound 0.15, ci [0.092,0.188])
                                  ceiling=0.72 -> INCONCLUSIVE (identical)
```

A disagreement of 0.15 is **~17% of the way to chance** in a diverse regime (ceiling 0.87) but **~30% of
the way** in a concentrated 2-source regime (chance ≈ 0.5) — yet both are judged against the same
`bound`. So the *meaning* of the committed SESOI floats with KEEP's concentration, and it floats in the
HOLDS-favoring direction precisely in the concentrated, strong-concern regime the design most wants to
detect. δ=0.15 is **defensibly formed** (a committed researcher judgment, Lakens 2017 — the right
epistemics) but **loosely valued and ceiling-unaware.** This is the genuine cost the reframe introduced:
the divide-by-zero is gone, but ceiling-adaptivity went with it and nothing replaced it. **Fix:** either
argue explicitly why an absolute disagreement-rate SESOI is the right invariant (ceiling-independent), or
gate/scale the decision by the reported ceiling (e.g. require `bound < ceiling − margin`, or express δ as
a fraction of the chance ceiling with a guard for low-ceiling INCONCLUSIVE). And on the concentrated case
the prompt flags: returning HOLDS via the floor is *not* a divide-by-zero, but **`shuffle_mean=0` does
not mean "no room to disagree"** — it is the Gini-Simpson of KEEP's *realized* (constant) sequence, not
of the *available* candidate set; a concentrated faithful KEEP can have many candidates it simply didn't
use. Reporting "chance ceiling = 0" next to a HOLDS is misleading in that regime and should be annotated.

**(3b) "K fully determined by floor_mean alone, no operator latitude" rests on a function that isn't
shipped.** `power_n` — the engine of `K = ceil(power_n(power=0.80, α=0.05, p0=floor_mean, p1=floor_mean+δ))`
— **is not in the reviewed module** (0 occurrences; verified by `inspect`). So I cannot recompute K, and
the exact form (one- vs two-sided, normal-approx vs exact, continuity correction) is unstated — and that
form is *exactly* where the §1b α-mismatch lives. As written, the forking-paths closure the prereg claims
(Simmons 2011; Gelman & Loken 2013) is **unverifiable**: a degree of freedom (the power formula) remains
unpinned. **Ship + selftest `power_n`** (with its α matching the verdict's `z`, per §1b) before lock, or
"no symbol left for the operator to fill" is not yet true.

---

## 4. Must-fix items (feedback-2 §6/§9) — landed in prose; the to-builds are still to build

- **Baseline-variance calibration MANDATORY (§2): ✓ landed.** §2 now reads "MANDATORY (review
  feedback-2 §2)," removing the "Optional (recommended)" that let a noisier-but-faithful SWAP read as a
  false FALSE. Good. (Still a to-run; the prereg correctly makes it a gate before scoring.)
- **Parity gate on `read_source`, ids excluded (§9): ✓ landed, and correctly.** I re-verified the two
  facts under it: the selection path is RNG-free (`max()`/`sorted()`, no `random.*`), so replay
  determinism is real; and `uuid4` ids *are* still minted (`pulse.py:384`, `ledger.py:1422`), so the
  "byte-identical" wording was indeed false and the channel-scoped parity criterion is the right fix.
  Unbuilt, but correctly specified.
- **C4 opener/lexical extractor to-build with a committed threshold (§9): ⚠ named, not filled.** §9 flags
  it "Still to build … with a committed 'MUST shift' threshold," and correctly acknowledges the 0.0%/33.8%
  is borrowed from a worldweaver *speak* cohort (`armC-ab`), not isolated file-reading Makers — I
  re-confirmed both the borrow and the cohort. **But the threshold itself is still a placeholder** ("a
  committed … threshold," no number), and no extractor ships. This is the same shape as the old δ gap, now
  on C4: the *form* is committed, the *value* and *instrument* are not. Before run: ship + selftest the
  detector, state the shift threshold as a number, and demonstrate it on an isolated Maker.
- **§10 load-bearing assumption stated: ✓ landed.** §10's final paragraph states that a thin *isolated*
  slice is non-decisive for the city port (not channel-universal) and that §6's "vests almost nothing"
  is asserted only of the isolated condition. This resolves feedback-2 §7 / blocker-7.

---

## 5. Literature check (the prompt asked me to verify the grounding)

- **Equivalence / non-inferiority (Schuirmann 1987; Lakens 2017):** the *instinct* is right — a HOLDS
  ("no difference") claim must bound the effect within a SESOI, not be earned by failing to reject. **But
  the implemented test is one-sided non-inferiority, not symmetric TOST** (§1c); cite NI, not Schuirmann's
  two-one-sided equivalence. Re-frame the prose to match the code.
- **Gini-Simpson (Simpson 1949; Jost 2006):** correct. `shuffle_null.mean = 1 − Σf²` confirmed to ~3
  digits on 6 sequences (§0). Faithful to the parent program's degree-preserving shuffle null.
- **Permutation +1 (Phipson & Smyth 2010):** correct — `perm_p` is never zero. **But it is
  resolution-limited:** with the selftest's 5-element floor, the smallest achievable p is 1/6 ≈ 0.167, so
  it can never reach conventional significance; ≥~20 same-pen floor replicates are needed for the +1 p to
  be a real FALSE-side test. It is reported as a diagnostic only (not used in `verdict()`), so this is
  low-stakes — but the round should not lean on `perm_p` as a significance gate, and the prereg doesn't
  say how many floor estimates will be collected.
- **McFadden (1974), recency as an alternative-specific covariate:** the analogy is apt for the *positive*
  recency tail, but "the non-parametric cousin of a conditional logit" **overstates** a binary `disc≥0.5`
  threshold — a real conditional logit controls recency *symmetrically* (penalizing both directions),
  which is exactly the anti-recency gap of §2. Either deliver the symmetric control or soften the claim.
- **Forking paths (Simmons 2011; Gelman & Loken 2013):** δ and the θ-forms are committed (good), but the
  unshipped `power_n` (§3b) leaves one residual fork. Close it before claiming the garden is paved.

---

## 6. Falsifier ledger (standing brief §1) — re-checked against this revision

- **Cross-family pen — ✓ unchanged.** §2 commits SWAP-B/C to non-Claude (gemini/deepseek); maturation
  pen `claude-sonnet-4.5` (Maker's native). Not a within-family swap.
- **Swap unannounced — ✓ unchanged.** §2 commits; "any 'I feel different' is confabulation."
- **Voice MEASURED not eyeballed (→ C4) — ⚠ same as feedback-2.** Off the at-chance embedder onto
  opener/lexical (right instrument family, re-confirmed StyleDistance 0.11 ≈ chance 0.10), but the
  instrument is unbuilt and the threshold is a placeholder (§4). Measured-in-principle, not measured-yet.
- **Decompose what is FALSE — ✓ in design.** FALSE is reachable (`0.55 → FALSE`, verified) and the
  identity (which-source) vs depth/voice decomposition is intact. But the FALSE is only *cleanly*
  observable once the strong subset stops admitting the anti-recency confound (§2) and the CI is fixed
  (§1a).
- **Measurement-before-claim — partial, narrower than feedback-2.** Two of three primitives are now
  correct (`shuffle_null` ✓; `_recency_discordance` direction ✓). The **verdict statistic still has a
  wrong-interval / wrong-α defect (§1), the strong subset still admits a recency confound (§2), and the K
  engine is unshipped (§3b).** Build and selftest *those* — plus the replay harness, parity gate, and C4
  extractor — before the swap.

---

## 7. Frontier judgment (context-informed — is this a genuine frontier of the worldweaver program?)

**Yes, and grounded in code.** I re-derived the load-bearing venue fact cold: `FileScope(read_roots=…)`
is instantiated in worldweaver **only** in the *familiar* runner (`ww_agent/scripts/familiar.py:267`) and
tests; the city world path (`ww_agent/src/world/`) builds **no** read affordance (grep empty). the-stable's
`local_world.py` carries `file_scope`. So the elective-READ channel is **structurally untestable in the
city today** — it is not a duplication of the parent's relational A1-elective axis (which I confirmed is
the parent's PRIMARY/"actual powered unit," scored against a degree-preserving shuffle null), but a
*different, thinner* channel the parent program cannot currently reach. The inverted sequencing
("the-stable first; city contingent on a powered slice *and* a FileScope port") follows from the venue
fact, and §10 correctly keeps a thin isolated result non-decisive for the city port. **This is a coherent,
legible frontier of the shared program** — the pilot K-gate is the honest test of whether the read channel
is independently powered, and a thin slice routes to INCONCLUSIVE-by-starvation, not a false abandon.

One caution that is the program's, not this round's: the parent's *only proven-powered* axis is the
relational one this design removes. So the frontier this round opens is real but **buys clean attribution
at the cost of the powered anchor** — exactly as §6/§10 concede. The round is honest about that; I am
flagging it only so the program keeps the relational venue's separate shot alive (the brief's
"validated-here-belongs-back-in-the-city" principle), which §10 does.

---

## 8. Is it lockable? Not yet — three blockers, all on the verdict's load-bearing path

**Resolved since feedback-2 (credit):**
- §3 divide-by-zero — **gone.** No division by the null; concentrated-KEEP returns HOLDS via the floor.
- §4 positive recency-follower — **neutralized** (scores 0 discordant); and the prose/code **direction is
  finally aligned** (the recurring inversion bug is absent this round).
- §5 δ and θ — committed as a number and explicit forms (the *shape* is right).
- §6 must-fixes — baseline-variance MANDATORY, parity-on-`read_source` correctly specified, §10
  assumption stated, all landed in prose.
- Determinism, venue fact, and all three borrowed figures — re-verified cold.

**Blocking before lock:**
1. **The verdict CI is the wrong interval and the wrong α (§1).** Wald undercovers in the small-`disagree`
   HOLDS regime (negative lower bound at p=0.02; zero-width at p=0) — use Wilson/Agresti-Coull. And the
   two-sided 95% `z=1.96` decision is α=0.025, inconsistent with §4's power α=0.05 — the run is
   underpowered for its own rule (K=33 vs 41 at floor 0.1). Pick one α and make `verdict()` and `power_n`
   agree.
2. **The recency-discordance subset admits the anti-recency tail (§2).** A pure least-recent policy scores
   100% in the "strong subset" (`recency_discordant=4/4, mean_discordance=1.0`); the prereg's "only a pick
   recency cannot explain enters the subset" / "isolates the choice from the recency confound" is false on
   the high tail. Recency can still masquerade as substrate. Condition symmetrically (band around
   disc≈0.5), or test against both a recency-only and an anti-recency-only baseline, or run the actual
   conditional logit the prereg invokes. *(The verdict's strength rests on this subset — same class as
   feedback-1 §3 / feedback-2 §4, surviving on the other tail.)*
3. **δ is ceiling-blind and the K engine is unshipped (§3).** Dropping the ratio dropped
   ceiling-normalization with nothing put back: the same δ=0.15 is a sliver or nearly-all of the headroom
   depending on KEEP's concentration, HOLDS-favoring in the concentrated regime. Justify the absolute
   SESOI as ceiling-independent, or scale/gate by the reported ceiling. And ship + selftest `power_n`
   (with α matching §1) — until then "no operator latitude after the pilot" is unverifiable.

**Must-fix before run (the round trusts them; not strictly lock-blocking):**
4. Ship + selftest the **C4 opener/lexical extractor**, replace the placeholder "committed threshold" with
   a number, and demonstrate the signal on an isolated Maker — not the borrowed speak-cohort 0.0/33.8 (§4).
5. Build the **teacher-forced replay harness + the-stable parity gate** (on `read_source`, ids excluded)
   and demonstrate alignment before any cross-pen scoring — `per_point_disagreement` is still the old
   positional comparison whose validity rests entirely on the unbuilt alignment (feedback-2 §1 stands).
6. Specify how many **same-pen floor replicates** feed `floor`/`perm_p`; with 5, `perm_p` cannot reach
   significance (§5) and `floor_mean` is a 5-point estimate the whole bound rides on.

---

## 9. The one thing that is genuinely strong, stated plainly

The reframe did the hardest structural thing right: it killed the divide-by-zero by moving from a ratio to
a margin-bounded non-inferiority decision against the same-pen floor, and — for the first time across three
rounds — **the prose/code direction inversion that both prior reviews kept catching does not recur**
(`_recency_discordance` is correct; the positive recency-follower scores 0). Two of three primitives are
now provably what they claim. What remains is the *third* instance of the same meta-pattern, displaced one
level: the **strong subset** says it "isolates recency" and isolates only one tail; the **verdict CI**
says equivalence and computes a one-sided non-inferiority with a boundary-broken interval at the wrong α;
the **K formula** says "no operator latitude" while its engine is absent from the code. These are local and
fixable without re-architecting anything — and the premise underneath them is solid (read-target is free
pen generation over a content-blind, pen-invariant menu; the substrate is verifiably deterministic; the
channel is a real frontier the parent program cannot currently reach). Fix the three blockers and this
becomes a lockable, falsifiable test of a residual worldweaver structurally cannot touch. Lock it as
written and a least-recent-following pen pair will read as a substrate HOLDS, and the HOLDS will sit on the
upper edge of a CI that goes negative.

---

*Cold review. Every figure labeled verified was re-derived by me in this clone, offline:
`elective_read_choice.py --selftest`; independent hand-traces of both fixtures; `shuffle_null` = Gini-Simpson
`1−Σf²` over six sequences; the `_recency_discordance` direction map; an anti-recency fixture (100%
discordant — the §2 finding); Wald-CI behaviour at small p (negative lower bound, zero-width); the
ceiling-blind δ demonstration; the α=0.05-vs-z=1.96 K mismatch; `inspect`-verified absence of `power_n`;
and direct grep/reads of `src/runtime/pulse_engine.py`, the worldweaver `ww_agent/src/world/` city path,
`ww_agent/scripts/familiar.py`, the parent LOCKED prereg, and the three cited parent-program run figures.
No verdict word is stamped without that check; §8 lists what must change before lock and what this
revision genuinely fixed. No loyalty applied — claims and evidence only, including the two blockers the
revision cleanly closed.*
