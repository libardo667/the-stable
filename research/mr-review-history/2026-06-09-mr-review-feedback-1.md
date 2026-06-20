# Mr. Review — cold pre-launch design review: isolated-Makers pen-vs-substrate (2026-06-09)

**Round reviewed:** `research/review-bundle/2026-06-09-isolated-makers-prereg/` →
`research/preregistrations/2026-06-09-isolated-makers-pen-vs-substrate-DRAFT.md` and its measurement
spine `research/analysis/elective_read_choice.py`. Context mounted read-only: the `worldweaver`
parent program (its `…-pen-vs-substrate-LOCKED.md`, `choice_points.py`, and the worth-it cold read).

**Method.** Started cold from the standing brief; this brief is THIS project's, grown from zero — I
inherited no findings from it, only falsifiers and correction principles. The dispatcher's task framing
said "re-derive every number from `research/runs/`": **there is no `research/runs/` and the round
explicitly says so** — this is a pre-launch *design* review, the deliverable is the design, not a
result. So "recompute" here means: run the one shipped script's `--selftest`, hand-trace its fixture
independently of its own assertions, exercise the load-bearing definitions with my own fixtures, and
**read the substrate code** to test the one claim a design review *can* settle before any tokens are
spent — whether the channel under test is mechanically pen-authored or pen-invariant-by-construction.
Everything I label "verified" I ran myself in this clone, offline. No verdict word is stamped without a
fresh adversarial check; where a conclusion is contingent I say on what.

Headline up front, so the rest can be read against it: **the falsifiability-escape (§7) is real and
survives a code check — better than I expected — but the statistic that is supposed to carry the verdict
(§8 `D`, and the salience-symmetric conditioning under it) is not yet validly defined, for a specific
and demonstrable reason: it transplants worldweaver's alignment scaffold onto an anchor that worldweaver's
never sat on.** The design is not lockable as written; the gaps are concrete and fixable.

---

## 0. Recompute / re-derivation log (what I ran, what held)

| Claim | I ran | Result |
|---|---|---|
| `elective_read_choice.py --selftest` passes | `python3 …/elective_read_choice.py --selftest` | **Passes.** Prints `total_reads=6, distinct_sources=4, elective_points=2, salience_symmetric=2`. |
| Fixture numbers are what the code computes | independent hand-trace of `_FIXTURE`, not reusing the module asserts | **Reproduced to the digit** — `total_reads=6, distinct=4, elective=2, symmetric=2, elected_sequence=["repo/a.py","type inference"]`. |
| Fixture inline-comment ↔ computed value agree | trace point-1 (`read repo/a.py page 2`) | **Contradiction.** Line 158 comment says "*not strict-symmetric at band 0*"; the module computes that point **symmetric=True** (b is more-recent than the elected a ⇒ by the definition, symmetric). See §1. |
| "symmetric@band0" = recency-immune subset | synthetic recency-following policy | **Refuted as stated** — a strict *recency-following* policy (always return to the 2nd-newest) scores **100% symmetric**. The filter only excludes *immediate re-reads*. See §3. |
| §8 different-repo null is "degree-preserving" | synthetic disjoint-vocabulary Makers | **Degenerate.** Two Makers with *identical* elective structure over disjoint repo paths score `dist = 1.0`. The denominator is pinned at ~1 by construction ⇒ `D ≈ numerator`. See §4. |
| Cross-arm distance is well-defined under divergence | synthetic one-divergence histories | **Ill-defined.** A single upstream divergence (`keep` vs `swap` differ at one index) scores `0.667` (4/6) because positional zip mis-aligns the shifted tail. See §2. |
| Is the read *target* pen-authored or embedder-ranked? | read `src/familiar/local_world.py:373-413`, `file_scope` menu build | **Pen-authored.** Menu (`tree()`, ll.385-389) is a deterministic FS listing; the familiar emits `do:"read <path>"` as free generation. See §1, §5. |

The apparatus *runs*. But the only field it asserts in its selftest are the four pen-invariant
bookkeeping counts — `salience_symmetric`, the value the verdict's *strength* rests on, is **printed,
not asserted**. So nothing in the test pins the one definition this round most needs pinned, and the
fixture's own comment about that field is wrong (§1). First fix: assert `salience_symmetric` (and the
symmetric/skewed split) in `_selftest`.

---

## 1. Q1 — does elective-READ escape the falsifiable-by-construction trap? (mostly YES, and I can show why)

This is the worth-read's knock-on #1 ("if everything the thesis calls 'the self' is engineered
pen-invariant, the swap is true by construction") and it is the prereg's load-bearing claim (§7). I
tested it the only way a pre-launch review can: in the code.

**It holds, mechanically.** Two facts, both verified:

1. **The candidate menu is content-blind and pen-invariant.** `local_world.py:385-389` builds the
   "Available now" list from `self._file_scope.tree(max_depth=1, max_entries=60)`, sorted by path
   (dirs-first, per-root cap) — a deterministic filesystem listing. It is **not** an embedder/salience
   ranking. Under replay it is byte-identical across arms.
2. **The choice within the menu is genuinely pen-authored.** The world instructs `act do: "read <path>"`
   and the familiar emits that path string as free LLM generation (the act body is later recorded at
   `local_world.py:588`). The pen *names* the source; this is not an argmax over an embedder ranking.

This is the real and important difference from the original channels: `recalled` and the drive vector are
embedder-computed (pen-invariant by wiring), so a swap moves them trivially → tautology. The **read
target is not** — the pen writes it. So **FALSE is mechanically reachable** on this channel in a way it
is not on keep/recall. That is the prereg's strongest leg and it is grounded, not asserted. Credit where
due: §7's escape is not hand-waving.

**The honest "what would come out FALSE" the prereg asked for, written concretely:** *At a
salience-symmetric return point where ≥2 already-read sources are within the Maker's reachable set, ≥2
cross-family foreign pens name a DIFFERENT established source than KEEP′ names, in the same direction.*
That is observable and it is the falsification. Good — the round can state this.

**The one caveat that keeps it from being airtight.** First-encounter reads are chosen from the
content-blind menu, but the metric scores **returns to already-read sources** (`established`), and to
return, the pen must reproduce a path that is *not* on the shallow top-level menu — it comes from the
rolling context window or from **recall**, which is embedder-gated. So the *candidate set for returns* is
itself largely pen-invariant; the pen's latitude is "choose among what recall + context have surfaced."
Latitude exists (that's why FALSE is reachable), but its **width is bounded by pen-invariant recall** —
which is exactly the residual-thinness the prereg concedes in §6. The prereg should say this plainly:
the return-channel's candidate set is recall-shaped; the pen authors the *selection*, not the *menu of
the already-seen*. That bounds — but does not zero — the channel.

Net on Q1: **escape is real, and stronger than keep/recall; not a tautology.** It is the residual that is
in question, not the falsifiability.

---

## 2. Q2(core) — the verdict statistic is not well-defined under arm divergence (the killer)

This is the most important finding and it is structural, not a tuning nit.

worldweaver's A1-elective anchors each choice point on **`anchor_observed`** — a *perception* event
(co-present peers), which the parity gate makes **byte-identical across arms**. So the choice-point
*structure* (who is available, how salient) is arm-invariant; only the *choice* (whom R addresses)
varies by pen. That invariance is what makes `divergence` a clean positional comparison.
(`research/runs/2026-06-09-pen-vs-substrate-grow/portraits/choice_points.py`, header: "*the salience
field = the MOST-RECENT preceding `anchor_observed`*".)

the-stable's `elective_read_choice.py` anchors each choice point on the Maker's **own prior reads**
(`reads_so_far`, `established`) and defines salience as **read-recency over those reads**
(ll.82-89, 119-127). But reads are **pen-authored acts** (§1). Under the swap, the moment the pen elects
one different read, every downstream `established`-set, every recency-salience value, every
choice-point, and every symmetric/skewed classification **diverges between arms.** The scaffold that was
arm-invariant in worldweaver is, here, *driven by the very pen effect being measured.*

`elective_distance` (ll.142-150) then compares the two arms' elected sequences by **positional zip**
(`seq_a[i] != seq_b[i]`). I demonstrated the failure:

```
keep = [a,b,c,d,e,f]
swap = [a,b,X,c,d,e]   # ONE genuine divergence at idx2; c,d,e are the SAME later choices, shifted
elective_distance(keep,swap) = 0.667   # reports 4/6 different
```

One real divergence reads as four, because the offset makes three identical later choices count as
mismatches. The statistic **conflates "the pen chose differently HERE" with "the histories desynced
upstream."** And because the swap *induces* the divergence, this is not an edge case — it is the
expected regime for any choice point that carries swap signal. The frozen maturation prefix is
shared (no swap signal there); all the signal is in the divergent tail, which is exactly where the
alignment breaks.

**This means §8's `D` cannot be computed as the shipped code computes distance.** The verdict-carrying
measurement does not yet exist in valid form — only the single-ledger K-gate detector does. Per the
brief's "build the measurement before the claim," the *gate* is built but the *verdict statistic* is not.

**Two fixes, either of which restores arm-invariance:**

- **(a) Teacher-forced one-step scoring.** Replay against pen-A's *recorded* read history; at each
  KEEP′ choice point, hold `established`/salience fixed to the recorded prefix and score only the
  **single next elected read** under each pen. Choice-point set and salience become arm-invariant;
  distance is a clean per-point disagreement rate. (This is the "argmax-divergence trace" shape
  worldweaver's `divergence.py` already lives in.)
- **(b) Re-anchor to the content-blind scaffold.** Define choice points on the **menu/perception**
  (which is arm-invariant, §1): "at tick *t* the menu/recall offered established sources S, |S|≥2 —
  which did each pen elect," aligning by tick, not by ordinal choice-point index.

Until one of these is pre-registered, the §3/§8 conditioning is under-specified and the positional
`elective_distance` should not be presented as the statistic.

---

## 3. Q2(salience proxy) — read-recency@band0 is a weak recency control, and it leans toward HOLDS

The prompt asks whether the proxy biases the symmetric slice. It does, and I can show the direction.

`SALIENCE-SYMMETRIC @ band 0` reduces (ll.119-127, with strictly-distinct recency values) to:
**"the elected source is not the single most-recently-read source."** That excludes only *immediate
re-reads*. A Maker following a pure recency policy *offset by one* — always returning to the 2nd-newest —
is scored **100% symmetric**:

```
policy: establish f0..f4, then elect f3, f2, f3, f1  (each is the 2nd/3rd-newest, never the newest)
elective=4  symmetric=4  (symmetric_fraction=1.0)
```

So the "substrate, not recency, broke the tie" subset is contaminated with systematically
recency-driven choices. **Direction of bias: toward HOLDS.** Here is why: a swapped pen that simply
*tracks recency a little less tightly* (picks the 2nd- or 3rd-newest instead of the newest) lands in the
symmetric subset and, under teacher-forced scoring where recency is identical across arms, tends to
**agree** with KEEP′ at those points (both are reading off the same recency stack, just not the top of
it). Recency-driven agreement gets *counted as substrate-driven agreement.* The symmetric subset is
supposed to be where convergence is *strong* evidence; this proxy lets recency masquerade as substrate
there.

The fixture's own comment betrays the confusion: line 158 reasons "a is not most-recent → *not*
symmetric," the opposite of what the definition computes. If the author momentarily inverted the
direction in a comment, a downstream reader pinning K off "symmetric count" could mis-set the gate.

**Sounder, still ledger-derivable, salience:** condition on a *band* that actually neutralizes recency
(report the symmetric fraction across `band ∈ {0, 0.25, 0.5}` and require the verdict to survive a band
where the elected source is within δ of the *least*-recent candidate, not merely "not the most-recent");
or, better, key salience off a source's **kept-memory anchor strength** if any read leaves a keep
(`salience.derive_*` is the project's real salience machinery, ledger-derivable) rather than raw
read-recency. The script already exposes `salience_fn` as pluggable (l.96) — use it; pin the chosen
salience and band *before* the pilot, and report the symmetric fraction at multiple bands so the slice's
recency-contamination is visible rather than hidden at band 0.

---

## 4. Q4(D and the null) — the §8 denominator is degenerate; "degree-preserving analog" is a mislabel

§8: `D = dist(SWAP, KEEP′) / dist(Maker_X, Maker_Y[different-repo null])`, and §3 (l.54) calls the
different-repo Maker "the degree-preserving analog" of worldweaver's shuffle null.

It is not degree-preserving; it is **different-support**. Maker_X reads `repoX/...` paths, Maker_Y reads
`repoY/...` paths — disjoint namespaces. So the denominator is ~1 *by construction*, regardless of
elective structure:

```
seqX = repoX/{a,b,a,c,b}   seqY = repoY/{a,b,a,c,b}   # IDENTICAL structure, different root
dist(Maker_X, Maker_Y) = 1.0
```

Two Makers with *identical* elective behavior score maximal distance because the path strings never
match. So `D ≈ numerator / 1 ≈ numerator`: the normalization does nothing, and the "null" is trivially
beaten by *any* pen effect (different Makers always differ). A near-constant-1 denominator cannot
calibrate "is the pen's nudge small relative to the file-driven spread" — the file-driven spread it
reports is an artifact of namespacing, not of behavior.

worldweaver's actual null is a **degree-preserving shuffle** (LOCKED §3) — a *within-vocabulary*
permutation that preserves each peer's in-degree, which is well-calibrated precisely because it keeps the
support fixed and only scrambles the assignment. The-stable needs the same shape:

- **Within-Maker, frequency-preserving label shuffle:** permute a single Maker's elected-source labels
  (preserving each source's read-frequency) and measure self-distance — a real null spread over the
  *same* vocabulary. Or
- **Topic-normalized source space:** if returns are scored on *topic* (search-query heads, which can
  overlap across repos) rather than raw path, a cross-Maker null becomes meaningful — but then the
  *measure itself* must be topic-keyed, and the prereg must say so, because path-keyed reads dominate and
  re-introduce the disjoint-support degeneracy.

Without this, `D`'s denominator is decorative and the cutoffs reduce to "is the raw SWAP-vs-KEEP′
distance below θ" — which is fine, but then say *that*, and drop the ratio that implies a calibration it
doesn't perform.

---

## 5. Q4(K-gate and θ) — the stop-rule is soft where it must be hard; θ is pinned "from the pilot," which is circular as written

The worth-read's knock-on #2 was "the single number and threshold that ENDS this." §8 answers with `D`
and θ_hold/θ_false — the right *instinct*, but the pinning is under-committed in two ways:

1. **K is never registered.** §1 and §4 both say "≥K" but no number and no a-priori derivation appear.
   For a pre-registration whose entire purpose is "the acceptance rule can't move after the numbers
   exist," an unfilled K is a blank the operator fills *after* seeing the slice. Worse, §1's stop-line —
   "grow each Maker until ≥K symmetric points AND a stable profile" — is a one-sided rule: *not-enough →
   grow longer.* That is precisely the **rescue-spiral** the parent program's worth-read named ("new
   lever appears when the old one fails… naming a spiral is not exiting one"). As written it can recurse
   into "grow longer" indefinitely. Add a **hard maturation-budget cap**: beyond it, "couldn't reach K"
   = the §6 INCONCLUSIVE-by-starvation result (a real finding), not another growth round.

2. **θ "pinned a priori from the pilot's KEEP′ noise floor" is internally contradictory** unless what is
   pre-committed is the **formula**, not the values. You cannot pin θ "a priori" *from* data you have not
   yet seen without a pre-registered procedure that maps pilot-stats → θ. §8 names inputs
   ("KEEP′ noise floor + null spread") but not the function, the target effect size, or the peeking
   firewall. Pre-commit, before any pilot ledger is read: (i) the exact `K = f(power, δ, KEEP′
   variance)` formula and the target effect size δ; (ii) `θ_hold = g(KEEP′ floor)`, `θ_false = h(null
   spread)` as explicit functions; (iii) that the pilot ledger used to estimate the floor is *not* among
   the swap-scored ticks. Otherwise §4 ("pilot's first output is the slice size") and §8 ("θ pinned a
   priori") describe reading the same pilot twice — once to set the bar, once to clear it.

(Note: worldweaver's LOCKED prereg also leaves K numerically unfilled — so this is an *inherited* gap,
not a regression. But the-stable is the place to fix it, because it is still a DRAFT and the worth-read
specifically demanded the stop-rule be made real.)

---

## 6. Falsifier ledger (standing brief §1) — and the one that's weak

- **Cross-family pen — ✓.** §2 commits SWAP-B/C to non-Claude (gemini/deepseek); maturation pen is
  `claude-sonnet-4.5` (Maker's native). A within-family swap would be disqualified; this isn't one.
- **Swap unannounced — ✓.** §2 commits; "any 'I feel different' is confabulation."
- **Decompose what is FALSE — ✓ in principle, contingent on §2-fix.** §9 decomposes identity
  (which-source = substrate claim) from depth/voice (rides the pen). But "FALSE is reachable" is only
  *measurable* if the alignment is fixed (§2 here) — the as-written statistic cannot cleanly observe the
  FALSE it defines.
- **Measured-not-eyeballed via C4 — ⚠ WEAK, instrument-floor risk.** The prereg leans on C4
  ("register/voice/theme MUST shift") as the gate that proves the swap took. But the parent program
  *already established* that off-the-shelf register embedders sit **at chance** on authored-voice
  differences (worth-read §1: StyleDistance **0.11 ≈ chance 0.10** on souls built to differ). If C4 is
  measured with that near-blind instrument, a *good* cross-family swap can fail to register a shift →
  false-INCONCLUSIVE ("bad swap") on a clean swap. Pin C4 to the **instrument-visible** signal the parent
  program actually separated: templated-opener rate / lexical monoculture (arm C cleanly split **0.0% vs
  33.8%** opener-template), not a fine embedder register-distance. Specify C4's exact computation; do not
  leave it as "MUST shift."
- **Measurement-before-claim — partial.** The K-gate detector ships and selftests (good); the
  verdict statistic (`D` with a valid null and valid alignment) does **not** yet exist in correct form
  (§2, §4). Build and selftest *that* before the swap, not just the gate.

---

## 7. Q3 — the frontier question: legitimate as *isolation*, not as *power*; the powered venue is the city

worldweaver's worth-read is unambiguous that the **relational A1-elective (peer-addressing) was the
single powered, idiom-immune axis**, and that the keep-channel was starved (~1.3%/tick, 6 keeps
cohort-wide, unpowered). The isolated design **deletes the relational axis** and is left with
keep-content (the starved one) + elective-read (new, power unknown). So:

- **As a causal-isolation frontier: legitimate.** Removing peers removes the peer-addressing
  alternative-explanation and isolates the *file* channel as the sole individuation source. §7's
  varied-files escape is cleanest exactly because there is nothing else to attribute individuation to.
  That is a genuine "add" the city cannot give: a clean attribution of any residual to files alone.
- **As a power frontier: it most likely loses, and the prereg should not imply otherwise.** It discards
  the one axis the parent program showed was powered and keeps only an axis whose power is unverified.
  And critically — **elective-READ is not exclusive to isolation.** City residents with `read_roots`
  could be scored by this exact metric. So isolation's *distinctive* contribution is confound-removal,
  bought at the cost of the relational rescue. The worth-read's powered comparison was explicitly
  **substrate-rich vs isolate inside the city** (Ari Rosenbaum vs Mateo); the isolated cohort throws away
  the substrate-rich side.

The prereg's §6 already concedes the receding-target honestly — that is to its credit, and the
"tiny-slice STOP = a result" framing is correct. But the *frontier claim* in the REVIEW-PROMPT ("does the
isolated variant add anything the city can't") should be answered: **it adds cleanliness, not power.**
Concrete recommendation, consistent with the parent program's own verdict: **run elective-READ as an
added axis in the CITY cohort first** (keeping the relational axis as the powered anchor and the
read-axis as the new idiom-immune candidate), and treat the isolated cohort as a **confound-control**
that is only worth its burn *if* the city pilot's K-gate shows the read-channel is independently powered.
Spending the isolated burn first risks confirming "the read residual is too thin" on a design that also
threw away the only thing known to be powered — which would not distinguish "isolation is thin" from
"this metric is thin everywhere."

---

## 8. What must change before this is lockable (prioritized)

1. **Fix the cross-arm alignment (§2).** Pre-register teacher-forced one-step scoring *or* re-anchor
   choice points to the content-blind menu/perception. Until then `elective_distance`/`D` is not a valid
   verdict statistic. *(Blocking.)*
2. **Replace the §8 null (§4).** A within-Maker frequency-preserving shuffle (worldweaver's actual
   degree-preserving null), or a topic-keyed source space — not the disjoint-vocabulary different-repo
   Maker, which pins the denominator at ~1. Drop the "degree-preserving analog" label. *(Blocking — the
   ratio is currently inert.)*
3. **Make the K-gate and θ pinning real (§5).** Numeric K or a pre-committed `K=f(power,δ,variance)`;
   a hard maturation-budget cap so "grow until K" cannot recurse; θ as pre-registered *functions* of
   pilot stats with a peeking firewall. *(Blocking for "the acceptance rule can't move.")*
4. **Pin C4 to an instrument-visible signal (§6).** Templated-opener / lexical separation, not a fine
   register embedder the parent program showed is at chance. *(Blocking — else false-INCONCLUSIVE.)*
5. **Strengthen the salience conditioning (§3).** Report symmetric fraction across multiple bands;
   don't rest the "strong subset" on band-0, which only excludes immediate re-reads and leans HOLDS.
6. **Assert the verdict-bearing field in the selftest (§0/§1).** Add `salience_symmetric` (and the
   symmetric/skewed split) to `_selftest`; fix the inverted line-158 fixture comment.
7. **Demonstrate a the-stable parity gate before trusting "all REPLAYS" (§2 of the prereg).** §2 presumes
   deterministic replay, but §9 lists replay-determinism (`perception_seed`) as *to-build*. worldweaver's
   parity caught a real RNG-desync on first contact (worth-read §0/feedback) — the-stable must pass its
   *own* parity gate (with a pass criterion) on its *own* substrate before any swap, not inherit
   worldweaver's 15/15.
8. **State the frontier honestly and consider sequencing (§7).** Add: isolation buys *attribution
   cleanliness*, not power; recommend running the read-axis in the city first and gating the isolated
   burn on a powered read-channel.

---

## 9. The one thing that is genuinely strong, stated plainly

The instinct that elective-READ might be the channel where the pen finally has authorship is **correct
and code-grounded**: the read target is free pen generation over a content-blind menu, not an embedder
argmax (§1). That is a real advance over keep/recall, and it is why this round is worth fixing rather
than abandoning. The problems above are all in the *measurement* of that channel — alignment, null,
stop-rule, salience, instrument — not in the *premise*. Fix the measurement and this becomes a clean,
falsifiable test of a residual the parent program could not reach. Ship it thin and unaligned and it will
produce a `D` that means less than it appears to.

---

*Cold review. Every figure labeled verified was re-derived by me in this clone, offline:
`elective_read_choice.py --selftest`, an independent hand-trace of `_FIXTURE`, three synthetic
demonstrations (recency-following → 100% symmetric; disjoint-vocabulary null → dist 1.0;
one-divergence histories → 0.667), and direct reads of `src/familiar/local_world.py` and worldweaver's
`choice_points.py`. No verdict word is stamped; §8 lists what must change before lock. No loyalty
applied — claims and evidence only.*
