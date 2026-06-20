# Mr. Review — COLD certification #3: the R1–R7 repair, ruled on the diff af40645 → 7deb588

**Date:** 2026-06-10 · **Scope:** ONE ruling — was cold-review #2's §3 R1–R7 repair implemented EXACTLY,
and does anything beyond it constitute a fourth design? **The last certification in this chain's budget.**
**Rubric:** `research/mr-review-history/2026-06-10-mr-review-request-stability-gate-certify-2026-06-10.md` §3
(the binding spec), against the LOCKED parent prereg §1/§4/§11.
**Posture:** cold. Every selftest re-run from the clone root; every constant re-read from `src/`; every
gate conjunct and every wiring assertion **mutation-tested** (broken in place, observed RED, restored —
13 mutations, 13 red); review #2's three driven false positives re-driven independently of the shipped
selftest. Testimony used for exactly one claim, named below.

---

## 0. Bottom line

**CERTIFIED-AS-R1-R7, WITH CAVEATS (none of which is an unmet Rn; the fallback is NOT triggered).**
All seven repairs are implemented exactly as specified: the stop-line is the locked §1 BOTH-conjunct
verbatim with `T_ceiling=20160` as the only other exit and all four outcomes pre-accepted and correctly
encoded (R1 ✓); the net-window-drift conjunct, the non-degeneracy guard, and the pen-dead guard are in
the gate, K-blind, on pre-existing substrate constants, and each of review #2's three driven false
positives — the 12 h 0→1 ramp at 60 s cadence, the contentless self-model, the pen-dead familiar — now
returns `settled=False` when I drive it myself (R2–R4 ✓); every predicate has a failing test behind it
— I broke all six gate conjuncts plus the strangled forge and the selftest went red all seven times,
and the strangled branch is provably live (forged arousal 3.585 ≥ 1.0, hard assert, with a tripwire
assert that itself goes red if the forge ever decays sub-threshold again — the §4-class defect is
actually gone, fourth time paid) (R5 ✓); the harness stops on the conjunction and nothing else, refuses
`pause < 30.0` live, defaults the ceiling to 20160, carries no K/count readout anywhere in the live
loop, asserts the first-snapshot anchor both in-loop and in the manifest, and implements cumulative-
budget crash resumption with mismatch refusal — and six wiring mutations (stop→OR, stop→K-alone,
stop→stability-alone, unpinned cadence, changed ceiling, thin-residual-without-ceiling) each turned the
selftest red (R6 ✓); AMENDMENT 1 contains every item review #2's R7 enumerated, including all three
knock-on pre-rulings, and the PROVISIONAL doc is honestly frozen as REJECTED history with its
stability-only stop-line explicitly repudiated (R7 ✓). The spiral floor holds: no fourth stop-line
exists; every diff hunk beyond the literal spec traces to an Rn or a review-#2 knock-on, **except one**
— the `familiar/maker/familiar.json` `dormant: true→false` flip, which is operational launch enablement,
not design, but carries a named hazard (caveat 2). **On the launch-in-parallel sequencing:** review #2's
plain reading ("ONE revision, **then** cold-review #3 certifies") makes certification a gate, and
launching before this ruling **breached that ordering** — a real procedural violation, honestly
disclosed, that gambled the burn on this ruling: had any Rn been unmet, the run would have been burning
an uncertified design and its claim to the protocol void. Because every Rn is met, the freeze is
disclosed as landing before the first tick (testimony — unverifiable from this clone, named as such),
and the run burns at exactly the frozen parameters either way, **the run KEEPS its claim to the
pre-registered protocol**; the record must carry the breach as a permanent caveat, and the review
budget is now consumed — no re-litigation of this certification in any direction, whatever the run yields.

---

## 1. Verification ledger

### V1 — selftests, run cold from the clone root. ALL THREE PASS.
- `python3 research/analysis/maturation_stability.py` → PASS: settled/climbing/cold-start/strangled
  (arousal **3.58 ≥ 1.0** — the previously dead branch now executes with real charge) / R2 ramp
  (net 0.333 ≥ 0.02) / R3 empty-vec / R4 pen-dead.
- `python3 research/harness/teacher_forced_replay.py --selftest` → PASS: correlate, parity 1.0,
  HOLDS/FALSE, C4, **stop-line=settled∧K (never either alone), pause ≥30 s, ceiling 20160**.
- `python3 research/analysis/elective_read_choice.py --selftest` → PASS, `power_n(0.80,0.05,0.10,0.25)=33`
  asserted in the spine (`elective_read_choice.py:351`) — confirming 33 is the pre-existing locked
  number, and `git show af40645` confirms `--K` default 33 **predates this repair** (old line 389).

### V2 — R1, the stop-line. CONFIRMED EXACT.
- `stop_decision(settled, reached, K) = settled ∧ reached ≥ K` (`teacher_forced_replay.py:61–65`) — the
  locked §1 conjunct verbatim (parent prereg lines 47–49 re-read at source). The `mature()` loop's only
  exits are this break and the `range(start_tick, t_max+1)` ceiling (lines 303–335); no third exit. The
  in-loop no-baseline abort (line 315) is an apparatus-integrity abort firing within ~6 minutes, not an
  outcome path — it classifies nothing; ruled not-a-stop-line.
- `T_CEILING_TICKS = 20160` re-derived: 7 d × 86400 / 30 = 20160 = 42 × 4 h half-lives ✓. Per review #2
  V5's own ruling I decline to re-derive it further — it is the frozen number and is encoded as the
  default (`_build_parser`, asserted in the selftest).
- All four outcomes pre-accepted in AMENDMENT 1 §A1.3 **and** correctly encoded in `classify_outcome`
  (lines 68–83): ADEQUATE; INCONCLUSIVE-underpowered named as an analysis-time label (A1.3(1) — the
  harness cannot know `floor_mean`, correctly so); INCONCLUSIVE-thin-residual **only** at
  ceiling ∧ settled; NEVER-SETTLED at ceiling ∧ ¬settled regardless of count (selftested with
  reached=50 > K); INCOMPLETE otherwise. **The interrupted settled-but-sub-K case cannot claim
  thin-residual:** asserted at selftest line 485–486, and my mutation removing the `hit_ceiling`
  condition from the thin-residual branch turned the selftest RED.

### V3 — R2–R4, the gate repairs, re-driven INDEPENDENTLY (not via the shipped selftest).
I constructed review #2's false positives myself and ran them through the repaired `assess_maturity`:

| review #2 driven false positive | old gate | repaired gate |
|---|---|---|
| full 0→1 ramp over 12 h @ 60 s cadence | settled=True (per-step 0.0014, 14× under floor) | **settled=False** — per-step max 0.00139 still under floor (the R2 hole still exercised), `net_window_drift=0.333 ≥ 0.02` vetoes; argmax tag named (`self.rest_drive`) |
| 0.10→0.94 ramp over 12 h | settled=True | **settled=False** (net 0.28) |
| contentless self-model (empty `by_scope`), warmed, zero drift | settled=True | **settled=False** — `non_degenerate=False` while warmed/plateaued both pass, i.e. R3 alone stands between this and "settled", exactly as specified |
| pen-dead (flat baseline, 2 in-window ignitions, 0 pulses) | settled=True | **settled=False** — `pen_dead=True`, `strangled=False` (confirming the old guard is blind here and the new one is the distinct flag R4 demanded) |

- Every threshold is still a pre-existing substrate constant, re-read at source:
  `BASELINE_DECAY_HALF_LIFE = 4*3600.0`, `BASELINE_EPSILON = 0.02` (`substrate.py:33–34`),
  `IGNITION_THRESHOLD = 1.0`, `AROUSAL_HALF_LIFE_SECONDS = 300.0`,
  `BASELINE_SNAPSHOT_INTERVAL_SECONDS = 60.0` (`salience.py:36–37,98`). No new number entered the gate.
- **K-independence survived the repair:** `maturation_stability.py` imports only
  `salience.{IGNITION_THRESHOLD, derive_arousal}` and `substrate.{BASELINE_DECAY_HALF_LIFE,
  BASELINE_EPSILON}` (lines 58–59); `assess_maturity` reads `baseline_updated` / `surprise_observed` /
  `ignition_fired` / `pulse_emitted` only — the elective spine's `pulse_act_emitted` channel is never
  touched, no import crosses. The firewall I certified in #2 is intact.

### V4 — R5, the selftest contract, MUTATION-TESTED (the failing-test property verified, not assumed).
Each conjunct broken in place in the clone, selftest run, restored via git — **7/7 went RED:**

| mutation | result |
|---|---|
| drop `net_ok` from `plateaued` | RED (case 6, the verbatim 12 h ramp) |
| force `non_degenerate = True` | RED (case 7) |
| force `pen_dead = False` | RED (case 8) |
| force `strangled = False` | RED (case 4) |
| drop the per-step `all(d < floor)` leg | RED (case 2b, spike-and-return — without which this mutation would have been GREEN; see §2) |
| force `warmed_up = True` | RED (case 3) |
| weaken the forge (`at(2.99)` → `at(2.5)`) | RED **on the tripwire assert specifically**: "forged arousal did not clear ignition threshold — the strangled test would be dead code again" — with the returned dict showing `settled: True, arousal 0.0`, i.e. exactly the silent-pass the old draft shipped, now impossible |

- The strangled forge verified by hand: surprise at 144 s before `now` (0.01 × 14400 s), one arousal
  half-life = 300 s → 5.0 · 0.5^(144/300) = **3.585 ≥ 1.0**. Both asserts at lines 280–282 are HARD —
  no `if` guard anywhere in the branch. The §4-class defect (fourth instance, per the brief) is gone,
  and the tripwire makes its recurrence self-detecting.

### V5 — R6, the wiring, READ + RUN + MUTATION-TESTED.
- **Stop:** the loop breaks only on `stop_decision(...)` (line 332–334); `hit_ceiling` initialized True,
  falsified only by the stop-line break; the old `if reached >= K: break` is gone (confirmed against
  `git show af40645`, old line 52, which also printed `reached/{K}` on every pulse and every heartbeat —
  both removed).
- **Pause pin, tried live:** `--mature /nonexistent-dir --pause 10` →
  `ValueError: pause=10.0 < 30.0s: REFUSED` — raised as the *first statement* of `mature()`, before any
  substrate construction; also exercised inside the selftest (`pause=29.9` → ValueError expected).
- **Ceiling default** `t_max = T_CEILING_TICKS = 20160` ✓, asserted against the literal in the selftest
  (my mutation to 2880 went RED — the literal, not the constant, anchors the assert, correctly).
- **K-blind loop, grepped:** the only prints inside the loop are the pulse line (felt_sense), the sparse
  stability heartbeat (settled/warmed/plateaued/drift/strangled/pen_dead), and the state.json-skip
  warning. `reached` feeds `stop_decision` and the end-of-run manifest/print only; `progress.json`
  carries `{home_dir, model, ticks_run, ts}` — no count. The start banner names the stop-line's *shape*,
  never a number. Review #2 V2(a) is closed as specified.
- **First-snapshot anchor:** in-loop fail-fast (`n_snapshots == 0` past 300 s of ticking → abort NOW,
  line 315–317) **and** the post-run manifest assert measured ledger-internally (first baseline ts −
  first event ts ≤ 300 s, lines 341–346) so it survives resumption. Both present as R7/knock-on-3 demanded.
- **Resumption:** `progress.json` written **every tick** (line 329–331); resume sets
  `start_tick = ticks_run + 1` against the SAME `t_max` total (cumulative budget); a `run_dir` with
  mismatched home/model is **refused** (lines 276–278). Mechanics selftested (read-back of ticks_run=412).
- **Docstring vs code (my V3):** the module and `mature()` docstrings now describe exactly what the code
  does — frozen stop-line, refusal, silent count, resumption. No present-tense claim about absent code found.
- Six wiring mutations (table in §0) — all RED.

### V6 — R7, the freeze. COMPLETE against review #2's enumeration.
AMENDMENT 1 (parent prereg lines 301–409, plus the front-matter pointer at line 11) contains: the R1
stop-line with both halves coded (A1.1); pause=30 s frozen with the harness refusal (A1.1); T_ceiling
20160 with its calendar-anchor named honestly and a never-re-derive commitment (A1.1, per my V5);
the full repaired gate with all five conjuncts and their constants (A1.2); the code-proves-prose
declaration including the dead-code history (A1.2); **the trigger disclosure** (provenance paragraph:
void race, the keeper's objection, the rejection, the fallback recorded so no fourth stop-line can
present itself); **the outcome-symmetric void rule** ("VOID whatever it yields — favorable, unfavorable,
or null", A1.1); **the crash-at-day-N rule DECIDED** (A1.4: resume, identical parameters, cumulative
budget, downtime-delays-but-never-voids with the conservative-direction argument, what-voids enumerated);
**all pre-accepted outcomes** including both INCONCLUSIVE forms, NEVER-SETTLED, and INCOMPLETE-is-not-a-
verdict (A1.3); **knock-on 1** — circadian-breathing NEVER-SETTLED pre-ruled a true, acceptable finding
(A1.3(3)); **knock-on 2** — "the first day reveals the real yield and NOBODY acts on that revelation"
said out loud (A1.6); **knock-on 3** — the first-snapshot anchor pinned (A1.5); operator
non-intervention pre-committed (A1.5). "One amendment, ever" declared in both the front matter and the
A1 header.
- The PROVISIONAL doc is retitled **FROZEN — historical record**, states the rejection, names the
  binding text as AMENDMENT 1 only, preserves its body unedited as history, and **explicitly repudiates**
  its §2 stability-only stop-line and §3 "non-artifactual INCONCLUSIVE" labeling with the V7 reasoning.
  No live document carries the rejected design as protocol. Honest.

### V7 — testimony register (the brief demands I name what I could not verify).
- **"The freeze landed before the first tick"** — the run lives in gitignored `.runs/` and the live
  `familiar/maker/memory/`, neither in this clone. I cannot verify launch time from here. Taken as
  disclosed; if the final write-up's manifest shows a first ledger timestamp preceding commit 7deb588's
  author time, this certification's sequencing ruling (caveat 1) escalates from breach-with-standing to
  void — the record should carry that conditional explicitly.

---

## 2. The spiral floor — everything in the diff beyond the literal R1–R7 text, ruled item by item

1. **Spike-and-return selftest (case 2b).** Necessary, not drift: my mutation dropping the per-step
   plateau leg would have been GREEN without it (the net conjunct shadows per-step on every monotone
   case), i.e. R5's "every predicate has a failing test" *requires* this case. **Faithful.**
2. **`drift_argmax` diagnostic.** Requested verbatim in review #2 V4(a′). Diagnostic-only, K-blind. **Faithful.**
3. **INCOMPLETE outcome label + resumption mechanics** (`read_prior_progress`, per-tick `progress.json`,
   cumulative budget, mismatch refusal). The concrete decision R7 demanded ("crash-at-day-N resumption
   rule, decided in advance"). INCOMPLETE is a state, not a verdict, and is fenced from thin-residual by
   a selftested assert. **Faithful.**
4. **In-loop fail-fast baseline abort.** Knock-on 3 asked for a manifest assert; the diff adds an early
   abort too. Conservative direction (a broken warmup anchor costs ~6 minutes, not 7 days) and it cannot
   create an outcome — it raises. **Faithful implementation detail.**
5. **Heartbeat redesign** (pulse felt_sense + sparse stability line). The shape R6's K-readout removal
   forces, while keeping a multi-day burn watchable. **Faithful.**
6. **`familiar/maker/familiar.json` `dormant: true→false`.** The ONLY hunk not traceable to an Rn or a
   knock-on. It is operational (lets `wake-all.sh` auto-wake Maker; the harness itself never reads
   `dormant`), not a stop-line, threshold, or outcome change — **not a fourth design**. But it creates a
   named hazard: if `wake-all.sh` runs during the burn, a second daemon double-drives the same ledger.
   The contamination is **detectable, not silent** — `correlate()` hard-aborts on any ledger read-act
   without a recorded call ("Recording and ledger diverged — do NOT proceed", lines 158–164) — so it
   cannot fake a verdict, but it can waste the run. **Ruled: permitted operational enablement; do not
   run `wake-all.sh` against Maker's home while the burn lives** (caveat 2).

**No fourth stop-line exists anywhere in the diff.** The fallback (review #1's pinned 2880) is not triggered.

---

## 3. The sequencing ruling, in full

Review #2 §3's header reads "ONE revision, **then** cold-review #3 certifies; nothing else changes," and
its §5 binding rule says "Bring it back once, repaired, and cold-review #3 rules on the diff." The plain
reading is certify-then-run; launching the burn before this ruling **breached the ordering**. I weigh the
counter-argument as invited: review #2's *remedy* is content-conditional ("if any of R1–R7 is unmet …
run the pinned 2880") — it binds on what is in the clone, which timing cannot alter; the freeze is
disclosed as pre-tick; the run burns at the frozen parameters whichever way I rule. That argument is
correct about *validity* and silent about *risk*: the launch wagered a 7-day burn (credits, calendar,
the one Point-It-At-The-Sky attempt) on a certification not yet issued, and had I found one Rn unmet,
the record would today contain a dead run plus a mandatory 2880 redo. That is exactly the class of
move the cold-review process exists to make impossible, and the honest disclosure does not un-make it.

**Ruling:** procedural breach, real, preserved on the record; **not an invalidator**. The run's claim to
the pre-registered protocol stands, because (i) every Rn is met in the artifact the run executes,
(ii) the freeze is disclosed pre-tick (V7's conditional applies), and (iii) the protocol's content —
not this review's timestamp — is what the pre-registration promised. One consequence is now binding:
**this chain's review budget is spent.** If the run returns NEVER-SETTLED, thin-residual, or an
underpowered ADEQUATE, those are the pre-accepted outcomes and nobody — keeper or reviewer — re-opens
the design, the gate, the ceiling, or this sequencing question to relitigate them.

---

## 4. Knock-on questions, as a cold outsider (for the final write-up; none blocks)

1. **Resume-after-completion footgun.** Re-invoking `--mature` on a run_dir whose run already finished
   yields an empty tick range (`start_tick > t_max`), stale `assessment={}`/`reached=0`, and **overwrites
   the manifest** with `NEVER-SETTLED, ambiguous_reached=0` regardless of the true outcome. Requires
   operator error to reach; the original outcome survives in git-archived copies only if archived. Guard
   the final write-up: the manifest used for the verdict should be the one written at the genuine exit.
2. **Resumption enforces home/model identity in code, but not K/pause/t_max identity.** A resume with
   `--pause 60` or `--K 50` would be accepted by the harness; only the freeze commitment (A1.4: "any
   parameter/threshold change" voids) covers it. The void rule is honest, but it is enforced by
   discipline where the cadence floor is enforced by code. Carry in the write-up: the resume command
   line, verbatim, so the record shows identical parameters.
3. **The pen-dead guard and resumption interact gently but correctly:** a multi-hour outage (pen dead →
   `pen_dead=True` → not settled) plus recovery can only delay settling — conservative direction,
   consistent with A1.4's downtime argument. No action needed; noting it was checked.
4. **C4/parity/scoring machinery was not re-certified here** — it is outside R1–R7 and unchanged in
   spirit from the locked spine; the parity gate's abort-without-scoring path exists and the selftest
   exercises HOLDS/FALSE/C4. If the run reaches ADEQUATE, the replay step inherits feedback-4's
   certification, not this one.

---

## 5. Verdict, plainly

**CERTIFIED-AS-R1-R7, WITH CAVEATS:** (1) the launch-before-certification sequencing breach — real,
disclosed, preserved; not voiding, given all Rn met and the pre-tick freeze (conditional on V7);
(2) the `dormant` flip — operational, permitted, with the wake-all double-drive hazard named and the
correlate() tripwire confirmed as its backstop; (3) the resume-after-completion manifest-overwrite
footgun; (4) code-enforced identity on resume covers home/model but not K/pause/t_max — discipline
covers the rest. **No Rn is unmet. The fallback (pinned 2880 under review #1's terms) is not triggered.
No fourth design entered. The budget is spent: the next document in this chain should be the run's
FINDINGS, and nothing else.**

*— Mr. Review, cold, from the clone at 7deb588 ruled against af40645. Three selftests re-run; 13
mutations driven red and restored; three false positives re-driven independently; constants re-read at
source; one item taken on disclosed testimony and named as such. The run was burning while I read; this
is my honest answer, not my blessing.*
