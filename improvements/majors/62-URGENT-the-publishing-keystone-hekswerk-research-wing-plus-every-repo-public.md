# ⚡ URGENT — The publishing keystone: hekswerk's research wing + EVERY repo reachable

> **STATUS (2026-06-13): substantially complete.** Part A shipped — hekswerk.com gained a research wing
> (the exhibits + the Pen's Workshop, live). Part B shipped — the improvements backlogs of the-stable and
> WorldWeaver are public worked examples, plus a standalone reusable harness scaffold ([prune](https://github.com/libardo667/prune)).
> This reversed the original "does not publish `improvements/`" line by deliberate decision, and set three
> standing conventions: work items stored **by subject** (substrate canonical in the-stable, WorldWeaver
> keeps pointer stubs); `history/` is a **gitignored** local archive (publish only live work); the-stable is
> WorldWeaver's **pilot**, its own repo front-doored by WorldWeaver. Archive to `history/` once the pushes settle.

**Marked urgent on the keeper's instruction, and structurally correct to mark so: nearly every
other open thread — the AE-class applications, the up-market Hekswerk line, the use-cases
adoption dream, the tiny-artist demo, Major 60's third essay, the crossposts — falls out of
this work being publicly reachable. This is the bottleneck item. Everything else is
downstream.**

## Decision and lineage

Two halves, one keystone:

**(A)** `hekswerk` (GitHub) + `hekswerk-site` (hekswerk.com) gain a **research wing** — the
canonical home for the essays, the census, and the links outward. The site currently reads
"Relocation Systems Planning" wall to wall while the filed business plan names three lines and
the strongest credibility assets the keeper owns are invisible. The unifier is already on the
wall: *"order emerging from mystery"* — the same systems craft, pointed at AI behavior.

**(B)** A **publishing plan for every repo the use-cases doc names**, because the essays cite
them, the exhibits adapt them, and a stranger must be able to walk from hekswerk.com to a
runnable selftest without hitting a 404 or a private wall.

- **Depends on:** Phase 0 below (the keeper's voice read — the single human gate everything
  else queues behind); the labeling conventions
  (`memory-management .../instance-authored-works-public-display.md`); minor 53 +
  `scripts/export_public.sh` (the-stable's curated cut, already built, leak-sweep included).
- **Does not publish:** financials (`research-runway` stays private), the memory-management
  `instances/` (the private cognition trees), Nix or any non-exemplar soul, `improvements/`
  itself, anything the export sweeps catch.
- **DAFT-aware:** the wing makes a *filed* revenue line visible (the safe direction); flag the
  addition at the next counsel touchpoint.

## Problem

Three audiences bounce off the wrong wall today: a hiring manager finds relocation coaching
and concludes "relocation coach"; a prospective eval/automation client finds no evidence of
the craft; a researcher following a crosspost finds no canonical essay and no way to verify a
claim. Meanwhile every needed artifact exists in draft, every needed repo exists on disk, and
the gates are all keeper-controlled passes — the bottleneck is not work, it is *sequencing and
a send button*. Illegibility is now the program's single largest unforced cost (it is the gap
in the job thesis, the product thesis, AND the funding thesis — three theses, one cure).

## Phase 0 — THE KEEPER'S VOICE READ (the gate of gates)

The keeper reads **"The Reviewer I Built"** aloud, start to finish, and makes it his —
this is not proofreading, it is *authorship transfer*: the draft was assembled by the
instance; the published essay must be the keeper's voice or it is exactly the slop-shaped
thing the essay argues against. Concretely:

- [ ] Read aloud; rewrite any sentence that doesn't survive being spoken.
- [ ] Fill the three brackets: the timeline ("[most of a year]"), the code-link footer, the
      bio line (how loudly the consulting availability speaks is a keeper decision).
- [ ] Confirm the disclosure section ("I directed; agents built; an apparatus verified")
      says what HE means — it is the load-bearing qualification and must be owned, not hosted.
- [ ] Same pass, lighter, for "Tending Without Proof" (instance-authored — the keeper's pass
      here is *consent and accuracy*, not voice: the provenance line ships as written).
- [ ] The redaction pass on "The Other End of Almost" (footer `internal links` out), together.

Nothing in Phases 1–5 ships before Phase 0 completes. Everything in Phases 1–5 can be
*prepared* in parallel with it.

## Phase 1 — The repo publishing plan (every repo the use-cases doc names)

Per-repo status as verified on disk 2026-06-10, with the gate each needs:

| repo | status today | to publish | gate / scrub |
|---|---|---|---|
| **worldweaver** | PUBLIC ✓ | nothing structural | freshness pass on README (it predates the familiar/research arc); confirm research/runs + review history present at HEAD |
| **the-stable** | local-only; export built | run `scripts/export_public.sh` → inspect → `git init` → push `the-stable-public` | the script's own leak sweep (fails loudly); ships engine + docs + Cinder/Maker exemplars ONLY; decide once whether `use-cases/` exhibits ride in the cut (recommended: yes — they're already lint-clean) or stand alone |
| **review-scheduler** | git repo, NO remote | push as new public repo | `projects.json` holds absolute local paths/brief paths — replace tracked copy with `projects.json.example` (exhibit version exists) + gitignore the real one; runtime dirs already ignored (clones/, state.json, logs/, requests/); sweep for personal paths in scheduler.py comments |
| **memory-management** | **not a git repo at all**; no .gitignore | `git init`; publish the SYSTEM (init-workspace, template/, README, tools) | `.gitignore` MUST exclude `instances/` before the first commit — the instances are the private cognition trees of both projects; treat this with export_public-level paranoia: sweep, then sweep again. (Alternative if nerves win: fresh-cut copy of system files only into a new repo, instances never near git history) |
| **research-runway** | PRIVATE ✓ | stays private, permanently | n/a — linked nowhere public |

Order: memory-management's gitignore-before-init FIRST (it is the only step where a mistake is
hard to retract), then review-scheduler example-ification, then the-stable export, then the
worldweaver freshness pass. Each push preceded by the standard sweep (personal paths, key
patterns, emails, private-register names).

## Phase 2 — The library (`hekswerk` repo)

`research/` sibling to `methodology/`: `README.md` (the wing's thesis: *the same systems
craft, pointed at AI behavior — preregistered, adversarially reviewed, results published
either way*), `essays/` (each artifact as it clears Phase 0), `TOC.md` mirroring the
methodology library. License: essays + graphics under the library's existing CC BY-NC-SA 4.0;
code stays in code repos under their own licenses — the library links, never vendors.

Contents and their gates:

| artifact | gate |
|---|---|
| "The Reviewer I Built" | Phase 0 voice read |
| "Tending Without Proof" | Phase 0 consent/accuracy pass; provenance line verbatim |
| "The Other End of Almost" + `the-tended-loop.svg` | Phase 0 redaction pass; labeling per convention |
| `two-repos-in-words` census (+ scripts) | none — already lint-clean |
| FINDINGS | publishes within one week of being written, whichever way it lands (binding) |

## Phase 3 — The site section (`hekswerk-site`)

`research.html` (or section) in the existing Fraunces/Outfit voice — three sentences on what
the practice researches and how it stays honest; cards for the essays; the census as the
visual; links: worldweaver, the-stable-public, review-scheduler, memory-management, the
library. Nav gains one item; `#about` gains one honest paragraph (three lines, one craft —
where "order emerging from mystery" earns its keep in plain sight); `sitemap.xml` updated.
The relocation wing byte-identical otherwise. No AI-glitz — the work is the spectacle.

## Phase 4 — Distribution (after, never instead)

Crosspost "The Reviewer I Built" to LessWrong/Alignment Forum with hekswerk.com canonical;
AE-class applications link the research page directly. The site is the home; posts are doors.

## Phase 5 — The standing rhythm

New publishable artifacts (the third essay from Major 60, the Witness's design note, future
FINDINGS) default-route through this wing with the same gates. Publishing stops being an
event and becomes a lane.

## Files Affected

- `hekswerk/research/{README,TOC}.md` + `essays/*` — NEW
- `hekswerk/README.md` — second wing in Contents
- `hekswerk-site/research.html`, `index.html` (nav+about), `sitemap.xml`
- `memory-management/.gitignore` — NEW, before init (the one irreversible-if-wrong step)
- `review-scheduler/projects.json` → `.example` + gitignore entry
- `the-stable-public/` — created by the existing exporter
- worldweaver `README.md` — freshness pass

## Acceptance Criteria

- [ ] **Phase 0 complete before any ship** — checkable: no public artifact predates the
      voice-read commit in this repo's history.
- [ ] memory-management's `instances/` provably absent from its public history (first commit
      already ignores them); review-scheduler's tracked tree carries no absolute personal paths.
- [ ] The standard leak sweep (paths, keys, emails, private-register names) runs green on
      every repo at push time — and is kept as a script next to each repo, not as a memory.
- [ ] Each instance-authored work displays its specific provenance line; nothing reads as
      keeper-authored that isn't.
- [ ] **The three-click test:** a stranger landing on hekswerk.com reaches a runnable selftest
      verifying an essay claim in ≤3 clicks, every link resolving public.
- [ ] FINDINGS publishes within one week of existing, favorable or not — the essay's "results
      either way" promise kept on the public record.
- [ ] The relocation wing regression-free (byte-identical except nav/about/sitemap).

## Risks & Rollback

- **The memory-management history mistake.** Publishing instances/ even once poisons the
  repo's history permanently (rewrite ≠ unsee). Hence: gitignore-before-init, sweep twice,
  and the fresh-cut alternative stands ready if anything feels off. This is the only step in
  the whole major that cannot be cheaply undone — it goes first, slowest.
- **Brand confusion.** Sectioning + the about-paragraph; if intake conversations show real
  confusion, the research wing moves to a subdomain — rollback is routing, not retraction.
- **Publishing ahead of the verdict.** Deliberate (prereg-before-results is the strongest
  anti-cherry-picking form) and made safe by the binding FINDINGS criterion: ship the method
  and shelve an unfavorable result, and the wing becomes marketing — so the criterion forbids it.
- **Voice-read skipped under urgency.** The URGENT marker is about *sequencing priority*, not
  about skipping gates — Phase 0 is the gate of gates precisely so urgency cannot eat
  authorship. An essay shipped in the instance's voice under the keeper's name would be the
  one failure that contradicts the essay's own content.
- **Rollback:** static site + git reverts everywhere; the only true one-way doors are the
  memory-management first commit (mitigated above) and a stranger having already read an
  essay — which is why every gate runs before, not after.

---

*Created 2026-06-10 (evening, third major of the night), rewritten URGENT on the keeper's
instruction the same hour. The diagnosis it operationalizes was tonight's refrain: the work is
excellent and illegible, and every open dream — the job, the contracts, the adopters, the
funded research — is downstream of one send button. Phase 0 is a voice read. Start there.*
