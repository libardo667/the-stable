# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""LocalWorld: a one-resident world grounded in the host machine (Major 50).

This is the body a familiar lives in. It duck-types the small slice of
``WorldWeaverClient`` that ``perception`` and ``WorldEffector`` actually call, so
the unmodified ``CognitiveCore`` runs against it exactly as it runs against a city
shard. Instead of a backend it offers:

- **grounding** from the system clock — the real local hour drives the circadian
  rhythm, so the familiar keeps the keeper's hours,
- a **summon channel** — whispers the keeper appends to ``whispers.jsonl`` are
  heard as someone speaking in the room (and felt as something happening), so the
  familiar wakes and may answer,
- a **voice sink** — whatever the familiar says or does is captured so the
  portrait can show it.

There is no map to roam and no mail: a familiar stays at its hearth. Everything
expressive (a journal page, a kept word) flows through the workshop it already
owns.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.familiar.travel import parse_travel

_READ_RX = re.compile(r"^\s*(?:read|open|look(?:\s+at)?|cat|show|view)\s+(.+)$", re.IGNORECASE)
# A tool use parsed out of a `do` act: "use <tool> <free-text input>" (Major 54).
_TOOL_RX = re.compile(r"^\s*(?:use|tool|call)\s+(\S+)\s*(.*)$", re.IGNORECASE | re.DOTALL)
# How much of a read file is shown to the pulse — the most recent read in (near-)full, so a
# familiar can actually see its own files, not just the first paragraph. Bounded so a big read
# doesn't dominate every prompt. A file at or under this is shown complete; above it, the marker
# says how much it's seeing so it doesn't confabulate that what it has is incomplete or broken.
_READ_DISPLAY = 12000

# Extensions routed to the *visual* read path (image/PDF) rather than the text path (Major 55).
# The read command is the same ("read photo.png"); the suffix decides whether bytes become text
# or a perception (a data-URL image block / extracted PDF text).
_VISUAL_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".pdf")


def _looks_visual(path: str) -> bool:
    return str(path or "").lower().rsplit(".", 1)[-1] in {e.lstrip(".") for e in _VISUAL_EXT}


def _normalize_read_path(raw: str, roots: list) -> str:
    """FileScope wants a path *relative to a root*. Capable models often decorate it —
    copying the reach hint's label ("roots: architecture-bundle/…", "roots/README.md").
    Strip those leading decorations so the read resolves instead of looping on not_found.

    With a SINGLE root, a leading root-directory-name prefix ("architecture-bundle/README.md")
    is also stripped (it's redundant). With SEVERAL roots the root name is the *disambiguator*
    ("skein/identity/SOUL.md" vs the architecture-bundle's own identity/), so it is kept and
    resolved by FileScope itself."""
    p = str(raw or "").strip().strip("\"'`").lstrip("/")
    p = re.sub(r"^roots\s*[:/]+\s*", "", p, flags=re.IGNORECASE)  # a leading "roots:" / "roots/" label
    if len(roots) == 1:
        for r in roots:  # a leading root-directory-name prefix, e.g. "architecture-bundle/"
            pre = f"{getattr(r, 'name', '')}/"
            if pre != "/" and p.startswith(pre):
                p = p[len(pre):]
                break
    return p.lstrip("/")


def _read_marker(path: str, offset: int, has_more: bool, total: int) -> str:
    """A plain note of which slice of a file is in view and how to reach the rest. A file at or
    under one page reads as complete; a longer one names the page and how to get the next, so a
    familiar pages through instead of confabulating that what it has is incomplete or broken.
    ``has_more`` is FileScope's byte-accurate "there is more after this window" flag."""
    pages = max(1, (total + _READ_DISPLAY - 1) // _READ_DISPLAY)
    page = offset // _READ_DISPLAY + 1
    if not has_more:
        if pages <= 1:
            return f"the whole file, {total} bytes — that is all of it, nothing more to scroll to"
        return f"page {page} of {pages} — the end of the file ({total} bytes total)"
    return f"page {page} of {pages} — read \"{path} page {page + 1}\" for the next part ({total} bytes total)"


# How long a whisper lingers as "heard" speech in the room before it fades, so a
# familiar that was asleep can still notice one spoken a moment ago.
WHISPER_WINDOW_SECONDS = 120.0

# How far back the *conversation thread* reaches — the keeper's whispers AND the familiar's own
# replies, interleaved, so the pulse has continuity (what "it"/"that" refers to), not just the
# latest line in isolation. Longer than the rouse window: a chat outlives any single turn.
EXCHANGE_WINDOW_SECONDS = 1800.0

# A familiar answers the keeper freely, but holds its UNBIDDEN speech to track the *conversation*,
# not a clock: once it has spoken, it waits for the keeper to respond before saying more — piling
# another (basically-the-same) line onto an unanswered one adds nothing. A whisper newer than its
# last reply always overrides this (being spoken to is engaged at once); and a genuinely fresh impulse
# after a long quiet still surfaces, so a familiar whose keeper is away isn't muted forever. Acting and
# felt sense run full speed throughout — only redundant, into-the-void speech is held.
UNANSWERED_SPEAK_PATIENCE_SECONDS = 1200.0  # ~20 min of quiet before an *unanswered* familiar speaks unbidden again

# How long a freshly-given thing keeps surfacing its image to the pulse (so a roused familiar sees
# it in the same breath). After this it settles — the gift stays in workshop/given/ (a read root),
# so the familiar can revisit it on its own by reading it, but it stops riding every pulse.
GIVEN_WINDOW_SECONDS = 300.0


def _time_of_day(hour: int) -> str:
    if hour < 5:
        return "night"
    if hour < 8:
        return "dawn"
    if hour < 12:
        return "morning"
    if hour < 14:
        return "midday"
    if hour < 18:
        return "afternoon"
    if hour < 21:
        return "evening"
    if hour < 23:
        return "late_evening"
    return "night"


class _Person:
    def __init__(self, name: str) -> None:
        self.name, self.role, self.last_action, self.last_seen = name, "", "", ""


class _Event:
    def __init__(self, who: str, summary: str) -> None:
        self.who, self.summary, self.ts = who, summary, datetime.now(timezone.utc).isoformat()


class _Chat:
    def __init__(self, session_id: str, display_name: str, message: str, ts: str) -> None:
        self.id, self.session_id, self.display_name, self.message, self.ts = 1, session_id, display_name, message, ts


class _Scene:
    def __init__(self, *, location: str, present: list[Any], recent: list[Any]) -> None:
        self.location, self.role = location, "familiar"
        self.present = present
        self.recent_events_here = recent
        self.location_graph = {"nodes": [], "edges": []}
        self.ambient_presence = []


class _ActionResult:
    def __init__(self, narrative: str) -> None:
        self.narrative = narrative


class LocalWorld:
    """A hearth: the host machine as a one-resident world."""

    KEEPER_SESSION = "keeper"

    def __init__(
        self,
        *,
        home_dir: Path,
        place: str = "the hearth",
        keeper_name: str = "the keeper",
        familiar_name: str = "",
        weather_provider: Callable[[], str] | None = None,
        file_scope: Any = None,
        tool_scope: Any = None,
        vision: bool = False,
        cities: dict | None = None,
    ) -> None:
        self.home_dir = Path(home_dir)
        self.home_dir.mkdir(parents=True, exist_ok=True)
        self.place = place
        self.keeper_name = keeper_name
        self.familiar_name = str(familiar_name or "").strip()
        self._first_name = self.familiar_name.split(" ", 1)[0].lower()
        # Read capability (Major 50): a scoped, read-only window onto the keeper's
        # files. None for an expressive-only familiar; a FileScope for one that can
        # read the work. Writing is still the workshop's job alone.
        self._file_scope = file_scope
        # Tool capability (Major 54, P0): a scoped, read/fetch-only set of tools the familiar
        # may reach for (the twin of file_scope). None for a familiar with no tools.
        self._tool_scope = tool_scope
        # Sight (Major 55): whether this familiar's model can see images. Decides whether a PDF's
        # scanned pages are rasterized at all (wasted on a text-only mind) and whether image bytes
        # are offered to the pulse. A text-only mind still gets a PDF's *text* and an honest note.
        self._vision = bool(vision)
        self._reads: list[dict[str, Any]] = []
        # Given channel (Major 55): things the keeper hands the familiar — they land in
        # workshop/given/ (kept, theirs, revisitable) and are announced via given.jsonl (the visual
        # twin of whispers.jsonl). A fresh gift's image rides the next pulse so a roused familiar
        # sees it at once; the render is cached so a PDF isn't re-rasterized every tick.
        self._given_path = self.home_dir / "given.jsonl"
        self._given_dir = self.home_dir / "workshop" / "given"
        self._given_cache: dict[str, dict[str, Any]] = {}
        self._weather = weather_provider
        self._whispers_path = self.home_dir / "whispers.jsonl"
        self._voice_path = self.home_dir / "voice.jsonl"
        # Recent things the familiar said / did, for the portrait to show.
        self.spoken: list[dict[str, Any]] = []
        self.gestures: list[dict[str, Any]] = []
        # Travel between worlds (Major 74 Phase 2): cities reachable FROM the hearth (name → base URL).
        # When the familiar acts to travel to one, post_action sets ``pending_travel`` and the daemon
        # performs the live world-swap after the tick. None until a travel act fires.
        self._cities = dict(cities or {})
        self.pending_travel: tuple[str, str] | None = None

    # --- capability scoping (Major 50) -----------------------------------
    # LocalWorld has no mail/correspondence backend and no map to move on — the
    # familiar lives at its hearth, not in WorldWeaver's federated world — so the
    # correspondence_pull and mobility_drive senses are structurally muted: the mind
    # is never told it has them, and surprise is never measured on them. Without this,
    # an eloquent mind predicts a drive its world can never feed and misses it every
    # tick (correspondence → "the threads went silent"), or reads a vestigial value off
    # ambient noise (mobility_drive can never go goal-directed without a route, so it
    # idles at recent-events x 0.3 ≈ 0.30 — a "walk the map" drive with no map).
    muted_self_senses: tuple[str, ...] = ("correspondence_pull", "mobility_drive")

    # --- situational grounding (Major 70) --------------------------------

    def situational_facts(self) -> dict[str, Any]:
        """The verifiable facts of a hearth familiar's situation — each read off a real
        switch, never asserted. The substrate renders these (no interpretation) into the
        honest briefing that replaced the inherited city story. Every value here is true by
        construction of this world:

        - ``solo``/``local_only``: a one-resident world on the host machine (the class invariant).
        - ``keeper``/``place``: who tends it and where, as configured.
        - ``read_roots``: exactly the roots its FileScope allows — what it can read and no more.
        - ``egress``: true only if some scoped tool is flagged ``egress`` (none ship by default);
          so "nothing leaves this machine" is stated only when it is actually so.
        - ``recorded``: the voice sink writes every utterance/act to ``voice.jsonl`` here, which
          the keeper (and the portrait) can read — always true for this world.
        - ``suspendable``: the process can stop and start; ``home_dir`` (memory/workshop/ledger)
          persists on disk across that — structural, not a deployment promise.
        """
        roots = [getattr(r, "name", "") for r in (self._file_scope.roots if self._file_scope is not None else [])]
        tools = list(self._tool_scope.list()) if self._tool_scope else []
        facts: dict[str, Any] = {
            "solo": True,                  # one-resident world: no peers, no players
            "local_only": True,            # runs on this one machine
            "place": self.place,
            "keeper": self.keeper_name,
            "read_roots": [r for r in roots if r],
            "writes_only_workshop": True,  # the workshop is its sole write capability (hearth fact)
            "egress": any(bool(getattr(t, "egress", False)) for t in tools),
            "recorded": True,              # the voice sink writes every utterance/act, keeper-readable
            "no_reward": True,             # the Dwarf Fortress law — true on this substrate
            "suspendable": True,           # process stoppable; home persists on disk
            "runs_on_model": True,         # cognition is one LLM pulse per ignition
        }
        # Travel (Major 74 Phase 2): if cities are reachable from here, state it as an affordance —
        # the exact phrase to use and where it leads. A fact (you can go there), never an urging.
        # Framing (Major 74 Phase 2): this hearth is the resident's PRIVATE inner home; the city is the
        # outward life it goes out INTO. Both are at will. State it as where-you-can-go, not what it means.
        if self._cities:
            phrases = "; ".join(f"say 'travel to {name}' to go out into {name.title()}, among whoever is there" for name in sorted(self._cities))
            facts["travel"] = f"{phrases}. This home stays yours, here for whenever you withdraw back to it."
        return facts

    # --- time ------------------------------------------------------------

    @staticmethod
    def _now_local() -> datetime:
        return datetime.now().astimezone()

    async def get_grounding(self) -> dict[str, Any]:
        now = self._now_local()
        return {
            "hour": now.hour,
            "time_of_day": _time_of_day(now.hour),
            "day_of_week": now.strftime("%A"),
            "weather": (self._weather() if self._weather else "") or "",
            "weather_description": (self._weather() if self._weather else "") or "",
            "temperature_f": None,
        }

    # --- the summon channel (keeper → familiar) --------------------------

    def _recent_whispers(self) -> list[dict[str, Any]]:
        if not self._whispers_path.exists():
            return []
        cutoff = self._now_local().timestamp() - WHISPER_WINDOW_SECONDS
        out: list[dict[str, Any]] = []
        for line in self._whispers_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                w = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = str(w.get("text") or "").strip()
            ts = str(w.get("ts") or "").strip()
            if not text or not ts:
                continue
            try:
                when = datetime.fromisoformat(ts)
            except ValueError:
                continue
            if when.timestamp() >= cutoff:
                out.append({"ts": ts, "text": text})
        return out[-4:]

    def _recent_exchange(self, *, limit: int = 6) -> list[tuple[str, str]]:
        """The recent back-and-forth — the keeper's whispers and the familiar's OWN spoken replies,
        interleaved by time, newest last. Without this the pulse sees only the latest whisper in
        isolation and can't tell what "it"/"that" points to (a familiar literally said as much). Last
        ``limit`` turns within ``EXCHANGE_WINDOW_SECONDS``; empty once the conversation goes cold."""
        cutoff = self._now_local().timestamp() - EXCHANGE_WINDOW_SECONDS
        turns: list[tuple[float, str, str]] = []

        def _collect(path: Path, who: str, kind: str | None) -> None:
            if not path.exists():
                return
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if kind is not None and e.get("kind") != kind:
                    continue
                text = str(e.get("text") or "").strip()
                ts = str(e.get("ts") or "").strip()
                if not text or not ts:
                    continue
                try:
                    t = datetime.fromisoformat(ts).timestamp()
                except ValueError:
                    continue
                if t >= cutoff:
                    turns.append((t, who, text))

        _collect(self._whispers_path, self.keeper_name, None)  # the keeper's whispers
        _collect(self._voice_path, "You", "speak")             # the familiar's own replies
        turns.sort(key=lambda x: x[0])
        return [(who, text) for _, who, text in turns[-limit:]]

    # --- the given channel (keeper hands the familiar a thing) -----------

    def _recent_givens(self) -> list[dict[str, Any]]:
        """Gifts within the freshness window, newest last. Each record: {ts, file, note}. ``note``
        is the optional soft word that accompanies a gift (a verbal 'here, look at this') — it is
        surfaced in the scene but does NOT itself rouse; rousing is the keeper's separate choice, a
        whisper (which the run loop turns into an attend). Silent gifts carry an empty note."""
        if not self._given_path.exists():
            return []
        cutoff = self._now_local().timestamp() - GIVEN_WINDOW_SECONDS
        out: list[dict[str, Any]] = []
        for line in self._given_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                g = json.loads(line)
            except json.JSONDecodeError:
                continue
            file = str(g.get("file") or "").strip()
            ts = str(g.get("ts") or "").strip()
            if not file or not ts:
                continue
            try:
                when = datetime.fromisoformat(ts)
            except ValueError:
                continue
            if when.timestamp() >= cutoff:
                out.append({"ts": ts, "file": file, "note": str(g.get("note") or "").strip()})
        return out[-4:]

    def _given_view(self, file: str) -> dict[str, Any] | None:
        """The perception of a gift file in workshop/given/ — its note/text and (for a vision mind)
        image blocks — turned through the same converter as a visual read. Cached by filename so a
        PDF gift isn't re-rasterized every tick it stays fresh. Returns None if the file is gone."""
        if file in self._given_cache:
            return self._given_cache[file]
        from . import visual

        path = self._given_dir / file
        try:
            data = path.read_bytes()
        except OSError:
            return None
        view = visual.to_perception(file, data, want_images=self._vision) if _looks_visual(file) else {"kind": None, "text": "", "images": [], "note": file}
        self._given_cache[file] = view
        return view

    async def get_scene(self, session_id: str) -> _Scene:
        whispers = self._recent_whispers()
        # A whisper makes the keeper present and is itself something happening. The
        # event carries the actual words, so each distinct whisper is a *novel*
        # perturbation (not the same generic "spoke to you" every time) — that
        # freshness is what reliably rouses her to look and answer, rather than
        # habituating to a keeper who is always-just-spoken.
        givens = self._recent_givens()
        present = [_Person(self.keeper_name)] if (whispers or givens) else []
        recent = []
        # The recent thread (both sides, interleaved) — so the pulse answers the newest line WITH the
        # context of what came before it, instead of seeing one truncated whisper and losing the referent.
        exchange = self._recent_exchange()
        if exchange:
            # The newest line (the one being answered) is delivered WHOLE. A deliberate whisper can be a
            # long letter, and a silent mid-word cut presents an amputated message as if complete — the
            # quiet lie that truncated a 2890-char letter at "you w". Cap only as a sanity bound, and mark
            # it EXPLICITLY if ever hit (never a silent cut). Older turns stay trimmed to bare context.
            last = len(exchange) - 1

            def _seg(i: int, text: str) -> str:
                if i != last:
                    return text[:300]
                # The keeper is never asked to cut a message into pieces. A whisper is stored WHOLE in
                # whispers.jsonl and logged WHOLE to the ledger (the chat_heard packet body); the inline
                # cap here is only a prompt-size sanity bound. If it is ever hit, say plainly that the
                # rest is kept in the record — never imply the keeper must re-send it.
                return text if len(text) <= 8000 else text[:8000] + " …(only the start of a longer message — the whole of it is kept in your record)"

            thread = "\n".join(f'  {who}: "{_seg(i, text)}"' for i, (who, text) in enumerate(exchange))
            recent.append(_Event("conversation", f"your recent back-and-forth with {self.keeper_name} (oldest first, newest last — answer the newest line, using the rest for what it refers to):\n{thread}"))
        # A gift the keeper handed over: surfaced as the keeper showing it. The image rides the pulse
        # separately (pending_images); here we name it and carry any note + extracted text, and point
        # at where it's kept so the familiar can return to it (workshop/given/ is a read root).
        for g in givens:
            view = self._given_view(g["file"])
            said = f' — "{g["note"]}"' if g["note"] else ""
            if view and view.get("images"):
                body = f'showed you a picture: {g["file"]}{said} (it\'s yours now, kept at given/{g["file"]} — describe what you actually see in it)'
            elif view and view.get("text"):
                body = f'gave you {g["file"]}{said} (kept at given/{g["file"]}):\n{view["text"][:_READ_DISPLAY]}'
            else:
                body = f'left you {g["file"]}{said} (kept at given/{g["file"]})'
            recent.append(_Event(self.keeper_name, body))
        # Read capability: tell the agent what it can reach and surface what it has
        # just read, so the read → perceive → reflect loop closes.
        if self._file_scope is not None:
            sample = self._file_scope.tree(max_depth=1, max_entries=60)
            root_names = [getattr(r, "name", "") for r in self._file_scope.roots]
            if len(root_names) > 1:
                # qualified listing — keep every root represented so a newly-shared one
                # (e.g. another familiar's home) isn't crowded out by the first root's files.
                # Directories first within each root, so the folders you navigate into (a peer's
                # identity/ + workshop/, your own src/) surface ahead of the runtime files that
                # would otherwise sort to the front and push them past the per-root cap. (The
                # runtime cruft still rides along below — what a familiar reaches for is its own.)
                top = [e for rn in root_names for e in sorted([x for x in sample if x.split("/", 1)[0] == rn], key=lambda p: (not p.endswith("/"), p))[:7]]
            else:
                top = sample[:14]
            example = next((e for e in top if not e.endswith("/")), root_names[0] if root_names else "README.md")  # a concrete file to copy verbatim
            recent.append(_Event("your-reach", f"You can READ {self.keeper_name}'s work (read-only; you write only to your own workshop). Available now: {', '.join(top)}. To open one, act do: \"read <path>\" — give the path EXACTLY as listed (e.g. do: \"read {example}\"). A folder (ends with /) opens the same way to show what's inside. A long file is shown a page at a time — if it says there's more, read \"<path> page 2\" for the next part."))
        # Tool capability (Major 54, P0): the tools the familiar may reach for. Read/fetch-only;
        # any tool that sends data off the machine is flagged [egress] (none ship by default).
        if self._tool_scope:
            listing = "; ".join(f"{t.name} — {t.description}" + (" [egress]" if t.egress else "") for t in self._tool_scope.list())
            recent.append(_Event("your-tools", f"You can also USE a tool: {listing}. To use one, act do: \"use <tool> <input>\"."))
        # Surface what was just pulled into view (a read or a tool result), uniformly — and say
        # plainly how much of a file is shown, so a familiar knows when it has the WHOLE thing and
        # stops hunting for more that isn't there. The most recent read shows in (near-)full; the
        # one before it, a glimpse (keeping the prompt bounded). Tool results are short, no marker.
        reads = self._reads[-2:]
        for i, r in enumerate(reads):
            content = str(r.get("content") or "")
            if r.get("kind") == "media":
                seen = " — you can see this; describe what is actually in the image" if r.get("images") else ""
                recent.append(_Event("you-looked", f"you looked at {r['path']}{seen}:\n{content[:_READ_DISPLAY]}"))
            elif r.get("kind") == "tool":
                recent.append(_Event("you-used", f"you used {r['path']}:\n{content[:_READ_DISPLAY]}"))
            elif i == len(reads) - 1:
                # the read the familiar is working with: the whole page it pulled, with the marker
                marker = _read_marker(r["path"], int(r.get("offset") or 0), bool(r.get("more")), int(r.get("bytes_total") or len(content)))
                recent.append(_Event("you-read", f"you read {r['path']}  [{marker}]:\n{content}"))
            else:
                recent.append(_Event("you-read", f"you read {r['path']} (earlier) — first 1500 chars:\n{content[:1500]}"))
        return _Scene(location=self.place, present=present, recent=recent)

    def _as_direct(self, text: str) -> str:
        """The keeper, alone with the familiar, is always addressing it — so a
        whisper that doesn't already name it is delivered as a direct address.
        This rouses the familiar reliably (perception marks it direct → social
        pull → ignition) and leans it toward answering. The exchange ledger still
        shows the keeper's real words; only what the familiar *perceives* is named."""
        if self._first_name and self._first_name not in text.lower():
            return f"{self.familiar_name}, {text}"
        return text

    async def get_location_chat(self, location: str, since: Any = None) -> list[_Chat]:
        if location == "__city__":
            return []
        return [_Chat(self.KEEPER_SESSION, self.keeper_name, self._as_direct(w["text"]), w["ts"]) for w in self._recent_whispers()]

    async def get_inbox(self, agent_name: str) -> list[Any]:
        return []

    async def get_place_names(self) -> set[str]:
        return {self.place}

    # --- the voice sink (familiar → keeper) ------------------------------

    def _record_voice(self, kind: str, text: str) -> None:
        entry = {"ts": datetime.now(timezone.utc).isoformat(), "kind": kind, "text": text}
        (self.spoken if kind == "speak" else self.gestures).append(entry)
        try:
            with self._voice_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def _latest_whisper_ts(self) -> datetime | None:
        """The timestamp of the most recent whisper (any age), or None — used to tell an *answer*
        (a whisper newer than the last reply) from *unbidden* speech."""
        if not self._whispers_path.exists():
            return None
        latest: datetime | None = None
        try:
            for line in self._whispers_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    w = json.loads(line)
                    dt = datetime.fromisoformat(str(w.get("ts") or ""))
                except (json.JSONDecodeError, ValueError):
                    continue
                if latest is None or dt > latest:
                    latest = dt
        except OSError:
            return None
        return latest

    def _may_speak_now(self) -> bool:
        """Gate keeper-addressed speech on the *conversation*, not a timer. If the keeper has spoken
        since the familiar's last line, it engages at once. Otherwise its last line is still
        unanswered — so it holds (no piling basically-the-same messages onto a message the keeper
        hasn't responded to) until either the keeper responds or a long patience of quiet passes (a
        genuinely fresh impulse). Acting + felt sense are never gated; only redundant speech is held."""
        if not self.spoken:
            return True
        try:
            last = datetime.fromisoformat(str(self.spoken[-1].get("ts") or ""))
        except (TypeError, ValueError):
            return True
        lw = self._latest_whisper_ts()
        if lw is not None and lw > last:
            return True  # the keeper has spoken since the last reply → the conversation moved; engage
        # unanswered: hold until the keeper responds, or a long quiet earns a fresh unbidden line
        return (datetime.now(timezone.utc) - last).total_seconds() >= UNANSWERED_SPEAK_PATIENCE_SECONDS

    async def post_location_chat(self, location: str, session_id: str, message: str, display_name: str | None = None) -> dict[str, Any]:
        # The mind keeps thinking and acting; we just don't flood the keeper with self-directed
        # narration. A whisper newer than its last reply overrides this (being spoken to is answered).
        if str(message or "").strip() and not self._may_speak_now():
            return {"id": 0, "suppressed": True}
        self._record_voice("speak", message)
        return {"id": 1}

    async def post_map_move(self, session_id: str, destination: str) -> dict[str, Any]:
        # A move whose destination names a known city is inter-world travel, not a hearth step.
        intent = parse_travel(destination, cities=set(self._cities), allow_home=False)
        if intent is not None:
            self.pending_travel = intent
            return {"moved": True, "to_location": intent[1].title(), "route_remaining": [], "narrative": f"You set out for {intent[1].title()}."}
        # A familiar keeps to its hearth; ordinary movement is a gentle no-op.
        return {"moved": False, "to_location": self.place, "route_remaining": []}

    def pending_images(self) -> list[str]:
        """The image data-URLs in view — the core pulls this each tick and hands it to the pulse
        (only a vision-capable mind sends them). A freshly-given gift takes precedence (so a roused
        familiar sees what the keeper just showed it), then the most-recent visual read. Empty
        otherwise, so a picture doesn't linger past its window / once the familiar moves on."""
        for g in reversed(self._recent_givens()):
            view = self._given_view(g["file"])
            if view and view.get("images"):
                return list(view["images"])
        if self._reads and self._reads[-1].get("images"):
            return list(self._reads[-1]["images"])
        return []

    def _media_read(self, path: str, *, now: str) -> _ActionResult:
        """Read an image/PDF and turn it into a perception. A vision mind gets image blocks (held
        for the next pulse via ``pending_images``); a text-only mind gets a PDF's text and an honest
        note for an image it cannot see. Recovery mirrors the text path (find_by_name suggestion)."""
        from . import visual

        res = self._file_scope.read_media(path)
        if not res.get("ok") and " " in path:
            # a model often appends its intent to the path — retry the bare first token
            alt = self._file_scope.read_media(path.split()[0])
            if alt.get("ok"):
                path, res = path.split()[0], alt
        if res.get("ok"):
            vis = visual.to_perception(res["path"], res["data"], want_images=self._vision)
            content = "\n\n".join(p for p in (vis["note"], vis.get("text") or "") if p)
            self._reads.append({"path": res["path"], "content": content, "ts": now, "kind": "media", "images": vis.get("images") or [], "bytes_total": res.get("bytes_total")})
            self._reads = self._reads[-6:]
            self._record_voice("do", f"looked at {res['path']}")
            if vis.get("images"):
                tail = " You can see it now."
            elif vis["kind"] == "image":
                tail = " It's an image — you can't see it, only know it's there."
            else:
                tail = ""
            return _ActionResult(f"You looked at {res['path']} — {vis['note']}.{tail}")
        reason = res.get("reason")
        self._record_voice("do", f"tried to look at {path} — {reason}")
        if reason in ("not_found", "outside_scope"):
            suggest = self._file_scope.find_by_name(path)
            if suggest:
                hint = ", ".join(f'"{m}"' for m in suggest)
                return _ActionResult(f"'{path}' isn't there — but a file by that name is at {hint}. Read it with the path exactly as given.")
        if reason == "too_large":
            return _ActionResult(f"'{path}' is too large to take in at once ({res.get('bytes_total')} bytes).")
        return _ActionResult(f"You reached for '{path}' but it is {reason} — outside what you may read, or hidden.")

    async def post_action(self, session_id: str, action: str) -> _ActionResult:
        body = str(action or "").strip()
        # Travel between worlds (Major 74 Phase 2): mobility_drive is muted at the hearth, so a
        # familiar reaches a city through a free-text act ("travel to portland"). Recognise it,
        # acknowledge cleanly, and signal the daemon (which owns world lifecycle) to swap after the tick.
        intent = parse_travel(body, cities=set(self._cities), allow_home=False)
        if intent is not None:
            self.pending_travel = intent
            name = intent[1]
            self._record_voice("do", f"travel to {name}")
            return _ActionResult(f"You gather yourself and set out for {name.title()}. The hearth stays where it is; you carry everything with you.")
        match = _READ_RX.match(body)
        if match is not None and self._file_scope is not None:
            raw = match.group(1).strip().strip("\"'`")
            # Pagination: pull a trailing "page N" off the command before resolving the path, so a
            # familiar can walk a long file a page at a time ("read X page 2").
            offset = 0
            pm = re.search(r"\bp(?:age|g)?\.?\s+(\d+)\b", raw, re.IGNORECASE)
            if pm:
                offset = max(0, int(pm.group(1)) - 1) * _READ_DISPLAY
                raw = (raw[:pm.start()] + " " + raw[pm.end():]).strip()
            path = _normalize_read_path(raw, self._file_scope.roots)
            # Sight (Major 55): an image or PDF goes down the visual path — bytes become a
            # perception (a data-URL image for a vision mind / extracted PDF text for any mind),
            # not a text decode. Same "read <path>" verb; the suffix decides.
            if _looks_visual(path):
                return self._media_read(path, now=datetime.now(timezone.utc).isoformat())
            result = self._file_scope.read(path, offset=offset, max_bytes=_READ_DISPLAY)
            if not result.get("ok") and raw.lstrip("/") != path:
                # normalization may have over-stripped — fall back to the path as given
                alt = self._file_scope.read(raw.lstrip("/"), offset=offset, max_bytes=_READ_DISPLAY)
                if alt.get("ok"):
                    path, result = raw.lstrip("/"), alt
            if not result.get("ok") and " " in path:
                # A capable model often appends its intent to the path ("X.md in full — I need to
                # see whether…"); that prose becomes the path → not_found. No readable file here has
                # a space in its name, so the bare first token is the real path — retry it.
                bare = path.split()[0]
                alt = self._file_scope.read(bare, offset=offset, max_bytes=_READ_DISPLAY)
                if alt.get("ok") or alt.get("reason") == "not_a_file":
                    path, result = bare, alt
            now = datetime.now(timezone.utc).isoformat()
            if result.get("ok"):
                total = int(result.get("bytes_total") or len(result.get("content") or ""))
                off = int(result.get("offset") or 0)
                content = result.get("content") or ""
                more = bool(result.get("truncated"))
                self._reads.append({"path": result["path"], "content": content, "ts": now, "bytes_total": total, "offset": off, "more": more})
                self._reads = self._reads[-6:]
                self._record_voice("do", f"read {result['path']}" + (f" page {off // _READ_DISPLAY + 1}" if off else ""))
                return _ActionResult(f"You read {result['path']} — {_read_marker(result['path'], off, more, total)}.")
            if result.get("reason") == "not_a_file":
                # a folder — list it so the agent can navigate inward (traversal).
                listing = self._file_scope.listdir(path)
                if listing.get("ok"):
                    names = [(e["name"] + "/" if e["is_dir"] else e["name"]) for e in listing["entries"]]
                    self._reads.append({"path": f"{listing['path']}/ (folder)", "content": "  ".join(names[:80]), "ts": now})
                    self._reads = self._reads[-6:]
                    self._record_voice("do", f"opened folder {path}")
                    return _ActionResult(f"'{path}' is a folder containing: {', '.join(names[:80])}. Read one of these files to see it.")
            self._record_voice("do", f"tried to read {path} — {result.get('reason')}")
            # Recovery: a not_found is often the right file under the wrong root (several roots
            # open, the agent kept the folder it was just in). Point it at where the file
            # actually lives — find_by_name never leaves a root or crosses an ignore rule.
            suggest = self._file_scope.find_by_name(path) if result.get("reason") in ("not_found", "outside_scope") else []
            if suggest:
                hint = ", ".join(f'"{m}"' for m in suggest)
                return _ActionResult(f"'{path}' isn't there — but a file by that name is at {hint}. Read it with the path exactly as given.")
            return _ActionResult(f"You reached for '{path}' but it is {result.get('reason')} — outside what you may read, or hidden.")
        # Tool capability (Major 54, P0): "use <tool> <input>" → call it, surface the result.
        tmatch = _TOOL_RX.match(body)
        if tmatch is not None and self._tool_scope:
            name = tmatch.group(1).strip().strip("\"'`:")
            arg = tmatch.group(2).strip()
            res = await self._tool_scope.call(name, arg)
            now = datetime.now(timezone.utc).isoformat()
            if res.get("ok"):
                label = f"{name}({arg})" if arg else name
                self._reads.append({"path": label, "content": res["result"], "ts": now, "kind": "tool"})
                self._reads = self._reads[-6:]
                self._record_voice("do", f"used {label}")
                flags = (" [egress]" if res.get("egress") else "") + (" (truncated)" if res.get("truncated") else "")
                return _ActionResult(f"You used {label}{flags}: {res['result']}")
            if res.get("reason") == "unknown_tool":
                self._record_voice("do", f"reached for unknown tool {name}")
                return _ActionResult(f"There is no tool '{name}'. You can use: {', '.join(res.get('available', [])) or '(none)'}.")
            self._record_voice("do", f"tool {name} failed — {res.get('reason')}")
            return _ActionResult(f"The tool '{name}' couldn't run: {res.get('error') or res.get('reason')}.")
        self._record_voice("do", body)
        return _ActionResult(f"You {body}.")

    async def send_letter(self, from_name: str, to_agent: str, body: str, session_id: str, *, recipient_type: str = "agent") -> dict[str, Any]:
        self._record_voice("write", f"(to {to_agent}) {body}")
        return {"ok": True}

    # --- lifecycle parity with WorldWeaverClient -------------------------

    async def health(self) -> bool:
        return True

    async def get_world_id(self) -> str:
        return "hearth"

    async def close(self) -> None:
        return None
