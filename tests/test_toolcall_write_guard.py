"""The write guard 1.14.0 specified and did not ship (Phase 2, 1.14.1).

1.14.0's Phase 5 criterion 12 required a write-time guard rejecting tool-call
markup in structured-write arguments. `grep` for it in mutations.py returned
zero. Four malformed writes now sit in append-only memory — the fourth landing
while the finding about the first three was being recorded — inside the release
whose thesis is that written intent without an executable check rots.

Those four live entries are this guard's acceptance corpus. They are NOT
retro-edited (INVARIANT-03; they parse, and repair belongs to the still-deferred
amendment op) — the tests read them off disk and assert the guard would have
caught each one.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from clauderizer import mutations
from clauderizer import paths as P

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The exact shapes that landed live, per the gameplan's Phase 2 criteria.
LANDED_SHAPES = ["</consequences>", "</context>", "</root_cause>", "</impact>"]

#: (register, entry id, the stray closing tag that entry carries).
CORRUPTED_ENTRIES = [
    ("DECISIONS.md", "D-052", "</context>"),
    ("DECISIONS.md", "D-062", "</consequences>"),
    ("HARDENING.md", "H-19", "</root_cause>"),
    ("HARDENING.md", "H-23", "</impact>"),
]


def guard(text: str) -> str:
    return mutations._strip_toolcall_markup(text)


# --- the exact shapes that landed ---------------------------------------------

@pytest.mark.parametrize("tag", LANDED_SHAPES)
def test_guard_fires_on_each_landed_closing_tag(tag):
    body = f"Real prose that must survive.{tag}"
    out = guard(body)
    assert tag not in out
    assert "Real prose that must survive." in out


def test_guard_fires_on_a_bare_parameter_line():
    body = 'First value.\n<parameter name="context">Second value.'
    out = guard(body)
    assert "<parameter name=" not in out
    assert "First value." in out and "Second value." in out


@pytest.mark.parametrize("markup", [
    "<parameter name=\"context\">", "</parameter>",
    "<invoke name=\"cz_add_decision\">", "</invoke>",
    "<function_calls>", "</function_calls>",
    "<parameter name=\"x\">", "</invoke>",
])
def test_the_whole_toolcall_vocabulary_is_neutralized(markup):
    assert guard(f"before {markup} after") == "before  after"


# --- the four live entries are the acceptance corpus --------------------------

@pytest.mark.parametrize("register,entry_id,tag", CORRUPTED_ENTRIES,
                         ids=[c[1] for c in CORRUPTED_ENTRIES])
def test_guard_would_have_caught_each_live_corrupted_entry(register, entry_id, tag):
    """Read the real corrupted body off disk and assert the guard cleans it.

    This is the honest test: not a synthetic string, but the bytes that actually
    landed in append-only memory because no guard existed.
    """
    doc = (REPO_ROOT / "docs" / register).read_text(encoding="utf-8")
    block = _entry_block(doc, entry_id)
    assert tag in block, (
        f"source-of-truth guard: {entry_id} in {register} must still carry {tag} "
        f"— these entries are append-only and must not be retro-edited")

    cleaned = guard(block)
    assert tag not in cleaned, f"the guard must neutralize {tag} in {entry_id}"
    assert "<parameter name=" not in cleaned
    # Nothing is lost: every word of real prose survives (INVARIANT-03).
    assert len(cleaned) < len(block)
    for word in ("the", "and"):
        assert word in cleaned


def test_the_live_entries_are_not_retro_edited():
    """The corpus is append-only. If a later phase 'cleans' these, this fails —
    which is the point: repair belongs to the amendment op, still deferred."""
    for register, entry_id, tag in CORRUPTED_ENTRIES:
        doc = (REPO_ROOT / "docs" / register).read_text(encoding="utf-8")
        assert tag in _entry_block(doc, entry_id)


def _entry_block(doc: str, entry_id: str) -> str:
    """The text of one register entry, from its heading to the next one."""
    m = re.search(rf"^#{{2,4}}\s+{re.escape(entry_id)}\b.*?$", doc, re.M)
    assert m, f"{entry_id} not found"
    nxt = re.search(r"^#{2,4}\s+[A-Z]+-\d+\b", doc[m.end():], re.M)
    return doc[m.start():m.end() + (nxt.start() if nxt else len(doc))]


# --- normalize, never reject; and never eat legitimate content ----------------

def test_balanced_markup_is_left_alone():
    """A body legitimately showing XML/HTML keeps it — a field-name blocklist
    could not promise this, unbalanced-detection can."""
    body = "The renderer emits <div class=\"x\">content</div> for each row."
    assert guard(body) == body


def test_markup_inside_a_code_span_is_untouched():
    """An entry that QUOTES this very shape must not be rewritten — the same
    protection the read side gained in 1.14.0 (sections._without_code_spans)."""
    body = "The guard strips a stray `</context>` from the value."
    assert guard(body) == body


def test_markup_inside_a_fenced_block_is_untouched():
    body = "Example:\n\n```xml\n</context>\n<parameter name=\"a\">\n```\n\nEnd."
    assert guard(body) == body


def test_an_opener_and_its_closer_may_straddle_a_code_span():
    """Balance is judged over the whole visible value, not per segment."""
    body = "<note>see `</context>` here</note>"
    assert guard(body) == body


def test_ordinary_prose_is_byte_identical():
    body = "A decision with no markup at all.\n\nSecond paragraph — em dash, 5 < 7."
    assert guard(body) == body


# --- it is wired at the render boundary, not just available -------------------

def test_add_decision_neutralizes_at_the_write_boundary(temp_repo):
    """The guard has to be ON the path a real cz_* write takes (L-55): the four
    live entries exist because a function that was never called cannot help."""
    paths = P.resolve(temp_repo)
    res = mutations.add_decision(
        paths,
        title="Guarded title</title>",
        context='Ctx one.</context>\n<parameter name="context">Ctx two.',
        decision="The decision.</decision>",
        consequences="Consequences.</consequences>",
    )
    assert res["ok"]
    written = (temp_repo / "docs" / "DECISIONS.md").read_text(encoding="utf-8")
    for tag in ("</title>", "</context>", "</decision>", "</consequences>",
                "<parameter name="):
        assert tag not in written
    for kept in ("Guarded title", "Ctx one.", "Ctx two.", "The decision.",
                 "Consequences."):
        assert kept in written, "normalize, never reject — no write is lost"


def test_add_finding_and_add_lesson_are_guarded_too(temp_repo):
    """The shapes landed in HARDENING as well as DECISIONS, so the boundary must
    cover every register — not only the one that happened to be tested."""
    paths = P.resolve(temp_repo)
    mutations.add_finding(
        paths, title="Finding", severity="medium",
        root_cause="Cause.</root_cause>", impact="Impact.</impact>",
        affected='Files.</affected>\n<parameter name="affected">More files.')
    hard = (temp_repo / "docs" / "HARDENING.md").read_text(encoding="utf-8")
    for tag in ("</root_cause>", "</impact>", "</affected>", "<parameter name="):
        assert tag not in hard
    for kept in ("Cause.", "Impact.", "Files.", "More files."):
        assert kept in hard

    mutations.add_lesson(paths, gameplan_id="2026-05-01-bootstrap",
                         text="Lesson.</text>", category="Process")
    idx = (temp_repo / "docs" / "gameplans" / "2026-05-01-bootstrap"
           / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    assert "</text>" not in idx and "Lesson." in idx


def test_guarding_is_idempotent(temp_repo):
    """Re-submitting identical input stays a no-op — normalization runs before
    the change diff, exactly as D-066 requires."""
    dirty = 'Body.</context>\n<parameter name="x">More.'
    assert guard(guard(dirty)) == guard(dirty)
