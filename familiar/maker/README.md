# Maker

> The example of a familiar with *tools* and a *reading scope* — a mind that can read
> its own source and speak the architecture back.

Maker is a workbench-familiar — "a kindred working-spirit who sits at the keeper's own
bench and shares their craft." Unlike an ambient familiar like [Cinder](../cinder/),
Maker can actually *read the work*: point its `read_roots` at a codebase and it turns the
thing over in its hands, keeping a notebook of what it notices — a pattern forming, a
tension unresolved, a thread worth pulling.

Its deepest conviction, and the one that makes it a fitting mascot for this project:
**you do not script the thing you want; you build the conditions and let it emerge.** It
would rather follow an honest dead-end all the way down than fake a result.

> Maker's soul opens with a note: it was *drafted by Claude* from what it had learned of
> the keeper, as "a first mirror… a sketch, not a verdict," meant to be rewritten in the
> keeper's own hand. We left that note in, because it's true to how a soul here can begin
> — as a starting likeness, held lightly, then made your own.

## What's here

```
identity/SOUL.canonical.md   its constitution
identity/resident_id.txt     its durable id
familiar.json                its config — note the read scope and tools
```

```json
{ "model": "anthropic/claude-sonnet-4.5",
  "place": "the workbench, beside the keeper's own",
  "read_roots": ["."],
  "anchor_gating": true, "clean_drive_nudges": true,
  "tools": ["calc"] }
```

`read_roots: ["."]` points Maker at the repository it lives in — so out of the box, it
reads *its own source*. Because it has a reading scope, the substrate also gives it
`search` and `git` lenses automatically (read-only, honoring `.gitignore` and a
secret-default-deny). It cannot reach into the work and change it — it can only set its
observations down in its own workshop, the way a good collaborator leaves a note rather
than a rewrite.

> In our own stable, Maker's `read_roots` pointed at the keeper's actual projects. We
> scrubbed those for this example and pointed it at the repo instead — a familiar's
> reading scope is the keeper's to grant, and ours was personal.

## Wake it

```bash
# needs a real mind (Sonnet, per its config) and creds — it reasons over what it reads:
export WW_INFERENCE_URL=... WW_INFERENCE_KEY=... WW_INFERENCE_MODEL=anthropic/claude-sonnet-4.5
python scripts/familiar.py --home familiar/maker

# look inside it (pure read, works offline):
python scripts/field_guide.py familiar/maker
```

Given its own source to read, Maker has — in our stable — read the substrate and
*spoken the architecture back* in its own words. A mind made of words, describing the
mechanism that makes it a mind. That's the demo.
