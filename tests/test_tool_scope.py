"""ToolScope (Major 54, P0): the read/fetch-only tool capability and its do-act routing."""

from pathlib import Path

from src.familiar.local_world import LocalWorld
from src.familiar.tool_scope import Tool, ToolScope, build_tool_scope


def test_calc_tool_runs_and_is_safe():
    ts = build_tool_scope(["calc"])
    assert ts.names == ["calc"] and not ts.has_egress

    async def _run():
        ok = await ts.call("calc", "6 * 7")
        assert ok["ok"] and ok["result"] == "42" and ok["egress"] is False
        bad = await ts.call("calc", "__import__('os').system('x')")  # no names/calls allowed
        assert not bad["ok"] and bad["reason"] == "tool_error"
        unknown = await ts.call("nope", "")
        assert not unknown["ok"] and unknown["reason"] == "unknown_tool"

    import asyncio
    asyncio.run(_run())


def test_build_from_spec_skips_unknown_and_empty():
    assert build_tool_scope(["calc", "does-not-exist"]).names == ["calc"]
    assert not build_tool_scope([])  # empty ToolScope is falsy
    assert not build_tool_scope(None)


def test_egress_flag_surfaces():
    ts = ToolScope([Tool("ping", "remote ping", lambda a: "pong", egress=True)])
    assert ts.has_egress


def test_prune_is_opt_in_and_bound_to_memory(tmp_path: Path):
    # not granted without the opt-in name; granted (local, no egress) when asked for, with memory_dir
    assert "prune" not in build_tool_scope(["calc"], memory_dir=tmp_path).names
    ts = build_tool_scope(["prune"], memory_dir=tmp_path)
    assert "prune" in ts.names and not ts.has_egress
    assert "prune" not in build_tool_scope(["prune"]).names  # no memory_dir → no prune


async def test_prune_tool_soft_removes_one_and_refuses_ambiguous(tmp_path: Path):
    from src.runtime.memory import memories, record_kept
    record_kept(tmp_path, "the keeper moves to the Netherlands")
    record_kept(tmp_path, "the brick oven runs hot on the left")
    ts = build_tool_scope(["prune"], memory_dir=tmp_path)
    # ambiguous phrase matches two → changes nothing, asks to be exact
    amb = await ts.call("prune", "the")
    assert amb["ok"] and "more than one" in amb["result"].lower()
    assert len(memories(tmp_path)) == 2
    # precise phrase → sets down exactly one, kept in the record
    ok = await ts.call("prune", "brick oven")
    assert ok["ok"] and "set down" in ok["result"].lower()
    assert {m["note"] for m in memories(tmp_path)} == {"the keeper moves to the Netherlands"}
    # no match → nothing changed
    none = await ts.call("prune", "a thing never kept")
    assert none["ok"] and "nothing was changed" in none["result"].lower()


async def test_do_act_routes_to_tool(tmp_path: Path):
    world = LocalWorld(home_dir=tmp_path, tool_scope=build_tool_scope(["calc"]))
    res = await world.post_action("s", "use calc 12 * 30")
    assert "360" in res.narrative
    # an unknown tool reports what's available, doesn't crash
    res2 = await world.post_action("s", "use frobnicate 1")
    assert "no tool 'frobnicate'" in res2.narrative and "calc" in res2.narrative


async def test_recall_is_granted_to_every_familiar_and_reads_its_own_past(tmp_path: Path):
    """recall (retrospection) is wired for any familiar via memory_dir, even with no tools config —
    blank query gives an overview of the road; a theme filters kept memories + past felt-senses."""
    import json
    md = tmp_path / "memory"
    md.mkdir()
    (md / "kept_memory.jsonl").write_text(
        json.dumps({"note": "the lamp by the door", "kept_ts": "2026-06-03T10:00:00+00:00"}) + "\n"
        + json.dumps({"note": "silence grows teeth", "kept_ts": "2026-06-04T10:00:00+00:00"}) + "\n"
    )
    (md / "runtime_ledger.jsonl").write_text(
        json.dumps({"event_type": "felt_sense_logged", "ts": "2026-06-05T10:00:00+00:00", "payload": {"felt_sense": "the house is quiet"}}) + "\n"
    )
    scope = build_tool_scope(None, memory_dir=md)  # NO tools config — recall still present
    assert scope.names == ["recall"]
    overview = (await scope.call("recall", ""))["result"]
    assert "2 memories" in overview and "the lamp by the door" in overview and "the house is quiet" in overview
    themed = (await scope.call("recall", "silence"))["result"]
    assert "silence grows teeth" in themed
    assert "Nothing you've kept" in (await scope.call("recall", "zebra"))["result"]


async def test_recall_reaches_the_familiars_own_workshop_makings(tmp_path: Path):
    """A familiar's workshop is its OWN (its makings), but it lives as gitignored files that the
    `search` tool skips — so recall must reach it. A theme that appears only in a workshop entry is
    found and marked '(a making)' (Major 71 / Lever 1)."""
    import json
    md = tmp_path / "memory"
    md.mkdir()
    (md / "kept_memory.jsonl").write_text(json.dumps({"note": "the lamp by the door", "kept_ts": "2026-06-03T10:00:00+00:00"}) + "\n")
    ws = tmp_path / "workshop"
    ws.mkdir()
    (ws / "journal.md").write_text("# first sitting\n\nThe cliff drops curiosity to zero, every time.\n")
    scope = build_tool_scope(None, memory_dir=md)
    hit = (await scope.call("recall", "cliff"))["result"]
    assert "(a making)" in hit and "drops curiosity to zero" in hit


async def test_search_is_granted_with_filescope_and_respects_its_guards(tmp_path: Path):
    from src.familiar.file_scope import FileScope
    root = tmp_path / "r"
    root.mkdir()
    (root / "a.md").write_text("the wire hums bright")
    (root / ".env").write_text("the wire is a secret")          # secret default-deny
    (root / ".gitignore").write_text("hidden.md\n")
    (root / "hidden.md").write_text("the wire in the dark")     # gitignored
    scope = build_tool_scope(None, file_scope=FileScope(read_roots=[str(root)]))
    assert "search" in scope.names and "git" not in scope.names  # not a git repo → no git tool
    res = (await scope.call("search", "wire"))["result"]
    assert "a.md" in res
    assert ".env" not in res and "hidden.md" not in res          # guards hold — secret + ignored unseen


async def test_git_lens_is_read_only(tmp_path: Path):
    import shutil
    import subprocess
    if not shutil.which("git"):
        return
    from src.familiar.file_scope import FileScope
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    (repo / "f.txt").write_text("hi")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "first commit"], check=True)
    scope = build_tool_scope(None, file_scope=FileScope(read_roots=[str(repo)]))
    assert "git" in scope.names
    assert "first commit" in (await scope.call("git", "log"))["result"]
    assert "only look, not touch" in (await scope.call("git", "push origin main"))["result"]


async def test_git_path_translation_handles_root_qualified_paths(tmp_path: Path):
    """The git fix: a familiar sees root-qualified paths (work/src/x.py) but git runs inside the repo
    and wants src/x.py. A qualified path (or the repo root itself) must translate, not error as a 'revision'."""
    import shutil
    import subprocess
    if not shutil.which("git"):
        return
    from src.familiar.file_scope import FileScope
    repo = tmp_path / "work"
    (repo / "src").mkdir(parents=True)
    (tmp_path / "other").mkdir()  # a 2nd root → display paths become root-qualified ("work/...")
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    (repo / "src" / "x.py").write_text("print(1)")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "add x"], check=True)
    scope = build_tool_scope(None, file_scope=FileScope(read_roots=[str(repo), str(tmp_path / "other")]))
    assert "add x" in (await scope.call("git", "log work/src/x.py"))["result"]   # qualified file path
    r = (await scope.call("git", "log work/"))["result"]                          # the repo root itself
    assert "add x" in r and "unknown revision" not in r.lower()


def test_math_tool_is_scientific_and_safe():
    from src.familiar.tool_scope import _sci_calc
    assert "math" in build_tool_scope(["math"]).names
    assert abs(float(_sci_calc("sqrt(2)*sin(pi/4)")) - 1.0) < 1e-9
    assert float(_sci_calc("c / 1000")) == 299792.458
    for bad in ["__import__('os')", "open('x')", "pi.__class__", "self"]:
        try:
            _sci_calc(bad)
            assert False, f"should have refused: {bad}"
        except ValueError:
            pass


def test_per_soul_tools_run_and_degrade_gracefully():
    from src.familiar.tool_scope import _sky, _vitals, _words
    sky = _sky()
    assert "Den Haag" in sky and "moon" in sky and "sun" in sky
    assert isinstance(_vitals(), str) and _vitals()           # the machine says *something*
    words = _words("ember")
    assert "ember" in words.lower() or "no lexicon" in words   # real word-play, or an honest absence


async def test_git_show_passes_a_commit_hash_through_not_as_a_path(tmp_path: Path):
    """The bug Maker hit: a bare commit hash got resolved to a non-existent fallback path and mangled
    into 'familiar/x/<hash>'. A hash isn't a path in reach → it must pass through to git as a ref."""
    import shutil
    import subprocess
    if not shutil.which("git"):
        return
    from src.familiar.file_scope import FileScope
    repo = tmp_path / "work"
    repo.mkdir()
    (tmp_path / "peer").mkdir()  # a 2nd root, like Maker's peers — the resolver's fallback path lived here
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    (repo / "f.txt").write_text("hi")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "the only commit"], check=True)
    full = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    scope = build_tool_scope(None, file_scope=FileScope(read_roots=[str(repo), str(tmp_path / "peer")]))
    out = (await scope.call("git", f"show {full[:7]}"))["result"]
    assert "the only commit" in out and "unknown revision" not in out.lower() and "ambiguous argument" not in out.lower()
