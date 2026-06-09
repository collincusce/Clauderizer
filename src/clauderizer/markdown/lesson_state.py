"""The single grammar for lesson-state markers (gameplan D8).

A lesson line's *state* lives in a structured marker at the very end of the
line — ``(obsolete <date>[: reason])`` or ``(promoted <date>: L-NN)`` — or in
legacy whole-line ``~~strikethrough~~``. Mentions of those words anywhere else
in the text are inert: a lesson *about* obsolescence is not obsolete. Every
consumer (the memory gauge, handoff roll-ups, obsolete/promote/consolidate
validation) parses through here; nothing substring-matches lesson state.
"""

from __future__ import annotations

import re

ACTIVE = "active"
OBSOLETE = "obsolete"
PROMOTED = "promoted"

# The trailing structured marker: "(obsolete 2026-06-09: reason)",
# "(promoted 2026-06-09: L-04)". Anchored to end of line — that is the grammar.
_STATE_RE = re.compile(r"\((obsolete|promoted)\b([^()]*)\)\s*$", re.IGNORECASE)


def parse_state(line: str) -> tuple[str, str]:
    """Return ``(state, detail)`` for a lesson line.

    ``state`` is ``active``, ``obsolete`` or ``promoted``; ``detail`` is the
    marker payload (date, reason, target id) when present.
    """
    s = line.strip()
    if s.startswith("~~"):
        return OBSOLETE, "struck through"
    m = _STATE_RE.search(s)
    if m:
        return m.group(1).lower(), m.group(2).strip(" :")
    return ACTIVE, ""


def is_active(line: str) -> bool:
    return parse_state(line)[0] == ACTIVE


def mark(line: str, state: str, date: str, detail: str = "") -> str:
    """Append a trailing state marker to a lesson line.

    Produces exactly the documented forms: ``(obsolete <date>)``,
    ``(obsolete <date>: reason)``, ``(promoted <date>: L-NN)``.
    """
    payload = f"{state} {date}" + (f": {detail}" if detail else "")
    return f"{line.rstrip()} ({payload})"
