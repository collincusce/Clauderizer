"""Locate and edit ``## Heading`` sections and ``<!-- marker -->`` blocks.

Operates on a document *body* (frontmatter already stripped). All functions are
pure: they take text and return new text, never mutating in place.
"""

from __future__ import annotations

import re

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def _heading_level(line: str) -> int | None:
    m = _HEADING_RE.match(line)
    return len(m.group(1)) if m else None


def find_section(text: str, heading: str) -> tuple[int, int, int] | None:
    """Find a heading by its title (any level).

    Returns ``(heading_line_idx, content_start_idx, content_end_idx)`` as line
    indices, where content runs from the line after the heading up to (but not
    including) the next heading of the same-or-shallower level. Returns ``None``
    if not found.
    """
    target = heading.strip().lstrip("#").strip()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if m and m.group(2).strip() == target:
            level = len(m.group(1))
            end = len(lines)
            for j in range(i + 1, len(lines)):
                lvl = _heading_level(lines[j])
                if lvl is not None and lvl <= level:
                    end = j
                    break
            return i, i + 1, end
    return None


def get_section(text: str, heading: str) -> str | None:
    """Return the content of a section (excluding the heading line)."""
    span = find_section(text, heading)
    if span is None:
        return None
    _, start, end = span
    lines = text.splitlines()
    return "\n".join(lines[start:end]).strip("\n")


def upsert_section(text: str, heading: str, content: str, level: int = 2) -> str:
    """Replace a section's content, or append the section if it doesn't exist.

    ``heading`` is the bare title (no leading ``#``). Idempotent: applying the
    same content twice yields the same document.
    """
    content = content.rstrip("\n")
    span = find_section(text, heading)
    lines = text.splitlines()
    if span is None:
        prefix = text.rstrip("\n")
        hashes = "#" * level
        block = f"{hashes} {heading}\n\n{content}\n"
        if prefix:
            return f"{prefix}\n\n{block}"
        return block
    h_idx, start, end = span
    new_lines = lines[:start] + ["", *content.splitlines(), ""] + lines[end:]
    # Normalize: collapse the leading inserted blank if heading already followed
    # by nothing, and trailing blanks before next heading.
    rebuilt = "\n".join(new_lines)
    rebuilt = re.sub(r"\n{3,}", "\n\n", rebuilt)
    return rebuilt.rstrip("\n") + "\n"


_PLACEHOLDER_RE = re.compile(r"^_\(.*\)_$", re.DOTALL)


def _is_placeholder(content: str) -> bool:
    """True if a section body is only a scaffold placeholder like ``_(add here)_``."""
    return bool(_PLACEHOLDER_RE.match(content.strip()))


def append_to_section(text: str, heading: str, entry: str, level: int = 2) -> str:
    """Append ``entry`` to the end of a section's existing content.

    A section whose body is empty or just a scaffold placeholder (``_(...)_``) is
    treated as empty, so the first real entry replaces the placeholder instead of
    stacking beneath it.
    """
    existing = get_section(text, heading)
    entry = entry.rstrip("\n")
    if existing is None or not existing.strip() or _is_placeholder(existing):
        return upsert_section(text, heading, entry, level=level)
    combined = existing.rstrip("\n") + "\n\n" + entry
    return upsert_section(text, heading, combined, level=level)


# --- marker blocks ------------------------------------------------------------


def _markers(name: str) -> tuple[str, str]:
    return f"<!-- {name}:start -->", f"<!-- {name}:end -->"


def has_marker_block(text: str, name: str) -> bool:
    start, end = _markers(name)
    return start in text and end in text


def upsert_marker_block(text: str, name: str, content: str) -> str:
    """Insert or replace a marker-delimited block, preserving everything else.

    Idempotent. If the markers exist, only the content between them changes;
    text outside the markers is byte-preserved.
    """
    start, end = _markers(name)
    block = f"{start}\n{content.rstrip(chr(10))}\n{end}"
    if has_marker_block(text, name):
        pattern = re.compile(
            re.escape(start) + r".*?" + re.escape(end), re.DOTALL
        )
        return pattern.sub(lambda _: block, text, count=1)
    prefix = text.rstrip("\n")
    if prefix:
        return f"{prefix}\n\n{block}\n"
    return block + "\n"


def get_marker_block(text: str, name: str) -> str | None:
    start, end = _markers(name)
    if not has_marker_block(text, name):
        return None
    s = text.index(start) + len(start)
    e = text.index(end)
    return text[s:e].strip("\n")
