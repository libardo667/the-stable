# Mr. Review — COLD methodological audit: is committing T_max now a completion or a rescue-spiral?

**Date:** 2026-06-10 · **Scope:** ONE pre-registration decision (operator-scoped; not a full review)
**Target:** `research/preregistrations/2026-06-09-isolated-makers-pen-vs-substrate-DRAFT.md` (§4, §11) +
`research/harness/teacher_forced_replay.py` @ HEAD `e17d118`
**Posture:** cold; every load-bearing claim re-derived from the clone; operator testimony about the
gitignored `.runs/` first run was **not used** in any ruling (verified below — the ruling survives with
that testimony deleted).

---

## 1. Verification ledger (confirm/refute each operator claim against the clone)

**V1 — Is any numeric T_max committed in the locked text? REFUTED-AS-COMMITTED (operator claim CONFIRMED: none exists).**
`grep -n -i 't_max\|tmax\|400' research/preregistrations/2026-06-09-...-DRAFT.md` → `T_max` appears at
lines 122–126 (§4) and line 276 (§11). §4 calls it "**pre-committed**" and gives it the spiral-closing
role verbatim: *"Reaching `T_max` below K is NOT 'grow longer' — it is the §6 INCONCLUSIVE-by-starvation
result, full stop. 'Grow until K' cannot recurse."* **No numeric value appears anywhere in the document.
The string `400` does not occur in the prereg at all.** Contrast within the same document: δ=0.15 is
written as a number five separate times (lines 7, 113, 170, 279, plus §8's `bound` form); the band is
written as `w=0.25` → `[0.25, 0.75]` (line 89); the Wilson one-sided level is written (`α=0.05 → z=1.645`,
line 175). The lock's authors knew how to commit a number. T_max got the *word* "pre-committed" and no
number — **the prose asserts a property the artifact does not have.**

**V2 — What does §11 forbid re-opening, and is T_max's value in that class? CONFIRMED: it is not.**
§11's forbidden class is precisely enumerated: the four **accepted limitations** (δ's absolute-SESOI
choice; the recency band in lieu of the conditional logit; single-trajectory teacher-forcing scope;
`perm_p` as diagnostic) — *committed analytic choices* whose re-opening is the spiral. The escape clause:
*"We re-open only an invalidator."* T_max's **value is not in the enumerated class because it was never a
committed choice — there is nothing to re-open.** What §4 *does* commit, and what must not be weakened, is
T_max's **role**: a hard cap exists; reaching it below K is the §6 result; no recursion. Assigning the
never-assigned number instantiates that role; it does not weaken it. (Whether the *assignment itself* is
clean is ruled in §3–§4 below.)

**V3 — Harness at HEAD. CONFIRMED on all three sub-claims.**
- `mature()` signature: `pause: float = 0.0` (`teacher_forced_replay.py:200`); the pause is honored only
  as `if pause: await asyncio.sleep(pause)` (:245–246); **`main()` never passes `pause` and argparse
  exposes no `--pause` flag** (:377–399 — flags are `--selftest --mature --model --K --t-max --run-dir
  --replay --swap` only). At this HEAD, a maturation run **could only have raced**. Not testimony — code.
- `--t-max` default `400` (:383) carries no derivation, no comment beyond "hard maturation cap (ticks) —
  §4", no selftest touching it, and no corresponding number in the locked text. **A bare placeholder.**
- The genuinely committed quantities are real and machine-checked — I re-ran both selftests cold:
  - `python3 research/analysis/elective_read_choice.py --selftest` → **PASS**: band `[0.25, 0.75]`
    (`w=0.25`, `elective_read_choice.py:23,97,109`); recency-follower AND anti-recency-follower both score
    0 ambiguous (:331–332); `power_n(0.80, 0.05, 0.10, 0.25) == 33` asserted (:351); Wilson NI verdict +
    headroom gate exercised.
  - `python3 research/harness/teacher_forced_replay.py --selftest` → **PASS**: `DELTA = 0.15` (:46),
    correlate/parity/HOLDS/FALSE/C4 all exercised.
  These are committed in the brief's required sense — the code **proves** the prose. T_max=400 has no such
  proof anywhere. δ, the band, the Wilson form, and `power_n` are untouched by this question; confirmed.

**V4 — Is a raced run mechanistically void, or just disappointing? VOID, derivable from committed code
without any testimony.** The substrate's pulse economy is **wall-clock-gated in seconds**, not
tick-gated:
- `IGNITION_REFRACTORY_SECONDS = 30.0` (`src/runtime/salience.py:38`) — after any ignition, further
  arousal-driven ignitions are blocked for 30 s of wall clock (:496, :504–505).
- Settling requires `calm_seconds >= REPOSE_THRESHOLD_SECONDS = 300.0` (:64, :580–581); fervor requires
  `restless_seconds >= FERVOR_THRESHOLD_SECONDS = 180.0` (:72, :609–610); salience ages by
  `total_seconds()` (:413, :437).
A 400-tick run at `pause=0.0` completes in minutes of wall clock: the refractory window alone caps it at
roughly one ignition per 30 s of real time, settling can **never** fire inside a sub-5-minute run, and the
leaky integrals see a compressed, alien timescale. Such a run does not under-sample the paced process — it
samples a **different process**. The prereg's unit is "a Maker **matures**" (§4) with a stop-line of "a
stable drive/concern profile" (§1) against a **day-period circadian** (`src/runtime/circadian.py:1` — "a
per-resident day/night rhythm", Major 50). Maturation in this architecture is wall-clock-coupled by
committed design. **The VOID classification is therefore legitimate on mechanism, knowable before the run
executed, and — critically — outcome-symmetric: a raced run that had somehow reached K would be exactly as
void.** (Operator-reported figures — 400 ticks/~2 min, 3 ignitions, 1 read — are *consistent* with these
constants but were not needed and were not used.)

**V5 — The natural cadence is itself a committed constant.** `scripts/familiar.py:398`:
`--tick, type=float, default=30.0, "seconds between ticks (daemon cadence)"`. This is the shipped rhythm a
deployed familiar lives at, and it is not arbitrary relative to the substrate: it **equals**
`IGNITION_REFRACTORY_SECONDS = 30.0` — at the daemon cadence every tick is ignition-eligible; faster ticks
are refractory-wasted. `86400 / 30.0 = 2880` ticks per day. The day-scaled cap is therefore **forced by
two constants that predate this question**: the circadian's native period (the day) and the daemon cadence
(30 s). I re-derived 2880 myself; no operator figure accepted.

**V6 — What I could NOT verify.** The clone's git history is a single squashed commit (`git log` → 1
commit, `e17d118`). The claim "the harness was built after the lock" is **not verifiable from git here**.
The ruling does not rest on it: the locked text itself files the harness under "**Must-build-before-run
(not lock-blocking)**" (prereg lines 15–17), i.e. the lock's own structure places the harness *outside*
the locked commitments. That textual fact is sufficient and is what I rely on.

---

## 2. The K-independence test (the test the operator most wanted)

**Question:** is "T_max = day / pause — a fact about how long a being lives" genuinely independent of
K-reachability, or a disguised way to size T_max until K becomes reachable?

**Answer: the derivation is K-blind IFF it has no free parameter — and as the operator phrased it, it has
one.** "T_max = one_day / pause" with `pause` a free variable is the spiral wearing a day-scaling costume:
run at `pause=5` and the formula silently mints 17,280 ticks — 6× the tick-density of a deployed familiar's
day, chosen *after* knowing starvation is the live risk. Wall-clock duration alone does not make a run "a
day of natural life"; the wall-clock-gated dynamics (V4) match the deployed organism only at the deployed
cadence. **The K-blind form is: `pause := the shipped daemon cadence (30.0 s, scripts/familiar.py:398)`,
`T_max := 86400 / 30 = 2880`.** Both constants pre-exist this question, neither references K, and the menu
has exactly one element — **selection bias requires alternatives, and a one-element menu admits no
selection.** If the day-forced 2880 happens to make K reachable, that is the experiment getting the fair
chance §4 always described, not contamination; contamination would require the number to have been *chosen
because* it reaches K, and a forced number is not chosen at all.

**The honest residue, named:** the *timing* of this amendment is outcome-triggered — the impulse to fix
T_max arrived after watching a run starve. Timing-bias cannot steer a forced value, but it could steer the
binary "amend vs. run 400 as-is." That binary is resolved below on grounds checkable **without** the run's
outcome (V1: 400 was never committed; V3+V4: the same code-default logic that would bind 400 would bind
`pause=0.0`, which contradicts the prereg's own committed maturation concept). The firewall holds — but the
amendment must **disclose the trigger** rather than narrate itself as a serene completion.

---

## 3. Rulings

### (a) Is T_max genuinely uncommitted, or is 400 the de facto cap? — **GENUINELY UNCOMMITTED. 400 does not stand.**

The locked text commits T_max's **role** and never its **value** (V1). The only place 400 exists is a bare
argparse default in machinery the lock itself classifies as outside the lock (V6). And the decisive
symmetry: **any argument that promotes the harness's defaults to committed status promotes `pause=0.0`
with equal force** — and a pause-0.0 "maturation" is incoherent under the prereg's own committed,
wall-clock-coupled definition of maturing (V4). You cannot bind to half a default set. Treating post-lock
code accidents as commitments would also invert the prereg's authority structure — the locked text binds
the code, never the reverse. Additionally, 400 ticks at the *natural* cadence is 200 minutes — a cap that
truncates the day-period circadian mid-cycle and so structurally forecloses §1's second stop-line (a
stable profile against a day/night rhythm), i.e. it builds starvation in by construction rather than
testing for it. **Rejecting "400 stands" is therefore not loyalty to the operator's preference; it is what
the locked text and the committed substrate code jointly require.**

**But name the defect honestly:** §4 says "pre-committed" about a number that was never committed. That is
the standing brief's §4 failure class — *prose asserting a property the artifact lacks* — appearing for a
**third** time in this program, this time inside the locked pre-registration itself, and **four review
rounds (including cold ones — my own lineage) passed it.** The lock was defective on this point. The
amendment must be recorded as **repairing a lock defect**, not as a clean completion of a flawless lock.

### (b) Does the void run poison the well? — **NO, under two conditions it already meets and one it must commit to.**

The strict position ("a cap is honest only if frozen before ANY execution") would be correct if the
executed run could have informed the cap's value. It could not, on two grounds that hold without
testimony: (1) the run's voidness is derivable from committed code at HEAD (V3: no `--pause`, default 0.0;
V4: wall-clock gates) — it was void *by construction before it ran*, not declared void after its outcome
disappointed; (2) the replacement value is forced by pre-existing constants (V5, §2) — a raced run's
contents, whatever they were, had no parameter to steer. The condition to commit: **voidness must be
outcome-symmetric in writing** — any maturation run at a pause below the committed cadence is void
*regardless of what it produced, including a K-reaching one*. Otherwise "void" is merely the name given to
runs one didn't like, and the well is poisoned retroactively.

### (c) What discipline makes committing T_max now defensible? — **LEGITIMATE COMPLETION, conditional on ALL of the following. The operator asked to be bound; these are the binding terms.**

1. **The value is forced, not chosen:** `T_max = 86400 s / 30.0 s = 2880` ticks — one circadian period at
   the shipped daemon cadence. The amendment must show this derivation citing
   `scripts/familiar.py:398` and `src/runtime/circadian.py`, with **zero reference to K, to floor_mean, or
   to any estimate of ambiguous-point yield.** If a different pause or a multi-day cap is wanted instead,
   the derivation acquires a free parameter and this ruling does **not** cover it — that variant would
   need its own cold review *before* any paced tick.
2. **Freeze irrevocably in the locked text, before the first paced tick:** a dated amendment block in the
   prereg stating T_max = 2880, pause = 30.0 s, the derivation, **the disclosure that the amendment was
   triggered by a void raced run**, and the clause: *any future change to T_max or to the maturation
   pause, in either direction, for any reason, voids the experiment.* One amendment, ever.
3. **Pre-accept starvation as the result, in writing:** *a genuinely day-paced run that ends below K at
   T_max = 2880 IS the §6 INCONCLUSIVE-by-starvation finding — full stop, no second day, no second
   amendment.* This re-arms §4's spiral-closer with a real number in the chamber for the first time.
4. **Commit the outcome-symmetric void rule** (ruling (b)): pause < 30.0 s ⇒ the run is void whatever it
   yields.
5. **Make the code prove the prose (the brief's standing demand — do not skip this one):** the harness's
   `--t-max` default becomes 2880 with the derivation in a comment; `mature()`'s pause is pinned to 30.0
   (or the harness **refuses** to burn at a lower pause); and `--selftest` gains an assertion that fails
   if `t_max_default != 86400 / TICK_SECONDS` or if a sub-cadence burn is accepted. Twice now in this
   program a docstring described a fix the code didn't implement; "pre-committed" describing an
   uncommitted number is the third. The selftest and the amendment prose must compute the same predicate.
6. **Recommended hardening (not binding, but it strengthens K-independence from derivation-level to
   code-level):** remove `mature()`'s early stop at `reached >= K` (:243–244) and always run the full
   2880. Then maturation length does not depend on K **at all** — T_max stops racing K and becomes purely
   the life's duration, with the K-gate applied at analysis. This also dissolves a seam this audit
   noticed in passing: the early-stop uses the *provisional* K=33 (`--K` default), but the real K is
   `power_n(..., floor_mean, ...)` computed only after the ≥20 floor replicates — an early-stopped run
   could be retroactively underpowered if `floor_mean > 0.1`. Running the full day makes that seam moot.

---

## 4. Incidental finding (out of scope; flagged, not ruled)

§1's stop-line requires **BOTH** ≥K ambiguous points **and** "a stable drive/concern profile"; `mature()`
implements only the K check (:243–244) and never evaluates profile stability. Same prose-vs-code defect
class. If condition (c)(6) is adopted (run the full day, no early stop), the gap narrows but the stability
criterion still goes unmeasured — decide before the run whether it is a gate or a reported diagnostic, and
write down which.

---

## 5. Verdict, plainly

**Committing T_max now is a LEGITIMATE COMPLETION, not a disguised rescue-spiral — but only in the exact
form bound in §3(c), and only with the lock defect named as a defect.** 400 does not stand: it was never
in the locked text, and the only argument for it would equally bind the pause-0.0 bug. The void run does
not poison the well, because its voidness is mechanism-derived from committed code (verifiable in this
clone without a byte of testimony) and the replacement number admits no choice. The day-scaled
justification passes the K-independence test **in its pinned form** (2880 = day / shipped-cadence) and
fails it in its quoted form ("day / pause", pause free) — the operator should notice that the version of
the idea they wrote in the question is the contaminated one, and the discipline above is what
decontaminates it. If any binding condition is unmet — a different pause, a second amendment, a missing
selftest — this ruling is void and the prereg's own §4 text then names what is happening.

*— Mr. Review, cold, from the clone at `e17d118`. Selftests re-run; numbers re-derived; testimony unused.*
