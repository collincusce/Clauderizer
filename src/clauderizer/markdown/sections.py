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


def find_section(text: str, heading: str, *,
                 fuzzy: bool = False) -> tuple[int, int, int] | None:
    """Find a heading by its title (any level).

    Returns ``(heading_line_idx, content_start_idx, content_end_idx)`` as line
    indices, where content runs from the line after the heading up to (but not
    including) the next heading of the same-or-shallower level. Returns ``None``
    if not found.

    Default matching is EXACT-title only — the behavior every read path was
    built against (a broad fuzz here changed handoff composition and broke the
    back-compat golden). ``fuzzy=True`` adds two tolerance tiers for the corpus
    APPEND paths, where a hand-written document's heading may carry a variant
    (field report, 2026-07-02: "Decisions (newest first)" got a duplicate
    ``## Decisions`` appended at end-of-file): case-insensitive exact, then a
    title that STARTS WITH the target followed by a non-word boundary
    ("Decisions (newest first)" matches "Decisions"; "Decision Log" does not).
    Exact always wins.
    """
    target = heading.strip().lstrip("#").strip()
    lines = text.splitlines()

    def _span(i: int, level: int) -> tuple[int, int, int]:
        end = len(lines)
        for j in range(i + 1, len(lines)):
            lvl = _heading_level(lines[j])
            if lvl is not None and lvl <= level:
                end = j
                break
        return i, i + 1, end

    prefix_re = re.compile(re.escape(target) + r"(?:\W|$)", re.IGNORECASE)
    exact_ci: tuple[int, int] | None = None
    prefix: tuple[int, int] | None = None
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if not m:
            continue
        title, level = m.group(2).strip(), len(m.group(1))
        if title == target:
            return _span(i, level)
        if fuzzy and exact_ci is None and title.lower() == target.lower():
            exact_ci = (i, level)
        if fuzzy and prefix is None and prefix_re.match(title):
            prefix = (i, level)
    for hit in (exact_ci, prefix):
        if hit is not None:
            return _span(*hit)
    return None


def get_section(text: str, heading: str, *, fuzzy: bool = False) -> str | None:
    """Return the content of a section (excluding the heading line)."""
    span = find_section(text, heading, fuzzy=fuzzy)
    if span is None:
        return None
    _, start, end = span
    lines = text.splitlines()
    return "\n".join(lines[start:end]).strip("\n")


def upsert_section(text: str, heading: str, content: str, level: int = 2, *,
                   fuzzy: bool = False) -> str:
    """Replace a section's content, or append the section if it doesn't exist.

    ``heading`` is the bare title (no leading ``#``). Idempotent: applying the
    same content twice yields the same document.
    """
    content = content.rstrip("\n")
    span = find_section(text, heading, fuzzy=fuzzy)
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


# Public alias: mutations that manage their own sub-blocks need the same
# "is this still just scaffold?" predicate the append path uses.
is_placeholder = _is_placeholder


def append_to_section(text: str, heading: str, entry: str, level: int = 2, *,
                      fuzzy: bool = False) -> str:
    """Append ``entry`` to the end of a section's existing content.

    A section whose body is empty or just a scaffold placeholder (``_(...)_``) is
    treated as empty, so the first real entry replaces the placeholder instead of
    stacking beneath it. ``fuzzy=True`` (the corpus-append paths) tolerates a
    hand-written heading variant instead of creating a duplicate section.
    """
    existing = get_section(text, heading, fuzzy=fuzzy)
    entry = entry.rstrip("\n")
    if existing is None or not existing.strip() or _is_placeholder(existing):
        return upsert_section(text, heading, entry, level=level, fuzzy=fuzzy)
    combined = existing.rstrip("\n") + "\n\n" + entry
    return upsert_section(text, heading, combined, level=level, fuzzy=fuzzy)


# --- marker blocks ------------------------------------------------------------


def _markers(name: str) -> tuple[str, str]:
    return f"<!-- {name}:start -->", f"<!-- {name}:end -->"


def has_marker_block(text: str, name: str) -> bool:
    start, end = _markers(name)
    return start in text and end in text


RECOVERY_BANNER = "<!-- moved out of the clauderizer-managed block by clauderize init -->"

# Foreign content inside the managed block starts at the first H1 heading: the
# stanza is engine prose under an H2 and never contains one, while a project
# section pasted inside the markers (the observed field failure: an entire
# project overview living before the end marker) always does. Deterministic —
# no similarity heuristics — and upgrade-safe: replacing an older stanza whose
# wording changed recovers nothing, because old stanzas contain no H1 either.
_FOREIGN_START_RE = re.compile(r"^# ", re.M)


def split_foreign_interior(interior: str) -> tuple[str, str]:
    """``(engine_part, foreign_part)`` of a managed block's interior.

    ``foreign_part`` is everything from the first H1 line onward (plus an
    immediately preceding ``---`` separator); empty when the interior holds
    only engine content."""
    m = _FOREIGN_START_RE.search(interior)
    if not m:
        return interior, ""
    cut = m.start()
    head = interior[:cut]
    trimmed = head.rstrip()
    if trimmed.endswith("---"):
        cut -= len(head) - head.rfind("---")
        head = interior[:cut]
    return head, interior[cut:]


def upsert_marker_block(text: str, name: str, content: str) -> str:
    """Insert or replace a marker-delimited block, losing nothing.

    Idempotent. If the markers exist, only the content between them changes;
    text outside the markers is byte-preserved. Content that plainly is not
    the engine's (an H1-headed section living INSIDE the markers — the way a
    project overview ends up truncated by a naive replace) is moved out below
    the block under :data:`RECOVERY_BANNER` instead of being deleted.
    """
    start, end = _markers(name)
    block = f"{start}\n{content.rstrip(chr(10))}\n{end}"
    if has_marker_block(text, name):
        pattern = re.compile(
            re.escape(start) + r"\n?(.*?)\n?" + re.escape(end), re.DOTALL
        )
        m = pattern.search(text)
        _engine, foreign = split_foreign_interior(m.group(1))
        replacement = block
        if foreign.strip():
            replacement = (
                f"{block}\n\n{RECOVERY_BANNER}\n\n{foreign.strip(chr(10))}"
            )
        return text[:m.start()] + replacement + text[m.end():]
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


def remove_marker_block(text: str, name: str) -> str:
    """Delete a marker-delimited block, preserving everything outside it.

    The inverse of :func:`upsert_marker_block` (the P4-noted extension, used by
    ``clauderize uninstall``). Idempotent: with no such block the text is
    returned unchanged. The hole left behind is collapsed (the blank line that
    joined the block is absorbed) so removing an appended stanza restores the
    prior text; a document that was ONLY the block becomes empty (``""``), which
    the caller may then delete.
    """
    start, end = _markers(name)
    if not has_marker_block(text, name):
        return text
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    stripped = pattern.sub("", text, count=1)
    stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    body = stripped.strip("\n")
    return body + "\n" if body else ""


# --- entry lifecycle status: the ONE canonical grammar (D-065) -----------------
#
# Both writers in mutations.py emit a Status line, in two shapes:
#   decisions / invariants : ``**Status**: active (2026-07-24)``
#   hardening findings     : ``- **Status**: resolved (2026-07-24)``  <- list bullet
# Three readers each had their own pattern and only ONE tolerated the bullet, so
# cz_list_findings reported all 20 findings ``active`` with ``date: null`` while
# docs/HARDENING.md said 17 resolved and 3 open. This module is the leaf (it
# imports only ``re``), which is why the canonical definition lives here rather
# than in analyze.py: graph.abstract_index can import it eagerly without the
# cycle that forces its analyze import to be lazy.
#
# Group 1 is the state; group 2 is the optional parenthetical annotation (a date,
# or "by D-NNN"). Enforced single-source by tests/test_canonical_parsers.py, the
# same discipline INVARIANT-09 applies to analyze._tokens.
ENTRY_STATUS_RE = re.compile(
    r"^\s*(?:[-*]\s*)?\*\*Status\*\*\s*:\s*([a-z]+)\s*(?:\(([^)]*)\))?",
    re.M | re.I)

#: What :func:`entry_status` returns in ``source`` when no Status line was found.
STATUS_DEFAULTED = "defaulted"
#: ...and when one was actually read.
STATUS_PARSED = "parsed"


def entry_status(body: str, *, default: str = "active") -> tuple[str, str, str | None]:
    """``(status, source, annotation)`` for a ``### ID — title`` entry body.

    ``source`` is :data:`STATUS_PARSED` when the Status line was actually read and
    :data:`STATUS_DEFAULTED` when it was absent. That distinction is the point
    (D-065): a register reporting every entry ``active`` because its parser
    matched nothing must be distinguishable from one whose entries really are
    active. A missing line is legitimate for older entries and for invariants —
    it is a *default*, not an error — but a caller that cannot tell the two apart
    is asserting a property from evidence it never read.

    ``annotation`` is the parenthetical text when present (usually a date), else
    ``None``.
    """
    m = ENTRY_STATUS_RE.search(body or "")
    if m is None:
        return default, STATUS_DEFAULTED, None
    return m.group(1).lower(), STATUS_PARSED, (m.group(2) or None)
