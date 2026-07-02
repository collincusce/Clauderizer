"""The single sanctioned mutation path for markdown files.

Every tool that changes a doc goes through here. Centralizing writes is what
makes mutations idempotent and keeps frontmatter valid — no tool ever does a
free-form string replace on a document.

Each function returns ``True`` if the file changed on disk, ``False`` if the
operation was a no-op (the idempotency signal the tests assert on).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import frontmatter, sections, tables


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def refuse_if_symlink(path: Path) -> None:
    """Refuse to write through a symlinked target.

    Engine-owned writes must land inside the repo. If ``path`` is a symlink, a
    pre-planted link in a hostile cloned working tree could redirect the write to
    an attacker-chosen location outside the repo, so we refuse rather than follow
    it — the link is never followed or deleted; the user reviews and removes it.
    """
    if path.is_symlink():
        raise OSError(
            f"refusing to write through a symlink: {path} — Clauderizer never "
            "writes through links; review your working tree and remove the link."
        )


def _write_if_changed(path: Path, new_text: str) -> bool:
    old = _read(path)
    if old == new_text:
        return False
    refuse_if_symlink(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new_text, encoding="utf-8")
    return True


def set_frontmatter_fields(path: Path, fields: dict[str, Any]) -> bool:
    """Merge ``fields`` into a document's frontmatter (creating it if absent)."""
    text = _read(path)
    data, body = frontmatter.parse(text)
    data = dict(data)
    data.update(fields)
    return _write_if_changed(path, frontmatter.serialize(data, body))


def write_entity(
    path: Path,
    data: dict[str, Any],
    body: str = "",
    *,
    preserve_body: bool = True,
) -> bool:
    """Create or update a frontmatter entity document.

    With ``preserve_body`` (default), an existing file's body is kept and only
    its frontmatter is merged — so re-running ``init`` or an upsert never clobbers
    prose someone wrote. A fresh file gets ``body``.
    """
    existing = _read(path)
    old_data, old_body = frontmatter.parse(existing)
    if existing and preserve_body:
        merged = dict(old_data)
        merged.update(data)
        out = frontmatter.serialize(merged, old_body)
    else:
        out = frontmatter.serialize(data, body)
    return _write_if_changed(path, out)


def upsert_section(path: Path, heading: str, content: str, level: int = 2) -> bool:
    text = _read(path)
    data, body = frontmatter.parse(text)
    new_body = sections.upsert_section(body, heading, content, level=level)
    return _write_if_changed(path, frontmatter.serialize(data, new_body))


def append_to_section(path: Path, heading: str, entry: str, level: int = 2, *,
                      fuzzy: bool = False) -> bool:
    text = _read(path)
    data, body = frontmatter.parse(text)
    new_body = sections.append_to_section(body, heading, entry, level=level,
                                          fuzzy=fuzzy)
    return _write_if_changed(path, frontmatter.serialize(data, new_body))


def upsert_marker_block(path: Path, name: str, content: str) -> bool:
    text = _read(path)
    new_text = sections.upsert_marker_block(text, name, content)
    return _write_if_changed(path, new_text)


def remove_marker_block(path: Path, name: str) -> bool:
    """Strip a marker block from a file, preserving the user's other content.

    The blessed reversal for ``clauderize uninstall`` (P8). Returns ``False`` if
    the file is absent or has no such block. When the block was the file's entire
    content, the now-empty file is deleted rather than left as a stray empty
    stub.
    """
    if not path.exists():
        return False
    text = _read(path)
    new_text = sections.remove_marker_block(text, name)
    if new_text == text:
        return False
    if not new_text.strip():
        path.unlink()
        return True
    refuse_if_symlink(path)
    path.write_text(new_text, encoding="utf-8")
    return True


def set_labeled_value(path: Path, label: str, value: str) -> bool:
    """Update the value of the first ``**Label**: value`` line in a document.

    The bold-label line is a recurring idiom in the tracked docs (baseline test
    count, finding fields); this is the structured write for refreshing one.
    Returns ``False`` when no such line exists (callers treat that as "this doc
    doesn't track the value" rather than an error).
    """
    text = _read(path)
    pattern = re.compile(rf"^(\s*\*\*{re.escape(label)}\*\*\s*:\s*).*$", re.M)
    if not pattern.search(text):
        return False
    new_text = pattern.sub(lambda m: m.group(1) + value, text, count=1)
    return _write_if_changed(path, new_text)


def set_blockquote_field(path: Path, label: str, value: str) -> bool:
    """Update the first ``> Label: value`` header line of a document.

    Tracker docs carry their living state in blockquote header lines
    (``> Status: …``, ``> Last updated: …``); these rotted for two whole
    gameplans because no blessed write owned them. Engine-owned now
    (gameplan D7) — agents and humans never hand-edit them. Returns
    ``False`` when the doc has no such line.
    """
    text = _read(path)
    pattern = re.compile(rf"^(>\s*{re.escape(label)}\s*:\s*).*$", re.M)
    if not pattern.search(text):
        return False
    new_text = pattern.sub(lambda m: m.group(1) + value, text, count=1)
    return _write_if_changed(path, new_text)


def upsert_table_row(path: Path, heading: str, row: str, *, key_col: int = 0,
                     level: int = 2) -> bool:
    """Insert or update one row of the table block under ``heading``.

    The structured write for tracker tables: the row joins (or replaces, by
    key cell) the section's first table block, and the whole block is
    rebuilt contiguous — so a historically fractured table (H-02) heals on
    any blessed touch. Returns ``False`` when the section doesn't exist.
    """
    text = _read(path)
    data, body = frontmatter.parse(text)
    sec = sections.get_section(body, heading)
    if sec is None:
        return False
    new_sec = tables.upsert_row(sec, row, key_col=key_col)
    new_body = sections.upsert_section(body, heading, new_sec, level=level)
    return _write_if_changed(path, frontmatter.serialize(data, new_body))


def create_if_absent(path: Path, content: str) -> bool:
    """Write ``content`` only if the file does not already exist (scaffolding)."""
    if path.exists():
        return False
    refuse_if_symlink(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def body_of(path: Path) -> str:
    _, body = frontmatter.parse(_read(path))
    return body


def full_text(path: Path) -> str:
    return _read(path)
