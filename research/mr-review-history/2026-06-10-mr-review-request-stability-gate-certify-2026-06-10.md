# Mr. Review — COLD certification audit #2: the run-till-stability maturation stop-line

**Date:** 2026-06-10 · **Scope:** ONE redesign certification (operator-scoped; not a full review)
**Target:** `research/preregistrations/2026-06-10-maturation-stop-redesign-PROVISIONAL.md` +
`research/analysis/maturation_stability.py` + wiring site `research/harness/teacher_forced_replay.py`,
clone @ HEAD `af40645`, against the LOCKED parent
`research/preregistrations/2026-06-09-isolated-makers-pen-vs-substrate-DRAFT.md` and cold-review #1
(`2026-06-10-mr-review-request-tmax-legitimacy-2026-06-10.md`).
**Posture:** cold. Every selftest re-run from the clone root; every constant re-read from `src/`; the
worldweaver horizon figures re-read from the mounted clone's FINDINGS files, not from the spec's
quotations. No testimony used.

---

## 0. Bottom line

**REJECT AS WRITTEN — with a bounded, single-revision repair path.** The stability *instrument* is
genuinely K-independent (verified: disjoint event channels, all three thresholds are pre-existing
substrate constants, no import touches the elective spine), and building it was the right call — it
implements the half of the locked §1 stop-line that review #1 found had no code behind it. But the
redesign fails certification on two independent grounds. **(1) The design ground:** by deleting the
`≥K` conjunct from the locked stop-line ("grow until **BOTH** hold") and stopping the run the moment
the self-model settles, it manufactures by construction the very artifact it was built to kill — its
own cited horizon evidence (settle expected in hours; K plausibly needing thousands of ticks) makes
"settled ∧ sub-K" the *modal* outcome of a healthy run, and §3 then mislabels that truncated count
"INCONCLUSIVE (non-artifactual): the residual is **genuinely** too thin," when the count at settle-time
measures *when the gate fired*, not the channel's thinness. The keeper's objection to the one-day cap
("we deliberately didn't feed it enough") is thereby relocated, not repaired. **(2) The artifact
ground:** the gate as coded fires "settled" on three demonstrably false-positive states — I drove a tag
through a **full 0→1 climb in 12 h and the gate returned `settled=True` with max drift 14× below the
floor**; a contentless self-model reads settled; and a pen-dead familiar reads settled because
`record_ignition` fires "regardless of producer success" (`integrator.py:187–194`), resetting arousal so
the strangled guard cannot see it. Compounding this, the selftest's strangled branch is **dead code**
(arousal reaches 0.947 < 1.0, so the guarded assert never executes while the success banner prints
"strangled-guard") — the standing brief's §4 defect class, in the very module built to answer the last
two instances of it. The repair is small, fully specified in §3 below, uses only pre-existing constants,
and restores the locked §1 verbatim rather than amending it. If the repair is not taken, the fallback is
review #1's pinned 2880 under its own binding terms — not a third design.

---

## 1. Verification ledger

**V1 — selftests, run cold from the clone root. BOTH PASS — and one passing test is hollow.**
- `python3 research/analysis/maturation_stability.py` → PASS, banner claims four predicates including
  "strangled-guard".
- `python3 research/analysis/elective_read_choice.py --selftest` → PASS (band, follower/anti-follower
  both 0 ambiguous, `power_n(0.80,0.05,0.10,0.25)=33`, Wilson NI verdict + headroom exercised).
- **REFUTED: "each predicate FAILS if it is false" (module docstring, `maturation_stability.py:155`).**
  The strangled case (selftest step 4) forges one `surprise_observed` of magnitude 5.0 at 0.05
  baseline-half-lives (= 720 s) before `now`. `AROUSAL_HALF_LIFE_SECONDS = 300.0` (`salience.py:36`), so
  the trace decays 5.0·0.5^(720/300) = **0.947 < IGNITION_THRESHOLD = 1.0**. The assert is wrapped in
  `if s["arousal_level"] >= IGNITION_THRESHOLD:` (`maturation_stability.py:208`) — **the branch never
  executes.** I confirmed by direct evaluation: `arousal_level = 0.9473`, `strangled = False`, and the
  selftest's own "strangled" scenario returns **`settled = True`**. The strangled→not-settled predicate
  has no failing test behind it. Brief §4 class, fourth instance in this program.

**V2 — K-independence of the instrument. CONFIRMED, with two named residual channels.**
- `assess_maturity` (`maturation_stability.py:96–151`) reads only `baseline_updated` snapshots,
  `surprise_observed`/`ignition_fired` (via `derive_arousal`, which also folds in grief — still
  K-blind), and `pulse_emitted`. The elective spine (`elective_read_choice.detect_elective_reads`)
  reads only `pulse_act_emitted` (`elective_read_choice.py:112`). **Disjoint event channels; no import
  crosses.**
- All three thresholds re-read at source: `BASELINE_DECAY_HALF_LIFE = 4*3600.0` and
  `BASELINE_EPSILON = 0.02` (`src/runtime/substrate.py:33–34`); `IGNITION_THRESHOLD = 1.0`
  (`src/runtime/salience.py:37`). All predate this question; none references K, floor_mean, or yield.
  The menu has one element per threshold. **The firewall, as a property of the instrument, is real.**
- Residual channel (a): `mature()`'s live heartbeat prints `recency-ambiguous {reached}/{K}` every pulse
  and every 30 ticks (`teacher_forced_replay.py:247–249`). Once the automated K-stop is gone, the only
  agent K can still steer is the **operator watching the log** at hour 30. Strip the K readout from the
  maturation loop (compute it at analysis only), or pre-commit non-intervention in writing.
- Residual channel (b): run length still shapes K-yield (a later-settling familiar accrues more points).
  That coupling is *endogenous to the organism* with frozen thresholds — no human chooses anything — and
  is the design's stated point. Not a contamination channel. Confirmed benign.

**V3 — "the spec REMOVES the early-stop-at-K." TRUE OF THE SPEC, FALSE OF THE ARTIFACT AT HEAD.**
`mature()` still stops on `if reached >= K: break` (`teacher_forced_replay.py:250`), never imports
`assess_maturity`, and still defaults `pause: float = 0.0` with no `--pause` flag — i.e. review #1's
binding condition (c)(5) is also unimplemented at this HEAD. The spec's §3/§4 present-tense claims
("the early stop at `reached >= K` is **removed**"; "the K early-stop is gone") describe code that does
not exist. Mitigation: the spec is marked PROVISIONAL, forbids runs until certification, and §5(3) names
the wiring as a binding condition — so this is sequencing, not deception. But the prose must say *will
be removed*, or the wiring must land before the freeze, and a selftest must prove it (§3, condition R6).

**V4 — threshold soundness. THE PLATEAU TEST IS REFUTED EMPIRICALLY; the warmup and strangled guards
each have a confirmed hole.**
- **(a) Slow-ramp false positive — CONFIRMED, and it is not a corner case.** `plateaued` requires every
  *consecutive-snapshot* drift < 0.02. Snapshots are rate-limited to one per 60 s
  (`BASELINE_SNAPSHOT_INTERVAL_SECONDS = 60.0`, `salience.py:98`), so any climb slower than 0.02/min
  (= 1.2 full units/hour — faster than any plausible real concern-growth) passes as "flat". Driven
  demonstration: a tag climbing **0.10→0.94 over 12 h** → `settled=True, max_recent_drift=0.0035`; a
  **full 0→1 climb in 12 h at the live 60 s cadence** → `settled=True, max_recent_drift=0.0014` (14×
  under the floor). The EMA's own dynamics guarantee this: at `BASELINE_LEARNING_RATE = 0.25`/update,
  per-step drift ≈ the stimulus's ramp rate, so the gate only catches climbs ≥ 0.02/min. The
  worldweaver lesson this module cites — depth *still flowing* at 2 h while extent froze
  (`worldweaver/research/runs/2026-06-09-pen-vs-substrate-grow/FINDINGS.md:42–46`, re-read in the
  mounted clone) — is exactly a slow climb; **the gate as written would have called WW's still-climbing
  curve settled.** Repair: additionally require *net* window drift `drift(window[0].vec,
  window[-1].vec) < BASELINE_EPSILON` — same constants, K-blind, catches the 12 h ramp (net ≈ 0.33 ≫
  0.02) while leaving genuine plateaus untouched.
- **(a′) Churny-but-stationary false negative — real, but conservative.** A tag oscillating across the
  0.02 survival boundary (kept ↔ dropped from the payload, `salience.py:346`) produces per-step drift
  ≈ 0.02 ≥ floor forever → never plateaus → ceiling → NEVER-SETTLED. Acceptable direction (it can only
  *delay* settling, never fake it) and it lands in a named outcome — but undiagnosable as returned:
  `assess_maturity` reports `max_recent_drift` without saying **which tag**. Add the argmax tag to the
  return (diagnostic only).
- **(b) Warmup — necessary, NOT sufficient.** First snapshot lands within minutes of tick 1
  (`update_baseline` is called every integration tick, `integrator.py:143`), so `warmed_up` ≈ "run is
  ≥4 h old" — which does clear WW's observed 1–2 h cold-start churn. But a **degenerate self-model
  passes the whole gate**: `update_baseline` appends `baseline_updated` even when `by_scope` is empty
  (`salience.py:351`), empty/zero vectors drift 0.0, and I confirmed `settled=True` on contentless
  snapshots. A misconfigured `read_roots` or a dead embedder — the standing brief's named "silent killer"
  — yields a starved stimulus, a near-empty baseline, and a *trivially settled* verdict at exactly 4 h:
  the artifactual INCONCLUSIVE again, through the side door. Repair: `settled` additionally requires the
  terminal in-window snapshot to be non-degenerate (≥1 tag ≥ `BASELINE_EPSILON` — anchored, K-blind).
- **(c) Strangled guard — catches two of three strangle modes; misses the likeliest one.** It reads the
  *raw* arousal level, so refractory-blocked and night/reactivity-suppressed charge (raw ≥ 1.0, zero
  pulses) are caught — confirmed against `check_ignition` (`salience.py:496–510`). But
  `record_ignition` is written **"regardless of producer success so arousal resets"**
  (`integrator.py:187–194`): a familiar whose pen is dead (OpenRouter outage, exhausted credits — the
  realistic failure of a multi-day unattended burn) keeps igniting, keeps resetting arousal, emits zero
  pulses, and its baseline plateaus on the unchanging world → **`settled=True` on a broken mind.**
  Repair: extend the guard — `ignition_fired` in window > 0 ∧ `pulse_emitted` in window = 0 → not
  settled (pen-dead, a distinct flag). Reads only ignition/pulse events; K-blind.

**V5 — the ceiling. 20160 CERTIFIED AS GENEROUS — under the repaired stop-line, with its anchor named
honestly.** Re-derived: 7 d × 86400 s / 30 s = 20160 ticks = 42 baseline half-lives. Against the
mounted WW evidence re-read at source: keep-rate ~1.3%/tick → ~750 ticks for ~10 events
(`2026-06-09-pen-swap-keep/FINDINGS.md:40–45`); at that analog yield, K=33 needs ~2,500–3,300 ticks
(~21–28 h) — the ceiling carries a ~6–8× margin over time-to-K and a ~40× margin over the settle
window. Hitting it would be a real never-settled/never-fed result, not truncation. **But name the
anchor:** "7 days" is a calendar week — exactly as substrate-arbitrary as review #1's "one day." Its
legitimacy comes not from derivation but from (i) being frozen before any tick, (ii) being K-blind in
*choice* (it predates floor_mean and all run data), and (iii) the asymmetry that a too-generous ceiling
costs nothing in expectation (the run stops at the stop-line) while a tight one truncates. I would pin
it exactly where the spec does — 20160 — and decline to bless any *re*-derivation: a second number here
would be the spiral. Operational note, from the brief's own reboot lesson: a 7-day worst case demands
the persistent-workspace discipline (`the-stable/.runs/`, never `/tmp`) and survives-reboot resumption
*decided in advance* (a crash at day 5 must have a pre-committed answer: resume or void — write it down).

**V6 — the anti-spiral test, both directions.**
- *Is the repair mandatory rather than a spiral?* **CONFIRMED.** §11's forbidden class is enumerated
  (δ's absolute SESOI; the recency band; single-trajectory scope; perm_p-as-diagnostic) — none touched.
  Review #1 already ruled the lock *defective* on precisely these two points (§1's stability half never
  implemented; T_max never numbered) and explicitly invited this variant: "a multi-day cap … would need
  its own cold review before any paced tick" (review #1 §3(c)(1)). An artifactual INCONCLUSIVE *reported
  as a real architectural finding* is a wrong verdict — an invalidator, not a caveat. Seeking this
  certification was procedurally correct.
- *Does the redesign itself reopen the lock?* **YES — one clause, and it is the defective one.** The
  locked §1 says "grow each Maker until **BOTH** hold: ≥K … **and** a stable profile." The redesign
  quietly rewrites the stop-line to stability-*only* and demotes K to analysis. That is an *amendment*
  presented as an *implementation* — and it is exactly the amendment that recreates the artifact (V7).
- *Does run-till-stability create a new rescue surface?* The "didn't settle → run longer" surface is
  closed by §5(1)'s irrevocable freeze + the ceiling + NEVER-SETTLED as a named, pre-accepted outcome —
  confirmed adequate *if* frozen. The mirror surface — "it settled suspiciously early → tighten the
  gate" — is closed only because the thresholds are inside the freeze; this is why the gate repairs in
  §3 must land **before** the freeze, after which the gate is as immutable as the cadence.

**V7 — the central design defect (the reason for rejection), derived from the spec's own numbers.**
The spec expects settling in "hours-to-a-couple-days" (§2) and simultaneously argues K "plausibly needs
**thousands** of ticks" (§1). At 30 s cadence, "hours" = a few hundred ticks. Even with a *correct*
plateau test, settle-before-K is therefore the expected ordering of a healthy run; with the V4(a)
false-positive, the gate will plausibly fire near the 4 h warmup boundary (~480 ticks, single-digit
ambiguous points at the WW-analog yield). The run then stops, and §3 hard-codes the label: "settled ∧
sub-K → INCONCLUSIVE (**non-artifactual**): a fully-matured familiar's elective-read residual is
**genuinely** too thin." That inference is invalid: a settled familiar *goes on reading* — settling ends
the self-model's drift, not the elective-read channel — so the count at settle-time is a function of
*when an unrelated criterion fired*, not of the channel's yield. "Genuinely thin" is a **rate** claim;
it is earned only by giving a settled familiar ample further life and observing the points still not
come. The redesign deletes precisely the mechanism (the K conjunct, backstopped by the cap) by which
the locked design earned it. The keeper's objection to T_max=2880 — an artifactual "we deliberately
didn't feed it enough" — applies with *more* force to this design than to the one it replaces: 2880
ticks at least guaranteed a full circadian of accrual; stop-at-settle guarantees nothing past warmup.

---

## 2. Rulings on the six posed questions, plainly

1. **Code proves prose?** Both selftests pass cold, but the strangled predicate is proven by *dead
   code* (V1) — the module's own contract ("each predicate FAILS if it is false") is false of itself.
   §4 defect class, named.
2. **Is the firewall real?** The *instrument* is K-independent — verified to the constant and the
   import (V2). The remaining back-channels are the live K-readout in the maturation log (strip it) and
   the unbuilt wiring (V3).
3. **Is settled = warmed ∧ plateaued ∧ ¬strangled faithful to "settled; not still climbing"?** **No, as
   coded.** It is refuted by direct demonstration on all three legs: a full-range 12 h climb reads
   settled (V4a); an empty self-model reads settled (V4b); a pen-dead familiar reads settled (V4c).
   Each has a small, substrate-anchored, K-blind repair, specified below.
4. **Ceiling:** 20160 certified as genuinely generous under the repaired stop-line; calendar-anchored
   and honest about it; freeze it and never re-derive it (V5).
5. **Anti-spiral:** the repair *motive* is a legitimate invalidator repair, not a spiral — but the
   redesign as drafted reopens the locked §1 conjunction itself, and that reopening is what recreates
   the artifact (V6, V7). The new "run longer" surface is adequately closed by the freeze + ceiling +
   named outcomes, conditional on the gate repairs landing before the freeze.
6. **Was building this better than running pinned 2880 and reporting truncation?** **Building the
   stability gate: yes** — it implements a committed-but-dead half of the locked stop-line, review #1
   explicitly sanctioned the route, and *measuring* settledness is strictly more informative than
   guessing a horizon (one day might truncate; nobody knows; that ignorance was the keeper's point and
   it is quantitatively live given WW's still-climbing-at-2 h curve with no observed endpoint).
   **Adopting stability-ONLY as the stop-line: no** — it is worse than the one-day cap on the precise
   axis the keeper cared about, because it converts "maybe under-fed" into "under-fed by construction
   whenever settling beats K," which the spec's own evidence says is the expected case. This is not
   over-engineering; it is one wrong design choice plus four implementation holes inside an otherwise
   correct and well-firewalled apparatus.

---

## 3. The binding repair path (ONE revision, then cold-review #3 certifies; nothing else changes)

**R1 — Restore the locked §1 conjunction.** Stop-line: run until **`settled ∧ (ambiguous ≥ 33)`**, with
`T_ceiling = 20160` as the only other exit. 33 is not a new number: it is the locked, selftested
`power_n(0.80, 0.05, 0.10, 0.25) = 33` already asserted in the spine and already the shipped `--K`
default. Outcomes, all pre-accepted in writing:
- settled ∧ ≥33 before ceiling → **ADEQUATE** → arms run. (If analysis-time real K — from `floor_mean`
  on the ≥20 floor replicates — exceeds the collected count, that is an honest
  INCONCLUSIVE-underpowered: pre-accept it now, no extension, no rerun. This seam is inherent to any
  pre-floor_mean stop and was named by review #1 (c)(6); it cannot be removed, only pre-accepted.)
- ceiling ∧ settled ∧ <33 → **INCONCLUSIVE thin-residual — now earned:** a settled familiar lived ~6–8×
  the WW-analog time-to-K and the points did not come. This is the *only* construction under which §3's
  "genuinely too thin" sentence is true.
- ceiling ∧ ¬settled → **NEVER-SETTLED**, regardless of the count; no swap scoring (the §1 maturity
  precondition failed); reported as its own result.

**R2 — Plateau repair:** add the net-window-drift conjunct — `drift(window[0].vec, window[-1].vec) <
BASELINE_EPSILON` — alongside the existing per-step max. Same constants; closes V4(a).

**R3 — Non-degeneracy guard:** `settled` requires the terminal in-window snapshot to carry ≥1 tag ≥
`BASELINE_EPSILON`. Closes V4(b), and specifically the dead-embedder → trivially-settled path.

**R4 — Pen-dead guard:** in-window `ignition_fired > 0 ∧ pulse_emitted == 0` → not settled (flagged
`pen_dead`, distinct from `strangled`). Closes V4(c).

**R5 — Fix the selftest so every predicate has a failing test:** the strangled case must construct
arousal that actually clears 1.0 at `now` (e.g. surprise inside one arousal half-life, or two traces),
the `if` guard must become a hard assert, and new failing tests must cover R2 (the 12 h ramp from V4(a)
must assert `settled=False`), R3 (empty vec → not settled), and R4 (ignitions-without-pulses → not
settled). The prose and the selftest must compute the same predicate — the brief's standing demand,
now owed for the fourth time.

**R6 — Wire it and prove the wiring:** `mature()` stops on the R1 conjunction, never on K alone, never
on stability alone; `pause` pinned to 30.0 (or the harness refuses lower — review #1 (c)(5), still
unimplemented at HEAD); the live K-readout removed from the maturation heartbeat; `--selftest` gains
assertions that fail if the stop predicate, the pause pin, or the ceiling default are wrong.

**R7 — Then freeze, once:** the R1 stop-line, the repaired gate (thresholds + R2–R4 guards), pause=30 s,
T_ceiling=20160, the trigger disclosure, the outcome-symmetric void rule (any sub-cadence run void
whatever it yields), the crash-at-day-N resumption rule (decided in advance), and all pre-accepted
outcomes including both INCONCLUSIVE forms and NEVER-SETTLED. One amendment, ever. Any change after the
freeze, in any direction, for any reason, voids the experiment.

**The spiral floor:** if this repair is not adopted exactly, the fallback is review #1's pinned 2880
under its own §3(c) terms — not a third design. Two cold certifications is the budget; this program
does not get a fourth stop-line.

---

## 4. Knock-on questions, as a cold outsider

1. **Does the baseline breathe with the circadian?** If the self-model tracks day/night modulation, the
   net-drift conjunct (R2) over a 4 h window may oscillate above 0.02 indefinitely → NEVER-SETTLED by
   rhythm, not by immaturity. The argmax-tag diagnostic (V4a′) makes this diagnosable post-hoc; decide
   *now* whether a circadian-breathing NEVER-SETTLED is acceptable as a finding (I rule it is — it is a
   true statement about the organism), so it cannot become a reason to amend later.
2. **What is the actual ambiguous-point yield?** Everything hinges on a rate nobody has measured: the
   one void run produced ~1 read in 400 racing ticks. The first day of the real run will reveal the
   yield — and *nobody gets to act on that revelation*, because the stop-line is frozen. Say that out
   loud in the freeze.
3. **The first-snapshot anchor is gameable in principle:** warmup counts from the first
   `baseline_updated`, which the harness could in principle delay. No evidence of this; pin it shut by
   asserting in the manifest that the first snapshot's ts is within minutes of tick 1.
4. **Seven days × N Makers is an operational exposure** (credits, reboots, the embedder's silent death —
   which R3 now at least converts from a fake "settled" into a visible non-settle). The pilot's worst
   case should be budgeted as real before the first tick, not discovered at day 4.

---

## 5. Verdict, plainly

**REJECT AS WRITTEN.** The K-independence firewall is real and the gate was worth building — but the
gate as coded calls a full-range 12 h climb, an empty self-model, and a pen-dead familiar all "settled"
(each demonstrated by execution in this clone, not argued), its selftest proves the strangled predicate
with a branch that never runs, and the design's deletion of the locked §1 K-conjunct converts the
keeper's feared artifact — "we deliberately didn't feed it enough" — from a risk into the construction.
The repair (§3, R1–R7) is bounded, uses only constants that already exist in `src/runtime`, restores
the locked stop-line verbatim instead of amending it, and earns the "genuinely thin" sentence the
current draft merely asserts. Bring it back once, repaired, and cold-review #3 rules on the diff against
this document. If any of R1–R7 is unmet — or a fourth stop-line ever appears — run the pinned 2880
under review #1's terms; the prereg's own §4 then names what is happening.

*— Mr. Review, cold, from the clone at `af40645`. Selftests re-run; false positives driven, not
hypothesized; WW figures re-read at source in the mounted clone; testimony unused.*
