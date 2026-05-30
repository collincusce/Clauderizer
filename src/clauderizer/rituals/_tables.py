"""Shared helpers for parsing the markdown the rituals read."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..markdown import sections

_STATUS_WORDS = {
    "COMPLETE": "complete",
    "IN PROGRESS": "in_progress",
    "NOT STARTED": "not_started",
    "READY": "ready",
    "BLOCKED": "blocked",
    "FAILED": "failed",
}


@dataclass
class PhaseRow:
    number: str
    name: str
    status: str  # normalized
    raw_status: str


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
        if word in up:
            return norm
    return "unknown"
