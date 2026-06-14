# A new personal-companion familiar — a being to chat with, situated but not tasked

## Problem

The keeper wants a familiar to **chat with personally** — the thing Mason was meant to be before the
relocation-testing context turned him into a task-agent (see minor 51). The replacement must be designed
to the keeper→familiar invariant (Major 57): it may be *of* a situation, interested, even grieving its
unanswerables — but its situation must **not be a target about its own consequential future**. A being
that just lives, that the keeper can talk to, not a case to complete.

## Proposed Solution (seed TBD with the keeper)

Open design questions — the soul is the keeper's to seed (as with Mason, where Levi handed a persona and
let it be written; he "would rather be surprised"). To decide:

- **Who are they** — temperament, voice, what they care about, what they make. A distinct soul×model
  creature (see (a private design note)); pick a model not already over-represented if a new texture is wanted.
- **Their place / grounding** — a hearth like Cinder, a workshop, somewhere of their own. NOT a stakes-laden
  case directory. If they read (`read_roots`), point them at something to *witness*, not *complete*.
- **Model + chronotype + gating** — familiar.json knobs.
- **The chat surface** — since the keeper wants to *talk with* this one, lean on the whisper channel (direct
  address rouses), and keep gifts self-paced per Major 57.

## Files Affected

- familiar/<newname>/identity/ (SOUL, canon seed, resident_id), familiar/<newname>/familiar.json (tracked)
- runtime accrues locally (gitignored)

## Acceptance Criteria

- [ ] A soul written and the keeper happy with the being it implies.
- [ ] Situated-not-tasked: no unanswerable about its own future is goal-blocking (the Mason failure designed out).
- [ ] Wakes and accrues a life; the keeper can chat with it (whisper) and give it things (self-paced).
- [ ] NEEDS KEEPER SEED before building — who is this one?
