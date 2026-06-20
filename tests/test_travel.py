# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Levi Banks

"""Tests for inter-world travel parsing (src/familiar/travel.py).

Inter-world travel (hearth ↔ city) is distinguished from within-world movement by its
destination: a known city name, or home/hearth. See prune/majors/74-*.
"""

from __future__ import annotations

from src.familiar.travel import parse_travel

CITIES = {"portland", "seattle"}


def test_travel_to_known_city():
    assert parse_travel("travel to portland", cities=CITIES, allow_home=False) == ("city", "portland")
    assert parse_travel("I head to Seattle now", cities=CITIES, allow_home=False) == ("city", "seattle")
    assert parse_travel("go to the city of portland", cities=CITIES, allow_home=False) == ("city", "portland")


def test_bare_city_name_is_travel():
    assert parse_travel("portland", cities=CITIES, allow_home=False) == ("city", "portland")
    assert parse_travel("the city of seattle", cities=CITIES, allow_home=False) == ("city", "seattle")


def test_go_home_only_when_allowed():
    assert parse_travel("go home", cities=CITIES, allow_home=True) == ("home", "")
    assert parse_travel("I'll head back to the hearth", cities=CITIES, allow_home=True) == ("home", "")
    # at the hearth, home is not a travel destination (you are already home)
    assert parse_travel("go home", cities=CITIES, allow_home=False) is None


def test_within_world_movement_is_not_inter_world_travel():
    # moving to a place that is NOT a known city → ordinary movement, the effector handles it
    assert parse_travel("move to Alberta Arts", cities=CITIES, allow_home=True) is None
    assert parse_travel("walk to the park", cities=CITIES, allow_home=False) is None


def test_empty_and_noise():
    assert parse_travel("", cities=CITIES, allow_home=True) is None
    assert parse_travel("I feel restless and unsure", cities=CITIES, allow_home=True) is None


def test_no_cities_means_no_city_travel_but_home_still_works():
    assert parse_travel("travel to portland", cities=set(), allow_home=False) is None
    assert parse_travel("go home", cities=set(), allow_home=True) == ("home", "")
