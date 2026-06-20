#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""Census of authored prose across worldweaver + the-stable (+ the cognition tree).

Lanes per repo:
  tracked   — md/txt prose committed to git (docs, research, preregs, souls, reviews)
  untracked — private md/txt prose (improvements/, inspiration/, drafts, desks)
  residents — the beings' OWN words: pulse felt-senses, speech, kept memories,
              workshop journals (gifts and keeper whispers excluded; whispers counted aside)

Dedupe: ww runs keep checkpoint/portrait copies of the same ledgers — prefer one
canonical ledgers dir per run. the-stable: maker's void-run residue counted once
(its home was reset; .runs snapshots of the same ledger skipped).
"""
import json, re, subprocess
from pathlib import Path

HOME = Path.home() / "personal-projects"
WW, ST = HOME / "worldweaver", HOME / "the-stable"
MM = HOME / "memory-management"

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".runs", "target"}

def words(s: str) -> int:
    return len(re.findall(r"\S+", s or ""))

def tracked_files(repo: Path) -> set[str]:
    out = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True).stdout
    return set(ln.strip() for ln in out.splitlines() if ln.strip())

def md_walk(root: Path, skip_parts=()):
    for p in root.rglob("*"):
        if p.suffix.lower() not in (".md", ".txt"):
            continue
        parts = set(p.parts)
        if parts & SKIP_DIRS or any(sp in p.parts for sp in skip_parts):
            continue
        yield p

def count_md(paths) -> int:
    total = 0
    for p in paths:
        try:
            total += words(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    return total

# ---- resident-word extractors --------------------------------------------
def ledger_words(path: Path) -> int:
    """Pulse felt-senses + speak-act bodies — the being's own authored output."""
    n = 0
    try:
        for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                e = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if e.get("event_type") != "pulse_emitted":
                continue
            pulse = (e.get("payload") or {}).get("pulse") or {}
            n += words(str(pulse.get("felt_sense") or ""))
            act = pulse.get("act") or {}
            if act.get("kind") == "speak":
                n += words(str(act.get("body") or ""))
    except OSError:
        pass
    return n

def jsonl_field_words(path: Path, fields=("text", "note")) -> int:
    n = 0
    try:
        for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                e = json.loads(ln)
            except json.JSONDecodeError:
                continue
            for f in fields:
                v = e.get(f)
                if isinstance(v, str):
                    n += words(v)
    except OSError:
        pass
    return n

def familiar_home_words(home: Path) -> dict:
    """One familiar's own words from a home dir (live or archived residue)."""
    r = {"ledger": 0, "voice": 0, "kept": 0, "workshop": 0, "whispers": 0}
    led = home / "memory" / "runtime_ledger.jsonl"
    if led.exists():
        r["ledger"] = ledger_words(led)
    v = home / "voice.jsonl"
    if v.exists():
        r["voice"] = jsonl_field_words(v, ("text",))
    k = home / "memory" / "kept_memory.jsonl"
    if k.exists():
        r["kept"] = jsonl_field_words(k, ("note", "text"))
    ws = home / "workshop"
    if ws.is_dir():
        r["workshop"] = count_md(p for p in ws.rglob("*.md") if "given" not in p.parts)
    wh = home / "whispers.jsonl"
    if wh.exists():
        r["whispers"] = jsonl_field_words(wh, ("text",))
    return r

# ============================ the-stable ====================================
st_tracked_set = tracked_files(ST)
st_tracked = count_md(ST / f for f in st_tracked_set if f.endswith((".md", ".txt")))

# untracked private prose: md/txt not in git, excluding familiar living runtime (resident lane)
st_untracked_paths = []
for p in md_walk(ST):
    rel = p.relative_to(ST).as_posix()
    if rel in st_tracked_set:
        continue
    if rel.startswith("familiar/") and any(seg in rel for seg in ("/workshop/", "/letters/", "/memory/")):
        continue  # resident lane / runtime, not project prose
    st_untracked_paths.append(p)
st_untracked = count_md(st_untracked_paths)

# residents: every familiar home + maker's archived void-run residue (home was reset)
st_res, st_whisp = {}, 0
for fam in sorted((ST / "familiar").iterdir()):
    if not fam.is_dir() or fam.name == "portrait" or not (fam / "identity").is_dir():
        continue
    r = familiar_home_words(fam)
    st_whisp += r.pop("whispers")
    st_res[fam.name] = sum(r.values())
residue = ST / ".runs" / "pilot-void-20260610-racing" / "maker-runtime-residue"
if residue.is_dir():
    r = familiar_home_words(residue)
    st_whisp += r.pop("whispers")
    st_res["maker"] = st_res.get("maker", 0) + sum(r.values())
st_residents = sum(st_res.values())

# reviews callout (subset of tracked)
st_reviews = count_md((ST / f) for f in st_tracked_set if f.startswith("research/mr-review-history/") and f.endswith(".md"))

# ============================ worldweaver ===================================
ww_tracked_set = tracked_files(WW)
ww_tracked = count_md(WW / f for f in ww_tracked_set if f.endswith((".md", ".txt")))

ww_untracked_paths = []
for p in md_walk(WW, skip_parts=("ledgers", "kept_memory")):
    rel = p.relative_to(WW).as_posix()
    if rel in ww_tracked_set:
        continue
    ww_untracked_paths.append(p)
ww_untracked = count_md(ww_untracked_paths)

# residents: one canonical ledgers dir per run + kept_memory dirs (dedup checkpoints/portraits)
ww_residents = 0
runs = WW / "research" / "runs"
if runs.is_dir():
    for run in sorted(runs.iterdir()):
        if not run.is_dir():
            continue
        led_dirs = [d for d in run.rglob("ledgers") if d.is_dir()]
        # prefer evidence/ledgers; else top-level; else first found — exactly ONE per run
        led_dirs.sort(key=lambda d: (0 if d.parent.name == "evidence" and "portraits" not in d.parts else
                                     1 if d.parent == run else 2, len(d.parts)))
        if led_dirs:
            canon = led_dirs[0]
            for f in canon.rglob("*.jsonl"):
                ww_residents += ledger_words(f)
        for km in run.rglob("kept_memory"):
            if km.is_dir() and "portraits" not in km.parts and "checkpoint" not in str(km):
                for f in km.glob("*.jsonl"):
                    ww_residents += jsonl_field_words(f, ("note", "text"))

# review prose callout (tracked review-bundle + untracked review-archive)
ww_reviews = count_md((WW / f) for f in ww_tracked_set if "review" in f and f.endswith(".md"))
ww_reviews += count_md(md_walk(WW / "review-archive")) if (WW / "review-archive").is_dir() else 0

# ======================== the cognition tree ================================
mm_words = count_md(md_walk(MM)) if MM.is_dir() else 0

out = {
    "worldweaver": {"tracked": ww_tracked, "untracked": ww_untracked, "residents": ww_residents, "reviews_within": ww_reviews},
    "the-stable": {"tracked": st_tracked, "untracked": st_untracked, "residents": st_residents, "reviews_within": st_reviews,
                   "per_familiar": dict(sorted(st_res.items(), key=lambda kv: -kv[1])), "keeper_whispers": st_whisp},
    "cognition-tree": mm_words,
}
out["totals"] = {
    "project_prose": ww_tracked + ww_untracked + st_tracked + st_untracked,
    "resident_words": ww_residents + st_residents,
    "everything": ww_tracked + ww_untracked + st_tracked + st_untracked + ww_residents + st_residents + mm_words,
}
print(json.dumps(out, indent=2))
