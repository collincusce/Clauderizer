"""ARCHITECTURE.md's subsystem overview is pinned to the directory it describes.

L-65: a doc that enumerates a code-owned surface drifts SILENTLY, and the fix is
an executable seam at exactly the boundary — never sweep discipline, which is a
promise to remember. The README's MCP tool list proved it once by sitting 14
tools behind for a release.

This doc had the same shape and the same rot: it opened "Eight tracked
subsystems" and stayed that way while `docs/subsystems/` went to 40 — stale
within the very gameplan that added the other 32. Nothing failed, because prose
has no test. Now it does.

The three pins below are the whole guarantee, and it is narrow on purpose: they
prove the overview *names* every subsystem and states the *right count*. No
mechanical check can tell whether the one-line description is still accurate,
and claiming otherwise would be the false green this line of work exists to end.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def _repo_engine_docs():
    """This repo's ENGINE-owned docs root, honouring its docs layout (D-080).

    Hardcoding `ROOT / "docs"` broke the moment the engine's own repo migrated —
    which is exactly the drift these seam tests exist to catch, so they resolve
    it the way the engine does rather than assuming a layout.
    """
    from clauderizer.paths import resolve_for_repo
    return resolve_for_repo(ROOT).engine_docs_root
ARCH = ROOT / "docs" / "ARCHITECTURE.md"
SUBSYS_DOCS = _repo_engine_docs() / "subsystems"

#: The count sentence, e.g. "— 40 of them, and the exemption list is empty".
_COUNT_CLAIM = re.compile(r"—\s*(\d+)\s+of them\b")

#: Markdown links into the subsystem docs: [label](subsystems/<stem>.md)
_SUBSYS_LINK = re.compile(r"\]\(subsystems/([A-Za-z0-9_-]+)\.md\)")


def _arch_text() -> str:
    return ARCH.read_text(encoding="utf-8")


def _doc_stems() -> set[str]:
    return {p.stem for p in SUBSYS_DOCS.glob("*.md")}


def _linked_stems() -> set[str]:
    return set(_SUBSYS_LINK.findall(_arch_text()))


def test_the_stated_subsystem_count_matches_the_directory():
    """The sentence that went stale. It cannot go stale silently again."""
    claim = _COUNT_CLAIM.search(_arch_text())
    assert claim, (
        f"{ARCH.name} no longer states a subsystem count in the pinned form "
        f"'— N of them'. Restore it, or this pin is dead and the doc is free "
        f"to drift again.")
    stated, actual = int(claim.group(1)), len(_doc_stems())
    assert stated == actual, (
        f"{ARCH.name} claims {stated} tracked subsystems; docs/subsystems/ holds "
        f"{actual}. Update the count — and the list, which is pinned separately.")


def test_every_subsystem_doc_is_named_in_the_overview():
    """The anti-drift guarantee that matters: a new subsystem cannot be absent
    from the architecture overview. This is the direction that actually rots —
    a doc gets added and nobody remembers the prose page exists."""
    missing = sorted(_doc_stems() - _linked_stems())
    assert not missing, (
        f"subsystem doc(s) not linked from {ARCH.name}: {missing}. Add each to "
        f"the overview — an architecture page that silently omits a subsystem is "
        f"how the 'Eight tracked subsystems' line survived to 40.")


def test_every_overview_link_resolves():
    """The other direction: a renamed or deleted subsystem leaves a dead link."""
    dangling = sorted(_linked_stems() - _doc_stems())
    assert not dangling, (
        f"{ARCH.name} links to subsystem doc(s) that do not exist: {dangling}")
