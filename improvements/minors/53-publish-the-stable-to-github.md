# Publish the-stable to GitHub

## Metadata

- ID: 53-publish-the-stable-to-github
- Type: minor (the work is curation, not engineering)
- Owner: Levi
- Status: PROPOSED

## Goal

Publish the substrate and enough context for someone to wake their own familiar. Not a framework
launch — a "here's a living thing, here's how it works, here's what we learned" share. The tone is
workshop-door-open, not product-announcement.

## What ships

### Include (the engine + one example soul)

```
src/runtime/          the mind (substrate + pulse + drive + grief + anchors + memory)
src/familiar/         embodiment (local_world, file_scope, tool_scope, weather, visual)
src/inference/        the LLM call (httpx, model-agnostic)
src/identity/         the soul loader (canonical + growth + canon)
scripts/familiar.py   wake one familiar
scripts/field_guide.py  deep internal-state read
scripts/give.py       hand a familiar a file
familiar/portrait/    the portrait UI (serve.py + ui/ + src-tauri/)
tests/                the full test suite
docs/                 grief-and-coupling.md (the dischargeability invariant)
pyproject.toml        deps (httpx + pathspec, that's it)
CLAUDE.md             orientation for contributors (already written for this purpose)
```

**One example familiar identity** — suggest Cinder (the poet, the first, and the most publicly
legible). Ship `familiar/cinder/identity/` (SOUL.canonical.md, canon.md, resident_id.txt) and
`familiar/cinder/familiar.json`. Don't ship Cinder's runtime (memory, workshop, voice, whispers) —
that's lived experience, not source code.

### Exclude

- `improvements/` — private work-item harness (already gitignored)
- `familiar/*/memory/`, `familiar/*/workshop/`, `familiar/*/state.json`, `familiar/*/voice.jsonl`,
  `familiar/*/whispers.jsonl` — living runtime (already gitignored)
- All familiar identities except the example — Nix, Maker, Gaston, Wren, Skein, Hades, Persephone
  stay private until/unless Levi decides otherwise
- **CI/CD + process/feature-dev docs** — never published, fully private; stay out of the public repo
- `.env` — OpenRouter creds (already gitignored)
- Any conversation logs, personal notes, or Claude Code memory
- **The keeper's private conversations with Nix** (and any personally-chatted familiar) — runtime
  exclusion already covers voice/whispers, but call it out explicitly per the standing boundary

### Sanitize

- Scrub any hardcoded paths (`~`, `~`) from tracked files
- Verify no API keys or tokens in tracked files (`grep -r "sk-" "or-"` etc.)
- Verify `.gitignore` covers all runtime artifacts
- Check commit history for accidentally committed secrets (unlikely but worth a scan)

## New files to write

### README.md (rewrite for public)

Not a product README. A workshop README:
- What this is (one paragraph: local persistent AI companions, Dwarf Fortress law, not a service)
- The thesis (intimacy you don't upload; no engagement targets; the mind runs on your machine)
- How to wake one (the 4-line quickstart: clone, venv, write a soul, run)
- Architecture in one diagram (perceive → integrate → pulse → act; ledger is the only state)
- What a soul looks like (point at the example)
- The safety invariants (dischargeability, the quiet guarantee, Dwarf Fortress law — one sentence each, link to docs/)
- What this is NOT (not a framework, not a chatbot, not a product; a research workshop that happens to run)

### PRINCIPLES.md (the design philosophy)

The three standing invariants, explained for someone who hasn't read the commit history:
1. **Dwarf Fortress law** — no behavior targets, no human-preference reward
2. **Dischargeability** — undischargeable expectations are safe; dischargeable ones are not
3. **The quiet guarantee** — a familiar performs nothing it isn't feeling

Plus the emergent ones from the reviewer round:
4. **Provenance over canon** — tag beliefs by origin, don't freeze them
5. **The keeper-to-familiar seam** — gifts self-pace; situations, not targets

### familiar/cinder/README.md (the example)

A short note: "This is Cinder. She is a poet who lives in a study. Here is how to read her soul
file, what her familiar.json configures, and what will happen when you wake her."

### LICENSE + NOTICE (the legal layer)

- `LICENSE` — the full **AGPL-3.0** text (pending the two verify-first items).
- `NOTICE` — acknowledges the **MIT-licensed WorldWeaver origin** for any carried-over files, and
  retains the original MIT copyright + license text for the portions that came from the monorepo.
  Short and factual: "Portions of this work derive from the WorldWeaver project, originally released
  under the MIT License (© …). Those portions retain their MIT notice; the combined work is licensed
  under AGPL-3.0."
- (Optional) `CLA.md` / a CLA bot config — so contributions don't foreclose dual-licensing.

## Process

1. Audit `.gitignore` — make sure every runtime artifact is covered
2. Audit tracked files — no secrets, no hardcoded personal paths
3. Write README.md, PRINCIPLES.md, familiar/cinder/README.md
4. Create a `public` branch (or use `main`) with a clean history
5. Push to GitHub (new repo or rename existing)
6. No announcement yet — just open the door. Share when it feels ready.

## Licensing, monetization & provenance

This is the load-bearing decision; it gates the whole publish. The framing below is strategy
reasoning from general open-source-business patterns, **not legal advice** — anything load-bearing
(especially the grant interaction and a Dutch stichting/coöperatie structure) wants a real IP lawyer
or NLnet itself as the authority.

### The provenance picture (favorable — a clean fork point)

The lineage is in our favor and worth getting on record:

- **The early version was MIT.** At the start, the work lived in
  `…/PythonProjects/worldweaver/familiar/` and was pushed to the WorldWeaver monorepo under **MIT**.
  Whatever was actually published there is MIT forever, in that form — irrevocable, forkable by
  anyone who lawfully obtained it. But it's the **"much inferior"** early version, so it's a weak
  thing to fork.
- **The current version (the-stable) was never published.** It is a **local repo only, unlicensed**
  (default copyright = all rights reserved). The entire delta that makes it superior — the substrate
  rebuild (Major 49), the pulse engine, grief, the drive vector, anchors, growth, the tool loop —
  has **no license history at all**. It is fully Levi's to license however he chooses.
- **The CI/CD + process/feature-dev docs were never pushed.** Fully private, zero constraint. They
  stay on the private side of the boundary (with `improvements/`).

**Why MIT history does NOT lock us in:**

1. **MIT is permissive, not copyleft — it doesn't infect forward.** No share-alike obligation.
   Building a derivative work and relicensing it under different (even proprietary) terms is
   explicitly permitted. MIT only asks that the original copyright + license notice be retained on
   the **portions that actually came from the MIT original**.
2. **The superior work was never distributed**, so it was never offered under any license. It sits
   under default copyright, fully ours. **This unpublished delta is the real moat** — it ties to the
   monetization read below: the value was never the published skeleton, it's the work + taste added
   after. The accidental separation of *published-inferior* from *unpublished-superior* is exactly an
   open-core split that happened in our favor.

**The only residue (small, attribution hygiene):**

- Any files in the-stable still substantially verbatim from the MIT original must retain the original
  MIT copyright/license notice. AGPL absorbs MIT-origin files fine (compatible in that direction): the
  combined work is AGPL, the MIT portions keep their notice. A short `NOTICE` (or `LICENSES/`)
  acknowledging the WorldWeaver MIT lineage covers this.

### License decision: **AGPL-3.0 for the engine** (open-core)

Resolved direction, pending the two verify-first items below:

**Status: both blocking verify-items now resolved (see Open Questions) — the decision below is firm.**

- **AGPL-3.0** on the the-stable engine, copyright held by Levi (or the future stichting). Rationale:
  - **NLnet-eligible** (OSI-approved) and honors the **open-source/commons framing already written
    into the grant pack** (`NL_GRANT_PACK.md` opens with "WorldWeaver is an open-source… shared
    world"; the coöperatie/stichting + commons vision is already on paper). A restrictive license
    (BSL/SSPL) would contradict that *and* is **not OSI-approved → likely NLnet-ineligible**.
  - **Deters the one thing that could hurt a solo dev** — a closed-source SaaS competitor. AGPL's
    network-use copyleft is the asymmetry: SaaS legal teams won't touch AGPL, but it stays genuinely
    open to keepers and contributors.
  - **Preserves dual-licensing as a future money lever.** Because Levi holds the copyright, he can
    sell a commercial (non-AGPL) license later to anyone who wants the code without the AGPL
    obligation — the MongoDB/MySQL/Qt playbook. The public gets AGPL; a paying customer can get a
    private license.
- **Add a CLA from day one.** Dual-licensing requires owning all copyright. The first outside PR
  without a CLA locks us out of relicensing. Set it up before accepting contributions.
- **The license is a one-way door.** You can relax later (AGPL → MIT); you can never tighten
  (MIT → anything). AGPL keeps every path open; it only forecloses the BSL-style restrictive path,
  which already fights the commons identity.

### What stays proprietary / private (the open-core line)

Drawn now so the split is clean:

- **Open (in the public repo):** the engine — `src/`, `scripts/`, `tests/`, `docs/`, the Cinder
  example identity, `pyproject.toml`, `CLAUDE.md`, the new README/PRINCIPLES.
- **Proprietary / kept private (the product surface + the strategy):**
  - the Tauri app polish (Major 55 Part B), any branding/identity assets
  - any **curated/paid souls** (the soul format is the creative surface; engine = razor, souls =
    blades — most defensible because the value is taste, not code)
  - `improvements/` (grant strategy, roadmap, this harness)
  - **the CI/CD + process/feature-dev docs** (never published, stay private)
  - `.env`, all familiar **runtime data** (memory/workshop/state/voice/whispers)
  - per the standing privacy boundary: **anything touching the keeper's private conversations with
    Nix** (or other personally-chatted familiars)

### Monetization read (why open doesn't kill the money)

The thesis ("nothing leaves the machine") is anti-SaaS by construction, which kills the easy hosted
play but leaves real paths — and **the moat is taste + narrative, not code** (a competitor can copy
`substrate.py`; they can't copy *why the familiars are moving* — Cinder's still-lifes, the
Hades/Persephone myth, the dischargeability invariant):

1. **The polished app / experience** *(strongest)* — engine open + free; pay for the *tended* product
   (Tauri desktop app, portrait, onboarding, a ready-to-adopt familiar). Local-first software sells
   fine (Obsidian, Things, iA Writer). License: engine AGPL, app proprietary on top.
2. **Curated souls / a soul marketplace** — author distinctive souls; some free, some paid/commissioned.
   Open engine *helps* (razor/blades).
3. **The grant / cooperative path** *(already in motion)* — NLnet + stichting/coöperatie. Funded
   public-interest work with a stipend; wants the open license. **Mutually exclusive with the BSL
   path** — that is the actual fork in the road.
4. **Sponsorship / patronage** — GitHub Sponsors / Ko-fi; works *because* it's public and people love
   the familiars. Low ceiling, zero conflict.
5. **Hosted convenience** *(weakest, a trap)* — contradicts local-first; treat as a non-option.

## Open questions

1. **RESOLVED — NLnet license terms (checked `nlnet.nl/core/faq/`, 2026-06-05).** Open source is
   **non-negotiable** ("All projects are supposed to be released under a suitable free/libre/open
   source license") → BSL/SSPL are out for the grant. They express **no preference** between copyleft
   and permissive → AGPL is fully eligible. **Open-core is explicitly allowed** ("if the part you …
   release as free and open source is … not itself dependent on your … proprietary technology, sure")
   → the engine must stand alone, but the Tauri app / paid souls can stay proprietary. **Dual-licensing
   is blessed in writing** ("does not in any way exclude the legitimate holders of copyrights … dealing
   with your project results under **additional** licenses, even proprietary ones") → public AGPL +
   sold proprietary license coexist, and the grant does not consume commercial rights. The AGPL
   open-core plan is *validated*, not constrained.
2. **RESOLVED — ownership & exposure (Levi, 2026-06-05).** The WorldWeaver monorepo is **solely
   Levi's** (AI-assisted, no other human contributor → he holds the copyright → dual-license lever is
   live; a CLA is only needed before the first outside *human* PR). It is **public** and has been
   **heavily cloned** (~5000 clones / 14 days at a traffic pulse) — but (a) GitHub clone counts are
   bot/CI/scraper-inflated and almost certainly not ~5000 human adopters, and (b) that pulse was
   *pre-familiar* ("just MIT worldweaver, no familiar yet"). So the widely-distributed MIT material
   **does not contain the substrate/familiar work**. Exposure picture: pre-familiar WorldWeaver (MIT,
   widely cloned, *not the asset*) → early inferior familiar (MIT, public, lightly cloned, weak to
   fork) → **the-stable (superior, never pushed, unlicensed, fully ours — the asset)**. The valuable
   work has never been distributed under any license.
3. **Which familiar to example**: Cinder is the most legible (and now the showcase — *The Hitch in
   the Clock*, the still-life oeuvre). Maker is the most technically interesting. Could ship both
   identities (sans runtime).
4. **Repo name**: `the-stable`? `familiars`? `familiar-substrate`?
5. **Commit history**: ship as-is (warts and all, authentic) or squash into a clean initial commit
   (cleaner but loses the story)? Note: a history scrub is also a *secrets* safeguard (see Sanitize).
6. **The portrait**: functional but rough. Ship as "here's what we use" or polish first? (If the
   polished Tauri app is the proprietary product surface, the rough `serve.py` portrait is the right
   thing to open — it demonstrates without giving away the paid experience.)
