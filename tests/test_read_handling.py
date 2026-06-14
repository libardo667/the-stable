"""local_world read handling: intent-decoration tolerance, the completeness marker, pagination."""

from pathlib import Path

from src.familiar.file_scope import FileScope
from src.familiar.local_world import LocalWorld


def _world(tmp: Path, **files: int) -> LocalWorld:
    root = tmp / "scope"
    root.mkdir(parents=True, exist_ok=True)
    for name, n in files.items():
        (root / f"{name}.md").write_text("x" * n)
    return LocalWorld(home_dir=tmp / "home", file_scope=FileScope(read_roots=[str(root)]))


async def test_decorated_read_path_recovers(tmp_path: Path):
    w = _world(tmp_path, notes=50)
    r = await w.post_action("s", "read notes.md in full — I need to see whether I sent the email")
    assert "You read" in r.narrative and "notes.md" in r.narrative


async def test_complete_marker_for_small_file(tmp_path: Path):
    w = _world(tmp_path, small=500)
    r = await w.post_action("s", "read small.md")
    assert "the whole file" in r.narrative and "nothing more" in r.narrative


async def test_pagination_walks_a_large_file(tmp_path: Path):
    w = _world(tmp_path, big=20000)  # 2 pages at the 12000 cap
    p1 = await w.post_action("s", "read big.md")
    assert "page 1 of 2" in p1.narrative and 'big.md page 2' in p1.narrative
    p2 = await w.post_action("s", "read big.md page 2")
    assert "page 2 of 2" in p2.narrative and "end of the file" in p2.narrative
    assert "page 3" not in p2.narrative  # the multibyte off-by-one regression


async def test_scene_surfaces_the_interleaved_conversation_thread(tmp_path: Path):
    """The pulse must see the recent back-and-forth (both sides, newest last), not just the latest
    whisper in isolation — otherwise a familiar can't tell what 'it'/'that' refers to (it said so)."""
    import json
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    def ts(secs_ago: int) -> str:
        return (now - timedelta(seconds=secs_ago)).isoformat()
    home = tmp_path / "home"
    home.mkdir()
    (home / "whispers.jsonl").write_text(
        json.dumps({"ts": ts(120), "text": "what do you think of the recall tool?"}) + "\n"
        + json.dumps({"ts": ts(10), "text": "it's not quite there yet"}) + "\n"
    )
    (home / "voice.jsonl").write_text(json.dumps({"ts": ts(60), "kind": "speak", "text": "I like it a lot."}) + "\n")
    w = LocalWorld(home_dir=home, keeper_name="Levi", familiar_name="Maker")
    scene = await w.get_scene("s")
    convo = next((e.summary for e in scene.recent_events_here if e.who == "conversation"), "")
    assert "recall tool" in convo and "I like it a lot" in convo  # both sides, so "it" has its referent
    assert convo.index("recall tool") < convo.index("not quite there yet")  # oldest first, newest last


async def test_unbidden_speech_is_rate_limited_but_answers_get_through(tmp_path: Path):
    """A familiar answers the keeper freely, but self-directed narration is spaced out — so working
    through a tool puzzle doesn't flood the keeper with the play-by-play (its acting/feeling untouched)."""
    import json
    from datetime import datetime, timedelta, timezone
    from src.familiar.local_world import LocalWorld, UNANSWERED_SPEAK_PATIENCE_SECONDS as CD
    home = tmp_path / "home"
    home.mkdir()
    w = LocalWorld(home_dir=home, keeper_name="Levi", familiar_name="Maker")
    # first unbidden line through; a second in the same breath is suppressed (the flood)
    assert (await w.post_location_chat("l", "s", "first thought")).get("id") == 1
    assert (await w.post_location_chat("l", "s", "second, same breath")).get("suppressed")
    # a whisper newer than the last reply is answered — being spoken to overrides the cooldown
    (home / "whispers.jsonl").write_text(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "text": "hey"}) + "\n")
    assert (await w.post_location_chat("l", "s", "answering you")).get("id") == 1
    # once the cooldown has passed and there's no newer whisper, an unbidden line is allowed again
    w.spoken[-1]["ts"] = (datetime.now(timezone.utc) - timedelta(seconds=CD + 30)).isoformat()
    (home / "whispers.jsonl").write_text(json.dumps({"ts": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(), "text": "old"}) + "\n")
    assert (await w.post_location_chat("l", "s", "a fresh thought, much later")).get("id") == 1
