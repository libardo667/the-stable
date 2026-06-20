#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""add_spdx_headers.py — idempotently stamp SPDX AGPL headers on first-party source.

the-stable is licensed AGPL-3.0-or-later (pyproject `license`; publish/LICENSE + publish/NOTICE),
and a curated copy is exported publicly. Per-file SPDX headers make each file's license unambiguous
when it travels apart from the repo root, and keep the non-enclosure commitment cold-verifiable file
by file. This mirrors the worldweaver fork's SPDX pass (worldweaver prune minor 60).

Scope (first-party Python only): src, scripts, research, tests. The top-level `familiar/` souls are
character DATA, not code, and are never stamped; third-party / generated trees (.venv, __pycache__,
node_modules, ...) are never touched. The insert is shebang- and encoding-cookie-aware, BOM-safe, and
idempotent (re-running adds nothing).

    python3 scripts/add_spdx_headers.py            # stamp (idempotent)
    python3 scripts/add_spdx_headers.py --check     # report unstamped, exit 1 if any
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SPDX = "SPDX-License-Identifier: AGPL-3.0-or-later"
COPYRIGHT = "Copyright (C) 2026 Levi Banks"

ROOT = Path(__file__).resolve().parent.parent  # the-stable/

SCOPE = ["src", "scripts", "research", "tests"]
EXCLUDE_PARTS = {"node_modules", "dist", "build", ".venv", "venv", "__pycache__", ".git"}

ENCODING_COOKIE = re.compile(r"^#.*coding[:=]")


def iter_files():
    for rel in SCOPE:
        base = ROOT / rel
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.py")):
            if not p.is_file() or EXCLUDE_PARTS & set(p.parts):
                continue
            yield p


def has_header(text: str) -> bool:
    # Only the first few lines count, so a stray SPDX deeper in a file is not mistaken for the header.
    head = "".join(text.splitlines(keepends=True)[:8])
    return SPDX in head


def stamp(text: str) -> str:
    """Return text with the SPDX header inserted after any shebang / encoding cookie."""
    bom = ""
    if text.startswith("﻿"):
        bom, text = "﻿", text[1:]

    lines = text.splitlines(keepends=True)
    i = 0
    if i < len(lines) and lines[i].startswith("#!"):
        i += 1
    if i < len(lines) and ENCODING_COOKIE.match(lines[i]):
        i += 1

    block = f"# {SPDX}\n# {COPYRIGHT}\n"
    rest = lines[i:]
    if rest and rest[0].strip() != "":  # one blank line before following content
        block += "\n"
    return bom + "".join(lines[:i]) + block + "".join(rest)


def main() -> int:
    ap = argparse.ArgumentParser(description="Idempotently stamp SPDX AGPL headers on first-party source.")
    ap.add_argument("--check", action="store_true", help="report unstamped files and exit 1 if any; change nothing")
    args = ap.parse_args()

    missing, stamped, already = [], [], 0
    for path in iter_files():
        text = path.read_text(encoding="utf-8")
        if has_header(text):
            already += 1
            continue
        if args.check:
            missing.append(path)
            continue
        path.write_text(stamp(text), encoding="utf-8")
        stamped.append(path)

    if args.check:
        if missing:
            print(f"✗ {len(missing)} file(s) missing the SPDX header ({already} already stamped):")
            for p in missing:
                print(f"   {p.relative_to(ROOT)}")
            return 1
        print(f"✓ all {already} first-party source files carry the SPDX header.")
        return 0

    print(f"stamped {len(stamped)} file(s); {already} already had the header.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
