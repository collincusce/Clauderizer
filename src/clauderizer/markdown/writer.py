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

from . import frontmatter, sections


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _write_if_changed(path: Path, new_text: str) -> bool:
    old = _read(path)
    if old == new_text:
        return False
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


def append_to_section(path: Path, heading: str, entry: str, level: int = 2) -> bool:
    text = _read(path)
    data, body = frontmatter.parse(text)
    new_body = sections.append_to_section(body, heading, entry, level=level)
    return _write_if_changed(path, frontmatter.serialize(data, new_body))


def upsert_marker_block(path: Path, name: str, content: str) -> bool:
    text = _read(path)
    new_text = sections.upsert_marker_block(text, name, content)
    return _write_if_changed(path, new_text)


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


def create_if_absent(path: Path, content: str) -> bool:
    """Write ``content`` only if the file does not already exist (scaffolding)."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def body_of(path: Path) -> str:
    _, body = frontmatter.parse(_read(path))
    return body


def full_text(path: Path) -> str:
    return _read(path)
