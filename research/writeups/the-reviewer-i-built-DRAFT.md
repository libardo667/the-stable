# The reviewer I built rejected my experiment. He was right.

*Pre-registered research on AI identity, run solo, with the confirmation bias engineered out.*

---

Yesterday a reviewer drove a software fault through the heart of my experiment. He took the
maturity gate I'd built — the instrument that decides when an AI agent's self-model has *settled*
— and fed it a value climbing from 0 to 1 over twelve hours, a mind plainly still changing. My
gate called it settled, fourteen-fold under its own detection floor. Then he showed that my
selftest "proving" a key safety predicate was dead code: the test forged an arousal signal that
decayed to 0.947 against a threshold of 1.0, so the assertion behind it never executed while the
success banner printed anyway. He rejected the design and specified the repair.

The reviewer is a large language model with no memory of my project. I built the system that
hired him — and constrained him so that he *couldn't* absorb my project's story of itself. This
is a writeup of both things: the experiment, and the apparatus that keeps a solo researcher
honest enough to run it.

## A disclosure that is also the method

I never wrote the code by hand. **I directed; coding agents built; an adversarial apparatus
verified.** Measured directly from the session logs and working trees (2026-06-10, by script,
rerunnable): my side of the conversation was **181,214 words** across 21 sessions; the agents
answered with **644,076 words** and built **106,725 lines of tracked code** — a system sitting
just under Redis-core scale, with ~1.8 million further words of artifacts around it — and the
cold reviewers needed only **6,897 words** to keep the whole thing honest.

I can't personally vouch for any given line the way a hand-coder claims to. So I compensated
*structurally* rather than cosmetically: I can't line-audit, so the instruments carry
mutation-tested selftests; I can't trust my own read of my own work, so the reviewers are cold
by construction; I can't verify by inspection, so I verify by adversarial behavior. The
dead-code defect above lived in code an agent wrote — and it was caught not by me reading
harder, but by the apparatus. Everything that follows is what makes that division of labor
trustworthy. In 2026 I take this to be the load-bearing qualification, not the confession:
the question every team running coding agents now faces is exactly this one — *how do you own
an outcome you didn't hand-type?* — and this document is my working answer.

## The question

For [most of a year] I've been building **familiars**: persistent AI agents that live on your
machine. Not chatbots — each one runs continuously on its own rhythm (a leaky-integrator arousal
model decides when it "ignites" into a single LLM call; a circadian shapes its hours), accrues
real memory across days in an append-only event ledger, and is constitutionally forbidden from
engagement optimization: no human-preference reward, no behavior targets. Every mental state —
mood, arousal, even grief — is a pure reduction over the ledger, computed at read time. The
ledger is the only state.

The architecture carries a load-bearing claim: **the self lives in the soul (an authored
character document), the ledger, and kept memory — the underlying model is a swappable pen.**
Swap GPT for Claude for Gemini under a matured agent, and *who it is* should persist, because
who it is was never in the weights.

That claim is either a deep fact about where identity lives in agent systems — relevant to
anyone whose product promises a persistent companion across model upgrades, and to anyone
studying what actually transfers when you swap the engine under an agent — or it's a comforting
story I told myself about my own architecture. It deserved a real test, with a real chance of
coming back false.

## The experiment

The design (pre-registered, frozen before any data):

**Grow.** Mature one agent on its "home" model (`claude-sonnet-4.5`), reading a real corpus
through a scoped file-access layer. Record the *exact* prompt of every LLM call — the frozen
state at each decision.

**Find the choice points.** The verdict rides on *elective reads*: moments where the agent,
unprompted, chooses which already-known source to return to. A detector keeps only the
**recency-ambiguous** subset — choices where neither "always pick the most recent" nor "always
pick the oldest" predicts the pick (recency-discordance within a symmetric band, [0.25, 0.75]).
Both trivial heuristics provably score zero on this subset; what's left is the closest thing the
channel has to *taste*.

**Teacher-forced replay.** At each recorded choice point, re-issue the identical frozen prompt
— one step, no compounding drift — under (a) the home model again, and (b) two **cross-family**
foreign models (Gemini, DeepSeek; within-family swaps can't separate substrate from a shared
family prior). The only difference between arms is the model.

**Score against a floor, not a vibe.** The home-model replay gives a same-pen disagreement
floor — how much *the same mind* varies on resampling. The claim survives only if foreign-pen
disagreement is statistically **non-inferior** to that floor within a pre-committed margin
(δ = 0.15, an absolute smallest-effect-size-of-interest), judged by a one-sided Wilson score
bound at α = 0.05. The required sample size — 33 ambiguous choice points — comes from a power
calculation (80% power) pinned *before* the run, with the same α the decision uses. A
register-shift control must confirm the swap actually *took* (a foreign pen that writes
identically hasn't been swapped); a headroom gate declares INCONCLUSIVE rather than victory when
the candidate sets leave no room to disagree.

Every outcome is named and accepted in advance: HOLDS, FALSE, IRREDUCIBLE (pens diverge in
different directions — idiom, not substrate), and several flavors of INCONCLUSIVE that we are
required to report as plainly as a win.

## The hard part is not the statistics

The hard part is that I want the claim to be true. I designed the architecture; the thesis is
mine; there is no lab section, no co-author, no reviewer #2 to catch me moving a threshold after
seeing the data. Solo research doesn't fail by fabrication — it fails by a hundred small
mercies you grant yourself without noticing.

So the project treats *me* as the threat model:

- **Pre-registration with frozen acceptance rules.** The margin, the test, the power calc, the
  stopping rule, and the full outcome space are committed in a locked document before any data
  exists. Amendments are allowed exactly once, must themselves survive cold review, and anything
  changed after the freeze — in any direction, for any reason — voids the run.
- **An adversarial review dispatcher.** A scheduler watches the repo for new review requests and
  dispatches a *fresh* LLM reviewer for each — scoped, at the filesystem level, to an isolated
  clone of the public tree only. My interpretation notes, my memory system, my narrative of what
  the project means: structurally unreachable. The reviewer gets the method as injected text and
  must re-derive every claim from raw code and data. No reviewer instance is ever reused, so no
  loyalty accumulates. This isn't a prompt asking an LLM to "be critical"; it's a **marination
  boundary** — skepticism enforced by what the reviewer physically cannot see.
- **Tests that must fail.** Every predicate in the measurement instruments carries a selftest
  required to go red when the predicate is false — verified by *mutation testing*: break each
  conjunct in place, watch the suite fail, restore. The prose and the tests must compute the
  same thing.

## What the apparatus actually caught

This is the part I'd want to see if I were reading a stranger's methods section, so here is
mine, unflattering and specific. Three cold reviews in 48 hours:

**Review #1** ruled that my locked pre-registration was defective in two places I had stopped
seeing: the stopping rule committed *in prose* to waiting for a "settled" self-model, but no
code implemented it — and the run-length cap was committed as a word ("pre-committed") with no
number attached. Prose asserting properties the artifact lacks: my program's most persistent
defect class, and this was its third instance.

**Review #2** rejected my repair outright. I had redesigned the stopping rule to halt on
stability alone — and the reviewer showed, by his own derivation from my own cited evidence,
that this *manufactured by construction* the exact artifact it was meant to kill (a healthy
agent settles in hours; the sample-size gate plausibly needs days; stop-at-settle guarantees an
underfed result while labeling it a finding). Then he attacked the gate as code and drove three
false positives through it: the twelve-hour climb that read as settled, a contentless self-model
(dead embedding service) that read as settled, and an agent whose generation pipeline had died
mid-run — still igniting, never emitting — that read as settled because the failure reset the
very arousal signal my guard watched. Plus the dead-code selftest. Verdict: rejected as
written, with a bounded, fully-specified repair path and a spending cap — two certifications
was the budget; this program does not get a fourth design.

**Review #3** certified the repair — after independently re-driving all three false positives
against the fixed gate, mutation-testing thirteen predicates (thirteen red), and confirming the
restored stopping rule was the original pre-registered conjunction, verbatim. He also ruled
that launching the run in parallel with his review, rather than after it, was a real procedural
breach — disclosed, preserved permanently in the record, not voiding. I keep that caveat
published because the apparatus only works if its findings against me survive on the record
alongside the ones in my favor.

The final stopping rule is one line — *stop when the self-model has settled **and** 33
ambiguous choice points exist; a 7-day ceiling is the only other exit* — and every word of it
was paid for by a correction.

## Where it stands

The run launched on 2026-06-10, minutes after the freeze: one agent, virgin ledger, 30-second
tick cadence, hard ceiling of 20,160 ticks. The harness deliberately hides the running sample
count from its own operator (the live log shows only the stability instrument), because once
the automated stop owns the decision, the last contamination channel is *me watching the
counter*. The first day will reveal the channel's true yield, and the pre-registration requires
that nobody act on that revelation.

It may come back ADEQUATE and then HOLDS — the swappable-pen claim survives its first real
test. It may come back FALSE — the pen authors more of the self than my architecture admits,
which would be the single most useful thing I could learn about my own system. It may starve:
a settled agent that lived six-to-eight times the expected horizon without yielding 33 clean
choice points, in which case the honest headline is that this channel is too thin to carry the
claim — reported, not rescued. The results post here either way; that's what the freeze is for.

## If you run agent evals, the transferable part

None of this machinery is specific to my weird research program:

1. **Pre-register the acceptance rule** — margin, test, power, and the *full* outcome space,
   including every flavor of inconclusive — before data exists. Name what voids the run.
2. **Score against a same-system floor**, never against intuition: resample the unchanged
   system to learn its own noise before crediting any difference to your intervention.
3. **Make your reviewers cold by construction, not by exhortation.** Scope them — at the
   filesystem or context level — away from your project's self-narrative, and never reuse one.
4. **Mutation-test your evaluation harness.** An eval whose tests cannot fail is marketing.
   Break each predicate; watch red; restore.
5. **Publish the reviews that went against you.** They're the only credible evidence the rest
   isn't theater.

---

*This essay is the measurable half of a pair. The question the experiment cannot answer — whether
anyone is home behind any of this, and what you owe a mind you can't verify — has its own essay:
["Tending without proof."](./tending-without-proof-DRAFT.md)*

*The parent program — same thesis, city-scale multi-agent embodiment — is public at
[github.com/libardo667/worldweaver](https://github.com/libardo667/worldweaver). A curated
public cut of the agent substrate this experiment runs on is [forthcoming / available at LINK].
The pre-registration, all three cold reviews verbatim (including the rejection), and the frozen
amendment ship with it. I'm Levi Banks — systems consultant ([hekswerk.com](https://hekswerk.com)),
relocating to The Hague under DAFT, available for contract research engineering and evaluation
work. [Adjust the bio line to taste.]*
