"""Tests for CityWorld — the body a familiar wears when it travels to a city shard.

The substrate is world-agnostic, so CityWorld must satisfy the same WorldClient
Protocol as LocalWorld, keep its `place` current as it roams, capture speech for the
portrait, and report only honest, recognised situational facts (no verdicts). See
prune/majors/74-residents-travel-between-the-hearth-and-a-city-shard.md.
"""

from __future__ import annotations

from src.familiar.city_world import CityWorld
from src.identity.loader import BRIEFING_FACT_KEYS


class _Scene:
    def __init__(self, location, present):
        self.location = location
        self.present = present
        self.recent_events_here = []


class _FakeClient:
    """Records calls; provides the slice of the Protocol surface CityWorld delegates."""

    def __init__(self, scene):
        self._scene = scene
        self.calls: list = []
        self.closed = False

    async def get_scene(self, session_id):
        self.calls.append(("get_scene", session_id))
        return self._scene

    async def get_grounding(self):
        return {"hour": 12, "time_of_day": "midday"}

    async def get_location_chat(self, location, since=None):
        return []

    async def get_inbox(self, agent_name):
        return []

    async def post_action(self, session_id, action):
        self.calls.append(("post_action", action))
        return type("R", (), {"narrative": "ok"})()

    async def post_location_chat(self, location, session_id, message, display_name=None):
        self.calls.append(("post_location_chat", message))
        return {"ok": True}

    async def post_map_move(self, session_id, destination):
        self.calls.append(("post_map_move", destination))
        return {"moved": True, "to_location": destination, "narrative": "you move"}

    async def send_letter(self, from_name, to_agent, body, session_id, *, recipient_type="agent"):
        return {"ok": True}

    async def close(self):
        self.closed = True


PROTOCOL_METHODS = [
    "get_grounding", "get_scene", "get_location_chat", "get_inbox",
    "post_action", "post_location_chat", "post_map_move", "send_letter", "close",
]


def _world(tmp_path, *, location="Mississippi Ave", present=None):
    client = _FakeClient(_Scene(location, present or []))
    world = CityWorld(client, home_dir=tmp_path, place="the city", familiar_name="Maker", solo=not present)
    return world, client


def test_cityworld_satisfies_the_world_client_protocol(tmp_path):
    world, _ = _world(tmp_path)
    for m in PROTOCOL_METHODS:
        assert callable(getattr(world, m)), f"CityWorld missing Protocol method {m}"
    assert callable(world.situational_facts)


async def test_get_scene_updates_place_as_it_roams(tmp_path):
    world, _ = _world(tmp_path, location="Alberta Arts")
    scene = await world.get_scene("maker-20260614")
    assert scene.location == "Alberta Arts"
    assert world.place == "Alberta Arts"  # the portrait shows where he is now


async def test_speaking_is_captured_for_the_portrait_and_delegated(tmp_path):
    world, client = _world(tmp_path)
    await world.post_location_chat("Alberta Arts", "maker-20260614", "Hello, PDX.")
    assert world.spoken and world.spoken[-1]["text"] == "Hello, PDX."
    assert ("post_location_chat", "Hello, PDX.") in client.calls


async def test_movement_delegates_to_the_client(tmp_path):
    world, client = _world(tmp_path)
    res = await world.post_map_move("maker-20260614", "Hawthorne")
    assert res["to_location"] == "Hawthorne"
    assert ("post_map_move", "Hawthorne") in client.calls


def test_situational_facts_are_honest_recognised_keys_only(tmp_path):
    world, _ = _world(tmp_path)
    facts = world.situational_facts()
    assert set(facts) <= BRIEFING_FACT_KEYS  # no unrendered keys → no drift warning
    assert facts["mobile"] is True and facts["mail"] is True and facts["world_legible"] is True
    assert facts["inner_private"] is True and facts["no_reward"] is True
    # facts/affordances, not verdicts: values are bools or bounded strings (a place name, a travel
    # clause), never an essay about what any of it means.
    for v in facts.values():
        assert isinstance(v, (bool, str))
        if isinstance(v, str):
            assert len(v) < 200
    assert len(str(facts["place"])) < 60  # a place name stays short


def test_solo_flips_peers(tmp_path):
    solo_world, _ = _world(tmp_path, present=[])
    assert solo_world.situational_facts()["solo"] is True
    assert solo_world.situational_facts()["peers"] is False
    crowd_world, _ = _world(tmp_path, present=[object()])
    assert crowd_world.situational_facts()["solo"] is False
    assert crowd_world.situational_facts()["peers"] is True


async def test_close_delegates_to_the_client(tmp_path):
    world, client = _world(tmp_path)
    await world.close()
    assert client.closed


# --- inter-world travel: "go home" is intercepted, not sent to the city backend ---

async def test_go_home_sets_pending_travel_and_does_not_hit_backend(tmp_path):
    world, client = _world(tmp_path)
    res = await world.post_action("maker-x", "go home")
    assert world.pending_travel == ("home", "")
    assert "hearth" in res.narrative.lower()
    assert not any(c[0] == "post_action" for c in client.calls)  # never delegated to the city


async def test_ordinary_city_action_delegates_and_does_not_travel(tmp_path):
    world, client = _world(tmp_path)
    await world.post_action("maker-x", "look around the square")
    assert world.pending_travel is None
    assert ("post_action", "look around the square") in client.calls


def test_city_situational_facts_advertise_going_home(tmp_path):
    world, _ = _world(tmp_path)
    facts = world.situational_facts()
    assert "travel" in facts and "go home" in facts["travel"].lower()
