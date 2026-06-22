"""The single grammar for skill-state markers (skill-awareness D1).

Mirrors ``lesson_state``: a skill line's *state* lives in a trailing structured
marker at the very end of the line -- ``(obsolete <date>[: reason])`` or
``(superseded <date>: S-NN)``. Mentions of those words anywhere else in the line
are inert. Every consumer (the memory gauge, handoff roll-ups,
obsolete/supersede validation, discovery's already-registered diff) parses
through here; nothing substring-matches skill state.

Divergence from lessons: skills *supersede* (a newer skill replaces an older
one) where lessons *promote* (gameplan -> project). Skills are already
project-level, so there is no promotion tier. A skill entry also carries
structured fields (name, description, source), so this module owns the entry
grammar (``format_entry`` / ``parse_entry``) as well as the state marker.
"""

from __future__ import annotations

import re

ACTIVE = "active"
OBSOLETE = "obsolete"
SUPERSEDED = "superseded"

EMDASH = "—"  # the "name -- description" separator (literal U+2014; module is UTF-8)

# A skill line's anchor -- the "**S-NN.**" numbered-entry prefix. The single
# shared matcher for "is this a skill line", used by the memory gauge and
# handoff roll-ups (one grammar, one home).
SKILL_LINE_RE = re.compile(r"\*\*S-\d+\.\*\*")

# The trailing structured marker: "(obsolete 2026-06-22: reason)",
# "(superseded 2026-06-22: S-04)". Anchored to end of line -- that is the grammar.
_STATE_RE = re.compile(r"\((obsolete|superseded)\b([^()]*)\)\s*$", re.IGNORECASE)

# A full entry: "**S-NN.** name -- description *(source: ...)*". Name is
# non-greedy up to the first " -- "; the remainder is the description (plus an
# optional source marker and state marker, both stripped by parse_entry).
_ENTRY_RE = re.compile(
    rf"\*\*(?P<id>S-\d+)\.\*\*\s*(?P<name>.+?)\s+{EMDASH}\s+(?P<rest>.*)$"
)
_SOURCE_RE = re.compile(r"\*\(source:\s*(?P<source>.+?)\)\*\s*$")


def parse_state(line: str) -> tuple[str, str]:
    """Return ``(state, detail)`` for a skill line.

    ``state`` is ``active``, ``obsolete`` or ``superseded``; ``detail`` is the
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
    """Append a trailing state marker to a skill line.

    Produces exactly the documented forms: ``(obsolete <date>)``,
    ``(obsolete <date>: reason)``, ``(superseded <date>: S-NN)``.
    """
    payload = f"{state} {date}" + (f": {detail}" if detail else "")
    return f"{line.rstrip()} ({payload})"


def format_entry(skill_id: str, name: str, description: str,
                 source: str | None = None) -> str:
    """Render a skill entry line. Inverse of :func:`parse_entry`."""
    line = f"**{skill_id}.** {name.strip()} {EMDASH} {description.strip()}"
    if source and source.strip():
        line += f" *(source: {source.strip()})*"
    return line


def parse_entry(line: str) -> dict | None:
    """Parse a skill entry into ``{id, name, description, source, state}``.

    Returns ``None`` for non-entry lines (headings, lesson lines, prose, or a
    legacy struck-through line that carries no " -- " field separator).
    """
    s = line.strip()
    m = _ENTRY_RE.match(s)
    if not m:
        return None
    state = parse_state(s)[0]
    rest = _STATE_RE.sub("", m.group("rest")).strip()
    source = None
    sm = _SOURCE_RE.search(rest)
    if sm:
        source = sm.group("source").strip()
        rest = rest[: sm.start()].strip()
    return {
        "id": m.group("id"),
        "name": m.group("name").strip(),
        "description": rest,
        "source": source,
        "state": state,
    }
