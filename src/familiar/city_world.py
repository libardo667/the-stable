"""CityWorld — a familiar's body when it travels OUT to a WorldWeaver city shard.

The city counterpart of ``LocalWorld``. Where ``LocalWorld`` grounds a familiar at
its hearth (system clock, whisper summons, a voice sink), ``CityWorld`` wraps a
``CityClient`` (the ported WorldWeaver HTTP client) so the *same* ``CognitiveCore``
perceives and acts in a populated, geographically-grounded city — over the same
``WorldClient`` Protocol the substrate already depends on.

The point is **travel, not migration**: the daemon, its ledger, kept memory,
workshop and soul all stay in ``familiar/<name>/`` — only the *world* it looks out
through changes. Slot a different cartridge into the same console; the save file
is untouched.

This is deliberately lean. It carries no city scale-tools (no ``chatter`` pull, no
incubation, no ``CityToolScope``) — a visitor roams, perceives, moves and may speak.
Everything not overridden here delegates to the shared client via ``__getattr__``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.familiar.city_client import CityClient, TurnResult
from src.familiar.travel import parse_travel


class CityWorld:
    """Wraps a ``CityClient`` so a hearth familiar can inhabit a city shard."""

    def __init__(
        self,
        client: CityClient,
        *,
        home_dir: Path,
        place: str,
        familiar_name: str,
        solo: bool = True,
        vision: bool = False,
        cities: dict | None = None,
    ) -> None:
        self._client = client
        # Read by scripts/familiar.py's state writer (the portrait surface). The memory dir
        # is the-stable-side and travels with the daemon regardless of which world it sees.
        self.home_dir = home_dir
        self.place = place
        self._name = familiar_name
        self._solo = solo
        self.vision = vision
        # The portrait reads world.spoken[-1]; in the city, speech goes out as location chat.
        self.spoken: list[dict[str, Any]] = []
        # Travel (Major 74 Phase 2): OTHER cities reachable from here (name → base URL); "home" is
        # always reachable from a city. A travel act sets ``pending_travel`` for the daemon to swap on.
        self._cities = dict(cities or {})
        self.pending_travel: tuple[str, str] | None = None

    # --- situational grounding (Major 70): state the city scenario, withhold the verdict ---
    def situational_facts(self) -> dict[str, Any]:
        """Verifiable facts about being OUT in the city. Only recognised briefing keys; no
        prose about what it should *feel* to be away from the hearth. The keeper-line is
        intentionally omitted (a city body reports the city's truth; the familiar already
        knows its keeper from its own kept memory)."""
        facts: dict[str, Any] = {
            "solo": bool(self._solo),       # an empty shard: say so, don't fake a bustle
            "peers": not self._solo,        # other residents live here too, when populated
            "players": True,                # humans tether to characters, present while attending
            "place": self.place,            # where it is in the city
            "local_only": False,            # this world is not just this one machine
            "world_legible": True,          # what it says/does is seen by those present and persists
            "inner_private": True,          # its felt_sense / predictions are read by no one
            "mobile": True,                 # it can move through the world (the city affordance)
            "mail": True,                   # it can send word that waits for an absent recipient
            "recorded": True,               # its words/acts are written where they can be read back
            "no_reward": True,              # the substrate holds no reward/goal for it
            "suspendable": True,            # it can be stopped and woken with its record kept
            "runs_on_model": True,          # its cognition is produced by a language model
        }
        # Travel (Major 74 Phase 2): this city is the resident's outward life; its hearth is the private
        # inner home it can withdraw to. From here, home is always reachable; other cities if configured.
        clauses = ["say 'go home' to withdraw to your hearth — your private home, where you are alone and unread"]
        clauses += [f"say 'travel to {name}' to go on to {name.title()}" for name in sorted(self._cities)]
        facts["travel"] = "; ".join(clauses) + "."
        return facts

    # --- perception: keep self.place current as it roams ---
    async def get_scene(self, session_id: str) -> Any:
        scene = await self._client.get_scene(session_id)
        loc = getattr(scene, "location", "")
        if loc:
            self.place = loc
        return scene

    # --- effector: capture spoken lines for the portrait, then send them on ---
    async def post_location_chat(self, location: str, session_id: str, message: str, display_name: str | None = None) -> dict[str, Any]:
        self.spoken.append({"text": message, "ts": datetime.now(timezone.utc).isoformat()})
        return await self._client.post_location_chat(location, session_id, message, display_name=display_name)

    # --- intercept inter-world travel before it reaches the city backend ---
    async def post_action(self, session_id: str, action: str) -> Any:
        intent = parse_travel(str(action or ""), cities=set(self._cities), allow_home=True)
        if intent is not None:
            self.pending_travel = intent
            dest = "your hearth" if intent[0] == "home" else intent[1].title()
            return TurnResult(narrative=f"You make ready to leave for {dest}. You carry everything with you.", choices=[], vars={})
        return await self._client.post_action(session_id, action)

    async def post_map_move(self, session_id: str, destination: str) -> dict[str, Any]:
        intent = parse_travel(str(destination or ""), cities=set(self._cities), allow_home=True)
        if intent is not None:
            self.pending_travel = intent
            dest = "your hearth" if intent[0] == "home" else intent[1].title()
            return {"moved": True, "to_location": dest, "route_remaining": [], "narrative": f"You set out for {dest}."}
        return await self._client.post_map_move(session_id, destination)

    async def close(self) -> None:
        await self._client.close()

    def __getattr__(self, name: str) -> Any:
        # Everything not overridden (get_grounding, get_inbox, get_location_chat, post_action,
        # post_map_move, send_letter, roster/map helpers) delegates to the shared client.
        return getattr(self._client, name)
