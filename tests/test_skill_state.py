"""Skill-state grammar -- a trailing structured marker parsed by one grammar
(skill-awareness D1; mirrors test_lesson_state). State and the entry fields
(name/description/source) are never substring-matched.
"""

from clauderizer.markdown import skill_state as SS

EM = SS.EMDASH


def test_trailing_markers_parse():
    assert SS.parse_state(f"**S-01.** n {EM} d (obsolete 2026-06-22)") == ("obsolete", "2026-06-22")
    assert SS.parse_state(f"**S-02.** n {EM} d (obsolete 2026-06-22: removed)") == (
        "obsolete", "2026-06-22: removed")
    assert SS.parse_state(f"**S-03.** n {EM} d (superseded 2026-06-22: S-09)") == (
        "superseded", "2026-06-22: S-09")
    assert SS.parse_state("~~**S-04.** struck~~") == ("obsolete", "struck through")


def test_mid_text_mentions_are_inert():
    line = f"**S-05.** debugger {EM} mentions '(obsolete' APIs mid-text yet is active"
    assert SS.parse_state(line) == ("active", "")
    assert SS.is_active(line)


def test_marker_reason_with_parentheses_parses():
    # H-18 (same defect class as lesson_state): a reason containing '()' must
    # not make the skill line read as active.
    assert SS.parse_state(
        f"**S-06.** n {EM} d (superseded 2026-06-22: replaced by S-09 (mcp))") == (
        "superseded", "2026-06-22: replaced by S-09 (mcp)")
    assert SS.is_active(
        f"**S-08.** n {EM} discusses (obsolete (foo) bar) markers then more prose")


def test_mark_produces_documented_forms():
    base = f"**S-07.** n {EM} d"
    assert SS.mark(base, "obsolete", "2026-06-22") == base + " (obsolete 2026-06-22)"
    assert SS.mark(base, "obsolete", "2026-06-22", "gone") == base + " (obsolete 2026-06-22: gone)"
    assert SS.mark(base, "superseded", "2026-06-22", "S-09") == base + " (superseded 2026-06-22: S-09)"


def test_format_and_parse_entry_round_trip():
    line = SS.format_entry("S-01", "frontend-design", "Build distinctive UIs",
                           ".claude/skills/frontend-design")
    assert line == ("**S-01.** frontend-design " + EM
                    + " Build distinctive UIs *(source: .claude/skills/frontend-design)*")
    e = SS.parse_entry(line)
    assert e == {"id": "S-01", "name": "frontend-design",
                 "description": "Build distinctive UIs",
                 "source": ".claude/skills/frontend-design", "state": "active"}


def test_parse_entry_without_source():
    e = SS.parse_entry(f"**S-02.** verify {EM} run it for real")
    assert e["name"] == "verify" and e["description"] == "run it for real"
    assert e["source"] is None and e["state"] == "active"


def test_parse_entry_strips_state_marker_and_keeps_fields():
    line = f"**S-03.** old {EM} legacy thing *(source: x)* (obsolete 2026-06-22: gone)"
    e = SS.parse_entry(line)
    assert e["name"] == "old" and e["description"] == "legacy thing"
    assert e["source"] == "x" and e["state"] == "obsolete"


def test_parse_entry_rejects_non_entries():
    assert SS.parse_entry("### Category: General") is None
    assert SS.parse_entry("**L-01.** a lesson, not a skill") is None
    assert SS.parse_entry("_(none yet)_") is None
