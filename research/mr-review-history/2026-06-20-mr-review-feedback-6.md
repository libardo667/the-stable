# Cold review #6 — Minor 64 Arm B pre-reg **v2** (order → pulse/act), run-readiness of B0

**Round:** `research/review-bundle/2026-06-20-minor64-armB-prereg-v2/`
**Design under review:** `research/preregistrations/2026-06-20-minor64-armB-order-vs-pulse-DRAFT.md` (v2)
**Checking against:** `research/mr-review-history/2026-06-20-mr-review-feedback-5.md` (v1, NEEDS-ONE-AMENDMENT)
**Reviewer:** Mr. Review, cold. Method = the standing brief in my system prompt; this project's
interpretations are off my desk by design.
**Date:** 2026-06-20

## What I actually did (nothing on testimony)

This is a **pre-build** round: `research/runs/` does not exist (confirmed — no such dir), and the new B0
script `research/analysis/affect_order_prompt_divergence.py` is **not yet written** (confirmed — absent).
So "re-derive every number cold" reduces to: (a) re-verify the premise in the bytes, (b) re-recompute the
two constructions v1 used to INVALIDATE the v1 B0, (c) verify the v1 fixes actually changed the design, not
just the changelog, and (d) run the no-burn selftests on the seams v2 reuses.

Cold-recomputed / verified, this session:
- **Arousal-scalar order channel (channel c).** Built a matched multiset `{1.0, 5.0}`, two fixed slots
  (age 0 and one half-life), permuted only the order, fed the **shipped** `derive_arousal`
  (`AROUSAL_HALF_LIFE_SECONDS = 300.0`, `salience.py:40`). Escalating (big→recent) renders **5.5**,
  de-escalating (big→old) **3.5**; the `round(level, 2)` opener at `pulse_engine.py:583` differs (Δ=2.0).
  My slot spacing is not feedback-5's (it got 5.11 vs 1.62 on a wider spacing), but the **falsifier-relevant
  fact reproduces independently**: the rendered arousal number is order-sensitive, so a trace-block-only
  falsifier is unsound. Sign and direction (escalating > de-escalating) are robust to the spacing.
- **The v1 Leak-B artifact (the empty fallback).** Re-read `affect_order_sensitivity.py:44–48` (`_ev`) and
  `:63–81` (`load_windows`): `_ev`'s payload has **no `features`/`valence`** and `trace_id = f"t{i}"`
  keyed to the **slot index**; `load_windows` returns `list[tuple[datetime, float]]` — only `(ts, mag)`.
  Rendered the trace block exactly as `pulse_engine.py:500–503` on `_ev`-style traces (no `features`):
  both orders collapse to `'  (a diffuse, unplaceable surprise)'`, **byte-identical = True**. So feedback-5's
  INVALIDATING Leak B was real; any B0 reusing those helpers would fire PREMISE-DEAD as a guaranteed
  artifact. v2's retraction is warranted.
- **The spine claims v2 makes.** `per_point_disagreement` docstring (`elective_read_choice.py:154–158`):
  *"Valid ONLY on teacher-forced-aligned sequences … It is NOT valid on free-run sequences."* `verdict`'s
  `floor` parameter is `list[float]` (`:224`) and `INSUFFICIENT_HEADROOM` fires on `ceiling <= floor_mean+δ`
  (`:253`). All three v2 §3/§5 claims check out in the bytes.
- **Selftests (no burn).** `teacher_forced_replay.py --selftest` → PASS (pen seam wired: `parity repro 1.0`,
  `HOLDS=HOLDS FALSE=FALSE`, ceiling 20160). `elective_read_choice.py --selftest` → PASS (the recency &
  anti-recency followers both score 0 in the strong subset — the existing "code proves prose" precedent).

**Headline:** Both v1 INVALIDATING bugs are genuinely fixed in the v2 **design bytes**, and the channel
taxonomy is now complete and correctly scoped. The B0 apparatus, as specified, is a sound, conservative,
zero-burn kill switch. One residual is a **scope-wording** issue (§6 overclaims past what B0 measures),
which is IMPERFECT-BUT-RUNNABLE and fixed at report time — not INVALIDATING. The B1 statistic is correctly
retracted and re-opened as required new machinery, gated to the separate B1 GO. **No rescue spiral.**

---

## Q1 — Did the B0 fix land, and is any order channel still missed? **Landed. Taxonomy complete; one scope caveat.**

**Fix 1 (premise completeness, §1) — landed.** v2 §1 now names all four channels and I confirmed each:
- (a) contribution-rank permutation: `salience.py:497,505` (`decayed = magnitude * 0.5^(age/HALF)`, stored
  as `contribution`), sorted descending `salience.py:513`. ✓
- (b) top-6 truncation: `pulse_engine.py:500` (`for trace in traces[:6]:`, passed order, no re-sort). ✓
- (c) the rendered arousal scalar **outside** the trace block: `pulse_engine.py:583`. Cold-recomputed
  above (5.5 vs 3.5 on my pair). ✓ This was v1's Leak A; it is now an acknowledged first-class channel.
- (d) stable-sort chronological tiebreak: `list.sort` is stable, `traces` appended in event order
  (`salience.py:501`), so equal-rounded `contribution` keeps chronological order — v1's "minor." Now named. ✓

**Fix 2 (apparatus, §2/§4) — landed.** §2 step 1 **explicitly forbids** `_ev`/`load_windows` and requires a
payload-preserving loader keeping `(observed_ts, magnitude, features, trace_id, valence)`; step 3 renders
the **full** prompt via `render_prompt_for_debug(traces=…, stimulus=…, arousal=state["level"])`
(`pulse_engine.py:621` → `_build_prompt` mode `react`) with a real `memory_dir` held fixed; step 2 makes the
matched precondition (identical slot-set + identical bundle-multiset) a **hard assert**. The falsifier is now
**full-prompt byte-identity**, not the trace-block slice. This is exactly the v1 amendment, and it is in the
v2 bytes (not just the changelog).

**Is there STILL an order channel B0 misses that would make PREMISE-DEAD unsound?** I walked `_build_prompt`
(`pulse_engine.py:459–587`) block by block to close the taxonomy:
- Order-of-surprise-dependent content reaches the prompt through **exactly two arguments**: `traces`
  (→ the `surprises` block, `:499–503,584`) and `arousal` (→ the opener, `:583`). Both are varied by B0.
- Everything else is derived from **`self._memory_dir`** (afterimage `:465`, felt nodes `:467–468,490–497`,
  baseline/settled `:466,470–474`, disorientation `:464`, grief-in-`level` `salience.py:519–521`) or from
  **`self.latest_perception`** (location/heard/inbox/workshop/anchors). Held fixed across both orders → they
  **cancel** in the diff. I also confirmed `stimulus` is **dead** inside `_build_prompt` (grep: used only as
  a feature-dict key at `:502`, never the argument) — so B0's choice of `stimulus` cannot perturb the diff.
- `resonance`/`recalled`/`self_sameness` are forced to `None/None/0.0` by `render_prompt_for_debug` (`:623`).
  I checked they are **not surprise-order channels** anyway: all three key off `_moment_text()`
  (`pulse_engine.py:371–379`) / `_recall_query()` (`:381–395`), which read **perception** (heard, recent
  events, location, anchors, makings) — **never the surprise traces or their order**. So suppressing them
  does not hide an order channel, and would cancel even if computed.

**Conclusion:** the taxonomy is complete — there is **no un-named** order channel. The only order routes B0
does **not** exercise are the **memory-derived** ones (felt projection, afterimage, grief surfaced beyond
`level`), and v2 **scopes the claim to "through the channels B0 varies"** in §1, §4, and §11. A PREMISE-DEAD
from B0 is therefore *sound as a scoped claim*. **IMPERFECT-BUT-RUNNABLE**, with the §6 wording caveat below.

---

## Q2 — Differential-probe validity (§2.3). **Sound; holding `memory_dir` fixed biases toward firing — scope, don't unscope.**

Holding `memory_dir` fixed makes the two renders **matched differential probes**: byte-for-byte identical in
every block except those fed by `traces`/`arousal`. That is the right construction — a positive (prompts
differ) cannot be a memory confound, and the diff cleanly isolates (a)–(d).

But the draft's own Q2 asks the sharp question, and the honest answer is **yes**: holding the memory-derived
blocks fixed **removes** their order-divergence, which biases the result **toward PREMISE-DEAD** (toward
killing the burn). In the *live* pulse the felt projection, afterimage, and grief are all derived from the
same surprise log and could carry order; B0 does not exercise them. So a B0 PREMISE-DEAD means *"order does
not reach the LLM through (a)–(d),"* **not** *"order does not reach the LLM."*

v2 handles this correctly in §1/§4/§11 (the falsifier wording is scoped, and §11 pre-registers the
memory-derived channels as an **accepted, deferred** limitation — the brief favors a pre-registered scope
over a spiral, so I accept it). **The one place it leaks is §6:** *"Arm B states where the order signal dies:
at the prompt-builder (PREMISE-DEAD, offline)."* That sentence drops the scope and asserts a property cleaner
than B0 computes — the exact failure mode the standing brief names (the spec prose describing a cleaner
result than the code). **Required limitation at lock:** §6 (and the eventual B0 report) must inherit the
§1/§11 scope verbatim — a PREMISE-DEAD closes the **(a)–(d) sub-question**, and the memory-derived channels
(felt / afterimage / grief) remain an **un-foreclosed** order route deferred to a future ledger-injection
probe. With that wording, the probe is sound. **IMPERFECT-BUT-RUNNABLE** (it caveats; it does not falsify).

---

## Q3 — The B1 statistic re-spec (§3). **The direction is right; v1's reuse was genuinely invalid. Name the estimator + the selftest.**

v2 correctly **retracts** v1's "reuse the spine, no new machinery." Confirmed in bytes: `per_point_disagreement`
is teacher-forced-aligned-only by its own docstring (`elective_read_choice.py:154–158`), and Arm B's two
prompts each resampled K times have **no shared decision point** (esc-sample-`i` ⊥ dee-sample-`i`), so the
function is invalid here; `verdict`'s `floor` is a per-point list (`:224`) and its Wilson CI (`:251`) assumes
iid points, which non-independent sample-pairs violate. v2's diagnosis is correct, and the re-spec
(two-sample window-level disagreement-rate comparison, continuous resample-rate floor, window-level CI) is
the right shape. It deliberately leaves the estimator open "to be fixed and selftested before the B1 GO" —
acceptable, since B1 is separately gated and does not block B0.

**The estimator I would require selftested before the B1 GO:** treat the **window as the resampling unit**.
Per qualifying window *w*, compute the **between-order** pairwise disagreement rate `d_b(w)` (esc-samples vs
dee-samples) and the **within-prompt** floor `d_w(w)` (averaged over the two same-prompt resample sets), and
the paired difference `Δ(w) = d_b(w) − d_w(w)`. Aggregate the window-level mean `Δ̄` with a CI obtained by
**resampling whole windows** — a BCa cluster bootstrap over windows, or a paired permutation test that
shuffles the order-label **within each window** (which respects the within-window non-independence). Decide
against **δ = 0.15** on the rate-difference scale: ORDER-MATTERS iff the CI lower bound on `Δ̄` exceeds δ
*and* the candidate-chance ceiling leaves headroom (§5/§8); ORDER-INERT iff the CI upper bound ≤ δ.

**The selftest must FAIL if the property is false** (the brief's standing rule, and there is precedent at
`elective_read_choice.py:321–340`). Require it to assert, on synthetic pens:
1. a **null pen** (between- and within-distributions identical by construction) → `Δ̄ ≈ 0`, CI covers 0,
   verdict ORDER-INERT;
2. a **planted-effect pen** (between exceeds within by ≥ δ) → verdict ORDER-MATTERS;
3. **the iid trap is avoided** — feed correlated within-window sample-pairs and assert the window-bootstrap
   CI is **wider** than a naive pair-level Wilson on the same data (proving the unit is the window, not the
   non-independent pair). Without (3) the re-spec would re-import the very flaw it was built to escape.

This is genuinely-required machinery, not a spiral (Q5). **INVALIDATING for B1 if skipped — but B1 is
separately gated; it does not block B0.**

---

## Q4 — Power honesty (§5, §8). **Now adequate, with one honest residual.**

v2 folds in both feedback-5 drains:
- **Read-act-rate gate (drain 1).** Now explicit (§8): the primary channel `read_source` is undefined unless
  the act is `kind == "do"` with a read (`teacher_forced_replay.py:118`), so at the B1 GO the read-act
  fraction is estimated from the first few burned windows and, if the *defined* primary-channel n projects
  below 8, the design falls back to the always-defined act-kind co-primary (channel 2) or stops. Act-kind is
  correctly **promoted to co-primary** for exactly this reason (§3). This is the right pre-commitment.
- **Headroom (drain 2).** §5 now states plainly that a high same-prompt floor can push `floor + δ ≥ ceiling`
  and make ORDER-MATTERS **unreachable** via `INSUFFICIENT_HEADROOM` (`elective_read_choice.py:253`,
  confirmed), and that the **modal outcome at n≈17 is INCONCLUSIVE**. That is the honest framing the brief
  asks for, not an optimistic one.

**Honest residual (not a blocker):** the read-act-rate gate is **not a $0 gate** — it spends the "first few
burned windows" before it can fire, so it is a *burn-limiting* gate, not a kill switch. That is inherent
(read-act rate is unmeasurable offline) and is named, so it is acceptable. **IMPERFECT-BUT-RUNNABLE.**

---

## Q5 — Anti-spiral. **The one new instrument is forced, not invented; B0 is a sound cheap kill switch.**

The single piece of new machinery (the §3 B1 statistic) is **required by a real invalidity** I confirmed in
the bytes (the teacher-forced precondition), not introduced to rescue a result. It is gated to the separate
B1 GO (§10 step 4), so it does not touch B0. B0 itself is deterministic, zero-burn, reuses the shipped
reducer and the real engine renderer, and can end Arm B offline (PREMISE-DEAD). I checked the v1→v2 delta
for a rescue pattern: each v1 INVALIDATING bug was *closed* (apparatus rebuilt, premise corrected, reuse
retracted), and **no fix spawned a new B0 blocker**. This is the cheap-first discipline the brief wants, not
a spiral. **Pass.** (The only thing standing between "sound" and "fully sound" is the §6 scope wording, Q2.)

---

## Q6 — Scope creep. **None.**

§9 keeps the trend-term / afterimage-recovery build gated behind this result **and** the dischargeability
gate (`docs/grief-and-coupling.md`) **and** the Dwarf Fortress law; §2/§9 commit to **no `src/` runtime
change** and pure-read B0; the afterimage is only *read* (`pulse_engine.py:465`), existing runtime. §11 is an
explicit anti-spiral limitations list. Nothing smuggles the gated build in. **OK / none.**

---

## Cross-project frontier note (worldweaver mounted read-only, for judgment only)

Confirmed the parent program exists (`worldweaver/research/preregistrations/2026-06-09-pen-vs-substrate-LOCKED.md`).
Arm B is a **legitimate transpose**, not a fork: the pilot holds the **prompt** fixed and varies the
**model** (pen vs substrate); Arm B holds the **model** fixed and varies surprise **order**, reusing the same
matched-floor discipline, the same `DELTA = 0.15` SESOI (`teacher_forced_replay.py:53`), and the same
`verdict` spine. The same-prompt resample floor is the order-analogue of the pilot's same-pen floor. This is
continuous with the LOCKED program. It informs my judgment that the design is on-program; it does not
substitute for the cold re-derivation above and changes no finding.

---

## Classification summary

| # | Issue | Stage | Class |
|---|---|---|---|
| Q1 — Fix 1 | All four order channels (a)–(d) now named; verified in bytes | B0 | FIXED |
| Q1 — Fix 2 | B0 forbids `_ev`/`load_windows`, preserves full payload, diffs full prompt, hard-asserts matched input | B0 | FIXED |
| Q1/Q2 | Memory-derived channels (felt/afterimage/grief) un-exercised; PREMISE-DEAD scoped to (a)–(d); §6 wording overclaims | B0 | **IMPERFECT-BUT-RUNNABLE** (required wording fix) |
| Q3 | v1's `per_point_disagreement` reuse correctly retracted; new two-sample window-level estimator required + selftested | B1 (gated) | INVALIDATING-for-B1, not blocking B0 |
| Q4 | Read-act-rate gate + headroom honesty now adequate; gate spends a little burn (inherent) | B1 | IMPERFECT-BUT-RUNNABLE |
| Q5 | One new instrument is forced, not a spiral; B0 a sound cheap kill switch | — | Pass |
| Q6 | Scope creep | — | OK / none |

Both v1 INVALIDATING B0 bugs are closed and verified in the bytes (not on the changelog). The remaining B0
item is a **scope-of-claim wording** fix, not a computation error — runnable as written, reported scoped.
The B1 statistic is real new machinery, but it lands at the **separate** B1 GO, not here.

---

## Verdict

**LOCKABLE-AND-RUN-B0** — with two binding limitations:

1. **PREMISE-DEAD is scoped to channels (a)–(d).** A B0 byte-identity result means *order does not reach the
   LLM through contribution-rank / top-6 membership / the rendered arousal scalar / the stable-sort
   tiebreak* — **not** *order does not reach the LLM*. The memory-derived channels (felt projection
   `pulse_engine.py:490–497`, afterimage `:465`, grief beyond `level` `salience.py:519–521`) are an
   **un-foreclosed** order route that B0 deliberately holds fixed (§11). **Correct §6 to carry the §1/§11
   scope verbatim** so a PREMISE-DEAD closes the (a)–(d) sub-question, not "order" writ large. (Also: have
   B0's selftest assert both the matched-input precondition AND a positive control — a constructed window
   whose order genuinely changes the trace block must render **non**-byte-identical — so the falsifier is
   shown able to *detect* divergence, not merely able to report identity.)

2. **The §3 B1 two-sample statistic must be built and selftested before the separate B1 burn-GO**, with the
   **window as the resampling unit** (cluster bootstrap or within-window permutation) and a selftest that
   FAILS on a null pen scoring nonzero, on a planted-effect pen scoring null, and — critically — on a
   pair-level CI that is not wider than the naive Wilson (the iid-trap guard). This does not block locking
   and running B0.

Everything else (the cheap-first staging, the matched differential-probe construction, the same-prompt
floor, the read-act-rate gate, the headroom/INCONCLUSIVE honesty, the anti-spiral pre-commitments, no scope
creep) is sound and lockable. B0 is run-ready; the B1 burn remains a separate GO.
