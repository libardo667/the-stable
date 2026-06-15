"""Travel — parsing a resident's intent to move BETWEEN worlds (hearth ↔ city).

This is distinct from movement *within* a world (the effector's ``move`` → the city's
map). Inter-world travel is recognised by its destination: a known **city name**, or
**home/hearth**. A world recognises a travel act among its own destinations, returns a
clean acknowledgement, and sets ``pending_travel`` for the daemon to act on after the
tick (the daemon owns world lifecycle; the world only signals). Pure, no I/O.
"""

from __future__ import annotations

import re

# A verb that leads somewhere ("travel to …", "head to …", "go to …", "set out for …").
_VERB = r"(?:travel|journey|go|head|walk|set\s*out|depart|move|leave|return)"
# "go home" / "head back to the hearth" / "return home" — needs the home/hearth word.
_HOME_RX = re.compile(r"\b(?:go|head|return|back|come|travel|journey|set\s*out)\b[^.!?]*\b(?:home|hearth)\b", re.IGNORECASE)


def parse_travel(text: str, *, cities, allow_home: bool) -> tuple[str, str] | None:
    """Classify a free-text act as inter-world travel.

    Returns ``("city", <canonical-name>)``, ``("home", "")``, or ``None``.

    - ``cities``: the known city destinations (names; matched case-insensitively).
    - ``allow_home``: whether "home/hearth" is a valid destination from here (False at
      the hearth — you're already home; True out in a city).
    """
    t = " ".join(str(text or "").split())
    if not t:
        return None
    low = t.lower()

    if allow_home and _HOME_RX.search(low):
        return ("home", "")

    names = {str(c).strip().lower() for c in (cities or []) if str(c).strip()}
    for name in sorted(names, key=len, reverse=True):  # longest name first (avoid prefix shadowing)
        if low == name or low == f"the city of {name}":
            return ("city", name)
        if re.search(rf"\b{_VERB}\b.*\b{re.escape(name)}\b", low):
            return ("city", name)
    return None
