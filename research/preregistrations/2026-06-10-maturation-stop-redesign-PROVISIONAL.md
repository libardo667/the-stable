# Maturation stop-line redesign — FROZEN 2026-06-10 (as repaired by cold-review #2 §3, R1–R7)

**Status: FROZEN — historical record; the binding text lives elsewhere.** Cold-review #2
(`research/mr-review-history/2026-06-10-mr-review-request-stability-gate-certify-2026-06-10.md`)
**REJECTED this redesign as written**: the stability-ONLY stop-line in §2/§3 below deleted the locked
§1 K-conjunct and thereby manufactured the artifact it was built to kill, and the gate as coded had
three driven false positives (slow ramp, contentless self-model, dead pen) plus a dead-code selftest
branch. The K-independent *instrument* was certified as real and worth building. The repair — R1–R7,
implemented exactly, no fourth design — is folded into the locked prereg as **AMENDMENT 1** of
`2026-06-09-isolated-makers-pen-vs-substrate-DRAFT.md`, which is the ONLY binding text. This document
is preserved unedited below as the honest record of the rejected intermediate design; read it as
history, not as protocol. Its §2 stability-only stop-line and §3 "settled ∧ sub-K → non-artifactual
INCONCLUSIVE" labeling are REPUDIATED (review #2 V7: the count at settle-time measures when the gate
fired, not the channel's thinness).

**Trigger disclosed (required honesty, per review #1):** this redesign was prompted by (a) a VOID first
run that raced at `pause=0.0` and produced no informative data, and (b) the keeper's objection that the
one-day cap (`T_max=2880`) proposed in cold-review #1 was a *vibe* — backfilled from an offhand "400
ticks isn't a full-day test" into a hard "exactly one day," which was never the committed design.

---

## 1. The defect being repaired

The locked §1 stop-line reads, verbatim:

> **Stop-line (stability, not tick count); grow each Maker until BOTH hold:** ≥K recency-ambiguous
> elective read-choice points, **and a stable drive/concern profile (the slow self-model settled; not
> still climbing).**

Two lock defects, both of the standing brief's §4 class (*prose asserts a property the artifact lacks*):

1. **The stability half of the stop-line was never implemented.** `mature()` only ever checked K. The
   committed "until the profile is settled" criterion had no code behind it.
2. **`T_max` was committed only as a *word* ("pre-committed"), never a number** (cold-review #1, V1).

Cold-review #1's `T_max=2880` correctly pinned the **cadence** (30 s, the shipped daemon cadence,
`scripts/familiar.py:398`, = `IGNITION_REFRACTORY_SECONDS`) but silently pinned the **horizon** to *one*
circadian period — and "maturation = one day" is committed nowhere. The thesis is that a familiar
"accrues a real memory across **days**" (CLAUDE.md). A one-day cap can truncate before the self-model
settles, making a sub-K result ambiguous between "the read-residual is genuinely thin" (a real finding)
and "we stopped it too soon" (an artifact). For our one Point-It-At-The-Sky attempt, that ambiguity is
the failure mode to eliminate.

**Worldweaver evidence the horizon is long and multi-cycle (the parent program, mounted as context):**
- grow cohort: the structural EXTENT curve froze in ~1 h, but the SCORED DEPTH curve was *"still
  flowing"* at the end of a ~2 h window; the monitor had to be changed mid-run to require **both** flat
  (`research/runs/2026-06-09-pen-vs-substrate-grow/FINDINGS.md` §2).
- keep-curation rate ~1.3%/tick → *"reaching ~10 keeps/resident would need ~750 ticks/resident — an
  infeasible run at this rate"*; the measure *"as drafted is unpowered"*
  (`research/runs/2026-06-09-pen-swap-keep/FINDINGS.md`). Our elective-read channel is the direct analog;
  K=33 plausibly needs **thousands** of ticks, and a starved residual is a *live, real* outcome — exactly
  why it must be measured only after genuine maturation.

## 2. The stop-line, operationalized (run-till-maturity, NOT a clock)

Maturation runs until the slow self-model is **SETTLED**, or a generous ceiling is hit. The settled test
is `research/analysis/maturation_stability.py::assess_maturity` — built + selftested, K-independent by
construction (it reads only the baseline self-model and the arousal/pulse waveform; it never sees an
elective-read count). All thresholds are anchored to the substrate's **own** habituation constants:

`settled ⇔ warmed_up ∧ plateaued ∧ ¬strangled`
- **warmed_up** — ≥ one habituation half-life (`BASELINE_DECAY_HALF_LIFE = 4 h`) since the self-model
  first formed. The gate *cannot* fire inside cold-start warmup (WW: warmup dominates the early hours).
- **plateaued** — across the trailing 4 h window there are ≥2 baseline snapshots and **every**
  consecutive-snapshot drift is below `BASELINE_EPSILON = 0.02` (the per-tag value below which a feature
  does not even survive into the self-model). Drift is the **max** over tags, never the mean: a single
  still-climbing concern vetoes "settled" (the WW "extent froze while depth climbed" lesson).
- **¬strangled** — NOT (terminal arousal ≥ `IGNITION_THRESHOLD = 1.0` with zero pulses discharged in the
  window). Charge with no falling edge is not maturity (WW feedback-2's three-silences: settled-quiet ≠
  strangled-quiet ≠ dark-room-quiet).

**Cadence:** `pause = 30.0 s`, the shipped daemon cadence (cold-review #1's forced derivation, retained).

**Generous ceiling (the spiral-closer, expected NOT to bind):** `T_ceiling = 20160 ticks` (= 7 days at
30 s ≈ 42 habituation half-lives). Its only job is to forbid grow-until-K recursion. The run stops the
*moment* stability fires (expected: hours-to-a-couple-days), so the ceiling bounds the worst case, not
the expected burn. **PROPOSED — the reviewer is asked to certify this is genuinely generous (rarely
binds) and not a disguised tight cap.**

## 3. The K-check is applied at ANALYSIS, on a disjoint instrument (review #1 (c)(6))

Maturation stops on **stability only** — the early stop at `reached >= K` is **removed**, so run length
cannot depend on K at all. After the run stops, K is read once, by the separate §3 spine:
- **settled ∧ ≥K recency-ambiguous reads** → **ADEQUATE** → run KEEP/KEEP′/SWAP-B/SWAP-C, score §3/§5.
- **settled ∧ sub-K** → **INCONCLUSIVE (non-artifactual):** *a fully-matured familiar's elective-read
  residual is genuinely too thin to carry a strong falsifiable claim* — the WW starved-measure finding,
  replicated in the isolated venue. A real, reportable result about the architecture.
- **ceiling hit without settling** → **NEVER-SETTLED:** a distinct result (did not stabilize in ample
  time), never conflated with the matured-but-thin case.

## 4. The K-independence firewall (the property the reviewer must certify)

- The stability instrument (`maturation_stability`) reads baseline + arousal/pulse only. The K instrument
  (`elective_read_choice`) reads elective-read choice points only. **Disjoint inputs.**
- Every stability threshold is a pre-existing substrate constant (4 h, 0.02, 1.0); none is fit to K,
  floor_mean, or ambiguous-read yield. The menu has one element per threshold → no selection.
- Run length is set by stability + the K-blind ceiling; the K early-stop is gone. K cannot steer when the
  run ends, so it cannot steer the powered slice's size by feedback.

## 5. Binding conditions on certification (carried/adapted from review #1)

On a certifying ruling, and only then:
1. **Freeze irrevocably** in the locked prereg: this stop-line, `pause=30 s`, `T_ceiling=20160`, the
   substrate-anchored thresholds, and the disclosure of the trigger. *Any later change to the stop-line,
   the cadence, or the ceiling, in any direction, for any reason, voids the experiment.* One amendment.
2. **Pre-accept all three §3 outcomes in writing**, including both INCONCLUSIVE forms — no second run, no
   second amendment, no growing the ceiling.
3. **Code proves prose:** `maturation_stability._selftest()` (each predicate fails when false) and the
   §3 spine selftest both green; `mature()` stops on `assess_maturity(...)["settled"]`, never on K.
4. **Outcome-symmetric void rule:** any run at `pause < 30 s` is void whatever it yields.

*Profile-stability is hereby promoted from cold-review #1's "incidental / reported diagnostic" to the
**gate** — which is precisely the keeper's objection, made load-bearing.*
