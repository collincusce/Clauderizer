from clauderizer.markdown import sections as S

BODY = """# Title

Intro paragraph.

## Decisions

### D-001
First decision.

## Open Items

None yet.

## Notes

Some notes.
"""


def test_find_and_get_section():
    assert S.get_section(BODY, "Open Items").strip() == "None yet."
    assert "First decision." in S.get_section(BODY, "Decisions")
    assert S.get_section(BODY, "Nonexistent") is None


def test_upsert_replaces_existing_section():
    out = S.upsert_section(BODY, "Open Items", "O1 — something")
    assert "O1 — something" in S.get_section(out, "Open Items")
    # Other sections survive.
    assert "Some notes." in S.get_section(out, "Notes")


def test_upsert_is_idempotent():
    once = S.upsert_section(BODY, "Open Items", "O1 — something")
    twice = S.upsert_section(once, "Open Items", "O1 — something")
    assert once == twice


def test_upsert_appends_when_missing():
    out = S.upsert_section(BODY, "Brand New", "fresh content")
    assert S.get_section(out, "Brand New").strip() == "fresh content"


def test_append_to_section_accumulates():
    out = S.append_to_section(BODY, "Decisions", "### D-002\nSecond decision.")
    sec = S.get_section(out, "Decisions")
    assert "D-001" in sec and "D-002" in sec


def test_marker_block_roundtrip_and_idempotency():
    text = "# CLAUDE.md\n\nUser content above.\n"
    once = S.upsert_marker_block(text, "clauderizer", "managed line")
    assert "User content above." in once
    assert S.get_marker_block(once, "clauderizer") == "managed line"
    twice = S.upsert_marker_block(once, "clauderizer", "managed line")
    assert once == twice
    # Replacing only touches inside the markers.
    updated = S.upsert_marker_block(once, "clauderizer", "new managed line")
    assert "User content above." in updated
    assert S.get_marker_block(updated, "clauderizer") == "new managed line"
