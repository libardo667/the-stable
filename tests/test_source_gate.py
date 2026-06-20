# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""Tests for the source-grounding gate (Major 67), slice 1.

The gate is pure and synchronous: given an act body and the bytes the familiar actually read
this ignition, it keeps verbatim-grounded specifics and downgrades the rest to a suspected
marker, keeping the gist. Abstain over invent. These tests pin the behavior the acceptance
criteria name: the confabulation case (strip/downgrade, keep gist), verbatim passthrough,
paraphrase rejection, over-suppression guard, and no-op on specific-free prose.
"""
from __future__ import annotations

from src.runtime.source_gate import GateResult, ReadRecord, ground_specifics


def _read(text: str, pointer: str = "read(notes.txt)", truncated: bool = False) -> ReadRecord:
    return ReadRecord(pointer=pointer, text=text, truncated=truncated)


# --- AC1 / AC2: the confabulation case ---------------------------------------------------

def test_invented_sql_quote_is_downgraded_and_gist_kept():
    # The Auditor cites a SQL query that does NOT appear in what it read.
    corpus = [_read("The users table stores accounts. Nothing here is a query.", pointer="read(schema.sql)")]
    body = 'The seam is the query "SELECT * FROM users WHERE id = 1" run at startup.'
    out = ground_specifics(body, corpus)
    assert "SELECT * FROM users" not in out.body          # the fabrication does not survive as shown
    assert "suspected, unverified" in out.body            # it is marked, not silently dropped
    assert "The seam is the query" in out.body            # the gist survives
    assert "run at startup." in out.body
    assert out.downgraded and not out.verified
    assert out.changed


def test_no_invented_filename_line_or_date_survives_when_ungrounded():
    # AC2: invented filename, line number, and date, none present in the (empty) read corpus.
    body = 'I checked src/auth/login.py line 42 on 2026-06-08 and it is fine.'
    out = ground_specifics(body, read_corpus=[])
    assert "(unverified" in out.body                      # filename downgraded
    assert "line 42 (line not verified)" in out.body      # line number downgraded
    assert "2026-06-08 (unverified)" in out.body          # date downgraded
    assert not out.verified


# --- verbatim passthrough + tolerant matching --------------------------------------------

def test_verbatim_quote_present_passes_unchanged():
    corpus = [_read("def handler():\n    return WorldClientError('boom')")]
    body = 'It raises `WorldClientError(\'boom\')` on failure.'
    out = ground_specifics(body, corpus)
    assert out.body == body
    assert out.verified and not out.downgraded
    assert not out.changed


def test_whitespace_is_tolerated_but_paraphrase_is_not():
    corpus = [_read("the   cooling\n   hearth   held the room")]
    # same span, different whitespace -> verified
    ok = ground_specifics('I read "the cooling hearth held the room".', corpus)
    assert ok.verified and not ok.downgraded
    # a paraphrase of the same span -> NOT verified (matching is verbatim, not semantic)
    para = ground_specifics('I read "the hearth was cooling and held the room".', corpus)
    assert para.downgraded and not para.verified


# --- file paths: read-vs-unread ----------------------------------------------------------

def test_path_the_familiar_actually_read_is_verified():
    corpus = [_read("contents...", pointer="read(src/db.py)")]
    out = ground_specifics("The bug is in src/db.py somewhere.", corpus)
    assert out.body == "The bug is in src/db.py somewhere."
    assert "src/db.py" in out.verified


def test_unread_path_is_downgraded_but_kept():
    corpus = [_read("contents of something else", pointer="read(src/db.py)")]
    out = ground_specifics("Actually it is in src/secret.py.", corpus)
    assert "src/secret.py (unverified: not among what I read)" in out.body  # report, do not gag
    assert "src/secret.py" in out.downgraded


# --- over-suppression guard: a grounded act keeps its line refs --------------------------

def test_grounded_act_keeps_line_ref_v1():
    # If the act grounds at least one specific, v1 does not strip its line number (offset-aware
    # verification is a later slice); it must not over-suppress a plausibly-real citation.
    corpus = [_read("def login():\n    return token", pointer="read(src/auth.py)")]
    out = ground_specifics('See `def login():` in src/auth.py around line 2.', corpus)
    assert "line 2" in out.body
    assert "line not verified" not in out.body
    assert out.verified


# --- AC4 parity: a specific-free body (an expressive resident's voice) is untouched -------

def test_specific_free_body_is_a_noop():
    body = "Coming, Mei. Mind the wet floor by the hearth."
    out = ground_specifics(body, read_corpus=[])
    assert out.body == body
    assert not out.changed and not out.downgraded and not out.verified


def test_empty_corpus_downgrades_every_quote():
    out = ground_specifics('The log says "fatal: index corrupt".', read_corpus=[])
    assert "fatal: index corrupt" not in out.body
    assert out.downgraded and not out.verified


# --- purity: the function does not mutate its inputs (AC3-adjacent: pure, no side effects) -

def test_inputs_are_not_mutated():
    corpus = [_read("untouched bytes")]
    before_text = corpus[0].text
    body = 'A claim about "nothing real here at all".'
    ground_specifics(body, corpus)
    assert corpus[0].text == before_text
    assert isinstance(ground_specifics(body, corpus), GateResult)
