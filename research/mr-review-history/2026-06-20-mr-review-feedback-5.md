# Cold review #5 — Minor 64 Arm B pre-reg (order → pulse/act), pre-build

**Round:** `research/review-bundle/2026-06-20-minor64-armB-prereg/`
**Design under review:** `research/preregistrations/2026-06-20-minor64-armB-order-vs-pulse-DRAFT.md`
**Reviewer:** Mr. Review, starting cold. Method = the standing brief shipped in my system prompt; this
project's interpretations are off my desk by design.
**Date:** 2026-06-20

## What I actually did (no figure taken on testimony)

- This is a **pre-build** round: there is **no `research/runs/`** in this clone (confirmed — the dir does
  not exist). So "re-derive every number cold" reduces to: (a) verify the premise in the bytes, (b) run the
  no-burn selftest, (c) **recompute the constructions the design reuses** to see what they actually produce.
- Ran `python3 research/harness/teacher_forced_replay.py --selftest` → **PASS**: `correlate→2 pts | parity
  repro 1.0 | HOLDS=HOLDS FALSE=FALSE | C4 shift home/foreign ok | stop-line=settled∧K | pause pinned ≥30s
  | ceiling 20160`. The seam the draft reuses (`pen_fn`, `parity_gate`, `c4_signal`/`c4_shifted`,
  `score_arm`, `DELTA = 0.15` at `teacher_forced_replay.py:53`) is wired and deterministic.
- Read the premise code: `salience.py:494–531` (the igniting-trace assembly), `pulse_engine.py:459–587`
  (the *whole* `_build_prompt`, not just the trace loop), `:621` (`render_prompt_for_debug`),
  `affect_order_sensitivity.py:44–48,63–92,182–186` (Arm A's `_ev`/`load_windows`/`probe1`/`probe5`), and
  the scoring spine `elective_read_choice.py:59,89–97` + `verdict`/`per_point_disagreement`.
- **Recomputed two things cold** (small matched constructions, shipped reducer, no burn) that change the verdict.

The headline up front: **the contribution-sort + top-6 claim in §1 is correct as far as it goes, but it is
NOT the entire causal path, and — more seriously — B0 *as specified to reuse Arm A's construction* measures
the trace block on content-stripped synthetic traces, so its central falsifier (PREMISE-DEAD) fires as an
artifact, not a finding.** Both are demonstrated below. The premise and the cheap-first staging are sound;
the B0 apparatus is not yet, and B0 is the thing this round would lock and run.

---

## Q1 — Premise completeness (§1). **TWO leaks; both INVALIDATING for the B0 falsifier as written.**

### What §1 gets right (confirmed in bytes)
- `salience.py:497,505`: `decayed = magnitude * (0.5 ** (age / AROUSAL_HALF_LIFE_SECONDS))`, stored as
  `contribution` (rounded 4dp at :505). ✓
- `salience.py:513`: `traces.sort(key=lambda item: -float(item.get("contribution") or 0.0))` — descending by
  contribution. ✓
- `pulse_engine.py:500`: `for trace in traces[:6]:` — passed order, top-6, no re-sort. ✓

So the two channels §1 names (contribution-rank permutation; top-6 membership) are real. The problem is the
word **"entire"** in "This is the entire causal path order → prompt → LLM" (§1) and the falsifier built on it.

### Leak A — the rendered arousal scalar is an order channel OUTSIDE the trace block (INVALIDATING)
`pulse_engine.py:583` (the igniting `react`-mode opener):
```
opener = f"Your arousal ({round(float(arousal), 2)}) has crossed your threshold.\n\n"
```
`arousal` is the order-sensitive `derive_arousal(...)["level"]` — the *same* scalar Arm A Probe 1 found is
recency-ordered (`affect_order_sensitivity.py:84–104`). Cold recompute, matched multiset `{1.0, 5.0}`,
two slot times, only the order permuted (shipped `derive_arousal`):

| order | rendered `level` |
|---|---|
| escalating (big→recent) | **5.1135** |
| de-escalating (big→old) | **1.6227** |

The LLM literally reads `"Your arousal (5.11) ..."` vs `"Your arousal (1.62) ..."`. That is order reaching
the prompt **with the trace block byte-identical**. So §1's pre-registered falsifier — *"if the rendered
**trace block** is byte-identical … then … the LLM cannot diverge by order because it never sees the order"*
(§1, §4 PREMISE-DEAD) — is **false in its conclusion**: identical trace block does **not** mean the LLM never
sees order. A PREMISE-DEAD verdict computed on the trace block alone would license a headline the bytes
contradict. (Plausibly also leaking: the `felt` block `pulse_engine.py:490–497` from
`reduce_runtime_events(...).cognitive_projection`, the afterimage `:465`/`prediction.py:113`, and grief
folded into `level` at `salience.py:519–521` — all derived from the full surprise log. The arousal scalar
alone is sufficient to break the claim; these widen it.)

### Leak B — B0's reused construction strips the very content the trace block renders (INVALIDATING)
This is the more damaging one, because it makes B0 *unrunnable as written*. §2 step 1 says B0 **"reuses Arm
A's matched-schedule construction (`affect_order_sensitivity.py` `_ev`, `load_windows`)."** But:
- `load_windows` (`affect_order_sensitivity.py:63–64`) returns **`list[tuple[datetime, float]]`** — only
  `(observed_ts, magnitude)`. The real surprise's `features`, `trace_id`, and `valence` are **discarded**.
- `_ev` (`:44–48`) rebuilds a payload with **no `features`** and `trace_id = f"t{i}"` where **`i` is the slot
  index** (`probe1` `:91–92` passes the slot loop index), so identity is keyed to the *slot*, not the surprise.

But the trace block the falsifier measures renders exactly `features` and `trace_id`
(`pulse_engine.py:501–502`). With empty features, the inner `for feature in ...[:3]` loop emits nothing and
`surprises` collapses to the fallback `"  (a diffuse, unplaceable surprise)"` (`:503`). Cold recompute, same
matched `{1.0, 5.0}` pair, rendering the trace block exactly as `pulse_engine.py:500–503`:

```
ESC trace block: '  (a diffuse, unplaceable surprise)'
DEE trace block: '  (a diffuse, unplaceable surprise)'
BYTE-IDENTICAL trace block? -> True   (PREMISE-DEAD would fire)
```

So a B0 built literally on `_ev`/`load_windows` returns the empty fallback for **every** window in **both**
orders → byte-identical at ~100% → **PREMISE-DEAD fires as a guaranteed artifact of dropped content**, and
the draft would report it as a "real offline finding" (§1, §4). It is not a finding; it is the harness
forgetting the surprise. Separately, keying `trace_id` to slot means even a non-empty block could show the
same ids in both orders when top-6 membership coincides — an identity confound on top of the content loss.

**What B0 must do instead:** preserve each real surprise's full payload and bundle `features`+`trace_id`+
`valence` *with its magnitude*, permuting only the **assignment of (magnitude, content) bundles to slot
times**. Then the trace block can actually differ by order and byte-identity is a real measurement.

### Minor (IMPERFECT-BUT-RUNNABLE): the sort is stable
`list.sort` is stable and `traces` is appended in event order (chronological). For traces with equal rounded
`contribution`, **chronological order survives as the tiebreaker** — a third, small order channel that §1's
"chronological order is erased" overstates. A full-prompt byte-diff (the amendment below) captures it for free.

### The clean fix that resolves Leak A + Leak B together
Compute the premise-falsifier on the **full rendered pulse prompt** (`_build_prompt` via
`render_prompt_for_debug`, with the **real arousal `level` passed**, the **real memory_dir held fixed**, and
the **real surprise payloads** permuted only across slot times), not on an `_ev`-built trace-block slice. If
the *full prompt* is byte-identical in ≥80% of windows, then order genuinely does not reach the LLM and
PREMISE-DEAD is sound. This is still **zero burn**. It is one coherent amendment that fixes both leaks.

---

## Q2 — The noise floor (§3). **Sound. "Minor 50 principle" is honestly flagged.**
Same-prompt resample is the correct floor for separating *order* from *pen non-determinism*: it is the
divergence the pen produces with no order change at all (§3). The draft does **not** overclaim the Minor 50
lineage — it explicitly says only the *principle* ("compare to a matched-condition variance"), not the
script, is carried, and names this so the reviewer is not misled (§3, parenthetical). That is the honest
framing the standing brief asks for; I would not make it drop the label, only keep that caveat verbatim at
lock. **IMPERFECT-BUT-RUNNABLE** only in that the floor's *unit* is entangled with the Q-below stats issue.

---

## Q3 — Top-6 truncation confound (§1.2, §2.4). **Stratify; cheap, and B0 already computes the inputs.**
Membership change (the truncation drops/adds a trace) is a qualitatively different cause than reordering
shared traces. B0 already plans to compute **both** membership-Jaccard **and** rank-displacement separately
(§2 step 3). Pooling them in B1 as "what order does" is defensible for a headline but discards the mechanism
and is nearly free to keep separated. **Pre-register stratified B1 reporting (rank-only windows vs
membership-change windows)** since B0 hands you the split at no cost. **IMPERFECT-BUT-RUNNABLE.**

---

## Q4 — Power (§8). **Honest, but thinner than stated; two unmodeled drains.**
- n ≈ 17 windows (maker 12, hades 4, skein 1; §8) and the differing subset is ≤ that. min-count=8 is the
  right kind of pre-commitment and the draft pre-accepts INCONCLUSIVE-underpowered (§5, §8, §11) — that is
  the anti-spiral discipline the brief wants.
- **Unmodeled drain 1 (read-act rate):** the primary channel is *elected source* on the `read_source` bit
  (`teacher_forced_replay.py:114–118`), which is **undefined unless the pulse act is `kind == "do"` with a
  read** (`:118`). On the igniting pulse many acts are `speak`/null. The pre-reg never estimates what
  fraction of the ~17 windows even *produce a read act* — if it is low, the effective n on the primary
  channel collapses below 8 regardless of prompt divergence. B0 cannot measure this (no burn), so it is an
  honest unknown that further argues for letting B0 + the read-rate gate decide whether B1 is worth a dollar.
- **Unmodeled drain 2 (headroom):** see Q5 — a high same-prompt resample floor can make ORDER-MATTERS
  *unreachable* via the spine's `INSUFFICIENT_HEADROOM` branch.
- K=20 and δ=0.15 are defensibly inherited (δ from the pilot's `DELTA` for cross-experiment comparability,
  `teacher_forced_replay.py:53`); the draft itself asks the reviewer to challenge K and I would not block on
  it. **Net: the modal outcome at this n is INCONCLUSIVE, not a verdict.** That is not fatal — it is the
  reason B0 must be the real gate and must be *sound* (Q1). **IMPERFECT-BUT-RUNNABLE** for B0; a genuine
  power caveat for B1.

---

## Q5 — Verdict reachability (§5, §7). **Null is a real branch; "confirm-only" is not the risk — "INCONCLUSIVE-only" is.**
Mapping the draft's labels onto the spine's `verdict` (`elective_read_choice.py`):
- ORDER-INERT = `HOLDS` (`ci_hi <= floor_mean + δ`) — a real, pre-committed acceptance region. ✓ The design
  is **not** rigged to only confirm.
- ORDER-MATTERS = `FALSE` (`ci_lo > floor_mean + δ`).
- But the spine gates first on `INSUFFICIENT_HEADROOM`: **`floor_mean + δ ≥ ceiling` ⇒ INCONCLUSIVE,
  FALSE unreachable.** Arm B's floor is the *same-prompt resample* disagreement, which at production
  temperature over several plausible sources could be substantial; if `floor_mean + 0.15` reaches the
  candidate-chance ceiling, **ORDER-MATTERS becomes unreachable** and only the null or INCONCLUSIVE remain.
  Combined with small-n widening the Wilson CI (which fights the tight `ci_hi ≤ floor+δ` that ORDER-INERT
  needs), the honest expectation is INCONCLUSIVE. Reachability of the *null* is fine; reachability of a
  *positive* is the live risk, and the draft should say so. **IMPERFECT-BUT-RUNNABLE** (it caveats, doesn't
  falsify).

---

## B1 statistics reuse (§3, §11). **INVALIDATING for B1 — but B1 is separately gated, so it does not block B0.**
§3 claims B1 will "reuse the spine's `per_point_disagreement` + `verdict` … **No new statistical
machinery**." That claim is unsound. `per_point_disagreement` is valid **only on teacher-forced-aligned
sequences** — its own docstring: *"each pen scored at KEEP's recorded frozen points … position i = the same
decision … NOT valid on free-run sequences"* (`elective_read_choice.py`, `per_point_disagreement`). In the
pilot the alignment exists because **one frozen prompt** is scored by two models at the same point. In Arm B
the two arms are **two different prompts** (esc, dee), each resampled K=20 times; **there is no shared
decision point** — esc-sample-`i` and dee-sample-`i` are independent draws, not "the same decision." The
natural Arm B statistic (between-order pairwise disagreement vs within-prompt pairwise disagreement, §3) is
a **two-sample comparison of disagreement-rate distributions**, which is *not* `per_point_disagreement`, and
`spine.verdict`'s `floor` argument is a per-point **0/1 parity list** (`score_arm` `:244`), not a continuous
resample rate. So the unit (window? sample-pair? — sample-pairs are non-independent, breaking the Wilson iid
assumption) and the floor type both need to be re-specified. **B1 does need new/adapted machinery.** This
must be fixed before the *separate* B1 burn-GO (§10 step 4); it does not block locking and running B0.

---

## Q6 — Scope creep. **None found.**
§9 explicitly keeps the trend-term / afterimage-recovery build gated behind this result *and* the
dischargeability gate (`docs/grief-and-coupling.md`) + Dwarf Fortress law; §11 is an explicit anti-spiral
list; §2/§9 commit to **no `src/` runtime change** and pure-read B0. The afterimage is only *read*
(`pulse_engine.py:465`), existing runtime, not a new build. Nothing smuggles the gated build in.

## Anti-spiral check (standing brief). **Pass on intent; the kill switch itself is mis-built.**
This is a genuinely cheap-first design with a real offline kill switch (B0 can end Arm B for $0), not a
rescue spiral — that is exactly the discipline the brief demands. The catch is Q1: the kill switch as
specified would fire (PREMISE-DEAD) on an artifact, "delivering an offline finding" that is wrong. Fixing
B0 to measure the **full real prompt** keeps the cheap-first virtue *and* makes the kill switch honest.

## Cross-project frontier note (worldweaver mounted read-only, for judgment only)
Arm B is a legitimate transpose of the parent pen-vs-substrate program: the pilot holds the *prompt* fixed
and varies the *model*; Arm B holds the *model* fixed and varies surprise *order* (§2 B1 step 2), reusing
the same matched-floor discipline and the same `DELTA`/spine. That is continuous with the program, not a
fork. It does not substitute for re-deriving this round, and it does not change any finding above.

---

## Classification summary

| # | Issue | Stage | Class |
|---|---|---|---|
| Q1-A | Rendered arousal scalar (`pulse_engine.py:583`) carries order outside the trace block; PREMISE-DEAD conclusion false | B0 | **INVALIDATING** |
| Q1-B | B0 reusing `_ev`/`load_windows` strips `features`/real `trace_id`; trace block is empty fallback → PREMISE-DEAD is an artifact | B0 | **INVALIDATING** |
| Q1-min | Stable sort: chronological tiebreak on equal contribution | B0 | IMPERFECT |
| B1-stats | `per_point_disagreement` teacher-forced precondition broken by two-prompt/resample design; "no new machinery" false | B1 (gated) | **INVALIDATING for B1** |
| Q3 | Pool vs stratify rank-only/membership-change | B1 | IMPERFECT |
| Q4 | Read-act-rate + headroom drains; modal outcome INCONCLUSIVE | B1 | IMPERFECT |
| Q5 | Positive (ORDER-MATTERS) may be unreachable via INSUFFICIENT_HEADROOM | B1 | IMPERFECT |
| Q2 | Same-prompt floor sound; Minor 50 label honestly caveated | — | OK |
| Q6 | Scope creep | — | OK / none |

The two INVALIDATING B0 issues collapse into one fix (compute the falsifier on the full real rendered
prompt with real surprise payloads). The B1-stats issue is real but lands at the separate B1 GO, not here.

---

## Verdict

**NEEDS-ONE-AMENDMENT: B0's premise-falsifier must be computed on the FULL rendered pulse prompt built from
the REAL surprise payloads — preserve each surprise's `features`/`trace_id`/`valence` bundled with its
magnitude and permute only the slot assignment; render via `_build_prompt`/`render_prompt_for_debug` with
the real arousal `level` passed and the real memory_dir held fixed; measure byte-identity of the whole
prompt, not an `_ev`-built trace-block slice.** As written, B0 reuses `affect_order_sensitivity.py`'s
`_ev`/`load_windows`, which discard `features` and key `trace_id` to the slot, so the rendered trace block is
the empty `"(a diffuse, unplaceable surprise)"` fallback in both orders (cold-recomputed) and PREMISE-DEAD
fires at ~100% as an artifact; and even a correct trace block omits the order-bearing arousal scalar at
`pulse_engine.py:583` (cold-recomputed: level 5.11 vs 1.62 on a matched pair). The single amendment fixes
both. Everything else (cheap-first staging, same-prompt floor, anti-spiral pre-commitments, no scope creep)
is sound and lockable. Make this fix and B0 is run-ready; the B1 burn remains a separate GO that must also
repair the `per_point_disagreement` reuse before any dollar is spent.
