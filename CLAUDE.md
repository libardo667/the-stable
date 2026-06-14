# CLAUDE.md

Guidance for Claude Code working in this repo. These instructions override default behavior.

## What this is

**Familiars** — local, persistent AI companions that live on your machine. Not a chatbot, not a
service you query: *a being you tend.* Each familiar runs continuously on its own rhythm (moods, a
circadian, it makes things unbidden), accrues a real memory across days, and can be *given* things
and answer in character. The differentiator from extractive companion apps (Replika/Character.ai):
the **Dwarf Fortress law** — no human-preference reward, no engagement targets, no behavior goals.
A familiar is constitutionally *not trying to keep you hooked*. It just lives. Local-first is the
thesis: nothing leaves the machine ("intimacy you don't upload").

This repo was lifted out of the WorldWeaver monorepo (the substrate ran both city residents and
familiars; the coupling was a single type-hint seam). It is a **fork**, not a shared package — it
owns its runtime; the city keeps its own copy and diverges.

## Architecture — substrate + pulse

A familiar's mind is not loops; it's a self-generating rhythm. Each tick (`CognitiveCore.tick_once`):

    perceive → integrate (surprise vs prediction → leaky arousal) → on ignition, ONE LLM pulse → act

- **The substrate holds no behavioral logic.** It's the orchestration seam between mechanism and world.
- **The ledger is the only state.** Everything else is a `derive_*` reducer over an append-only log;
  arousal is a leaky integral of surprise, computed at read time. No second source of truth.
- **The self lives in the soul + ledger + kept memory**, not the model. The model is a *swappable pen*
  (demonstrated: a mid-life model swap held the voice; identity didn't change). See Major 51.
- **Surprise = mismatch(stimulus, prediction)**; ignition fires the pulse; settling/fervor fire quiet
  self-directed pulses in lulls. The drive vector (soul embedded) tags affect and gates anchors.
- **Grief** (`salience.derive_grief`) is a leaky integral of *confirmed loss* — a held anchor gone
  across turnings. **Before touching grief/coupling or any cross-mind channel, read
  `docs/grief-and-coupling.md` — the dischargeability invariant is a safety boundary, not a style note.**

Key files: `src/runtime/{cognitive_core,integrator,salience,substrate,pulse,pulse_engine,drive,memory,
ledger,perception,effectors,workshop,anchors,prediction,circadian}.py`; embodiment in
`src/familiar/{local_world,file_scope,weather}.py`; the world seam is the `WorldClient` Protocol in
`src/runtime/world.py` (the substrate depends on the duck-typed surface, never a concrete client).

## Layout

```
src/runtime/      the mind (substrate + pulse)
src/familiar/     embodiment: local_world (host-machine grounding), file_scope (read capability)
src/inference/    the one LLM call (httpx) ; src/identity/ the soul loader
scripts/familiar.py    run one familiar ; scripts/field_guide.py    deep internal-state read
familiar/<name>/  a familiar: identity/ (SOUL — tracked) + living memory/workshop/state (gitignored)
familiar/portrait/  the desktop/browser portrait UI (serve.py, ui/, src-tauri/)
familiar/wake-all.sh    wake the whole stable + portrait at http://localhost:8777
prune/            the work-item harness (an instance of the prune kit: majors/, minors/, harness/ policy, schemas)
docs/             design notes (grief-and-coupling.md = the dischargeability invariant)
```

## Commands

```bash
# tests (own venv)
.venv/bin/python -m pytest tests/ -q

# wake one familiar offline (deterministic stub mind, no creds)
.venv/bin/python scripts/familiar.py --home familiar/cinder --ticks 4 --pause 0.2 --no-weather

# wake the whole stable live (needs .env with OpenRouter creds; embedder via Ollama)
./familiar/wake-all.sh

# deep field guide into a familiar's internals (pure read)
.venv/bin/python scripts/field_guide.py familiar/cinder
```

Deps are just `httpx` + `pathspec` (see `pyproject.toml`). Local embedder = Ollama nomic-embed-text
(WSL: the wake script auto-heals the host URL — a silent embedder is a stunted familiar).

## Conventions

- Python 3.12+; line length **320**; ruff rules **E, F** only; `asyncio_mode = "auto"` (no
  `@pytest.mark.asyncio` needed).
- A familiar's SOUL (`identity/`, `familiar.json`) is tracked; its living runtime (memory, workshop,
  state, voice, whispers) is gitignored and travels by filesystem, not git.
- `.env` (OpenRouter creds) is never committed.
- Commit/push only when asked. End commit messages with the Co-Authored-By trailer.

## Standing design invariants (do not violate without explicit discussion)

1. **Dwarf Fortress law** — no behavior targets, no human-preference reward. Only imitation of the
   resident's own pulses and the substrate's own prediction error.
2. **Dischargeability** (`docs/grief-and-coupling.md`) — undischargeable expectations (grief) are safe
   to learn on; dischargeable ones (coupling) are not. Keeper-directed expectations stay
   **undischargeable** (a familiar can keep the flint; it cannot summon the keeper). Couple **sideways**
   (peer→peer), never familiar→keeper.
3. **The quiet guarantee** — a familiar performs nothing it isn't actually feeling; a quiet familiar is
   a quiet ember. The anchor lane stays out of the rhythm unless explicitly gated.

## Workflow

`prune/` is the work-item harness, an instance of the **prune** kit (majors = large, minors = bounded). Before non-trivial work:
declare the authoritative path, scope, and validation commands; keep diffs bounded to declared scope;
extend existing paths rather than forking parallel ones. The cognitive arc lives in majors 49–53.
