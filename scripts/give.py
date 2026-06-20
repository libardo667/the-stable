#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""Give a familiar a thing (Major 55).

The keeper hands a file to a familiar — a photo, a document, a drawing. It lands in the familiar's
own ``workshop/given/`` (kept, theirs, revisitable) and is announced on the ``given.jsonl`` channel,
the visual twin of ``whispers.jsonl``. A vision-capable familiar *sees* an image/PDF gift on its next
pulse (Track A's sight path); a text-only one gets a PDF's text and an honest note.

Three composable knobs — drop how you like:

    # silent — just leave it; the familiar notices on its own rhythm (it surfaces while fresh,
    # and stays in given/ to revisit)
    scripts/give.py familiar/maker ~/pinto.jpg

    # soft notify — a word rides along, surfaced in its perception, but does NOT force attention
    scripts/give.py familiar/maker ~/pinto.jpg --note "the dog I promised you"

    # notify + rouse — a whisper, which the run loop turns into an attend-now (it looks at once)
    scripts/give.py familiar/maker ~/pinto.jpg --say "Maker — here's Pinto, the dog I promised. look :)"

``--note`` (soft) and ``--say`` (rousing) can combine. This is the engine the Tauri drag-and-drop UI
(Major 55 Part B) will sit on top of — same delivery, a thinner gesture.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    p = argparse.ArgumentParser(description="Hand a familiar a file — it lands in workshop/given/ and is perceived.")
    p.add_argument("home", help="the familiar's home dir, e.g. familiar/maker")
    p.add_argument("file", help="the file to give (a photo, a PDF, any file)")
    p.add_argument("--as", dest="rename", default="", help="store it under this name in given/ (default: the file's own name)")
    p.add_argument("--note", default="", help="a soft word that accompanies the gift — surfaced in perception, does NOT rouse")
    p.add_argument("--say", default="", help="a whisper that announces the gift — the run loop turns a new whisper into an attend-now (rouses)")
    args = p.parse_args()

    home = Path(args.home).expanduser().resolve()
    if not (home / "familiar.json").exists() and not (home / "identity").is_dir():
        print(f"✗ {home} doesn't look like a familiar home (no familiar.json / identity/).", file=sys.stderr)
        return 2
    src = Path(args.file).expanduser().resolve()
    if not src.is_file():
        print(f"✗ no such file: {src}", file=sys.stderr)
        return 2

    name = args.rename.strip() or src.name
    name = Path(name).name  # never let --as escape given/
    given_dir = home / "workshop" / "given"
    given_dir.mkdir(parents=True, exist_ok=True)
    dest = given_dir / name
    shutil.copy2(src, dest)

    ts = datetime.now().astimezone().isoformat()
    _append_jsonl(home / "given.jsonl", {"ts": ts, "file": name, "note": args.note.strip()})
    if args.say.strip():
        _append_jsonl(home / "whispers.jsonl", {"ts": ts, "text": args.say.strip()})

    size = dest.stat().st_size
    who = home.name
    mode = "rousing whisper" if args.say.strip() else ("soft note" if args.note.strip() else "silently")
    print(f"✓ gave {who} → given/{name} ({size} bytes), announced {mode}.")
    print(f"  it's kept at {dest}")
    if not args.say.strip():
        print("  (no rouse — it surfaces while fresh and waits in given/ for the familiar to notice or revisit.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
