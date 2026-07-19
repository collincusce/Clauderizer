"""Shared helpers for parsing the markdown the rituals read."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..markdown import sections

# Recognized status vocabulary, matched on WORD BOUNDARIES inside the cell so
# decorated rows ("🟡 READY — kickoff", "⬜ GATED (deps)") normalize instead of
# vanishing (field bug, 2026-07-02). Dict order is match priority. Synonyms map
# to the canonical six; anything else normalizes to "unknown" and the
# transition error names both what was found and this vocabulary.
_STATUS_WORDS = {
    "NOT STARTED": "not_started",
    "IN PROGRESS": "in_progress",
    "COMPLETED": "complete",
    "COMPLETE": "complete",
    "DONE": "complete",
    "READY": "ready",
    "PENDING": "not_started",
    "TODO": "not_started",
    "GATED": "blocked",
    "WAITING": "blocked",
    "PAUSED": "blocked",
    "BLOCKED": "blocked",
    "FAILED": "failed",
}


@dataclass
class PhaseRow:
    number: str
    name: str
    status: str  # normalized
    raw_status: str


@dataclass
class FullPhaseRow(PhaseRow):
    """A phase row with the tracker table's remaining cells (O-11): the
    Started / Completed / Handoff columns, ``None`` when the cell is an em-dash
    placeholder or the table predates the column."""

    started: str | None = None
    completed: str | None = None
    handoff: str | None = None


def _cell_or_none(cells: list[str], i: int) -> str | None:
    if i >= len(cells):
        return None
    v = cells[i].strip()
    return v if v and v not in ("—", "-", "–") else None


def parse_phase_table_full(text: str) -> list[FullPhaseRow]:
    """``parse_phase_table`` plus the date/handoff cells, same row detection."""
    out: list[FullPhaseRow] = []
    for heading in ("Phase Status Table", "Phase Status"):
        sec = sections.get_section(text, heading)
        if sec:
            rows = _full_rows_from_table(sec)
            if rows:
                return rows
    return _full_rows_from_table(text)


def _full_rows_from_table(text: str) -> list[FullPhaseRow]:
    rows: list[FullPhaseRow] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        num = cells[0]
        if not re.match(r"^\d+[A-Za-z]?$", num):
            continue
        raw_status = cells[2]
        rows.append(FullPhaseRow(
            number=num,
            name=cells[1],
            status=_normalize_status(raw_status),
            raw_status=raw_status,
            started=_cell_or_none(cells, 3),
            completed=_cell_or_none(cells, 4),
            handoff=_cell_or_none(cells, 5),
        ))
    return rows


def parse_phase_table(text: str) -> list[PhaseRow]:
    """Parse a phase-status markdown table from a handoff-index / status doc.

    Looks under a 'Phase Status' heading first, then falls back to the first
    table whose header mentions 'Phase'.
    """
    body = text
    for heading in ("Phase Status Table", "Phase Status"):
        sec = sections.get_section(body, heading)
        if sec:
            rows = _rows_from_table(sec)
            if rows:
                return rows
    return _rows_from_table(body)


def _rows_from_table(text: str) -> list[PhaseRow]:
    rows: list[PhaseRow] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        num = cells[0]
        # skip header + separator rows
        if not re.match(r"^\d+[A-Za-z]?$", num):
            continue
        raw_status = cells[2]
        rows.append(
            PhaseRow(
                number=num,
                name=cells[1],
                status=_normalize_status(raw_status),
                raw_status=raw_status,
            )
        )
    return rows


def _normalize_status(raw: str) -> str:
    up = raw.upper()
    for word, norm in _STATUS_WORDS.items():
        # Word-boundary match: "INCOMPLETE" must not read as COMPLETE.
        if re.search(rf"(?<![A-Z]){re.escape(word)}(?![A-Z])", up):
            return norm
    return "unknown"
