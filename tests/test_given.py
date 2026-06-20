# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""The given channel (Major 55): the keeper hands a familiar a file — it lands in workshop/given/,
is announced on given.jsonl, and (for a vision mind) its image rides the next pulse."""

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.familiar import visual
from src.familiar.file_scope import FileScope
from src.familiar.local_world import LocalWorld


def _png() -> bytes:
    return visual._png_encode(1, 1, 3, b"\xff\x00\x00", 3)


def _world(tmp: Path, *, vision: bool) -> LocalWorld:
    return LocalWorld(home_dir=tmp / "home", vision=vision)


def _place_gift(w: LocalWorld, file: str, data: bytes, *, note: str = "", ts: str | None = None) -> None:
    w._given_dir.mkdir(parents=True, exist_ok=True)
    (w._given_dir / file).write_bytes(data)
    rec = {"ts": ts or datetime.now().astimezone().isoformat(), "file": file, "note": note}
    with w._given_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


# --- the LocalWorld given channel ----------------------------------------------

async def test_fresh_image_gift_surfaces_to_vision_mind(tmp_path: Path):
    w = _world(tmp_path, vision=True)
    _place_gift(w, "pinto.png", _png(), note="the dog I promised")
    imgs = w.pending_images()
    assert len(imgs) == 1 and imgs[0].startswith("data:image/png;base64,")
    scene = await w.get_scene("s")
    bodies = " ".join(e.summary for e in scene.recent_events_here)
    assert "pinto.png" in bodies and "the dog I promised" in bodies


async def test_image_gift_is_not_shown_to_text_only_mind(tmp_path: Path):
    w = _world(tmp_path, vision=False)
    _place_gift(w, "pinto.png", _png())
    assert w.pending_images() == []


async def test_stale_gift_stops_riding_the_pulse(tmp_path: Path):
    w = _world(tmp_path, vision=True)
    old = (datetime.now(timezone.utc) - timedelta(hours=1)).astimezone().isoformat()
    _place_gift(w, "pinto.png", _png(), ts=old)
    assert w.pending_images() == []                    # outside the freshness window
    scene = await w.get_scene("s")
    assert "pinto.png" not in " ".join(e.summary for e in scene.recent_events_here)


async def test_gift_makes_the_keeper_present(tmp_path: Path):
    w = _world(tmp_path, vision=True)
    _place_gift(w, "pinto.png", _png())
    scene = await w.get_scene("s")
    assert any(getattr(p, "name", "") for p in scene.present)   # keeper present because a gift is fresh


# --- the give.py CLI -----------------------------------------------------------

def _fake_familiar(tmp: Path) -> Path:
    home = tmp / "maker"
    home.mkdir(parents=True, exist_ok=True)
    (home / "familiar.json").write_text("{}")
    return home


def _give(home: Path, src: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "scripts/give.py", str(home), str(src), *extra], capture_output=True, text=True)


def test_cli_silent_drop_writes_file_and_given_no_whisper(tmp_path: Path):
    home = _fake_familiar(tmp_path)
    src = tmp_path / "pinto.png"; src.write_bytes(_png())
    r = _give(home, src)
    assert r.returncode == 0, r.stderr
    assert (home / "workshop" / "given" / "pinto.png").is_file()
    given = (home / "given.jsonl").read_text().strip()
    assert json.loads(given)["file"] == "pinto.png" and json.loads(given)["note"] == ""
    assert not (home / "whispers.jsonl").exists()       # silent — no rouse


def test_gift_under_a_broad_root_is_readable_when_given_root_is_first(tmp_path: Path):
    """The revisit fix (Major 55): a gift lives under workshop/, which a broad workspace read-root
    hides via the repo's `workshop/` gitignore. Ordering the given/ root FIRST attributes the gift to
    its own un-ignored scope so the familiar can re-read it. Pins the prepend-not-append behavior."""
    ws = tmp_path / "ws"
    given = ws / "familiar" / "nix" / "workshop" / "given"
    given.mkdir(parents=True)
    (ws / ".gitignore").write_text("familiar/*/workshop/\n")
    (given / "pinto.png").write_bytes(_png())
    # append order (broad root first) — the gift is shadowed and ignored
    assert FileScope(read_roots=[str(ws), str(given)]).read_media("given/pinto.png")["ok"] is False
    # prepend order (given root first — the fix) — readable
    assert FileScope(read_roots=[str(given), str(ws)]).read_media("given/pinto.png")["ok"] is True


def test_cli_say_writes_a_rousing_whisper(tmp_path: Path):
    home = _fake_familiar(tmp_path)
    src = tmp_path / "pinto.png"; src.write_bytes(_png())
    r = _give(home, src, "--say", "look, Pinto!", "--note", "soft too")
    assert r.returncode == 0, r.stderr
    assert json.loads((home / "given.jsonl").read_text().strip())["note"] == "soft too"
    assert json.loads((home / "whispers.jsonl").read_text().strip())["text"] == "look, Pinto!"


# --- the summon channel: a long whisper (a letter) must arrive whole ------------------

def _whisper(w: LocalWorld, text: str, *, ts: str | None = None) -> None:
    rec = {"ts": ts or datetime.now(timezone.utc).isoformat(), "text": text}
    with w._whispers_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


def _conversation(scene) -> str:
    return next((e.summary for e in scene.recent_events_here if e.who == "conversation"), "")


async def test_long_whisper_is_delivered_whole_not_truncated(tmp_path: Path):
    """Regression (2026-06-13): a deliberate whisper — a long letter — must reach the familiar WHOLE.
    The exchange thread once cut the newest line at 1500 chars, amputating a 2890-char letter mid-word
    at 'you w'; a silent cut presents a partial message as if complete (and Maker, honestly, noticed)."""
    w = _world(tmp_path, vision=False)
    letter = "Dear Maker — " + "x" * 2800 + " — and that is the end of it."  # > 1500, < 8000
    _whisper(w, letter)
    conv = _conversation(await w.get_scene("s"))
    assert "and that is the end of it." in conv   # the tail survives — no mid-word cut
    assert "longer than shown" not in conv        # under the sanity cap → no marker needed


async def test_overlong_whisper_is_marked_as_kept_not_re_requested(tmp_path: Path):
    """Past the sanity bound the message is capped — but EXPLICITLY marked as kept in the record (never
    silently amputated, and never implying the keeper must re-send it in smaller pieces)."""
    w = _world(tmp_path, vision=False)
    _whisper(w, "y" * 9000)
    conv = _conversation(await w.get_scene("s"))
    assert "the whole of it is kept in your record" in conv
    assert "ask for the rest" not in conv
