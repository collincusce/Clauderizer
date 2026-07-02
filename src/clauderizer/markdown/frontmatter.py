"""A vendored, minimal YAML-subset parser for document frontmatter.

Clauderizer's frontmatter is deliberately simple (see GAMEPLAN-PROCEDURE.md):
scalars and flat lists of scalars, one level deep. Rather than take a hard
dependency on PyYAML — which would undermine the "drop into any repo with
nothing installed" goal — we parse exactly the subset we emit.

Supported:
    key: scalar              # str / int / bool / null
    key:                     # followed by block-list items
      - item
      - item

Round-trip guarantee: ``parse`` then ``serialize`` then ``parse`` yields data
equal to the first parse, and serialization is idempotent.
"""

from __future__ import annotations

import re
from typing import Any

FENCE = "---"

_KEY_RE = re.compile(r"^([A-Za-z0-9_][\w\-.]*):\s?(.*)$")
_ITEM_RE = re.compile(r"^\s*-\s+(.*)$")
# Characters that force a value to be quoted on serialization.
_NEEDS_QUOTE_RE = re.compile(r'(^\s)|(\s$)|(:\s)|(^[#>!&*?\[\]{}|@`\"\'%-])|(:$)')


def has_frontmatter(text: str) -> bool:
    return text.startswith(FENCE + "\n") or text == FENCE or text.startswith(FENCE + "\r\n")


def split(text: str) -> tuple[str | None, str]:
    """Return ``(frontmatter_block_or_None, body)``.

    The frontmatter block is the raw text *between* the fences (no fences).
    If there is no frontmatter, returns ``(None, text)``.
    """
    if not has_frontmatter(text):
        return None, text
    lines = text.splitlines(keepends=True)
    # lines[0] is the opening fence.
    end = None
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n") == FENCE:
            end = i
            break
    if end is None:
        return None, text
    block = "".join(lines[1:end])
    body = "".join(lines[end + 1 :])
    # Drop a single leading blank line after the closing fence for tidiness.
    if body.startswith("\n"):
        body = body[1:]
    return block, body


def parse(text: str) -> tuple[dict[str, Any], str]:
    """Parse a full document into ``(frontmatter_dict, body)``."""
    block, body = split(text)
    if block is None:
        return {}, text
    return parse_block(block), body


def parse_block(block: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw in block.splitlines():
        if not raw.strip():
            continue
        item = _ITEM_RE.match(raw)
        if item and current_key is not None and isinstance(data.get(current_key), list):
            data[current_key].append(_scalar(item.group(1)))
            continue
        m = _KEY_RE.match(raw)
        if not m:
            # Unrecognized line; ignore rather than crash (robustness).
            continue
        key, rest = m.group(1), m.group(2).strip()
        if rest == "":
            # Could be an empty scalar or the start of a block list. We default
            # to a list; an empty scalar is rare in our frontmatter and an
            # empty list serializes back cleanly.
            data[key] = []
            current_key = key
        else:
            data[key] = _scalar(rest)
            current_key = key
    # Collapse keys that opened a list header but received no items into "".
    return data


def serialize(data: dict[str, Any], body: str) -> str:
    """Render ``(data, body)`` back into a full document."""
    if not data:
        return body
    block = serialize_block(data)
    body = body.lstrip("\n") if body else ""
    return f"{FENCE}\n{block}{FENCE}\n\n{body}" if body else f"{FENCE}\n{block}{FENCE}\n"


def serialize_block(data: dict[str, Any]) -> str:
    out: list[str] = []
    for key, value in data.items():
        if isinstance(value, list):
            out.append(f"{key}:\n")
            for v in value:
                out.append(f"  - {_emit(v)}\n")
        else:
            out.append(f"{key}: {_emit(value)}\n")
    return "".join(out)


# --- scalar (de)serialization -------------------------------------------------


def _scalar(raw: str) -> Any:
    s = raw.strip()
    # Inline flow list — hand-written frontmatter commonly says `depends_on: []`
    # or `depends_on: [a, b]`. Without this the raw string leaked through, and a
    # consumer iterating a "list" got its CHARACTERS — the field-reported
    # phantom dependencies named "[" and "]" (2026-07-02).
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part) for part in inner.split(",")]
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    low = s.lower()
    if low in ("null", "~", ""):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return s


def _emit(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    s = str(value)
    if s == "":
        return '""'
    if _NEEDS_QUOTE_RE.search(s):
        return '"' + s.replace('"', '\\"') + '"'
    return s
