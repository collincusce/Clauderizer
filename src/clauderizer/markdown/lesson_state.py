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

# A lesson line's anchor — the "**N.**" numbered-entry prefix. The single shared
# matcher for "is this a lesson line", used by the memory gauge, handoff
# roll-ups, and the critique gate (one grammar, one home).
LESSON_LINE_RE = re.compile(r"\*\*\d+\.\*\*")

# The trailing structured marker: "(obsolete 2026-06-09: reason)",
# "(promoted 2026-06-09: L-04)". Anchored to end of line — that is the grammar.
# The payload tolerates one level of nested parentheses so a reason like
# "(obsolete 2026-06-09: superseded (see L-50))" still parses as the marker
# instead of reading the line as active (H-18); the end-anchor + "\b" after the
# keyword keep mid-text mentions inert.
_STATE_RE = re.compile(
    r"\((obsolete|promoted)\b([^()]*(?:\([^()]*\)[^()]*)*)\)\s*$", re.IGNORECASE
)


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
