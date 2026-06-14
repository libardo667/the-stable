"""Growth distillation: promote staged self-delta proposals to the growth soul.

Phase 1 of Major 58. A periodic step (called at daemon shutdown) that reads
accepted soul_edit proposals from the ledger, clusters them by semantic
similarity, applies a concordance threshold, and appends the mature ones to
identity/soul_growth.md — completing the pipeline the constitution gate started.

The concordance threshold (≥N proposals spanning ≥2 calendar days) prevents a
single runaway pulse session from rewriting the growth soul. A theme must recur
across separate waking periods to be promoted — the familiar has to keep coming
back to it.
"""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.identity.loader import IdentityLoader
from src.runtime.ledger import append_runtime_event, load_runtime_events

logger = logging.getLogger(__name__)

MIN_CONCORDANCE = 3
MIN_DAYS_SPAN = 2
CLUSTER_THRESHOLD = 0.70
GROWTH_CAP = 20
DEDUP_THRESHOLD = 0.85


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))


def _l2norm(vec: list[float]) -> list[float]:
    mag = math.sqrt(sum(x * x for x in vec))
    return [x / mag for x in vec] if mag > 0.0 else vec


def _day_key(ts: str) -> str:
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return ""


def _load_metadata(home_dir: Path) -> dict[str, Any]:
    path = IdentityLoader.growth_metadata_path(home_dir)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"promoted_pulse_ids": [], "last_distillation": None, "lines": []}


def _save_metadata(home_dir: Path, meta: dict[str, Any]) -> None:
    path = IdentityLoader.growth_metadata_path(home_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


async def distill(home_dir: Path, embedder: Any = None) -> dict[str, Any]:
    """Run one distillation pass over a familiar's staged self-deltas.

    Reads accepted soul_edit proposals from the ledger, clusters by semantic
    similarity, and promotes themes that meet the concordance threshold to
    identity/soul_growth.md. Returns a summary dict for logging.
    """
    memory_dir = home_dir / "memory"
    if not memory_dir.is_dir():
        return {"status": "no_memory", "promoted": 0}

    if embedder is None:
        from src.runtime.drive import DeterministicEmbedder
        embedder = DeterministicEmbedder()

    meta = _load_metadata(home_dir)
    promoted_ids = set(meta.get("promoted_pulse_ids") or [])

    events = load_runtime_events(memory_dir)
    candidates: list[dict[str, Any]] = []
    for e in events:
        if e.get("event_type") != "self_delta_staged":
            continue
        p = e.get("payload") or {}
        if p.get("verdict") != "accepted" or p.get("kind") != "soul_edit":
            continue
        pulse_id = p.get("pulse_id", "")
        if pulse_id in promoted_ids:
            continue
        body = str(p.get("body") or "").strip()
        if not body:
            continue
        ts = str(e.get("ts") or p.get("cast_ts") or "")
        candidates.append({"body": body, "pulse_id": pulse_id, "ts": ts, "day": _day_key(ts)})

    if not candidates:
        return {"status": "no_candidates", "promoted": 0}

    # Embed all candidate bodies
    vecs = await embedder.embed([c["body"] for c in candidates])
    for c, v in zip(candidates, vecs):
        c["vec"] = _l2norm(v)

    # Greedy clustering by cosine similarity
    assigned = [False] * len(candidates)
    clusters: list[list[int]] = []
    for i in range(len(candidates)):
        if assigned[i]:
            continue
        cluster = [i]
        assigned[i] = True
        for j in range(i + 1, len(candidates)):
            if assigned[j]:
                continue
            if _cosine(candidates[i]["vec"], candidates[j]["vec"]) >= CLUSTER_THRESHOLD:
                cluster.append(j)
                assigned[j] = True
        clusters.append(cluster)

    # Apply concordance threshold
    mature: list[list[int]] = []
    for cluster in clusters:
        if len(cluster) < MIN_CONCORDANCE:
            continue
        days = {candidates[i]["day"] for i in cluster if candidates[i]["day"]}
        if len(days) < MIN_DAYS_SPAN:
            continue
        mature.append(cluster)

    if not mature:
        return {
            "status": "none_mature",
            "promoted": 0,
            "candidates": len(candidates),
            "clusters": len(clusters),
            "note": f"no cluster met concordance (≥{MIN_CONCORDANCE} proposals across ≥{MIN_DAYS_SPAN} days)",
        }

    # Dedup against existing growth lines
    growth_path = IdentityLoader.growth_soul_path(home_dir)
    existing_lines = [ln.strip() for ln in growth_path.read_text(encoding="utf-8").splitlines() if ln.strip()] if growth_path.exists() else []
    existing_vecs = [_l2norm(v) for v in await embedder.embed(existing_lines)] if existing_lines else []

    new_lines: list[str] = []
    new_pulse_ids: list[str] = []
    promoted_details: list[dict[str, Any]] = []

    for cluster in mature:
        if len(existing_lines) + len(new_lines) >= GROWTH_CAP:
            break
        members = [candidates[i] for i in cluster]
        latest_day = max(m["day"] for m in members if m["day"])
        latest = [m for m in members if m["day"] == latest_day]
        representative = max(latest, key=lambda m: len(m["body"]))

        if existing_vecs and any(_cosine(representative["vec"], ev) >= DEDUP_THRESHOLD for ev in existing_vecs):
            continue

        new_lines.append(representative["body"])
        cluster_ids = [candidates[i]["pulse_id"] for i in cluster if candidates[i]["pulse_id"]]
        new_pulse_ids.extend(cluster_ids)
        promoted_details.append({
            "line": representative["body"],
            "cluster_size": len(cluster),
            "days": sorted({candidates[i]["day"] for i in cluster if candidates[i]["day"]}),
            "source_pulse_ids": cluster_ids,
        })

    if not new_lines:
        return {"status": "all_deduped", "promoted": 0, "candidates": len(candidates)}

    # Append to soul_growth.md
    all_lines = existing_lines + new_lines
    growth_path.parent.mkdir(parents=True, exist_ok=True)
    growth_path.write_text("\n".join(all_lines) + "\n", encoding="utf-8")

    # Update metadata
    meta["promoted_pulse_ids"] = list(promoted_ids | set(new_pulse_ids))
    meta["last_distillation"] = datetime.now(timezone.utc).isoformat()
    prior = meta.get("lines") or []
    meta["lines"] = [{"line": d["line"], "cluster_size": d["cluster_size"], "days": d["days"]} for d in promoted_details] + prior
    _save_metadata(home_dir, meta)

    # Log growth_promoted events
    for detail in promoted_details:
        append_runtime_event(memory_dir, event_type="growth_promoted", payload={"line": detail["line"], "cluster_size": detail["cluster_size"], "days": detail["days"], "source_pulse_ids": detail["source_pulse_ids"][:10]})

    logger.info("[%s] growth: promoted %d line(s) from %d candidates (%d clusters, %d mature)", home_dir.name, len(new_lines), len(candidates), len(clusters), len(mature))
    return {"status": "promoted", "promoted": len(new_lines), "candidates": len(candidates), "clusters": len(clusters), "mature_clusters": len(mature), "lines": [d["line"][:80] for d in promoted_details]}
