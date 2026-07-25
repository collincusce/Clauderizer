"""Dream NOTES and dream PROPOSALS stop sharing a name (Phase 5, A-002).

The dream loop has two artifacts and two verbs:

    raw NOTES      captured by cz_add_dream          consumed by DREAMING
    staged PROPOSALS produced by the dreamer          consumed by TRIAGE

Live failure that motivated this: asked to "take care of the dream notes", a
session ran the DREAMER — capturing more notes and staging four new proposals —
when the ask was to triage what the dreamer had already produced. The notes that
pass consumed cannot be un-consumed (the watermark is append-only), so the
ambiguity was materially expensive once.

This phase changes what things are CALLED, never what they do.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from clauderizer.rituals import status_bundle as S

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_RENDER = REPO_ROOT / ".claude" / "skills" / "clauderizer-dream" / "SKILL.md"
SKILL_SOURCE = (REPO_ROOT / "src" / "clauderizer" / "skills"
                / "clauderizer-dream" / "SKILL.md")


def _notes_line(n: int = 6) -> str:
    bundle = {"active_gameplan": "gp", "summary": "S", "size": "standard",
              "host_profile": "python",
              "memory": {"active_lessons": 0, "project_lessons": 0,
                         "dream_notes": n}}
    return next(ln for ln in S.render_digest(bundle).splitlines()
                if "note" in ln.lower())


def _proposals_line(dream: int = 4, total: int = 4) -> str:
    bundle = {"active_gameplan": "gp", "summary": "S", "size": "standard",
              "host_profile": "python", "memory": None,
              "pending_proposals": total, "pending_dream_proposals": dream}
    return next(ln for ln in S.render_digest(bundle).splitlines()
                if "proposal" in ln.lower())


# --- each line names its own verb ---------------------------------------------

def test_the_notes_line_names_dreaming_as_the_action():
    line = _notes_line()
    assert "cz_dream" in line
    assert re.search(r"\bdream", line, re.I), "the raw-note line must name DREAMING"


def test_the_notes_line_does_not_read_as_triage():
    """The exact confusion: raw notes are not triaged, they are dreamed."""
    line = _notes_line()
    assert "triage" not in line.lower() or "not" in line.lower(), (
        "if the raw-note line mentions triage at all, it must be to DENY it")


def test_the_proposals_line_names_triage_as_the_action():
    line = _proposals_line()
    assert "triage" in line.lower()
    assert "cz_handle_dream_proposal" in line


def test_the_proposals_line_says_dreaming_is_blocked():
    """A-001 gates cz_dream on untriaged proposals and the line only ever said
    'to unblock cz_dream' — which reads as an optional benefit, not a gate. A
    reader who sees this line alone must learn that dreaming is BLOCKED."""
    line = _proposals_line().lower()
    assert re.search(r"blocked until|gated until|blocks .*dream", line), (
        "state the gate affirmatively — 'unblock' describes the reward, not the rule")


def test_the_two_lines_are_distinguishable_by_their_subject():
    """A reader seeing either line alone must know which artifact it is about.

    Word-absence is the wrong test — the notes line naming what dreaming
    PRODUCES is helpful. What must differ is the SUBJECT: whichever artifact the
    line counts and demands an action for, stated before any other is mentioned.
    """
    notes, proposals = _notes_line().lower(), _proposals_line().lower()
    assert notes.index("note") < notes.index("proposal"), \
        "the raw-note line must be ABOUT notes, whatever else it mentions"
    assert "proposal" in proposals
    assert "note" not in proposals.split("proposal")[0], \
        "the proposal line must be ABOUT proposals"
    # And the demanded verb differs.
    assert "dreaming" in notes and "triage" in proposals


def test_no_lag_no_notes_no_line():
    """Unchanged behavior: zero notes emits nothing (INVARIANT-08)."""
    bundle = {"active_gameplan": "gp", "summary": "S", "size": "standard",
              "host_profile": "python",
              "memory": {"active_lessons": 0, "project_lessons": 0, "dream_notes": 0}}
    assert not [ln for ln in S.render_digest(bundle).splitlines()
                if "dream" in ln.lower()]


# --- the skill routes the right half ------------------------------------------

def _description(path: Path) -> str:
    m = re.search(r"^description:\s*(.+)$", path.read_text(encoding="utf-8"), re.M)
    assert m, f"{path} has no description in its frontmatter"
    return m.group(1)


@pytest.mark.parametrize("path", [SKILL_RENDER, SKILL_SOURCE],
                         ids=["render", "source"])
def test_skill_description_distinguishes_both_halves(path):
    d = _description(path).lower()
    # Merely CONTAINING both words is what the old description already did while
    # still misrouting a session. Each artifact must sit beside its own verb.
    assert re.search(r"note[sx]?\b[^.]{0,60}dream|dream[^.]{0,60}\bnote", d), \
        "raw NOTES must be named beside DREAMING"
    assert re.search(r"proposal[^.]{0,60}triage|triage[^.]{0,60}proposal", d), \
        "staged PROPOSALS must be named beside TRIAGE"
    # The phrase that actually misrouted a real session must be a listed trigger.
    assert "take care of" in d, (
        "'take care of the dream notes' misrouted a live session — list it")


@pytest.mark.parametrize("path", [SKILL_RENDER, SKILL_SOURCE],
                         ids=["render", "source"])
def test_skill_body_leads_with_which_half_is_actionable(path):
    body = path.read_text(encoding="utf-8")
    head = body.split("# ", 1)[-1][:1200].lower()
    assert "note" in head and "proposal" in head
    assert "triage" in head


def test_skill_source_and_render_are_identical():
    """L-55 seam 1: generated content has a SOURCE — edit the source, not just
    the render, or a future `clauderize init` silently reverts the edit. Nothing
    pinned this seam for skills before now."""
    assert SKILL_SOURCE.exists(), "the src/ template is the source of truth"
    assert SKILL_RENDER.read_text(encoding="utf-8") == \
        SKILL_SOURCE.read_text(encoding="utf-8")


# --- the glossary carries both terms ------------------------------------------

def test_readme_glossary_distinguishes_the_two():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "**dream note**" in readme, "the raw-capture term needs its own row"
    assert "**dream proposal**" in readme, "the staged term needs its own row"
    # Each row must carry its own verb.
    note_row = next(ln for ln in readme.splitlines() if "**dream note**" in ln)
    prop_row = next(ln for ln in readme.splitlines() if "**dream proposal**" in ln)
    assert "dream" in note_row.lower()
    assert "triage" in prop_row.lower()
