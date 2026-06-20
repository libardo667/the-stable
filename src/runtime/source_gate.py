# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""source_gate.py — the source-grounding gate for epistemic familiars (Major 67).

An epistemic familiar's committed act may not present a concrete source-specific (a
filename, a quoted span, a date, a line number) as *shown* unless that specific appears
verbatim in the bytes the familiar actually read this ignition. Unverified specifics are
downgraded to a "suspected (unverified)" marker, or stripped, while the surrounding gist
is kept. Abstain over invent.

This is a MECHANICAL check on output text against read bytes. No LLM, no extended thinking,
no cognitive-mode change: Major 67 ships the gate; thinking-enablement is a separate, fenced
item. The gate matches against the SOURCE bytes, never the model's claim or its reasoning,
so a confabulated specific can never bless itself.

Pure and synchronous, so it is unit-testable in isolation and fork-portable (the worldweaver
reconvergence, Major 76, calls the same function). v1 verifies quoted spans, file paths, and
ISO dates verbatim; line numbers are downgraded only when the whole act grounded nothing
(offset-aware line verification is a later slice).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReadRecord:
    """One thing the familiar actually read this ignition: the raw result bytes plus a
    human-readable pointer to where they came from (the tool call it made). ``truncated``
    flags a read the tool cut off, so a specific that would fall outside the captured window
    cannot be silently treated as verified."""

    pointer: str
    text: str
    truncated: bool = False


@dataclass
class GateResult:
    """The gated act body plus a provenance report (for the ledger)."""

    body: str
    verified: list[str] = field(default_factory=list)
    downgraded: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.downgraded)


# Tolerant matching: normalize quote style and collapse whitespace, but never case or content.
# A paraphrase still fails; only a contiguous verbatim run (modulo whitespace and curly/straight
# quotes) passes.
_CURLY = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})
_WS = re.compile(r"\s+")

_KNOWN_EXT = "py|js|ts|tsx|jsx|md|txt|json|jsonl|sql|toml|ya?ml|sh|csv|html|css|cfg|ini"
_QUOTE_RX = re.compile(r'"([^"]{3,})"|`([^`]{3,})`|“([^”]{3,})”')
_PATH_RX = re.compile(r"(?<![\w/])(?:[\w.\-]+/)*[\w.\-]+\.(?:" + _KNOWN_EXT + r")\b")
_DATE_RX = re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)")
_LINE_RX = re.compile(r"\blines?\s+\d+(?:\s*[-–—]\s*\d+)?\b", re.I)

_MARK_QUOTE = "(suspected, unverified: a quoted span not found in what I read)"


def _norm(s: str) -> str:
    return _WS.sub(" ", s.translate(_CURLY)).strip()


def ground_specifics(act_body: str, read_corpus: list[ReadRecord]) -> GateResult:
    """Gate one epistemic act body against the bytes read this ignition.

    Returns the rewritten body (verified specifics intact, unverifiable ones downgraded to a
    suspected marker) and a provenance report. The caller decides who is epistemic; this
    function makes no such judgment, and on a body with no source-specifics it is a no-op."""
    body = act_body or ""
    corpus = _norm(" \n ".join(r.text for r in read_corpus))
    pointers = " \n ".join(r.pointer for r in read_corpus)
    result = GateResult(body=body)

    def _grounded(span: str) -> bool:
        n = _norm(span)
        return bool(n) and n in corpus

    # 1) quoted spans — the core confabulation vector. A claimed quote must exist verbatim.
    def _on_quote(m: "re.Match[str]") -> str:
        inner = next(g for g in m.groups() if g is not None)
        whole = m.group(0)
        if _grounded(inner):
            result.verified.append(whole)
            return whole
        result.downgraded.append(whole)
        return _MARK_QUOTE

    body = _QUOTE_RX.sub(_on_quote, body)

    # 2) file paths — grounded if the familiar read that file (its pointer) or it appears in the bytes.
    def _on_path(m: "re.Match[str]") -> str:
        p = m.group(0)
        if p in corpus or p in pointers:
            result.verified.append(p)
            return p
        result.downgraded.append(p)
        return f"{p} (unverified: not among what I read)"

    body = _PATH_RX.sub(_on_path, body)

    # 3) ISO dates presented as source facts.
    def _on_date(m: "re.Match[str]") -> str:
        d = m.group(0)
        if d in corpus:
            result.verified.append(d)
            return d
        result.downgraded.append(d)
        return f"{d} (unverified)"

    body = _DATE_RX.sub(_on_date, body)

    # 4) line numbers — v1 cannot verify a line offset against raw bytes. Only downgrade them when
    #    the whole act grounded nothing (then its line numbers are invented too); a grounded act keeps
    #    its line refs until offset-aware verification lands (a later slice). Report, do not gag.
    if not result.verified:

        def _on_line(m: "re.Match[str]") -> str:
            ref = m.group(0)
            result.downgraded.append(ref)
            return f"{ref} (line not verified)"

        body = _LINE_RX.sub(_on_line, body)

    result.body = body
    return result
