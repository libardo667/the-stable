#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""A1-elective-READ slice detector — the isolated-Maker analog of worldweaver's choice_points.py.

Operationalizes the PRIMARY metric of `research/preregistrations/2026-06-09-isolated-makers-pen-vs-
substrate-DRAFT.md`. Where worldweaver scores *which established peer R addresses*, this scores
*which established (previously-read) source a Maker elects to return to* — an idiom-immune identity
choice the pen authors, shaped by the unauthored varied files.

Definitions (pre-registration-sensitive — FLAGGED for cold review):

  * READ-ACT = a `pulse_act_emitted` with kind=="do" whose body is a read/open/search over the file
    scope ("read <path>", "opened folder <path>", "looked at <path>", "used search(<q>)"). The SOURCE
    is the path/query head (a file, a folder, or a search topic).
  * ESTABLISHED SOURCE (at tick t) = a source the Maker has already read at some tick < t. A
    revisit-choice is a choice AMONG already-engaged sources.
  * ELECTIVE READ-CHOICE POINT = >=2 established sources available AND the Maker elected to read one of
    them (a choice among already-engaged sources, not a first-encounter or only option).
  * RECENCY-DISCORDANCE of an elective return = the fraction of established candidates MORE recent than
    the elected source — how many more-recent sources the pen SKIPPED. 0.0 = elected the most-recent
    (pure recency); 1.0 = elected the LEAST-recent (pure ANTI-recency). BOTH extremes are
    recency-DETERMINED, just on opposite tails.
  * RECENCY-AMBIGUOUS (the STRONG subset) = discordance in a SYMMETRIC band around 0.5,
    `|disc − 0.5| ≤ w` (w=0.25 pre-committed → band [0.25, 0.75]). These are picks NEITHER a recency
    rule (disc→0) NOR an anti-recency rule (disc→1) strongly predicts — where the substrate, not a
    recency disposition on either tail, plausibly drove the choice. A recency-follower (all disc 0) AND
    an anti-recency-follower (all disc 1) both score 0 here (verified) — closing the feedback-3 §2 hole
    (a one-sided "discordant ≥ τ" subset admitted the anti-recency tail at 100%). This is the
    non-parametric, TWO-SIDED recency control; the full conditional logit (recency as a covariate
    penalized on BOTH sides, McFadden 1974) is the principled robustness backstop, not claimed here.

The strong-subset SIZE sets the pilot K-gate (§4): below K -> INCONCLUSIVE, never FALSE.

Usage:  python3 elective_read_choice.py --ledger <runtime_ledger.jsonl[.gz]> [--ambiguity-width 0.25]
        python3 elective_read_choice.py --selftest
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

# read-act body patterns -> the source string
_READ_PATTERNS = [
    re.compile(r"^read\s+(?P<src>\S+)"),
    re.compile(r"^looked at\s+(?P<src>\S+)"),
    re.compile(r"^opened folder\s+(?P<src>\S+)"),
    re.compile(r"^used\s+search\((?P<src>[^)]+)\)"),
]


def read_source(body: str) -> str | None:
    """The source a read-act elected, or None if the act isn't an elective read.

    Strips a trailing ' page N' so re-reads of the same file at different offsets count as one source.
    A search is keyed by its query head (the topic elected), not the file."""
    b = str(body or "").strip()
    for rx in _READ_PATTERNS:
        m = rx.match(b)
        if m:
            src = m.group("src").strip()
            src = re.sub(r"\s+page\s+\d+$", "", src)  # collapse paged re-reads of one file
            return src or None
    return None


def _iter_events(path: Path) -> list[dict[str, Any]]:
    opener = gzip.open if str(path).endswith(".gz") else open
    out: list[dict[str, Any]] = []
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def _recency_discordance(elected: str, last_seen: dict[str, int], n_candidates: int) -> float:
    """Fraction of established candidates MORE recent than the elected source (the pen skipped them).
    0.0 = the most-recent was elected (recency); 1.0 = the least-recent (anti-recency). `last_seen` maps
    each established source to its last read position; `n_candidates` = established sources at the point."""
    if n_candidates < 2:
        return 0.0
    elected_pos = last_seen.get(elected, -1)
    skipped = sum(1 for s, pos in last_seen.items() if s != elected and pos > elected_pos)
    return skipped / (n_candidates - 1)


def detect_elective_reads(events: list[dict[str, Any]], *, ambiguity_width: float = 0.25) -> dict[str, Any]:
    """Walk a Maker's ledger and count elective + recency-AMBIGUOUS read-choice points.

    The pilot K-gate input is `recency_ambiguous` (the strong subset — discordance within
    `ambiguity_width` of 0.5, symmetric). Also returns the ordered elected sequence (the teacher-forced
    numerator) and `candidate_chance_ceiling` (the headroom reference for verdict(): the mean chance a
    uniform-random pick differs, over the strong subset — the room there WAS to disagree)."""
    last_seen: dict[str, int] = {}        # established source -> its last read position (recency)
    established: set[str] = set()
    total_reads = 0
    pos = 0
    elective: list[dict[str, Any]] = []   # each: {idx, elected, candidates, discordance, ambiguous}
    lo, hi = 0.5 - ambiguity_width, 0.5 + ambiguity_width

    for e in events:
        if str(e.get("event_type") or "") != "pulse_act_emitted":
            continue
        p = e.get("payload") or {}
        if str(p.get("kind") or "") != "do":
            continue
        src = read_source(p.get("body") or "")
        if src is None:
            continue
        total_reads += 1

        # Is THIS read elective? (>=2 established sources available, and `src` is one of them — a return)
        if src in established and len(established) >= 2:
            disc = _recency_discordance(src, last_seen, len(established))
            elective.append({"idx": total_reads, "elected": src, "candidates": len(established),
                             "discordance": round(disc, 4), "ambiguous": lo <= disc <= hi})

        last_seen[src] = pos
        established.add(src)
        pos += 1

    ambiguous = [c for c in elective if c["ambiguous"]]
    # headroom = mean chance a uniform-random pick differs, over the STRONG subset (the room to disagree)
    chance = [(c["candidates"] - 1) / c["candidates"] for c in ambiguous if c["candidates"] >= 2]
    return {
        "total_reads": total_reads,
        "distinct_sources": len(established),
        "elective_points": len(elective),
        "ambiguity_band": [round(lo, 4), round(hi, 4)],
        "recency_ambiguous": len(ambiguous),          # the strong-subset count (the §4 K-gate input)
        "ambiguous_fraction": round(len(ambiguous) / len(elective), 3) if elective else 0.0,
        "mean_discordance": round(sum(c["discordance"] for c in elective) / len(elective), 3) if elective else 0.0,
        "candidate_chance_ceiling": round(sum(chance) / len(chance), 4) if chance else 0.0,
        "points": elective,  # per-choice-point records {idx, elected, candidates, discordance, ambiguous} — lets the replay harness tie each point to its frozen prompt WITHOUT re-deriving the definition (one source of truth)
        "elected_sequence": [c["elected"] for c in elective],                  # teacher-forced numerator
        "ambiguous_sequence": [c["elected"] for c in ambiguous],               # the strong subset
    }


def per_point_disagreement(elected_keep: list[str], elected_swap: list[str]) -> float:
    """The §8 NUMERATOR (teacher-forced): the per-point disagreement rate between two arms scored on the
    SAME recorded choice points — fraction of points where SWAP names a different established source than
    KEEP′. Valid ONLY on teacher-forced-aligned sequences (each pen scored at KEEP's recorded frozen
    points, same length, position i = the same decision). It is NOT valid on free-run sequences, which
    desync upstream and make a single divergence read as many (review feedback-1 §2 — the killer flaw)."""
    n = min(len(elected_keep), len(elected_swap))
    if n == 0:
        return 0.0
    return round(sum(1 for i in range(n) if elected_keep[i] != elected_swap[i]) / n, 4)


# Back-compat alias (the old name); same computation, same teacher-forced-only validity.
elective_distance = per_point_disagreement


def shuffle_null(elected: list[str], *, n: int = 1000, seed: int = 0) -> dict[str, float]:
    """A within-Maker, frequency-preserving label shuffle — `mean = 1 − Σf²` (Gini-Simpson diversity of
    the elected-source distribution): the disagreement if the pen re-elected at random over the same
    REALIZED vocabulary. REPORTED as a FALSE-side reference; NOT a denominator (feedback-2 §3 — dividing
    by it exploded at ~0 under concentration) and NOT the verdict's headroom gate (feedback-3 §3a — the
    realized-sequence ceiling understates the AVAILABLE room to disagree; verdict() uses the
    candidate-chance ceiling instead). Returns mean / std / p95 over n permutations."""
    import random as _random
    import statistics as _stats
    n_pts = len(elected)
    if n_pts < 2:
        return {"mean": 0.0, "std": 0.0, "p95": 0.0, "n_points": n_pts}
    rng = _random.Random(seed)
    dists: list[float] = []
    for _ in range(n):
        perm = elected[:]
        rng.shuffle(perm)  # a permutation -> frequency-preserving by construction
        dists.append(sum(1 for i in range(n_pts) if perm[i] != elected[i]) / n_pts)
    ordered = sorted(dists)
    return {
        "mean": round(_stats.fmean(dists), 4),
        "std": round(_stats.pstdev(dists), 4),
        "p95": round(ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))], 4),
        "n_points": n_pts,
    }


def _wilson_ci(p: float, n: int, z: float) -> tuple[float, float]:
    """Wilson score interval for a proportion — bounded in [0,1] (no negative lower bound / no zero-width
    at p=0), which the Wald interval is not. The standard choice near 0/1 (Brown, Cai & DasGupta 2001),
    exactly the small-disagreement HOLDS regime this design targets (feedback-3 §1a)."""
    if n <= 0:
        return (0.0, 1.0)
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def power_n(power: float, alpha: float, p0: float, p1: float) -> int:
    """One-proportion sample size for an UPPER one-sided non-inferiority test: the n at which a true
    p1 (= floor + δ) is distinguished as exceeding p0 (= floor) with the given power at one-sided α.
    Normal approximation. The α here MUST equal verdict()'s decision α (feedback-3 §1b) — both are the
    one-sided NI α (default 0.05 → z=1.645), so K is powered for the rule that actually decides."""
    if not (0 < p0 < 1 and 0 < p1 < 1) or p1 <= p0:
        return 0
    z_a = _inv_norm(1 - alpha)
    z_b = _inv_norm(power)
    num = z_a * math.sqrt(p0 * (1 - p0)) + z_b * math.sqrt(p1 * (1 - p1))
    return math.ceil((num / (p1 - p0)) ** 2)


def verdict(
    disagree_swap: float,
    n_points: int,
    floor: list[float],
    *,
    delta: float,
    ceiling: float,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """The §8 acceptance rule — NO RATIO (feedback-2 §3). HOLDS is a ONE-SIDED NON-INFERIORITY claim
    (feedback-3 §1c — SWAP agreeing MORE than the same-pen floor is still "no pen effect," so there is no
    lower equivalence bound; this is NOT symmetric TOST/Schuirmann). Decide `disagree(SWAP, KEEP′)`
    against the same-pen KEEP/KEEP′ floor within a committed margin δ = the SESOI (Lakens 2017):

      * INSUFFICIENT_HEADROOM (INCONCLUSIVE) : `floor_mean + δ ≥ ceiling` — the FALSE region sits above
                       the chance disagreement available given the candidate sets, so FALSE is
                       unreachable and the test is not fair. (Uses the CANDIDATE-chance ceiling, not the
                       realized shuffle — feedback-3 §3a.)
      * HOLDS        : the Wilson upper bound of disagree_swap ≤ floor_mean + δ.
      * FALSE        : the Wilson lower bound of disagree_swap > floor_mean + δ.
      * INCONCLUSIVE : the CI straddles the bound (underpowered — see the §4 K-gate).

    The CI is a Wilson interval at a 100(1−α)% one-sided level (`z = Φ⁻¹(1−α)`; α=0.05 → z=1.645), which
    `power_n` powers K for — same α, no decision/power mismatch (feedback-3 §1b). `floor` is the same-pen
    distribution (estimated on points DISJOINT from the swap-scored ones — the peeking firewall); its
    permutation p uses the +1 correction so it is never zero (Phipson & Smyth 2010), reported as a
    diagnostic. Nothing is divided by any null."""
    floor_mean = sum(floor) / len(floor) if floor else 0.0
    bound = floor_mean + delta
    z = _inv_norm(1 - alpha)
    ci_lo, ci_hi = _wilson_ci(disagree_swap, n_points, z)
    perm_p = ((sum(1 for f in floor if f >= disagree_swap) + 1) / (len(floor) + 1)) if floor else None
    if ceiling <= bound:
        v, reason = "INCONCLUSIVE", "insufficient_headroom"
    elif ci_hi <= bound:
        v, reason = "HOLDS", "noninferior_to_floor"
    elif ci_lo > bound:
        v, reason = "FALSE", "exceeds_floor_by_delta"
    else:
        v, reason = "INCONCLUSIVE", "underpowered"
    return {
        "verdict": v,
        "reason": reason,
        "disagree_swap": round(disagree_swap, 4),
        "floor_mean": round(floor_mean, 4),
        "delta": delta,
        "bound": round(bound, 4),
        "ci": [round(ci_lo, 4), round(ci_hi, 4)],
        "candidate_chance_ceiling": round(ceiling, 4),
        "perm_p": round(perm_p, 4) if perm_p is not None else None,
    }


def _inv_norm(p: float) -> float:
    """Acklam's inverse-normal approximation (so verdict()/power_n take any alpha without scipy)."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p <= ph:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)


# --------------------------------------------------------------------------------------------------
_FIXTURE = [  # a tiny synthetic ledger exercising the detector (selftest)
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "read repo/a.py"}},          # first-read a (not elective)
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "opened folder repo/b/"}},   # first-read b
    {"event_type": "anchor_observed", "payload": {"anchors": []}},                                      # ignored
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "read repo/a.py page 2"}},   # ELECTIVE return to a, skip the more-recent b -> disc 1.0 (anti-recency EXTREME -> NOT ambiguous)
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "used search(type inference)"}},  # first-read of a search topic
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "read repo/b/x.py"}},        # b/x.py is a NEW source (folder b != file b/x.py) -> first-read
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "used search(type inference)"}},  # ELECTIVE return to ti (2nd-most-recent of 4) -> disc 0.333 -> AMBIGUOUS (in [0.25,0.75])
    {"event_type": "pulse_act_emitted", "payload": {"kind": "speak", "body": "hello"}},                 # not a read
]

_RECENCY_FOLLOWER = [  # elects only the most-recent (immediate re-reads) -> disc 0 -> 0 ambiguous
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "read a"}},
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "read b"}},
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "read b"}},   # b most-recent -> disc 0
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "read c"}},
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "read c"}},   # c most-recent -> disc 0
]

_ANTI_RECENCY = [  # elects only the LEAST-recent -> disc 1 -> 0 ambiguous (the feedback-3 §2 hole, now closed)
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "read a"}},
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "read b"}},
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "read c"}},
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "read a"}},   # a least-recent -> disc 1.0
    {"event_type": "pulse_act_emitted", "payload": {"kind": "do", "body": "read b"}},   # b least-recent -> disc 1.0
]


def _selftest() -> int:
    r = detect_elective_reads(_FIXTURE, ambiguity_width=0.25)
    assert r["total_reads"] == 6, r
    assert r["distinct_sources"] == 4, r
    assert r["elected_sequence"] == ["repo/a.py", "type inference"], r
    assert r["elective_points"] == 2, r
    # The STRONG subset is recency-AMBIGUOUS (symmetric band). The a-return (disc 1.0 = anti-recency
    # extreme) is EXCLUDED; only the ti-return (disc 0.333, middle) is ambiguous. Assert the field.
    assert r["recency_ambiguous"] == 1, r
    assert r["ambiguous_sequence"] == ["type inference"], r
    assert r["candidate_chance_ceiling"] == round(3 / 4, 4), r  # the ti point had 4 candidates
    # THE FIX (feedback-3 §2), proven on BOTH tails: a recency-follower AND an anti-recency-follower
    # each score 0 in the strong subset. A one-sided "discordant ≥ τ" let the anti-recency tail score 100%.
    rf = detect_elective_reads(_RECENCY_FOLLOWER, ambiguity_width=0.25)
    ar = detect_elective_reads(_ANTI_RECENCY, ambiguity_width=0.25)
    assert rf["elective_points"] == 2 and rf["recency_ambiguous"] == 0, rf
    assert ar["elective_points"] == 2 and ar["recency_ambiguous"] == 0, ar
    assert read_source("read repo/a.py page 7") == "repo/a.py", "paging collapse"
    assert read_source("used search(provenance in safety systems)") == "provenance in safety systems"
    assert read_source("said something") is None
    # teacher-forced per-point disagreement (the §8 numerator) — valid ONLY on aligned sequences
    assert per_point_disagreement(["a", "b"], ["a", "b"]) == 0.0
    assert per_point_disagreement(["a", "b"], ["x", "y"]) == 1.0
    assert per_point_disagreement(["a", "b", "c"], ["a", "x", "c"]) == round(1 / 3, 4)
    assert elective_distance is per_point_disagreement
    # FALSE-side shuffle reference (Gini-Simpson 1-Σf²) — reported, never a denominator/headroom gate
    assert shuffle_null(["a", "a", "a"])["mean"] == 0.0
    assert abs(shuffle_null(["a", "b"], n=2000)["mean"] - 0.5) < 0.06
    # Wilson CI is boundary-respecting where Wald failed (feedback-3 §1a)
    lo0, _ = _wilson_ci(0.02, 150, 1.645)
    assert lo0 >= 0.0, lo0                                        # never negative (Wald gave -0.0024)
    assert _wilson_ci(0.0, 200, 1.645)[1] > 0.0                   # non-zero width at p=0 (Wald gave 0)
    # power_n: α matches the verdict z; reproduces the reviewer's K (floor 0.1, δ 0.15 -> 33)
    assert power_n(0.80, 0.05, 0.10, 0.25) == 33, power_n(0.80, 0.05, 0.10, 0.25)
    assert abs(_inv_norm(1 - 0.05) - 1.6449) < 1e-3              # the decision z and power z_a agree
    # verdict(): NO RATIO, one-sided NI, Wilson CI, candidate-chance headroom guard
    floor = [0.08, 0.10, 0.12, 0.09, 0.11]                       # same-pen floor, mean 0.10
    holds = verdict(0.12, 200, floor, delta=0.15, ceiling=0.60)
    assert holds["verdict"] == "HOLDS" and holds["reason"] == "noninferior_to_floor", holds
    false = verdict(0.55, 200, floor, delta=0.15, ceiling=0.60)
    assert false["verdict"] == "FALSE", false
    incon = verdict(0.28, 25, floor, delta=0.15, ceiling=0.60)
    assert incon["verdict"] == "INCONCLUSIVE" and incon["reason"] == "underpowered", incon
    # concentrated realized sequence BUT ample candidates -> HOLDS via floor (headroom is fine); no division
    conc = verdict(0.02, 150, [0.01, 0.02, 0.03], delta=0.15, ceiling=0.80)
    assert conc["verdict"] == "HOLDS", conc
    # genuinely few candidates -> FALSE unreachable -> INCONCLUSIVE by insufficient headroom (feedback-3 §3a)
    starved = verdict(0.02, 150, [0.01, 0.02, 0.03], delta=0.15, ceiling=0.10)
    assert starved["verdict"] == "INCONCLUSIVE" and starved["reason"] == "insufficient_headroom", starved
    assert false["perm_p"] is not None and false["perm_p"] > 0.0
    print("✓ elective_read_choice selftest passed:",
          {k: r[k] for k in ("elective_points", "recency_ambiguous", "candidate_chance_ceiling")},
          "| recency & anti-recency followers ambiguous:", rf["recency_ambiguous"], ar["recency_ambiguous"],
          "| power_n(.8,.05,.1,.25)=33 | verdict HOLDS/FALSE/INCON/headroom ok")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, help="a Maker's runtime_ledger.jsonl[.gz]")
    ap.add_argument("--ambiguity-width", type=float, default=0.25, help="half-width of the recency-ambiguous band around disc=0.5 (default 0.25 -> [0.25,0.75])")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if not a.ledger:
        ap.error("give --ledger or --selftest")
    r = detect_elective_reads(_iter_events(a.ledger), ambiguity_width=a.ambiguity_width)
    print(json.dumps({k: v for k, v in r.items() if not k.endswith("sequence")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
