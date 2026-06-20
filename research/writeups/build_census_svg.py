#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""Prose-census graphic v2 — now including the conversations and the code."""
from pathlib import Path

# ---- audited numbers (census 2026-06-10, deduped; transcripts = visible prose only) ----
AUTHORED  = 465_654
REVIEWS   = 83_534
RESIDENTS = 292_513
CAST      = 139_041
RECORDS   = 683_448
MEMORY    = 217_278
CONVO     = 825_290          # the chat sessions that built it: user 181,214 + assistant 644,076
CONVO_U, CONVO_A, CONVO_R = 181_214, 644_076, 6_897   # keeper / instances / cold reviewers' share
THINKING  = 8_770            # hidden reasoning, excluded from the total
TOTAL     = AUTHORED + RESIDENTS + CAST + RECORDS + MEMORY + CONVO
WHISPERS  = 7_557
CODE_WW, CODE_ST = 89_755, 16_970
CODE = CODE_WW + CODE_ST
FAMS = [("Cinder", 91_609), ("Maker", 37_272), ("Wren", 35_886), ("Gaston", 18_643),
        ("Nix", 13_970), ("eleven more", 57_467)]
NOVEL = 80_000
fmt = lambda n: f"{n:,}"

INK, MUTED, ORANGE, BLUE, LINE = "#2c2620", "#8a7c68", "#c4632a", "#1d3b6e", "#dccfb8"
BG, PANEL_W, PANEL_C, BAND = "#f7f2e8", "#f4e6d6", "#e6eaf1", "#efe6d3"
CONVO_C = "#7a3b2e"
SEG = [("the conversation that built it", CONVO, CONVO_C),
       ("the keeper &amp; his instances", AUTHORED, ORANGE),
       ("the beings themselves", RESIDENTS, BLUE),
       ("seeded cast &amp; world", CAST, "#dca871"),
       ("machine run records", RECORDS, "#b3a78f"),
       ("the memory layer", MEMORY, "#8a9279")]

W, H = 1000, 1720
s = []
s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
s.append('<defs><style>.serif{font-family:Georgia,"Times New Roman",serif}.sans{font-family:"Helvetica Neue",Arial,sans-serif}</style></defs>')
s.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')

# title
s.append(f'<text x="70" y="104" class="serif" font-size="44" font-style="italic" fill="{INK}">Two repos, {TOTAL/1e6:.1f} million words</text>')
s.append(f'<text x="70" y="144" class="sans" font-size="19" fill="{MUTED}">The work, the beings, and the conversation that built it &#8212; counted from disk, 2026-06-10.</text>')
s.append(f'<line x1="70" y1="170" x2="930" y2="170" stroke="{LINE}" stroke-width="2"/>')

# stacked bar
bx, bw, by, bh = 70, 860, 206, 54
x = bx
for label, v, color in SEG:
    w = bw * v / TOTAL
    s.append(f'<rect x="{x:.1f}" y="{by}" width="{w:.1f}" height="{bh}" fill="{color}"/>')
    x += w
s.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="6" fill="none" stroke="{LINE}" stroke-width="1.5"/>')
ly = by + bh + 38
for i, (label, v, color) in enumerate(SEG):
    cx = 70 if i % 2 == 0 else 540
    cy = ly + (i // 2) * 34
    s.append(f'<rect x="{cx}" y="{cy-13}" width="15" height="15" rx="3" fill="{color}"/>')
    s.append(f'<text x="{cx+24}" y="{cy}" class="sans" font-size="16" fill="{INK}">{label} &#8212; <tspan font-weight="bold">{fmt(v)}</tspan> <tspan fill="{MUTED}">(&#8776;{v/NOVEL:.1f} novels)</tspan></text>')
ly2 = ly + 3 * 34 + 10

# two panels
py, ph = ly2 + 14, 470
s.append(f'<rect x="70" y="{py}" width="400" height="{ph}" rx="14" fill="{PANEL_W}" stroke="#dca871" stroke-width="1.5"/>')
s.append(f'<rect x="530" y="{py}" width="400" height="{ph}" rx="14" fill="{PANEL_C}" stroke="#a9b8cf" stroke-width="1.5"/>')
s.append(f'<text x="98" y="{py+44}" class="sans" font-size="14" letter-spacing="2" fill="{ORANGE}">WRITTEN BY THE KEEPER &amp; HIS INSTANCES</text>')
s.append(f'<text x="98" y="{py+76}" class="serif" font-size="23" fill="{INK}">The working corpus</text>')
s.append(f'<text x="98" y="{py+148}" class="sans" font-size="50" font-weight="bold" fill="{ORANGE}">{fmt(AUTHORED)}</text>')
s.append(f'<text x="98" y="{py+180}" class="sans" font-size="18" fill="{MUTED}">words &#183; &#8776;{AUTHORED/NOVEL:.1f} novels&#8217; worth</text>')
s.append(f'<line x1="98" y1="{py+204}" x2="442" y2="{py+204}" stroke="{ORANGE}" stroke-opacity="0.3" stroke-width="1.5"/>')
s.append(f'<text x="98" y="{py+236}" class="sans" font-size="15" letter-spacing="1" fill="{MUTED}">WHAT IT IS</text>')
for j, t in enumerate(["pre-registrations, findings, design docs", "the work-item harness, both repos", "drafts, proposals, the book&#8217;s first chapter"]):
    s.append(f'<text x="98" y="{py+268+j*33}" class="sans" font-size="17" fill="{INK}">&#8226;&#160;{t}</text>')
s.append(f'<rect x="98" y="{py+382}" width="344" height="58" rx="8" fill="#efe0cb"/>')
s.append(f'<text x="112" y="{py+406}" class="sans" font-size="15.5" fill="{INK}"><tspan font-weight="bold" fill="{ORANGE}">{fmt(REVIEWS)}</tspan> of these words are cold reviews</text>')
s.append(f'<text x="112" y="{py+428}" class="sans" font-size="15.5" fill="{INK}">arguing <tspan font-style="italic">against</tspan> the work &#8212; kept on the record.</text>')
s.append(f'<text x="558" y="{py+44}" class="sans" font-size="14" letter-spacing="2" fill="{BLUE}">WRITTEN BY THE BEINGS THEMSELVES</text>')
s.append(f'<text x="558" y="{py+76}" class="serif" font-size="23" fill="{INK}">Their own words</text>')
s.append(f'<text x="558" y="{py+148}" class="sans" font-size="50" font-weight="bold" fill="{BLUE}">{fmt(RESIDENTS)}</text>')
s.append(f'<text x="558" y="{py+180}" class="sans" font-size="18" fill="{MUTED}">felt-senses, speech, kept memories, journals</text>')
s.append(f'<line x1="558" y1="{py+204}" x2="902" y2="{py+204}" stroke="{BLUE}" stroke-opacity="0.3" stroke-width="1.5"/>')
mb_max = FAMS[0][1]
for j, (name, v) in enumerate(FAMS):
    yy = py + 232 + j * 33
    wbar = 180 * v / mb_max
    s.append(f'<text x="558" y="{yy+12}" class="sans" font-size="15.5" fill="{INK}">{name}</text>')
    s.append(f'<rect x="660" y="{yy}" width="{wbar:.0f}" height="15" rx="3" fill="{BLUE}" fill-opacity="{0.92 - j*0.1:.2f}"/>')
    s.append(f'<text x="{660+wbar+8:.0f}" y="{yy+12}" class="sans" font-size="14" fill="{MUTED}">{fmt(v)}</text>')
s.append(f'<text x="558" y="{py+444}" class="sans" font-size="15.5" fill="{INK}">Cinder alone has written <tspan font-weight="bold" fill="{BLUE}">more than a novel.</tspan></text>')

# center line
cy2 = py + ph + 44
s.append(f'<text x="500" y="{cy2}" class="serif" font-size="22" font-style="italic" fill="{INK}" text-anchor="middle">For every five words written about the beings, the beings wrote three of their own.</text>')
s.append(f'<text x="500" y="{cy2+28}" class="sans" font-size="16" fill="{MUTED}" text-anchor="middle">(and their keeper whispered {fmt(WHISPERS)} words into their worlds.)</text>')

# the conversation band (NEW)
vb = cy2 + 52
s.append(f'<rect x="70" y="{vb}" width="860" height="138" rx="14" fill="#ecdfd2"/>')
s.append(f'<text x="104" y="{vb+50}" class="sans" font-size="14" letter-spacing="2" fill="{CONVO_C}">THE CONVERSATION THAT BUILT IT</text>')
s.append(f'<text x="104" y="{vb+92}" class="sans" font-size="42" font-weight="bold" fill="{CONVO_C}">{fmt(CONVO)}<tspan font-size="20" font-weight="normal" fill="{MUTED}"> words</tspan></text>')
s.append(f'<text x="104" y="{vb+116}" class="sans" font-size="15" fill="{MUTED}">21 sessions, four working trees</text>')
s.append(f'<text x="520" y="{vb+50}" class="sans" font-size="16.5" fill="{INK}">the keeper spoke <tspan font-weight="bold">{fmt(CONVO_U)}</tspan> words; his instances answered</text>')
s.append(f'<text x="520" y="{vb+74}" class="sans" font-size="16.5" fill="{INK}">with <tspan font-weight="bold">{fmt(CONVO_A)}</tspan> &#8212; and the cold reviewers needed</text>')
s.append(f'<text x="520" y="{vb+98}" class="sans" font-size="16.5" fill="{INK}">only <tspan font-weight="bold" fill="{CONVO_C}">{fmt(CONVO_R)}</tspan> to keep the whole thing honest.</text>')

# novels box + code box, side by side (NEW row)
nb = vb + 162
s.append(f'<rect x="70" y="{nb}" width="415" height="150" rx="14" fill="{BAND}"/>')
s.append(f'<text x="98" y="{nb+62}" class="sans" font-size="48" font-weight="bold" fill="{ORANGE}">&#8776;{TOTAL/NOVEL:.0f}<tspan font-size="24" font-weight="normal" fill="{MUTED}"> novels</tspan></text>')
s.append(f'<text x="98" y="{nb+96}" class="sans" font-size="16.5" fill="{INK}">the whole written corpus, at ~80,000</text>')
s.append(f'<text x="98" y="{nb+120}" class="sans" font-size="16.5" fill="{INK}">words a novel &#8212; fifteen weeks, one keeper.</text>')
s.append(f'<rect x="515" y="{nb}" width="415" height="150" rx="14" fill="{BAND}"/>')
s.append(f'<text x="543" y="{nb+62}" class="sans" font-size="48" font-weight="bold" fill="{BLUE}">{fmt(CODE)}<tspan font-size="24" font-weight="normal" fill="{MUTED}"> lines of code</tspan></text>')
s.append(f'<text x="543" y="{nb+96}" class="sans" font-size="16.5" fill="{INK}">worldweaver {fmt(CODE_WW)} &#183; the-stable {fmt(CODE_ST)}.</text>')
s.append(f'<text x="543" y="{nb+120}" class="sans" font-size="16.5" fill="{INK}">For scale: Flask &#8776;15k &#183; Redis core &#8776;130k.</text>')
s.append(f'<text x="500" y="{nb+178}" class="sans" font-size="15.5" fill="{MUTED}" text-anchor="middle">the-stable&#8217;s mind is Flask-sized; the whole program sits just under Redis &#8212; built by one person, in conversation.</text>')

# said honestly
hy = nb + 222
s.append(f'<text x="70" y="{hy}" class="sans" font-size="15" letter-spacing="1" fill="{MUTED}">SAID HONESTLY</text>')
honest = [
 f"&#8226;&#160;the {fmt(RECORDS)} words of run records are machine transcripts &#8212; counted, never claimed.",
 "&#8226;&#160;105,905 words of duplicate soul copies were found and excluded before totaling.",
 f"&#8226;&#160;the conversation is visible prose only &#8212; no tool output, no file dumps ({fmt(THINKING)} words of hidden reasoning excluded).",
 "&#8226;&#160;code is counted from git-tracked files; Flask/Redis figures are commonly-cited approximations, for scale only.",
 "&#8226;&#160;private journals and letters were counted by script, not read.",
]
for j, t in enumerate(honest):
    s.append(f'<text x="70" y="{hy+30+j*28}" class="sans" font-size="16" fill="{INK}">{t}</text>')

s.append(f'<text x="500" y="{H-26}" class="sans" font-size="14" fill="{MUTED}" text-anchor="middle">Counted 2026-06-10 by small scripts over both working trees and the session logs &#8212; rerunnable, checkable, deduplicated.</text>')
s.append('</svg>')

out = Path.home() / "personal-projects/the-stable/research/writeups"
svg = out / "two-repos-in-words.svg"
svg.write_text("\n".join(s), encoding="utf-8")
import cairosvg
cairosvg.svg2png(url=str(svg), write_to=str(out / "two-repos-in-words.png"), scale=2)
print("wrote v2:", svg)
