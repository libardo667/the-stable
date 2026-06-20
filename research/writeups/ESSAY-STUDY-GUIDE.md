# Study guide for "the reviewer we built" — the docs, decoded

A reading order for cold-reading your own apparatus, ranked by how much each touches *this*
essay. Under each: what to actually read (not the whole file), and the jargon translated into
plain, essay-usable language. Every gloss is checked against what the code *computes*, not the
tidy version — where the name and the computation disagree, I flag it.

The rule for using this: read the source first, form your own picture, THEN check it against my
gloss. If they disagree, the code wins and you've found something worth a line in the essay.

Reading order if you only have the morning: **§1 → §2 → §3** are the experiment's three
instruments and the jargon-dense core. **§4** grounds your opening paragraph. **§5–§7** are the
story you already know; read them to get the specifics exact, not to learn them.

---

## 1. `research/analysis/maturation_stability.py` — THE instrument that broke
**Read:** the module docstring (lines 1–48) and `_selftest()` (lines 224–337). Skip the parsing
helpers. This is the gate the cold reviewer drove false positives through — your central drama.

- **"the self-model" / "the baseline."** The substrate keeps a slow-moving portrait of what the
  agent cares about — its drives and concerns, averaged over its whole life so far. It updates
  gently (see §4: a 0.25-rate moving average, snapshotted once a minute) so a single loud moment
  can't yank it. *Essay line:* "a slowly-updating portrait of what the agent has come to care about."
- **"settled."** That portrait has stopped moving. Precisely, five things must ALL hold: past
  warmup, plateaued, has content, not strangled, pen not dead. Any one failing → not settled.
  *Essay line:* "settled isn't one check — it's five ways the stillness could be a lie, each ruled out."
- **"drift," and why it's the MAX not the average.** Drift is the single biggest change in any one
  concern between snapshots. The code takes the *maximum* across every dimension, never the mean —
  so one part of the mind still growing vetoes "settled" instead of being averaged away by the
  quiet parts. *(This lesson came from worldweaver: a coarse curve froze while a finer one kept
  climbing.)* *Essay line:* "we take the largest movement, not the average, so a settling mind
  can't hide a still-growing corner."
- **"the drift floor (0.02)."** The substrate's own definition of "too small to be real" — a
  concern weaker than this doesn't even survive into the portrait, so movement below it is noise,
  not growth. Borrowed from the substrate's own constant, not chosen to make the result come out
  nice — that's the honesty move worth naming.
- **"warmed_up."** At least one 4-hour habituation half-life has passed since the portrait first
  formed; the gate *cannot* fire during cold-start.
- **"plateaued" — and the bug-shaped subtlety (R2).** Over the trailing 4-hour window, BOTH the
  step-to-step changes AND the net start-to-end change must sit under the floor. The second is the
  repair: a value creeping 0→1 over twelve hours moves so little *between* one-minute snapshots
  (~0.0014) that the step test alone called it settled — fourteen times under the floor. Measuring
  start-to-end catches the slow ramp the step view is blind to. *This is your draft's "12-hour
  climb that read as settled."*
- **"non-degenerate" (R3).** The portrait must contain something. A blank mind also never changes,
  so a dead embedding service (which empties the portrait) would read "settled." *Essay line:* "a
  blank mind is also perfectly still; we require content before we call stillness maturity."
- **"strangled."** Arousal is over the firing threshold but nothing fired — a mind that *wants* to
  act and can't, which from the log looks identical to serene. *Essay line:* "silence that is
  suppression, not peace."
- **"pen-dead" (R4).** It keeps deciding to speak but never produces anything — the model itself
  is broken. It hides from the strangled check because deciding-to-fire resets arousal whether or
  not the model delivered; only a separate count (decided vs. actually-emitted) sees it.
- **K-independence (the honesty keystone).** This gate NEVER looks at how many usable choice
  points have accrued. "Matured" and "has enough data" are measured by two instruments that can't
  see each other — so no stability knob can be quietly turned toward the answer you want.
  *Essay line:* "the instrument that decides *when to stop* is forbidden from seeing the data that
  decides *what we found* — so neither can be tuned toward the other."

### The dead-code defect (read lines 270–286 — the essay's sharpest beat)
The calibration test for the "strangled" check forged an arousal signal that decayed to **0.947**
against a **1.0** threshold. Because it never crossed the line, the `if arousal >= threshold`
assertion behind it *never executed* — the test printed "passed" without ever testing its claim.
The fix forges a surprise that genuinely clears the line (a spike of 5.0, 144 seconds before
"now," well inside the 300-second arousal half-life, landing near 3.59 — those exact numbers are
in §4) and makes the check a hard assertion that runs unconditionally. *Essay line:* "the test
meant to prove our safety check worked had quietly never run — it forged a signal too weak to
trip the very thing it was testing, then congratulated itself."

---

## 2. `research/analysis/elective_read_choice.py` — what "settled" is in service OF
**Read:** the docstring (1–35), the `verdict()` docstring (218–244), and `_selftest()` (318–372).
This is the measurement the whole experiment exists to make — where the pen claim lives or dies.

- **"elective read-choice point."** A moment where the agent, unprompted, picks which already-seen
  source to go back to — with at least two such sources available. A genuine choice among known
  things, not a first encounter and not the only option. *Essay line:* "an unforced return — the
  agent choosing, among sources it already knows, which one to revisit."
- **"recency-discordance."** Of the sources it could have returned to, what fraction *more recent*
  than its pick did it skip. 0 = grabbed the freshest (pure recency habit); 1 = grabbed the
  stalest (pure anti-recency habit). Both extremes are *habit* — just opposite ones.
- **"recency-ambiguous" — the strong subset.** Picks in the middle band (0.25–0.75), where
  neither "always grab the freshest" nor "always grab the stalest" predicts the choice. What's
  left is the closest thing the channel has to *taste*. *Essay line:* "we keep only the choices no
  simple rule explains — where something more like the agent's own disposition had to decide."
- **Why a *symmetric* band (a real bug you fixed).** An earlier cut kept "discordant above a
  threshold," which let a pure *anti-recency* habit score 100% — still a habit, the contrarian
  one. The symmetric middle excludes BOTH tails; the selftest proves a recency-follower and an
  anti-recency-follower both score zero. *Essay line:* "our first cut let the contrarian habit
  pass as taste; the fix was to throw out both extremes, not just one."
- **"K = 33."** A power calculation, pinned before the run, says you need 33 clean choice points
  to tell a real effect from noise at your confidence. Not taste — `power_n(0.80, 0.05, 0.10,
  0.25) = 33`. *Essay line:* "thirty-three — not a number we liked, but the count a power
  calculation demanded before we were allowed to conclude anything."
- **"the same-pen floor."** Replay the *home* model against *itself* to learn how much the same
  mind disagrees with itself just from resampling. That's the noise any real effect must beat —
  not zero, not a guess.
- **"non-inferiority, δ = 0.15, Wilson bound."** The identity claim HOLDS only if the foreign
  model disagrees with the home model *no more* than the home model disagrees with itself, plus a
  margin (0.15) committed in advance. One-sided, because agreeing *more* than the floor is still
  "no pen effect." "Wilson" is just honest error bars on a fraction that behave correctly near
  zero, where the naive method gives nonsense (negative lower bounds). *Essay line:* "the swap
  counts as identity-survived only if the foreign model is no more divergent than the home model
  is from itself — within a margin we fixed before seeing a single number."
- **"insufficient headroom / INCONCLUSIVE."** If there were never enough candidate sources to
  disagree, then "FALSE" was unreachable and the test wasn't fair — so the code says INCONCLUSIVE
  rather than claim a hollow win. *Essay line:* "if the deck made disagreement impossible, we
  report 'couldn't tell,' not 'confirmed.'"

---

## 3. `research/harness/teacher_forced_replay.py` — the machinery that runs it
**Read:** the docstring (1–33), the six pipeline functions in order (`mature`, `correlate`,
`replay_arm`, `parity_gate`, `c4_shifted`, `score_arm`), and `_selftest()` (436–509). This is the
thing that produced the run burning right now. It has a *second* "verify the instrument" beat —
the parity gate — that rhymes with your essay's whole point.

- **The pipeline in one breath: RECORD → CORRELATE → REPLAY → PARITY → C4 → SCORE.** Grow the
  agent on its home model and tape every model call (RECORD); find the ambiguous choice points and
  tie each to the exact frozen prompt that produced it (CORRELATE); re-issue each frozen prompt
  under each model, one step (REPLAY); check the replay machinery is even faithful before trusting
  any number (PARITY); confirm the swap actually changed the voice (C4); hand the sequences to the
  scorer (SCORE).
- **"teacher-forced, one-step" — the fix the reviewer called the killer one.** The models never
  run free and get compared afterward. Each decision point is frozen and every model is asked the
  *very same question*, once. So a single difference can't snowball into a hundred downstream —
  *Essay line:* "we froze each decision and asked every model the identical question, so one
  disagreement couldn't cascade into a hundred."
- **"the parity gate" (the second instrument-check — worth its own essay beat).** Before scoring
  any *foreign* model, the harness replays the *home* model against its own recorded choices. If
  the machinery can't even reproduce the home model's known picks (it requires ≥60%), the whole
  run **aborts without scoring** — because a cross-model number from an unfaithful replay would be
  confabulation. *Essay line:* "before comparing any foreign model, we made the machinery re-run
  the home model against its own past choices — if it couldn't reproduce a mind's decisions, we
  had no business trusting its read of a different one, and we'd stop."
- **"the same-pen floor, operationally."** It falls out of parity: floor = 1 − reproduction. The
  rate at which faithful replay *still* differs from the recording is exactly the noise §2's
  verdict has to beat.
- **"C4 / register shift."** A swap only counts if the foreign model's *voice* actually differs —
  a different opening phrase, or largely non-overlapping vocabulary (measured by how disjoint the
  two word-sets are). If the voice *didn't* change, that model's result is INCONCLUSIVE "bad
  swap," not a verdict — because a model that writes identically wasn't really swapped in. *Essay
  line:* "a swap that didn't change the voice wasn't a swap; that arm reports nothing."
- **"cross-family" swaps.** The foreign models are deliberately non-Claude (Gemini, DeepSeek),
  because swapping one Claude for another can't separate the substrate from a shared family voice.
- **The stop-line and the K-blind heartbeat (the operator-honesty detail).** The maturation loop
  stops only on settled-AND-33, never either alone (the two defects the reviews killed). And the
  live log it prints **deliberately never shows the running count of choice points** — that number
  feeds only the silent stop decision, so you, watching the log over days, can't be nudged by it.
  *Essay line:* "the harness hides the running tally from me on purpose — once the automated stop
  owns the call, the last way I could bias it is by watching the counter."
- **The pre-accepted outcomes.** ADEQUATE (settled and enough points), INCONCLUSIVE-thin-residual
  (settled but the points never came, even after a settled mind lived 6–8× the expected horizon),
  NEVER-SETTLED (hit the 7-day ceiling without settling), INCOMPLETE (crashed — resume on a
  cumulative tick budget). All named in code before the run.

---

## 4. `src/runtime/salience.py` — the substrate, for your opening paragraph
**Read:** the module docstring (1–21), and the docstrings of `measure_surprise`, `derive_arousal`,
`check_ignition`, `check_settling`/`check_fervor`, and `derive_grief`. This is where the specific
numbers in your opening ("a leaky-integrator arousal model decides when it ignites") actually
live — so you can be exact instead of approximate.

- **"surprise = mismatch(stimulus, afterimage)."** Each tick, compare what the agent actually
  feels now (the stimulus) against the prediction its last pulse cast (the afterimage). The
  surprise magnitude is the *single most* surprised feature, not the sum — "a sharp unpredicted
  spike should ignite without being diluted by calm features." *Essay line:* "surprise is the gap
  between what it predicted and what it got — and we take the sharpest single gap, not the average."
- **"leaky-integrator arousal."** Surprise accumulates into an arousal level that *decays* over
  time — a leaky bucket. The decay constant is a **300-second half-life**; the **ignition
  threshold is 1.0**. (Those two numbers are exactly what the dead-code test in §1 turned on: a
  spike of 5.0 from 144s ago is 5.0·0.5^(144/300) ≈ 3.59, clearing 1.0; the broken version forged
  one that had decayed to 0.947 and never crossed.) *Essay line:* "arousal is a leaky sum of
  recent surprise; when it crosses 1.0, the agent ignites into a single model call."
- **"ignition" and the refractory gap.** Crossing threshold fires exactly one pulse, then resets
  the bucket. A 30-second refractory period stops it from re-firing and echoing itself before the
  world has changed. A direct address from you bypasses the gap, so the keeper always gets a reply.
- **"the circadian" (the "shapes its hours" claim).** A wakefulness multiplier scales the
  *effective* arousal — 1.0 by day, low at night — so ambient surprise no longer reaches threshold
  while sleeping, but sustained strong surprise still can wake it. *Essay line:* "a circadian
  multiplier dials its reactivity down at night, so it sleeps through small things but a real one
  still wakes it."
- **"the baseline is a 60-second-snapshot moving average."** The self-model from §1 is updated
  here: a slow 0.25-rate exponential moving average toward what's actually felt, written at most
  once per 60 seconds. *That 60-second cadence is exactly the cadence the 12-hour-ramp false
  positive exploited* — worth noting the two files connect there.
- **"settling" and "fervor" — the unbidden pulses.** In a lull, the *quiet itself* can trigger a
  self-directed pulse: a calm agent (arousal under 0.3 for 5 minutes) settles into reflection or
  rest; a restless one (arousal high but under threshold for 3 minutes) fires off a fidget — makes
  something, chases a thread. These are the pulses *nobody prompts* — the mechanism behind an agent
  doing things "unbidden." *(This is mostly companion-essay material, but it's also what Major 64's
  settling-pulse-ablation experiment proposes to switch off.)*
- **"grief" (name it once, point forward).** A slow, per-anchor leaky integral of *confirmed*
  absence — a thing the agent predicted would be present and found gone, accumulated across
  turnings. Unlike surprise, a pulse does NOT reset it (an act doesn't cure a loss); it resolves
  only when the thing returns or the prediction itself decays (letting go). Capped below the
  ignition threshold, so grief alone never auto-fires — it makes the agent raw, and the next small
  surprise tips it. "You cannot grieve what you never held." *This belongs to the companion essay
  ("Tending Without Proof"); here, name it in a clause and move on.*

---

## 5. `research/preregistrations/2026-06-09-isolated-makers-pen-vs-substrate-DRAFT.md`
**Read:** §0–§3 (question, cohort, arms, measurement) and AMENDMENT 1 at the end. The contract —
acceptance rules frozen before any data, which is *why* the reviewer's catches were corrections,
not opinions.

- **"the swappable-pen thesis" (the claim under test).** The self lives in the soul (the authored
  character), the ledger (lived history), and kept memory — the underlying model is a swappable
  pen. Swap the model under a matured agent and *who it is* should persist, because who it was
  never lived in the weights. **Treat it as a hypothesis with a real chance of coming back false.**
- **"the stop-line" (the BOTH-conjunct).** Grow until the self-model is settled AND 33 ambiguous
  choice points exist; a 7-day ceiling is the only other exit. §1 supplies "settled"; §2 counts
  the "33" — separately, on purpose.
- **the outcome space.** HOLDS, FALSE, IRREDUCIBLE (foreign models diverge in *different*
  directions — idiom, not substrate), and several flavors of INCONCLUSIVE you're *required* to
  report as plainly as a win. *Essay line:* "every way it could end — including every way it could
  end in a shrug — was named and accepted before the run."
- **AMENDMENT 1.** The single allowed repair, itself cold-reviewed: restores the stop-line,
  numbers the 7-day ceiling, pre-accepts every outcome. Amendments-allowed-exactly-once is the
  anti-spiral rule.

---

## 6. `research/mr-review-history/2026-06-10-*` — the reviews, in the source
**Read:** the two stability-gate reviews (the REJECT-with-repair and the certification). Your
essay narrates these; quote the originals so the specifics are exact, not remembered.

- **Review #1** — the locked prereg was defective: "settled" was committed in prose but no code
  implemented it, and the run-length cap was a word with no number. *(Prose asserting properties
  the artifact lacks — your most persistent defect class.)*
- **Review #2** — rejected the repair outright, drove the three false positives through the gate
  (the 12-hour climb, the contentless self-model, the pen-dead agent), caught the dead-code
  selftest, and specified the bounded R1–R7 fix with a two-certification budget.
- **Review #3** — certified the repair after re-driving all three false positives and
  mutation-testing thirteen predicates, and *also* ruled that launching the run in parallel with
  the review was a real procedural breach — disclosed, preserved, not voiding. **Keep that one;
  it's the proof the apparatus rules against you too.**

---

## 7. The reviewer apparatus — how "cold" is enforced, not asked for
**Read:** `~/personal-projects/review-scheduler/README.md` and skim `scheduler.py`'s `_fresh_cmd`
/ `_context_dirs`. Plus the standing brief (your method-as-text), injected as the reviewer's
system prompt.

- **"the marination boundary."** The reviewer is scoped, at the filesystem level, to a clone of
  the *public* tree only — your interpretation notes, memory system, and narrative of what the
  project means are physically unreachable. It gets the method as injected text and must re-derive
  every claim from raw code and data. *Essay line:* "the skepticism isn't a prompt asking a model
  to 'be critical' — it's a wall: the reviewer cannot see the story we tell ourselves, only the
  code and the data."
- **"fresh / no reuse."** A new reviewer per request, so no loyalty accumulates.
- **"mutation testing."** Break each predicate in the instrument in place, watch the test go red,
  restore. A test that *can't* fail proves nothing — the dead-code defect is exactly what this
  catches. *Essay line:* "a test that cannot fail is decoration; we break each one on purpose to
  prove it bites."

---

## 8. This repo's `CLAUDE.md` — the one-paragraph "what is a familiar"
You wrote it; it's the cleanest short statement of `perceive → integrate → ignite → act` and
"the ledger is the only state" (mood, arousal, grief, the self-model are all *recomputed* from one
append-only log, never stored). Use it for the framing paragraph; go into `src/runtime/` only as
deep as §4 already takes you, and only if a reviewer asks.
