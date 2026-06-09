"""Structural table-block edits inside a section body.

A "table block" is the first markdown table found in a section: one header
row, one separator row, then data rows — contiguous, with no blank lines or
prose between rows, which is what external renderers require. Tracker rows
were historically appended as paragraphs (finding H-02), fracturing the
table; these helpers rebuild the block contiguously on every write, so any
blessed touch heals a broken tracker (gameplan D3: write-through
normalization, no one-off migration). Non-table lines — legends, prose — are
preserved after the block in their original order.
"""

from __future__ import annotations

import re


def _is_pipe_row(line: str) -> bool:
    return line.strip().startswith("|")


def _is_separator(line: str) -> bool:
    s = line.strip().strip("|").replace("|", "").strip()
    return bool(s) and set(s) <= set("-: ") and "-" in s


def cell(row: str, idx: int) -> str:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return cells[idx] if 0 <= idx < len(cells) else ""


def split(text: str) -> tuple[list[str], list[str], list[str]]:
    """Partition a section into ``(table_head, data_rows, other_lines)``.

    ``table_head`` is the header + separator of the first table; every other
    pipe-prefixed line anywhere in the section counts as a data row — the
    tolerant read that lets a fractured table heal. Everything else lands in
    ``other_lines`` in document order.
    """
    head: list[str] = []
    data: list[str] = []
    other: list[str] = []
    for line in text.splitlines():
        if _is_pipe_row(line):
            if not head:
                head.append(line.strip())
            elif len(head) == 1 and _is_separator(line):
                head.append(line.strip())
            else:
                data.append(line.strip())
        else:
            other.append(line)
    return head, data, other


def _assemble(head: list[str], data: list[str], other: list[str]) -> str:
    rest = re.sub(r"\n{3,}", "\n\n", "\n".join(other)).strip("\n")
    block = "\n".join(head + data)
    if block and rest:
        return f"{block}\n\n{rest}"
    return block or rest


def normalize(text: str) -> str:
    """Rebuild the section as one contiguous table block + trailing prose.

    Idempotent (apply-twice == apply-once); a section without a table passes
    through with only blank-run collapsing.
    """
    return _assemble(*split(text))


def upsert_row(text: str, row: str, *, key_col: int = 0) -> str:
    """Insert ``row`` — or replace the data row sharing its ``key_col`` cell —
    then normalize the block contiguous."""
    head, data, other = split(text)
    row = row.strip()
    if not head:
        # No table in the section yet: the row starts one (callers' templates
        # normally ship a header, so this is a degenerate fallback).
        return _assemble([row], [], other)
    key = cell(row, key_col)
    for i, existing in enumerate(data):
        if cell(existing, key_col) == key:
            data[i] = row
            break
    else:
        data.append(row)
    return _assemble(head, data, other)
