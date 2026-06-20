# Mr. Review — cold re-review (v2): isolated-Makers pen-vs-substrate, after the feedback-1 punch-list (2026-06-09)

**Round reviewed:** `research/review-bundle/2026-06-09-isolated-makers-prereg-v2/REVIEW-PROMPT.md` →
the revised `research/preregistrations/2026-06-09-isolated-makers-pen-vs-substrate-DRAFT.md` and its
rewritten measurement spine `research/analysis/elective_read_choice.py`. Prior review checked against:
`research/mr-review-history/2026-06-09-mr-review-feedback-1.md`. Context mounted read-only and used only
to judge the cross-seam (§10) claim and to verify the parent-program figures the prereg cites: the
`worldweaver` parent program.

**Method.** Started cold from the standing brief (this project's own — I inherited falsifiers and
correction principles, no findings). The dispatcher framing says "re-derive every number from
`research/runs/`": **there is no `research/runs/` and the round says so** — this is the second *pre-launch*
design review; the teacher-forced replay harness is gated on THIS review and is not built. So "recompute"
means what it meant in feedback-1: run the shipped script's `--selftest`; **hand-trace the two new
primitives (`shuffle_null`, `per_point_disagreement`) independently of the module's asserts**; build my
own fixtures to test the load-bearing definitions; read the substrate to settle the claims a design
review *can* settle before tokens are spent (is the swap-took gate measurable? is the substrate actually
RNG-free? does the city actually lack the read affordance?). Everything labeled "verified" I ran in this
clone, offline. No verdict word without a fresh adversarial check.

**Headline.** Two of feedback-1's three *blocking* items are substantially resolved and one is cleanly
resolved: **the null fix (§4) is the best work in this revision — it is correct, and I verified it is the
non-degenerate Gini-Simpson null the parent program actually uses.** **The K rescue-spiral is
structurally closed** by the hard maturation cap. But the revision **introduced one new flaw and left one
old one merely re-reported, not fixed**, and both sit on the verdict's load-bearing path: (1) the headline
statistic `D = disagree / shuffle_null` now **divides by ~zero in the strong-concern HOLDS regime** — the
old null was inert-at-1, the new null is **explosive-at-0** exactly where the target effect lives; (2)
**the salience band is a monotone *loosener*, not a recency-neutralizer** — the prose describes a
different predicate than the code computes (the same prose/code direction-inversion feedback-1 caught at
line 158, recurring at the prereg level), and a pure recency-follower still scores 100% symmetric at every
band. The §10 cross-seam correction **holds in code and legitimately corrects a factual error in my own
prior review.** **Not yet lockable. Three concrete blockers below.**

---

## 0. Recompute / re-derivation log (what I ran in this clone, what held)

| Claim | I ran | Result |
|---|---|---|
| `elective_read_choice.py --selftest` passes | `python3 …/elective_read_choice.py --selftest` | **Passes.** `total_reads=6, distinct_sources=4, elective_points=2, salience_symmetric=2`, shuffle-null(a,b)≈0.4995. |
| §0/§1 fix: verdict field now **asserted**, not printed | read `_selftest` ll.203-205 | **Landed.** `assert r["salience_symmetric"]==2` and `assert r["symmetric_fraction"]==1.0` present. |
| §0/§1 fix: inverted line-158 comment fixed | read fixture comment l.189 | **Landed.** Comment now says the point IS salience-symmetric, matching the True the code computes. An honest "KNOWN WEAKNESS … §3 NOT yet fixed here" comment (ll.206-209) is added. |
| `shuffle_null.mean` == Gini-Simpson `1−Σf²` (a real null over the same vocab) | independent fixtures vs my own `1−Σf²` | **Confirmed to ~3 digits** across 5 sequences (e.g. `[a,b]`→0.503 vs 0.500; `[a,a,b,b,c]`→0.640 vs 0.640). Non-degenerate. The §4 fix is real. |
| `per_point_disagreement` is the SAME function as the old `elective_distance` | `elective_distance is per_point_disagreement` | **True (alias).** Teacher-forcing is a *protocol* property, not a code change — see §1. |
| Old killer bug still latent if fed free-run sequences | `pp_disagree([a,b,c,d,e,f],[a,b,X,c,d,e])` | **0.6667** (the feedback-1 bug). Same inputs aligned (`…,[a,b,X,d,e,f]`) → **0.1667.** Fix lives in alignment, which is unbuilt. |
| **NEW:** `D = numer / shuffle_null(KEEP′)` divides by ~0 when KEEP concentrates | sweep denom vs concentration | **single-source returns → denom 0.000 (D undefined); 9:1 → 0.180; 4:1 → 0.319.** Monotone. Selftest itself encodes `shuffle_null([a,a,a]).mean==0.0`. See §3. |
| §3 band is a recency *neutralizer* (prose) | 400 random ledgers + a recency-follower | **Refuted.** `symmetric_fraction` is **monotone non-decreasing** in band (0 violations / 395 non-vacuous); a recency-following-offset-by-one policy scores **100% symmetric at band 0, 0.25, AND 0.5.** See §4. |
| §10 venue fact: city has no `FileScope`/`read_roots` | grep the worldweaver mount | **Verified.** `FileScope(` is instantiated only in `ww_agent/scripts/familiar.py:267`; `city_world.py`/`client.py` build no read affordance; the-stable `local_world.py` carries `file_scope`. See §7. |
| §2/§9: the-stable substrate is RNG-free (replay-determinism a no-op) | grep runtime + read `pulse_engine.py` selection | **Substantially true.** No `random.*` in `pulse_engine/pulse/perception/integrator/cognitive_core`; selection is `max()`/`sorted()`. Only `uuid4()` event-IDs remain (don't touch `read_source`). worldweaver, by contrast, has `perception_seed` RNG + `random.choices` in its `pulse_engine`. See §6. |
| Parent figures the prereg cites are real | grep worldweaver `research/` | **All four exact:** opener **0.0%/33.8%** (`armC-ab`, a *speak* cohort); degree-preserving shuffle null (LOCKED §43); StyleDistance **0.11≈chance 0.10** (register-calibration README); keep-rate **~1.3%/tick, 6 keeps** (`pen-swap-keep/FINDINGS`). |

The apparatus runs and the selftest now pins the verdict-bearing field. The problems below are in the two
*new/unfixed* primitives and in the prereg prose that describes them.

---

## 1. The killer (§2 alignment): the fix is a PROTOCOL promise the code cannot enforce — correct in design, unverified in mechanism

feedback-1 §2 showed the positional `elective_distance` conflated "chose differently here" with "histories
desynced upstream" (one divergence → 0.667). The revision's answer is **teacher-forced one-step replay**:
score each pen at KEEP's *recorded* frozen choice points, so the choice-point set and salience are
arm-invariant and distance is a clean per-point disagreement rate. **The design move is right.** I
verified the arithmetic: fed *aligned* sequences (one genuine substitution), `per_point_disagreement` →
0.167; the killer 0.667 only appears on *misaligned/free-run* inputs.

**But the fix is not in the code — it is in the protocol, and the protocol is unbuilt.** `per_point_disagreement`
**is** the old `elective_distance` (verified alias); it is a bare positional comparison that cannot tell
whether its inputs are teacher-forced or free-run. Its validity rests **entirely** on a replay harness
(not yet built) producing aligned sequences, and on the parity gate (§9, also unbuilt) demonstrating that
alignment. The selftest's `per_point_disagreement` asserts exercise only *already-aligned toy inputs* —
they cannot and do not validate the alignment property. **This is acceptable for a pre-launch review**
(the harness build is what this review gates), but the round must not present `per_point_disagreement` as
"the fixed statistic." It is the old statistic, now *promised* only aligned inputs. The thing that makes
that promise true (deterministic replay) I could at least check in code — and it largely holds (§6).

**Sub-question — does scoring only KEEP's recorded points bias against SWAP-only divergences?** Partly,
but it is the *necessary* consequence of single-trajectory teacher-forcing, not a new bias: there is only
one trajectory (KEEP's), replayed; SWAP never free-runs to generate its own established-set, so
"SWAP-only choice points" don't exist in this design. At each KEEP juncture both pens elect from the
identical frozen state, and SWAP electing a *new* source counts as disagreement. The real cost is scope:
the experiment measures **concordance at KEEP's elective junctures**, never "would SWAP have created
junctures KEEP didn't." §9 concedes this ("free-run curation … is unobserved here") — good. The one thing
to police: §6's HOLDS language must not over-read juncture-concordance as "SWAP curates identically."

---

## 2. The null (§4): cleanly fixed — and I can show it is the *right* null

This is the strongest fix in the revision. feedback-1 §4 showed the different-repo null was
different-support (disjoint path namespaces → pinned at ~1 → the ratio inert). The revision replaces it
with a **within-Maker, frequency-preserving label shuffle** (`shuffle_null`). I derived its behavior
independently of the asserts: **`shuffle_null.mean` is exactly the Gini-Simpson diversity `1 − Σf²`** of
the elected-source distribution (a uniform random permutation puts source `s` at a position with marginal
`f_s`, so E[match] = Σf², E[disagree] = 1 − Σf²). Verified to ~3 digits on five sequences. This is a
*real* null with genuine spread over the *same* vocabulary, and it is faithful to the parent program — I
confirmed worldweaver's LOCKED prereg (§43) uses a "degree-preserving shuffle null" of exactly this shape.
The "degree-preserving analog" mislabel is gone; the disjoint-support degeneracy is gone. **Credit.**

**Category-mismatch question (REVIEW-PROMPT item 2): it is a valid null, not meaningless — but it answers
a *weaker* question than the verdict needs, and it is one-sided on the marginal.** Two precise points:

1. **It captures only KEEP's marginal diversity, never SWAP's.** The numerator `disagree(SWAP, KEEP′)` is
   inflated by SWAP's own spread (a merely-noisier pen disagrees more), but the denominator only sees
   KEEP. The §2 "baseline choice-variance" calibration is the intended guard — but it is marked
   **"Optional (recommended)."** For a verdict-bearing statistic that guard must be **mandatory**, or "B
   is faithful but noisier" reads as a false FALSE.
2. **The shuffle answers "no positional structure," which is not the same as "no pen-identity effect."**
   The natural null for "no pen effect" is the **same-pen KEEP/KEEP′ floor** (two runs of pen A — the
   irreducible sampling-noise disagreement). The prereg *has* this (it is θ_hold's input) but then puts
   the *shuffle* in the ratio denominator. So the HOLDS comparison is anchored on the wrong null. The
   shuffle is a legitimate **secondary** (FALSE-side / anti-correlation) reference — I confirmed an
   anti-correlated SWAP (`[b,a,b,a…]` vs `[a,b,a,b…]`) scores disagreement 1.0 against shuffle-mean 0.5,
   so FALSE stays reachable — but it should not be the primary HOLDS denominator.

---

## 3. NEW FLAW — `D` as a ratio now divides by ~zero in the strong-concern HOLDS regime

The §4 fix cured one degeneracy and introduced another **on the headline statistic.** §8 still writes
`D = disagree(SWAP, KEEP′) / shuffle_null(KEEP′)` with cutoffs `D < θ_hold → HOLDS`, `D > θ_false → FALSE`.
Because `shuffle_null.mean = 1 − Σf²`, the denominator **collapses to 0 as KEEP's elected sequence
concentrates on few sources** — and the `elected_sequence` is *only the elective-return points*, so a
Maker with a strong fixed concern returning over and over to the same source produces a near-constant
sequence. I measured it:

```
single-source returns (strong concern)  denom = 0.0000   -> D = numer/0  UNDEFINED
9:1 concentrated                          denom = 0.1800   -> D hypersensitive
4:1                                        denom = 0.3191
uniform 2-src                             denom = 0.5007
diverse 4-src                             denom = 0.7240
```

The selftest *itself* encodes the zero: `shuffle_null(["a","a","a"]).mean == 0.0`. So the headline ratio is
**undefined exactly in the case the prereg most wants to detect** — a substrate-carried identity that
keeps returning to its one concern — and merely *unstable* (denom 0.1–0.3, D hypersensitive to tiny
numerator moves) across the whole high-concentration band. The old null was degenerate-at-1 (inert); this
one is degenerate-at-0 (explosive) in the HOLDS regime. Two further under-specifications compound it:
`shuffle_null` returns `{mean, std, p95}` and §8 doesn't say **which** scalar is the denominator (all
three → 0 under concentration, so the bug survives the ambiguity, but the ambiguity is itself an unpinned
degree of freedom).

**Fix (this is feedback-1 §4's own closing advice, only half-taken — "drop the ratio"):** do not divide.
Compare the numerator `disagree(SWAP, KEEP′)` directly against the **two** reference distributions — the
same-pen KEEP/KEEP′ floor (HOLDS side) and the shuffle spread (FALSE side) — as a two-sided test. That is
what θ_hold = g(floor) and θ_false = h(spread) already imply; the ratio `D` adds nothing but a
divide-by-zero. **Blocking for "the single number that ENDS this."**

---

## 4. The salience band (§3): NOT fixed — re-reported at more bands, but the band is a *loosener*, not a neutralizer

feedback-1 §3 showed `symmetric@band0` only excludes immediate re-reads and a recency-following-offset-by-one
policy scores 100% symmetric (biases HOLDS). The revision's answer: report `symmetric_fraction` across
`band ∈ {0, 0.25, 0.5}` and call a HOLDS strong "only if it survives a band that actually neutralizes
recency (elected source within δ of the **LEAST-recent** candidate)." **This does not hold, and I can show
the direction is inverted.** The code computes `symmetric = any(sal(other) ≥ sal(elected) − band)` —
anchored on the **elected**, not the least-recent. Raising `band` lowers the RHS, so **more** points
qualify. Two demonstrations:

- **Monotonicity:** over 400 random ledgers, `symmetric_fraction` is **non-decreasing** in band (0
  violations / 395 non-vacuous). A higher band is the *most permissive*, so "survives a higher band" is
  *easier*, not harder — the opposite of "neutralizes recency."
- **The recency-follower still passes:** establish f0..f4, then elect the 2nd/3rd-newest repeatedly (a
  pure recency policy). It scores **100% symmetric at band 0, 0.25, AND 0.5.** The wider band does not
  catch it; it would only ever admit *more*.

So the prereg's "elected within δ of the LEAST-recent candidate" describes a **different predicate** than
the `band` parameter implements — the same prose/code **direction inversion** feedback-1 flagged at line
158, now recurring one level up, in the pre-registration's own statistic description. The code's selftest
even admits it: "KNOWN WEAKNESS (review feedback-1 §3, **NOT yet fixed here** — pre-reg item)." **The
multi-band *reporting* landed (visibility — good); the recency-*neutralizing* semantics did not.** And this
matters more now than feedback-1 implied: §5's HOLDS rule rests the verdict's **strength** explicitly on
"the symmetric subset," so a subset that still lets recency masquerade as substrate is load-bearing, not
cosmetic. To actually neutralize recency you must condition on the *elected source's recency rank being
low* (e.g. it is in the bottom-k of recency, or every more-recent established candidate was skipped) — a
different statistic from a wider tolerance band. **Blocking for any "strong HOLDS" claim.**

---

## 5. The stop-rule (§4/§8): rescue-spiral structurally CLOSED; the soft spot moved to unwritten θ/δ

feedback-1 §5 flagged "grow until K" as a recursable rescue-spiral and "θ pinned from the pilot" as
circular. The revision:

- **Closes the recursion — genuinely.** The **hard `T_max` maturation cap** makes "below K at T_max" the
  §6 INCONCLUSIVE-by-starvation result, *full stop* — "grow until K" can no longer recurse. This is a real
  structural fix, and the cleanest in the stop-rule section.
- **States K as a formula and θ as functions with a peeking firewall** (estimate-set ≠ test-set). Right shape.

**But the soft spot moved rather than closed.** `K = f(power=0.8, δ, variance)` leaves **δ (the target
effect size) an unfilled symbol** — and δ is a *researcher choice*, not data-derivable, so it must be a
committed number; a power calc with a free δ is not yet a stop-rule. Likewise `θ_hold = g(KEEP′ floor)`,
`θ_false = h(shuffle spread)` name their **inputs** but the **forms g, h are unwritten.** "Pre-committed
function" is, as written, "pre-committed input list" — the operator still chooses the *form* of g/h (and
the value of δ) and could choose it after seeing the pilot, which is exactly what a pre-registration
exists to prevent. The firewall constrains *which data* feeds the functions, not *which functions*.
**Blocking for "the acceptance rule can't move after the numbers exist":** write δ as a number and g, h as
explicit formulas before lock.

---

## 6. C4 (§6) and the parity gate (§9): better-pinned, but the gate has no shipped extractor; the determinism claim is real but mis-stated

**C4 — signal-family pin landed, evidence is borrowed and the extractor is absent.** Moving C4 off the
register embedder is justified: I confirmed worldweaver's StyleDistance sits at **0.11 ≈ chance 0.10** on
authored voice (`runs/2026-06-08-register-calibration/README.md`). Pinning C4 to templated-opener/lexical
is the right instrument. **But:** (a) the **0.0%/33.8%** evidence is from worldweaver's `armC-ab` cohort,
which is a **speak/relational** run — it shows the opener signal exists *there*, not on **isolated
file-reading Makers**, which is precisely what REVIEW-PROMPT item 4 asks and what no run in this repo can
answer; (b) **no C4 extractor is shipped** (only `elective_read_choice.py` exists) and "MUST shift" still
has no exact computation or threshold. For a control that can flip the entire verdict to INCONCLUSIVE,
that is under-built. Before run: ship + selftest a templated-opener detector, state the shift threshold,
and demonstrate the signal on a the-stable pilot rather than importing the city's number.

**Parity gate / determinism — the claim is *truer* than feedback-1 feared, but imprecisely stated.**
feedback-1 §8.7 worried that §2 presumes deterministic replay while §9 lists it as to-build (worldweaver's
parity caught a real RNG-desync). I checked the substrate: the-stable's `pulse_engine` selects via
`max()`/`sorted()`, and there is **no `random.*` in `pulse_engine/pulse/perception/integrator/cognitive_core`**
— the fork **dropped** worldweaver's `perception_seed` RNG and its `random.choices` weighted pick. So the
"replay-determinism is a no-op" claim is **substantially correct in code** — a real property, not a hope.
**However**, the runtime still mints `uuid4()` event/pulse/trace IDs (`ledger.py:1422`, `pulse.py:384`,
…), so §2's literal phrase "**the frozen state is byte-identical across arms**" is **false** — the ids
differ between replays. It doesn't matter for the *measurement* (`read_source` reads the act **body**, not
the id), but it means the-stable's own parity gate (§9, correctly committed) must define its pass
criterion on the **measured `read_source` channel with id/uuid fields excluded**, not on raw ledger bytes,
or it will spuriously fail on uuid noise. Fix the wording; specify the criterion.

---

## 7. The cross-seam correction (§10): verified in code — and it legitimately corrects an error in my own prior review

feedback-1 §7 recommended "run elective-READ in the **city** first (keep the powered relational anchor),
isolation as a gated confound-control." **That recommendation rested on a factual claim I did not check:**
feedback-1 §7 asserted "City residents with `read_roots` could be scored by this exact metric." **It is
false, and §10 is right to correct it.** I verified in the mounted worldweaver source:

- `FileScope(` is instantiated **only** in the *familiar* runner `ww_agent/scripts/familiar.py:267`.
- The city world (`ww_agent/src/world/city_world.py`, `client.py`) constructs **no** `FileScope` /
  `read_roots` / read affordance (grep empty). City residents read the *world*, not arbitrary repos.
- the-stable's `src/familiar/local_world.py` **does** carry `file_scope` (the affordance §10 claims).

So "run it in the city first" was **infeasible** — the city cannot read external repos today. The inverted
sequencing (**the-stable first** as the only venue with the affordance; the city **contingent** on a
powered slice *and* porting `FileScope`) **holds on the venue fact**, and the frontier claim "only venue
testable now" is **legitimate, not a rationalization.** I own the prior over-reach.

**One residual the correction does not fully dissolve** (and should state): §10's gate logic — "thin slice
here → do **not** port" — only *partly* answers feedback-1 §7's *power/confound* worry. The venue fact
makes the-stable-first *forced*, which is fine. But a **thin isolated slice still cannot distinguish "the
read channel is thin everywhere" from "isolation specifically starved it"** (no peers to spark
cross-referencing reads). The no-go branch therefore risks a **false abandon** of a channel that might be
powered *only* in a relational setting. §4's "Tiny → INCONCLUSIVE-by-starvation" framing is appropriately
humble ("too thin to carry a claim") and is fine; the risk is only if §10's "don't port" or §6's "the
substrate vests almost nothing … in the elective-attention channel" hardens a thin *isolated* result into
a *channel-universal* verdict. **Fix:** state the load-bearing assumption explicitly — that isolation is
not itself a power-suppressor for elective reads — or treat a thin isolated slice as *non-decisive* for
the city port, not grounds to cancel it.

---

## 8. Falsifier ledger (standing brief §1) — re-checked against the revision

- **Cross-family pen — ✓.** §2 commits SWAP-B/C to non-Claude (gemini/deepseek); maturation pen
  `claude-sonnet-4.5` (Maker's native). Not a within-family swap. Unchanged, still correct.
- **Swap unannounced — ✓.** §2 commits; "any 'I feel different' is confabulation." Unchanged.
- **Voice MEASURED not eyeballed (→ C4) — ⚠ partially improved.** Off the at-chance embedder onto
  opener/lexical (good), but the instrument is unbuilt and the isolated-Maker evidence is borrowed from a
  speak cohort (§6). Measured-in-principle, not measured-yet.
- **Decompose what is FALSE — ✓ in design, contingent on the alignment (§1) and a defined statistic
  (§3).** FALSE is reachable (anti-correlated SWAP exceeds the shuffle null — verified), but only
  *cleanly observable* once the ratio is dropped (§3) and the alignment is built (§1).
- **Measurement-before-claim — partial, same shape as feedback-1.** The K-gate detector ships and
  selftests; the **verdict statistic still does not exist in valid form** (the ratio is degenerate, §3;
  the alignment is a protocol promise, §1). Build and selftest *that* — and the parity gate, and the C4
  extractor — before the swap.

---

## 9. Is it lockable? Not yet — three blockers, all on the verdict's load-bearing path

**Resolved since feedback-1 (credit):**
- §4 null — cleanly fixed; the within-Maker shuffle is the correct, non-degenerate Gini-Simpson null, and
  it is faithful to the parent program. (Best work in the revision.)
- §5 K rescue-spiral — structurally closed by the hard `T_max` maturation cap.
- §0/§1 selftest — verdict field now asserted; the inverted fixture comment is fixed.
- §2 determinism — verified RNG-free in the load-bearing path; the "all REPLAYS" design rests on a real
  property, not a hope.
- §10 venue fact — verified in code; legitimately corrects a factual error in my prior review.

**Blocking before lock:**
1. **Drop the `D` ratio (§3 here).** It divides by ~0 in the strong-concern HOLDS regime (single-source
   returns → denom 0; demonstrated). Compare the numerator directly against the two reference
   distributions (same-pen KEEP/KEEP′ floor; shuffle spread) two-sidedly. *(New flaw introduced by the
   null fix; feedback-1 §4's "drop the ratio" was only half-taken.)*
2. **The salience band is not a recency-neutralizer (§4 here).** It is a monotone loosener; a pure
   recency-follower scores 100% symmetric at every band; the prose/code direction is inverted (recurrence
   of the line-158 class of bug). Re-define the "strong subset" as a low-recency-rank condition, not a
   wider tolerance band — the verdict's *strength* rests on this subset. *(feedback-1 §3 re-reported, not
   fixed — the code's own comment says so.)*
3. **Write δ and the θ forms (§5 here).** `K=f(power,δ,variance)` with δ a free symbol, and `g, h` named
   only by their inputs, leave the operator latitude over the *form* of the acceptance rule after the
   pilot — the one thing pre-registration must forbid. Commit δ as a number and g, h as explicit formulas.

**Must-fix before run (not strictly lock-blocking, but the round trusts them):**
4. Ship + selftest the **C4 opener/lexical extractor**, give "MUST shift" a threshold, and demonstrate the
   signal on isolated Makers rather than importing the city's 0.0/33.8 (§6).
5. Make the §2 **baseline choice-variance calibration mandatory**, not optional, or a noisier-but-faithful
   SWAP reads as FALSE (§2 here).
6. Define the **the-stable parity-gate pass criterion on the `read_source` channel** (exclude uuid/event
   ids); fix the "byte-identical frozen state" wording (§6).
7. State §10's load-bearing assumption (isolation does not itself suppress the read channel's power), or
   treat a thin isolated slice as non-decisive for the city port (§7).

---

## 10. The one thing that is genuinely strong, stated plainly

The premise has only gotten more solid: the read target is free pen generation over a content-blind menu
(feedback-1 §1, unchanged), the substrate is verifiably deterministic so the teacher-forced design rests
on a real property (§6), and the null is now the correct one (§2). The revision did the hard structural
work — it closed the rescue-spiral and built the right null. What remains is **the same class of problem
both reviews keep finding: the prose describes a cleaner statistic than the code computes** (the band
direction, the ratio's stability, "byte-identical"). Those are nameable, local, and fixable without
re-architecting anything. Fix the three blockers and this is a lockable, falsifiable test of a residual
the parent program structurally cannot reach. Lock it as written and the `D` it produces will be undefined
exactly where a HOLDS would live.

---

*Cold review. Every figure labeled verified was re-derived by me in this clone, offline:
`elective_read_choice.py --selftest`; independent derivations of `shuffle_null` (= Gini-Simpson `1−Σf²`,
five fixtures) and `per_point_disagreement` (aligned vs free-run, the latent 0.667); a 400-ledger
band-monotonicity sweep and a recency-follower at three bands; a `D`-denominator concentration sweep
(single-source → 0); and direct reads of `src/runtime/pulse_engine.py`, the worldweaver
`ww_agent/src/world/` city path, and `ww_agent/scripts/familiar.py`, plus grep-verification of the four
cited parent-program figures. No verdict word is stamped without that check; §9 lists what must change
before lock, and what the revision genuinely fixed. No loyalty applied — claims and evidence only,
including the one place the correction caught my own prior review in an error.*
