# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""Tests for growth distillation (Major 58, Phase 1)."""

from pathlib import Path

import pytest

import json
import uuid

from src.runtime.drive import DeterministicEmbedder
from src.runtime.growth import (
    CLUSTER_THRESHOLD,
    GROWTH_CAP,
    MIN_CONCORDANCE,
    MIN_DAYS_SPAN,
    distill,
)


def _stage(memory_dir: Path, body: str, *, kind: str = "soul_edit", verdict: str = "accepted", day: int = 1, pulse_id: str = "") -> None:
    ts = f"2026-06-{day:02d}T12:00:00+00:00"
    event = {"event_id": f"evt-{uuid.uuid4().hex[:12]}", "ts": ts, "event_type": "self_delta_staged", "payload": {"kind": kind, "body": body, "verdict": verdict, "pulse_id": pulse_id or f"pls-{body[:8]}", "cast_ts": ts}}
    ledger = memory_dir / "runtime_ledger.jsonl"
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


async def test_no_candidates_no_crash(tmp_path):
    home = tmp_path / "fam"
    (home / "memory").mkdir(parents=True)
    (home / "identity").mkdir(parents=True)
    result = await distill(home, embedder=DeterministicEmbedder())
    assert result["status"] == "no_candidates"
    assert result["promoted"] == 0


async def test_single_day_does_not_promote(tmp_path):
    """Proposals from a single day never meet the MIN_DAYS_SPAN threshold."""
    home = tmp_path / "fam"
    mem = home / "memory"
    mem.mkdir(parents=True)
    (home / "identity").mkdir(parents=True)
    for i in range(5):
        _stage(mem, f"staying on the sill is choosing — iteration {i}", day=1)
    result = await distill(home, embedder=DeterministicEmbedder())
    assert result["status"] == "none_mature"
    assert result["promoted"] == 0
    assert not (home / "identity" / "soul_growth.md").exists()


async def test_concordance_across_days_promotes(tmp_path):
    """Proposals that recur across multiple days meet the threshold and promote."""
    home = tmp_path / "fam"
    mem = home / "memory"
    mem.mkdir(parents=True)
    (home / "identity").mkdir(parents=True)
    _stage(mem, "the proof is in choosing to stay on the sill", day=1, pulse_id="p1")
    _stage(mem, "staying on the sill is the proof — choosing it", day=1, pulse_id="p2")
    _stage(mem, "the sill is the choice — the proof is in the staying", day=2, pulse_id="p3")
    _stage(mem, "choosing to stay on the sill — that is the proof", day=3, pulse_id="p4")
    result = await distill(home, embedder=DeterministicEmbedder())
    assert result["promoted"] >= 1
    growth = (home / "identity" / "soul_growth.md").read_text()
    assert "sill" in growth
    meta_path = home / "identity" / "soul_growth.json"
    assert meta_path.exists()


async def test_dropped_verdicts_ignored(tmp_path):
    """Only 'accepted' proposals are considered; dropped ones are skipped."""
    home = tmp_path / "fam"
    mem = home / "memory"
    mem.mkdir(parents=True)
    (home / "identity").mkdir(parents=True)
    _stage(mem, "staying on the sill is choosing", day=1, verdict="dropped")
    _stage(mem, "staying on the sill is choosing again", day=2, verdict="dropped")
    _stage(mem, "staying on the sill is choosing once more", day=3, verdict="dropped")
    result = await distill(home, embedder=DeterministicEmbedder())
    assert result["status"] == "no_candidates"


async def test_reveries_not_promoted_in_phase1(tmp_path):
    """Phase 1 only promotes soul_edit, not new_reverie or goal_update."""
    home = tmp_path / "fam"
    mem = home / "memory"
    mem.mkdir(parents=True)
    (home / "identity").mkdir(parents=True)
    for day in range(1, 5):
        _stage(mem, f"the quiet holds both the sound and the staying — rev {day}", kind="new_reverie", day=day)
    result = await distill(home, embedder=DeterministicEmbedder())
    assert result["status"] == "no_candidates"


async def test_growth_cap_respected(tmp_path):
    home = tmp_path / "fam"
    mem = home / "memory"
    mem.mkdir(parents=True)
    (home / "identity").mkdir(parents=True)
    # Pre-fill growth to near cap
    growth_path = home / "identity" / "soul_growth.md"
    growth_path.write_text("\n".join(f"existing line {i}" for i in range(GROWTH_CAP - 1)) + "\n")
    # Stage a concordant cluster
    for day in range(1, 4):
        _stage(mem, f"brand new theme about staying day {day}", day=day)
    result = await distill(home, embedder=DeterministicEmbedder())
    lines = [ln for ln in growth_path.read_text().splitlines() if ln.strip()]
    assert len(lines) <= GROWTH_CAP


async def test_idempotent_no_double_promote(tmp_path):
    """Running distill twice doesn't promote the same proposals again."""
    home = tmp_path / "fam"
    mem = home / "memory"
    mem.mkdir(parents=True)
    (home / "identity").mkdir(parents=True)
    for day in range(1, 4):
        _stage(mem, f"the sill is choosing day {day}", day=day, pulse_id=f"p-{day}")
    r1 = await distill(home, embedder=DeterministicEmbedder())
    r2 = await distill(home, embedder=DeterministicEmbedder())
    assert r1["promoted"] >= 1
    assert r2["promoted"] == 0 or r2["status"] in ("no_candidates", "all_deduped")
