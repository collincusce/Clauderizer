"""Regression tests for the four field bugs from the first native-Windows
install (2026-07-02, gameplan windows-field-fixes-1-5-2)."""

import io
import sys

from clauderizer._stdio import harden_stdio
from clauderizer.markdown import frontmatter, sections


# --- bug 1: cp1252 console crash on glyphs ------------------------------------


def test_cp1252_stream_survives_glyphs(monkeypatch):
    buf = io.BytesIO()
    stream = io.TextIOWrapper(buf, encoding="cp1252")  # errors='strict' default
    monkeypatch.setattr(sys, "stdout", stream)
    harden_stdio()
    print("✗ doctor output ✓ with ⚙ glyphs ⚠ and → arrows")  # must not raise
    stream.flush()
    out = buf.getvalue()
    assert b"doctor output" in out  # text survives; glyphs degrade to '?'


def test_harden_stdio_never_raises_on_exotic_streams(monkeypatch):
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", object())  # no reconfigure attribute
    harden_stdio()  # must be a no-op, not a crash


# --- bug 2: inline flow lists in frontmatter -----------------------------------


def test_inline_empty_list_parses_as_empty_list():
    data = frontmatter.parse_block("id: x\ndepends_on: []\n")
    assert data["depends_on"] == []


def test_inline_list_with_items_parses():
    data = frontmatter.parse_block('deps: [subsys.a, "subsys.b", 3]\n')
    assert data["deps"] == ["subsys.a", "subsys.b", 3]


def test_inline_list_round_trips_through_serializer():
    text = frontmatter.serialize({"id": "x", "depends_on": []}, "body\n")
    again, _body = frontmatter.parse(text)
    assert again["depends_on"] == []


# --- bug 3: heading-title tolerance --------------------------------------------


def test_fuzzy_matches_suffixed_and_case_variant_titles():
    assert sections.get_section("# Decisions (newest first)\n\ncontent\n",
                                "Decisions", fuzzy=True) == "content"
    assert sections.get_section("## decisions\n\nx\n", "Decisions",
                                fuzzy=True) == "x"


def test_default_matching_stays_exact():
    # The read paths were built against exact matching — fuzz is opt-in, so
    # e.g. a phase lookup can never silently match "Phase 1: Name" (the
    # back-compat golden guards the composed consequence of this).
    assert sections.get_section("# Decisions (newest first)\n\nx\n",
                                "Decisions") is None


def test_fuzzy_does_not_match_different_words():
    assert sections.get_section("## Decision Log\n\nx\n", "Decisions",
                                fuzzy=True) is None


def test_exact_title_still_wins_over_prefix_variant():
    doc = "## Decisions (archive)\n\nold\n\n## Decisions\n\nnew\n"
    assert sections.get_section(doc, "Decisions", fuzzy=True) == "new"


def test_append_lands_in_suffixed_section_not_a_duplicate():
    from clauderizer.markdown.sections import append_to_section

    doc = "# Decisions (newest first)\n\nexisting entry\n"
    out = append_to_section(doc, "Decisions", "### D-002 — new one", fuzzy=True)
    assert out.count("Decisions") == 1  # no duplicate '## Decisions' created
    assert "D-002" in out


# --- bug 4: --run-cmd help wording ----------------------------------------------


def test_run_cmd_help_describes_a_launcher_prefix():
    import inspect

    from clauderizer import cli

    src = inspect.getsource(cli)
    assert "launcher PREFIX" in src
    assert "not a path to a single binary" in src
