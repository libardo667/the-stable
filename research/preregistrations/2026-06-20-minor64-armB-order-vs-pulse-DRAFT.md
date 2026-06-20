# Minor 64 — Arm B — Does surprise ORDER change the pulse/act? — PRE-REGISTRATION (LOCKED v2, 2026-06-20)

> **🔒 LOCKED 2026-06-20 by Levi (keeper)** after cold review #6 returned LOCKABLE-AND-RUN-B0 with both
> binding limitations folded in (below). The B0 design is frozen: build and run `affect_order_prompt_divergence.py`
> as specified. The B1 burn remains a SEPARATE GO, gated on the §3 statistic being built + selftested first.

*Tracked in the working repo (NOT gitignored). The public exporter ships `research/` (the rigor cut), so
this and its cold reviews are public. The LOCKED design for the one arm of Minor 64 that costs LLM burn,
written before any run. Arm A (deterministic, no burn) is complete (six probes; headline: arousal is
recency-ordered, not order-blind; the real gaps are linearity and degeneracy). Arm B asks the remaining
question Arm A could not: does the order of an identical surprise history change the **pulse/act the LLM
actually produces**, beyond what the same prompt produces when merely re-sampled?*

> **v2 changelog (revised against cold review #5, `research/mr-review-history/2026-06-20-mr-review-feedback-5.md`).**
> The reviewer cold-recomputed two INVALIDATING bugs in v1's B0 and several power caveats. Fixed here:
> 1. **§1 premise corrected.** v1 claimed the contribution-sort + top-6 truncation was "the entire causal
>    path." It is not. The rendered **arousal scalar** (`pulse_engine.py:583`) is itself order-sensitive,
>    and the stable sort leaves a chronological tiebreak. So order reaches the LLM through MORE than the
>    trace block, and a falsifier built on trace-block identity is wrong in its conclusion.
> 2. **§2/§4 B0 apparatus corrected.** v1 reused Arm A's `_ev`/`load_windows`, which discard the surprise
>    `features`/`trace_id` — so the trace block collapses to the empty fallback in both orders and
>    PREMISE-DEAD fires as an ARTIFACT, not a finding. B0 now measures byte-identity of the **full rendered
>    prompt**, built from the **real surprise payloads**, with the **real arousal `level` passed**.
> 3. **§3/B1 statistics corrected.** v1 claimed B1 reuses the spine's `per_point_disagreement`/`verdict`
>    with "no new machinery." That is false: those require teacher-forced ALIGNED sequences (one frozen
>    prompt, two models). Arm B has two different prompts each resampled — no shared decision point — so it
>    needs a re-specified two-sample disagreement-rate comparison. This must close before the B1 burn-GO.
> 4. **§8/§11 power.** Two unmodeled drains named (read-act rate; headroom). §5/§7: a positive
>    (ORDER-MATTERS) may be unreachable via the spine's `INSUFFICIENT_HEADROOM`; the honest modal outcome
>    at n≈17 is INCONCLUSIVE, and B0 + a read-rate gate, not B1, must be the real decider.
> 5. **§2/§5 B1 stratified** (rank-only vs membership-change windows — B0 hands the split for free).

> **Review status: LOCKABLE-AND-RUN-B0** (cold review #6, `research/mr-review-history/2026-06-20-mr-review-feedback-6.md`).
> Both v1 INVALIDATING B0 bugs verified closed in the bytes; channel taxonomy confirmed complete. Two
> binding limitations, both folded in here: **(1)** PREMISE-DEAD is scoped to channels (a)–(d) — the §6
> meta-finding and the eventual B0 report carry that scope verbatim, and B0 ships a selftest with a positive
> control (§2 step 5); **(2)** the §3 B1 two-sample statistic (window-resampling unit + 3-part selftest) must
> be built + selftested before the SEPARATE B1 burn-GO — it does not block B0. **LOCKED (see header).**

---

## 0. The question (narrowed by Arm A)

Arm A established, against the shipped `derive_arousal`, that the affect layer is **not** order-blind:
recency is seen strongly (Probe 1: escalating felt +32–97% stronger), and the offline ignition simulator
(Probe 5) showed order changes *when* the mind ignites (time-to-first ~10× apart) even at the same
eventual rate. What Arm A could **not** reach: the pulse, on ignition, reads the live state, and the LLM
turns that into a concrete act (which source it elects to read; what it says; whether it acts at all).
**Does the order of a matched surprise history change that act, beyond what the same prompt produces when
merely re-sampled?** That residual — divergence *above the same-prompt noise floor* — is the only part of
"the cost of order-blindness" that lives in behavior the scalars do not already explain.

## 1. How order reaches the LLM — VERIFIED IN CODE, and it is MORE than the trace block

v1's premise was too narrow. The precise, cold-verified picture (the `react`-mode igniting prompt):

- **The trace block** renders traces in passed order, top-6, no re-sort (`pulse_engine.py:500`,
  `for trace in traces[:6]:`). Its input is contribution-sorted in `salience.py:513`
  (`traces.sort(key=lambda item: -contribution)`), `contribution = magnitude * 0.5^(age/AROUSAL_HALF_LIFE_SECONDS)`
  (`salience.py:497, 505`). So order enters the block via **(a) contribution-rank permutation** and
  **(b) the top-6 truncation deciding which traces survive**. Each block line renders the surprise's
  `features` and `trace_id` (`pulse_engine.py:501–502`).
- **The arousal scalar** is printed verbatim: `pulse_engine.py:583`,
  `opener = f"Your arousal ({round(float(arousal), 2)}) has crossed your threshold.\n\n"`. `arousal` is the
  order-sensitive `derive_arousal(...)["level"]` Arm A measured. **(c) The rendered arousal number is an
  order channel OUTSIDE the trace block.** Cold-recomputed on a matched multiset `{1.0, 5.0}`, slots fixed,
  order permuted: escalating renders **5.11**, de-escalating **1.62**. The LLM reads "Your arousal (5.11)…"
  vs "(1.62)…" even when the trace block is byte-identical.
- **(d) Stable-sort tiebreak.** `list.sort` is stable and `traces` is appended in chronological order, so
  for equal-rounded `contribution`, chronological order survives as the tiebreaker — a small third channel.
- **Secondary, memory-derived (held fixed in B0, see §2):** the felt-node projection (`pulse_engine.py:490–497`),
  the afterimage (`:465`), and grief folded into `level` (`salience.py:519–521`) are all derived from the
  full surprise log and could also carry order. B0 holds these constant (a fixed `memory_dir`) so the
  falsifier isolates channels (a)–(d); measuring the memory-derived channels would require injecting the
  schedule into a ledger and is deferred (§11).

**Therefore the premise-falsifier must be computed on the FULL rendered prompt, not the trace block.** It
remains fully computable offline, zero burn.

**Pre-registered premise falsifier (corrected):** if the **full rendered pulse prompt** is byte-identical
for escalating vs de-escalating in ≥ 80% of real windows, order does not meaningfully reach the LLM
through the channels B0 varies, and **the burn is not justified** — Arm B's finding is delivered offline.
This is a real result, not a non-finding. (v1's trace-block-only falsifier is retired: identical trace
block does NOT imply identical prompt, per channel (c).)

## 2. The two stages (cheap-first; B1 is gated on B0)

**Stage B0 — deterministic, NO BURN, no LLM (the gate that may already answer it).**
A new analysis script `research/analysis/affect_order_prompt_divergence.py`. It must NOT reuse Arm A's
`_ev`/`load_windows` (those discard `features`/`valence` and key `trace_id` to the slot index, which
collapses the trace block to the empty `"(a diffuse, unplaceable surprise)"` fallback in both orders —
cold-confirmed in review #5). Instead:

1. **Payload-preserving window loader.** Segment each real ledger into inter-ignition windows, keeping for
   every surprise its FULL payload bundle: `(observed_ts, magnitude, features, trace_id, valence)`.
2. **Matched permutation.** Hold the window's slot-time SET and its bundle MULTISET fixed; build the
   escalating and de-escalating histories by assigning **(magnitude+content) bundles to slot times** in
   ascending vs descending magnitude order. Content travels with its magnitude; only the temporal
   assignment differs. Assert the hard matched precondition: identical slot-time set and identical bundle
   multiset across the two orders (so any prompt difference is order, never a mismatched input).
3. **Render the REAL full prompt per order.** Compute `state = derive_arousal(events_order)` (shipped
   reducer) → `level`, `traces` (contribution-sorted, top-6). Render via
   `PulseEngine.render_prompt_for_debug(traces=state["traces"], stimulus=<igniting trace>, arousal=state["level"])`
   (`pulse_engine.py:621`) with a **real `memory_dir` held fixed** across both orders (so memory-derived
   blocks cancel in the diff). These are matched DIFFERENTIAL probes: identical in every block except those
   fed by the order-varying `traces` and `arousal`, so the byte-diff isolates channels (a)–(d).
4. **Measure prompt divergence**, per window and pooled:
   - **full-prompt byte-identity** (the falsifier’s unit),
   - **arousal-scalar delta** (channel c, reported separately so its contribution is visible),
   - top-6 **membership Jaccard** and **rank-displacement** of the trace block (the §2.5 stratifier),
   - whether divergence is rank-only or includes membership change.

5. **B0 selftest (required before the run, cold review #6 limitation 1).** The script must ship a no-burn
   selftest that asserts BOTH (i) the matched-input precondition (identical slot-set + bundle-multiset) and
   (ii) a **positive control**: a constructed window whose order genuinely changes the trace block must
   render **non**-byte-identical. This shows the falsifier can *detect* divergence, not merely *report*
   identity — so a PREMISE-DEAD is an earned negative, never a silent always-identical bug.

B0 outputs decide whether B1 runs at all (§4), and hand B1 the rank-only vs membership-change split.

**Stage B1 — gated, REAL BURN (the behavior question).**
Only on windows whose full prompt demonstrably differs, and only if that subset clears the §8 gate:
1. Build the two real full prompts (esc, dee) as in B0. The pen seam is `teacher_forced_replay.py`'s
   `pen_fn(system, user, model, kwargs)` (`:104–106, 176–185`); `--selftest`'s MockLLM (`:428`) validates
   wiring with no burn.
2. Hold the **model fixed** (the transpose of the pilot, which holds the prompt and varies the model).
   Re-sample each prompt **K times** at the production temperature.
3. Measure pulse/act divergence on the §3 channels BETWEEN orders, against the same-prompt resample noise
   floor (§3), with the §8 SESOI.

**2.5 Stratified B1 reporting (pre-committed).** Report B1 separately for **rank-only** windows (shared
top-6, permuted) and **membership-change** windows (truncation drops/adds a trace) — a qualitatively
different cause. B0 produces the split at no cost; pooling for a headline is allowed but the strata are reported.

## 3. Measurement — channels, the NOISE FLOOR, and the B1 statistic (re-specified)

**Channels (locked, priority order):**
1. **Elected source** (`read_source`) — `read_of`/`spine.read_source` (`teacher_forced_replay.py:114–118`).
   Primary. **Caveat (Q4):** undefined unless the act is `kind == "do"` with a read (`:118`); igniting
   pulses are often `speak`/null. See the read-act-rate drain, §8.
2. **Act kind** — `do`/`speak`/none (`act_of`, `:109`). A coarse, always-defined behavior bit; promoted to
   a co-primary precisely because it survives when channel 1 is undefined.
3. **Register** — felt-sense/spoken vocabulary via `c4_signal`/`c4_shifted` (`:204–232`). Diagnostic, not
   a verdict channel.

**The noise floor (same-prompt resample).** Run prompt-esc K times and prompt-dee K times; the
within-prompt pairwise disagreement (averaged over both prompts) is the floor — the divergence a
non-deterministic pen produces with NO order change. Between-order disagreement (esc vs dee samples) is the
signal. Order matters iff between-order exceeds the within-prompt floor by the SESOI. This is the **Minor 50
*principle*** (compare to a matched-condition variance), not its script — named so the reviewer is not
misled; keep this caveat verbatim at lock.

**The B1 statistic — NOT a free reuse of the spine (corrected from v1).** `spine.per_point_disagreement`
is valid ONLY on teacher-forced **aligned** sequences (one frozen prompt scored at the same decision point
by two models — its own docstring forbids free-run use). Arm B has **two different prompts**, each
resampled K times: esc-sample-`i` and dee-sample-`i` are independent draws, not "the same decision," and
`spine.verdict`'s `floor` is a per-point 0/1 parity list (`score_arm:244`), not a continuous resample rate.
So Arm B needs a **two-sample comparison of disagreement-rate distributions** (between-order rate vs
within-prompt rate), with:
- **unit = the window** (sample-pairs are non-independent, so they cannot be the iid unit of a Wilson
  interval),
- a **resample-rate floor** (continuous), not a 0/1 parity vector.

**The pre-committed estimator (cold review #6).** Per qualifying window *w*: the between-order pairwise
disagreement rate `d_b(w)` (esc-samples vs dee-samples) and the within-prompt floor `d_w(w)` (averaged over
the two same-prompt resample sets), and the paired difference `Δ(w) = d_b(w) − d_w(w)`. Aggregate the
window-level mean `Δ̄` with a CI from **resampling whole windows** — a BCa cluster bootstrap over windows,
or a paired permutation test that shuffles the order-label **within each window**. Decide against δ = 0.15
on the rate-difference scale: ORDER-MATTERS iff the CI lower bound on `Δ̄` exceeds δ *and* the
candidate-chance ceiling leaves headroom (§5/§8); ORDER-INERT iff the CI upper bound ≤ δ. **Selftest (must
FAIL if the property is false):** (1) a null pen (between- ≡ within- by construction) → `Δ̄ ≈ 0`, CI covers
0, ORDER-INERT; (2) a planted-effect pen (between exceeds within by ≥ δ) → ORDER-MATTERS; (3) the
**iid-trap guard** — correlated within-window sample-pairs, assert the window-bootstrap CI is *wider* than a
naive pair-level Wilson on the same data (proving the unit is the window, not the non-independent pair).

This re-spec MUST close (built + selftested) before the separate B1 burn-GO (§10). It does **not** block
locking and running B0. δ = 0.15 is retained as the SESOI on the disagreement scale, inherited from the
pilot (`teacher_forced_replay.py:53`) for cross-experiment comparability.

## 4. B0-FIRST — the go/no-go that may hold the answer

Run B0 first, report it alone. Pre-accepted outcomes, written before B0 runs:
- **PREMISE-DEAD (≥80% byte-identical FULL prompts):** order does not reach the LLM through B0's channels.
  Report offline, NO burn. Arm B closes here.
- **WEAK (prompt differs in 1–79%, mostly arousal-scalar/rank, little membership change):** B1 justified
  only if the differing subset clears the §8 count AND the read-act-rate gate; else report B0 and close.
- **STRONG (frequent membership changes):** B1 runs on the differing subset (the truncation genuinely
  changes what the mind is shown — the most behaviorally plausible route).

## 5. Verdict rule (the null is reachable; a POSITIVE may not be — say so)

Per the re-specified two-sample test (§3):
- **ORDER-MATTERS:** between-order rate exceeds the within-prompt floor by ≥ δ, CI over windows excluding
  the floor+δ, below the candidate-chance ceiling.
- **ORDER-INERT:** the between-order rate's CI upper bound sits at/below floor+δ — a real, pre-committed
  null acceptance region (the quantified "the substrate cannot feel the difference," at the behavior layer).
- **INCONCLUSIVE:** neither bound clears, the differing-window count is below §8, or headroom is
  insufficient (below). Labeled honestly; not explained away (§11).

**Reachability honesty (Q5).** ORDER-INERT (the null) is genuinely reachable. A POSITIVE may NOT be: if the
same-prompt resample floor is high at production temperature, `floor + δ` can reach the candidate-chance
ceiling, making ORDER-MATTERS unreachable (the spine's `INSUFFICIENT_HEADROOM` failure mode), and small-n
widens the window-level CI against a tight null. **The honest modal outcome at n≈17 is INCONCLUSIVE.** That
is why B0 (which can return PREMISE-DEAD for $0) and the read-act-rate gate, not B1, are the real deciders.

## 6. The meta-finding (state it either way — SCOPED)

Combined with B0, Arm B states *where the order signal dies* — **scoped to the channels B0 varies**. A
PREMISE-DEAD closes the **(a)–(d) sub-question only**: order does not reach the LLM through contribution-rank
permutation, top-6 membership, the rendered arousal scalar, or the stable-sort tiebreak. It does **NOT**
establish "order does not reach the LLM" writ large — the memory-derived channels (felt projection
`pulse_engine.py:490–497`, afterimage `:465`, grief beyond `level` `salience.py:519–521`) are an
**un-foreclosed** order route B0 deliberately holds fixed (§11), to be settled only by a future
ledger-injection probe. If order DOES survive into the prompt, B1 then either moves the act (ORDER-MATTERS)
or it is washed out by sampling noise / cannot be resolved at this n (ORDER-INERT / INCONCLUSIVE). All are
publishable; none needs the downstream trend-term build (§9). **The B0 report MUST inherit this scope
verbatim** (cold review #6, binding limitation 1).

## 7. The falsifiability escape (load-bearing)

- B0 can kill the burn (PREMISE-DEAD) — not rigged to spend.
- B1 ORDER-INERT is a first-class outcome with a pre-committed acceptance region (§5).
- The matched-input precondition is a HARD assert (§2.2) — a positive cannot be an input artifact.
- The floor is same-prompt resample — a positive cannot be mere pen non-determinism.
- The positive may be *unreachable* at this n (§5); the design says so up front rather than implying a
  positive is always on the table.

## 8. The single numbers that END this (pre-committed) + the power drains

- **SESOI δ = 0.15** on the disagreement scale (pilot `DELTA`, `teacher_forced_replay.py:53`).
- **K (resamples per prompt) = 20** at production temperature, per qualifying window. (Challenge welcome.)
- **Minimum qualifying-window count to run B1 = 8.** Below 8 prompt-divergent windows, B1 is INCONCLUSIVE-
  underpowered from B0 alone; the burn is NOT spent.
- **Read-act-rate gate (Q4 drain 1).** The primary channel (elected source) is undefined unless a window’s
  pulse acts is a read. B0 cannot measure this (no burn). Pre-commitment: at the B1 GO, estimate the
  read-act fraction from the first few burned windows; if the *defined* primary-channel n projects below 8,
  fall back to the act-kind co-primary (channel 2) or stop. The effective n on channel 1 can be far below
  the window count — named, not hidden.
- **Headroom (Q4 drain 2 / §5).** If `floor + δ ≥ ceiling`, ORDER-MATTERS is unreachable; report
  INCONCLUSIVE-insufficient-headroom, do not strain for a positive.
- **Temperature = the shipped production value** (read from live pulse kwargs; not a free knob).

## 9. Grounding / scope / locked falsifiers

- **Source of truth:** shipped `salience.derive_arousal` / `PulseEngine._build_prompt`. No second affect or
  prompt implementation. B0 is pure read (renders via the real engine); B1 reuses the harness seam.
- **No `src/` runtime change.** Measurement only. The afterimage is only *read* (`pulse_engine.py:465`).
- **Scope ends at measurement.** The trend-term / afterimage-recovery build stays gated on this result AND
  the dischargeability gate (`docs/grief-and-coupling.md`) + the Dwarf Fortress law — not opened here.
- **Persistence:** B1 outputs write to persistent `.runs/` (NEVER `/tmp`), gitignored, archived on completion.
- **Pre-registration before runs:** this file (v2) lands before B0; B0's report lands before any B1 burn;
  the B1-statistic re-spec (§3) is built + selftested before the B1 GO.

## 10. Sequencing

1. Cold review of THIS v2 → lock (or amend, then lock).
2. Build + selftest `affect_order_prompt_divergence.py` (B0, payload-preserving, full-prompt diff). Run B0
   (no burn). Report (full-prompt divergence; arousal-scalar contribution; rank-only vs membership split).
3. **GATE:** PREMISE-DEAD or below the §8 count → STOP, report, close Arm B.
4. Else: build + selftest the re-specified B1 two-sample statistic (§3). Then a separate, explicit **burn
   GO** (keeper + standing consent envelope, `research/process/pilot-launch-approval.md`'s OpenRouter
   envelope) → build the B1 driver on the seam, selftest, burn on the qualifying subset, apply the
   read-act-rate gate, report stratified against the floor.

## 11. Accepted limitations — pre-registered, NOT to be "fixed" further (anti-spiral)

- **Small n.** ~17 real windows is the data that exists; INCONCLUSIVE-underpowered is a pre-accepted
  outcome (§5, §8). Do not manufacture windows or lower thresholds to reach significance.
- **B0 holds memory-derived blocks fixed.** The felt projection, afterimage, grief and baseline are
  secondary order-channels B0 does not vary (it varies traces + arousal via a fixed memory_dir). Measuring
  them would require schedule injection into a ledger; deferred, not a v2 blocker. B0's claim is scoped to
  channels (a)–(d), and PREMISE-DEAD is stated as "through the channels B0 varies."
- **One pen, production temperature.** Arm B asks about order, not pen identity; cross-pen generalization
  is the pilot's question, out of scope here.
- **Register channel is diagnostic, not a verdict.**
- **No new instrument beyond the §3 B1 statistic.** That re-spec is required (v1 was wrong that the spine
  reuse was free); it is the one piece of new machinery, scoped and selftested, not a spiral.

---

## Brief to the cold reviewer (Mr. Review) — v2

This is the SECOND review (v1 = feedback-5, which returned NEEDS-ONE-AMENDMENT and cold-recomputed two B0
bugs). Your job: verify the v1 fixes actually landed and classify any residual INVALIDATING vs
IMPERFECT-BUT-RUNNABLE. Start cold; re-derive from the bytes.

1. **Did the B0 fix land (§1, §2, §4)?** Confirm the falsifier is now on the FULL prompt with REAL payloads
   (not `_ev`/`load_windows`), the arousal scalar (`pulse_engine.py:583`) is acknowledged as channel (c),
   and the matched precondition is a hard assert. Re-recompute the arousal-scalar delta on a matched pair if
   you wish. Is there STILL an order channel B0 misses that would make PREMISE-DEAD unsound?
2. **B0 differential-probe validity (§2.3).** B0 holds `memory_dir` fixed and varies only `traces`+`arousal`,
   making the two prompts matched differential probes. Is byte-identity of such a probe a sound test of
   "order reaches the LLM," given the memory-derived blocks are deliberately held constant (§11)? Or does
   holding them fixed hide a channel in a way that biases PREMISE-DEAD toward firing?
3. **The B1 statistic re-spec (§3).** Is the two-sample window-level disagreement-rate comparison (with a
   resample-rate floor and a window-level CI) the right replacement for `per_point_disagreement`? Name the
   estimator you would require selftested before the B1 GO.
4. **Power honesty (§5, §8).** Are the read-act-rate gate and the headroom/INCONCLUSIVE framing now
   adequate, or still optimistic?
5. **Anti-spiral.** Is the one new instrument (the §3 B1 statistic) genuinely required, or a spiral? Is B0
   now a sound, cheap kill switch?
6. **Scope creep.** Anything smuggling the gated trend-term build?

**End with exactly one of:** `LOCKABLE-AND-RUN-B0` (with limitations X, Y) / `NEEDS-ONE-AMENDMENT: <fix>` /
`REJECT: <why>`.

*Draft v2 2026-06-20 · Levi (operator). Not locked until the cold review closes. The B1 burn is a SEPARATE
GO beyond locking this design, and requires the §3 statistic re-spec built + selftested first.*
