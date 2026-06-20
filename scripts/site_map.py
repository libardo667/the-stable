#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""site_map.py — render a static HTML site as legible, formatted text.

A map of where things are and how they connect, so a person (or an agent) can see at a glance
where a new page ought to go and whether the existing site needs finagling to fit it in. Derived
from the files every run, so it can't drift from the real site the way a hand-drawn map would.

For each page it shows: the <title>, the section structure (h1/h2, with their eyebrow tag if any),
the internal pages it links to, the assets it pulls, and a link-graph summary at the end —
including ORPHANS (pages no other page links to) so a freshly-added, not-yet-wired exhibit is
obvious. No dependencies; regex-based and resilient to imperfect markup.

Usage:
  python3 scripts/site_map.py                         # defaults to the hekswerk-site path
  python3 scripts/site_map.py --root /path/to/site    # any static site
  python3 scripts/site_map.py --out site-map.txt      # also write to a file
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

DEFAULT_ROOT = "."
SKIP_DIRS = {".git", "node_modules", "assets", "src-tauri", "__pycache__"}

_title = re.compile(r"<title>(.*?)</title>", re.S | re.I)
_nav = re.compile(r"<nav\b[^>]*>(.*?)</nav>", re.S | re.I)
_href = re.compile(r'href="([^"#?]+\.html)(?:[#?][^"]*)?"', re.I)
_head = re.compile(r"<(h[12])\b[^>]*>(.*?)</\1>", re.S | re.I)
_tag = re.compile(r'<[^>]*class="[^"]*\b(?:section-tag|tag|eyebrow|kicker)\b[^"]*"[^>]*>(.*?)</', re.S | re.I)
_css = re.compile(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', re.I)
_js = re.compile(r'<script[^>]+src="([^"]+)"', re.I)


def _txt(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def _pages(root: Path) -> list[Path]:
    out = []
    for p in sorted(root.rglob("*.html")):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        out.append(p)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Render a static HTML site as a text map.")
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    root = Path(args.root).expanduser().resolve()

    lines: list[str] = []
    w = lines.append
    if not root.exists():
        w(f"(no site at {root})")
        print("\n".join(lines))
        return

    pages = _pages(root)
    links_from: dict[str, set[str]] = {}
    rel_of = {p: p.relative_to(root).as_posix() for p in pages}
    page_set = set(rel_of.values())

    w("=" * 72)
    w(f"SITE MAP  ·  {root}")
    w(f"{len(pages)} page(s)")
    w("=" * 72)

    for p in pages:
        src = p.read_text(encoding="utf-8", errors="replace")
        rel = rel_of[p]
        title = _txt(_title.search(src).group(1)) if _title.search(src) else "(no title)"
        # internal links from this page, resolved relative to the page's folder
        raw = {h for h in _href.findall(src)}
        resolved: set[str] = set()
        for h in raw:
            try:
                tgt = (p.parent / h).resolve().relative_to(root).as_posix()
            except (ValueError, OSError):
                continue
            if tgt != rel:
                resolved.add(tgt)
        links_from[rel] = resolved
        navlinks: set[str] = set()
        for nav in _nav.findall(src):
            navlinks |= set(_href.findall(nav))
        sections = [(_txt(t), lvl) for lvl, t in _head.findall(src) if _txt(t)]
        assets = _css.findall(src) + _js.findall(src)

        w("")
        w(f"📄  {rel}")
        w(f"     title : {title}")
        if navlinks:
            w(f"     nav   → {', '.join(sorted(navlinks))}")
        if sections:
            w("     sections:")
            for t, lvl in sections[:14]:
                w(f"        {'·' if lvl.lower()=='h2' else '#'} {t[:88]}")
        out_links = sorted(l for l in resolved if l in page_set)
        if out_links:
            w(f"     links → {', '.join(out_links)}")
        if assets:
            w(f"     assets: {', '.join(sorted(set(assets)))}")

    # ── link graph summary ──────────────────────────────────────────────
    linked_to: set[str] = set()
    for s in links_from.values():
        linked_to |= s
    orphans = sorted(page_set - linked_to)
    w("")
    w("-" * 72)
    w("LINK GRAPH")
    home = "index.html" if "index.html" in page_set else (sorted(page_set)[0] if page_set else "")
    # reachability from home (BFS over internal links)
    seen, frontier = {home} if home else set(), [home] if home else []
    while frontier:
        cur = frontier.pop()
        for nxt in links_from.get(cur, ()):
            if nxt in page_set and nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    unreached = sorted(page_set - seen)
    w(f"  reachable from {home or '(none)'}: {len(seen)}/{len(page_set)}")
    if unreached:
        w(f"  NOT reachable from {home}: {', '.join(unreached)}")
    if orphans:
        w(f"  orphans (no page links here): {', '.join(orphans)}")
    if not orphans and not unreached:
        w("  every page is linked and reachable.")

    text = "\n".join(lines)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"\n(wrote {args.out})")


if __name__ == "__main__":
    main()
