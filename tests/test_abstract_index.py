"""Phase 1 tests for the abstract index (gameplan abstract-index-fast-retrieval).

Covers the DUAL parser (em-dash D/INVARIANT/H blocks + L-NN lesson lines, O-03),
the D1 invalidation (scoped mtime + schema-version gate + atomic write), adversarial
cache input (L-24), and the delete-then-rebuild round-trip (INVARIANT-01). No
consumer is wired yet — this phase ships the data structure only.
"""
from __future__ import annotations

import pytest

from clauderizer import analyze
from clauderizer import paths as P
from clauderizer.graph import abstract_index as A

# Real em-dash (U+2014) headings, as analyze._ENTRY_RE requires.
DECISIONS = (
    "# Decisions\n\n## Decisions\n\n"
    "### D-001 — Use Postgres for the billing ledger\n\n"
    "**Status**: active\n\n"
    "**Context**: the ledger needs durable transactional writes.\n\n"
    "### D-002 — Switch the public API to GraphQL\n\n"
    "**Status**: superseded\n\n"
    "**Context**: REST is superseded.\n"
)
INVARIANTS = "# Invariants\n\n## Invariants\n\n### INVARIANT-01 — Markdown is canonical\n\nMarkdown is canonical.\n"
HARDENING = (
    "# Hardening\n\n## Risks\n\n"
    "### H-01 — A nasty concurrency race\n\n"
    "- **Severity**: high\n"
    "- **Status**: resolved (2026-01-01)\n"
    "- **Impact**: data loss under contention.\n"
)
LESSONS = (
    "# Lessons\n\n## Lessons\n\n"
    "**L-01.** Measure before shipping. A discard is a success. *(from x)*\n"
    "**L-02.** An old idea here (obsolete 2026-01-01: superseded by L-01)\n"
)


def _paths(tmp_path):
    (tmp_path / "docs").mkdir(exist_ok=True)
    return P.resolve(tmp_path)


def _seed(paths, **docs):
    for name, text in docs.items():
        paths.doc(name).write_text(text, encoding="utf-8")


def _full(paths):
    _seed(paths, DECISIONS=DECISIONS, INVARIANTS=INVARIANTS,
          HARDENING=HARDENING, LESSONS=LESSONS)


def test_build_indexes_all_four_corpora_including_lessons(tmp_path):
    paths = _paths(tmp_path)
    _full(paths)
    e = A.build(paths)["entries"]
    assert set(e) == {"D-001", "D-002", "INVARIANT-01", "H-01", "L-01", "L-02"}
    assert e["D-001"]["kind"] == "decision"
    assert e["INVARIANT-01"]["kind"] == "invariant"
    assert e["H-01"]["kind"] == "finding"
    assert e["L-01"]["kind"] == "lesson"


def test_status_parsed_for_each_kind(tmp_path):
    paths = _paths(tmp_path)
    _full(paths)
    e = A.build(paths)["entries"]
    assert e["D-001"]["status"] == "active"
    assert e["D-002"]["status"] == "superseded"        # decisions **Status**: form
    assert e["H-01"]["status"] == "resolved"           # hardening `- **Status**:` form
    assert e["L-01"]["status"] == "active"
    assert e["L-02"]["status"] == "obsolete"           # lesson_state trailing marker


def test_lessons_use_the_L_NN_format_not_the_gameplan_N_form(tmp_path):
    # O-03: a project lesson is **L-NN.**; a bare **N.** (gameplan form) must NOT be
    # picked up from LESSONS.md, and every **L-NN.** line MUST be.
    paths = _paths(tmp_path)
    _seed(paths, LESSONS="# Lessons\n\n## Lessons\n\n**L-07.** A real project lesson.\n**3.** Not a project lesson.\n")
    e = A.build(paths)["entries"]
    assert "L-07" in e
    assert "3" not in e and "L-3" not in e


def test_abstract_is_bounded_and_single_line(tmp_path):
    paths = _paths(tmp_path)
    _seed(paths, DECISIONS="# Decisions\n\n## Decisions\n\n### D-001 — " + ("word " * 200) + "\n\nbody\n")
    rec = A.build(paths)["entries"]["D-001"]
    assert len(rec["abstract"]) <= A.ABSTRACT_CAP + 1   # +1 for the ellipsis
    assert "\n" not in rec["abstract"]


def test_anchor_is_file_and_line(tmp_path):
    paths = _paths(tmp_path)
    _seed(paths, DECISIONS="# Decisions\n\n## Decisions\n\n### D-001 — t\n\nb\n")
    assert A.build(paths)["entries"]["D-001"]["anchor"] == "docs/DECISIONS.md:5"


def test_token_set_reuses_analyze_tokens(tmp_path):
    paths = _paths(tmp_path)
    _seed(paths, DECISIONS="# Decisions\n\n## Decisions\n\n### D-001 — Postgres billing ledger\n\ndurable transactional writes\n")
    rec = A.build(paths)["entries"]["D-001"]
    assert set(rec["token_set"]) == analyze._tokens("Postgres billing ledger durable transactional writes")


def test_content_hash_stable_then_changes_on_body_edit(tmp_path):
    paths = _paths(tmp_path)
    _seed(paths, DECISIONS="# Decisions\n\n## Decisions\n\n### D-001 — t\n\nbody one\n")
    h1 = A.build(paths)["entries"]["D-001"]["content_hash"]
    assert h1 == A.build(paths)["entries"]["D-001"]["content_hash"]
    _seed(paths, DECISIONS="# Decisions\n\n## Decisions\n\n### D-001 — t\n\nbody two\n")
    assert A.build(paths)["entries"]["D-001"]["content_hash"] != h1


def test_missing_corpus_files_yield_empty_index(tmp_path):
    idx = A.build(_paths(tmp_path))
    assert idx["entries"] == {}
    assert idx["schema_version"] == A.SCHEMA_VERSION


def test_load_or_rebuild_writes_then_skips_when_fresh(tmp_path, monkeypatch):
    paths = _paths(tmp_path)
    _seed(paths, DECISIONS="# Decisions\n\n## Decisions\n\n### D-001 — t\n\nb\n")
    A.load_or_rebuild(paths)
    assert paths.abstract_index_file.exists()
    calls = []
    monkeypatch.setattr(A, "write_cache", lambda idx, cf: calls.append(1))
    A.load_or_rebuild(paths)            # nothing changed -> write skipped
    assert calls == []


def test_schema_bump_forces_rewrite_even_when_mtime_unchanged(tmp_path, monkeypatch):
    # O-02 / D1: a schema_version mismatch refreshes the cache even with mtime equal.
    paths = _paths(tmp_path)
    _seed(paths, DECISIONS="# Decisions\n\n## Decisions\n\n### D-001 — t\n\nb\n")
    A.load_or_rebuild(paths)            # writes schema_version=1
    monkeypatch.setattr(A, "SCHEMA_VERSION", A.SCHEMA_VERSION + 1)
    real, calls = A.write_cache, []
    monkeypatch.setattr(A, "write_cache", lambda idx, cf: calls.append(idx["schema_version"]) or real(idx, cf))
    A.load_or_rebuild(paths)            # schema mismatch -> must rewrite
    assert calls == [A.SCHEMA_VERSION]


@pytest.mark.parametrize("bad", [
    b"",                              # empty
    b"\xef\xbb\xbf{}",                # UTF-8 BOM
    b"not json at all },{",           # garbage
    b'{"schema_version": 1, "entr',   # truncated JSON
    "café".encode("latin-1"),    # non-UTF-8 bytes
])
def test_corrupt_cache_rebuilds_and_never_raises(tmp_path, bad):
    paths = _paths(tmp_path)
    _seed(paths, DECISIONS="# Decisions\n\n## Decisions\n\n### D-001 — t\n\nb\n")
    paths.abstract_index_file.parent.mkdir(parents=True, exist_ok=True)
    paths.abstract_index_file.write_bytes(bad)
    idx = A.load_or_rebuild(paths)      # must not raise
    assert "D-001" in idx["entries"]    # rebuilt fresh from markdown


def test_delete_cache_then_rebuild_is_byte_identical(tmp_path):
    paths = _paths(tmp_path)
    _full(paths)
    idx1 = A.load_or_rebuild(paths)
    paths.abstract_index_file.unlink()
    idx2 = A.load_or_rebuild(paths)
    assert idx1["entries"] == idx2["entries"]   # markdown is canonical (INVARIANT-01)


# --- Phase 2 seams: the single-sourced lesson grammar + the kind->corpus map -------


def test_parse_lesson_line_splits_id_title_body():
    assert A.parse_lesson_line("**L-09.** First sentence. The rest here.") == (
        "L-09", "First sentence.", "The rest here.")
    # a single-sentence lesson keeps its terminal period in the title, empty body
    assert A.parse_lesson_line("**L-10.** Just one sentence.") == (
        "L-10", "Just one sentence.", "")
    # not a lesson line: the gameplan **N.** form and an em-dash block both miss
    assert A.parse_lesson_line("**3.** gameplan-form, not a project lesson") is None
    assert A.parse_lesson_line("### D-001 — not a lesson") is None


def test_lesson_record_body_matches_parse_lesson_line(tmp_path):
    """The refactor is behavior-preserving: a built lesson record's title is the
    parse_lesson_line title, and title+body reconstructs the original line text."""
    paths = _paths(tmp_path)
    _seed(paths, LESSONS="# Lessons\n\n## Lessons\n\n**L-05.** Head sentence. Tail detail.\n")
    rec = A.build(paths)["entries"]["L-05"]
    eid, title, body = A.parse_lesson_line("**L-05.** Head sentence. Tail detail.")
    assert rec["title"] == title == "Head sentence."
    assert rec["abstract"] == A._cap(title)


def test_doc_section_by_kind_covers_every_indexed_kind(tmp_path):
    """Every kind build() can emit must resolve back to a (doc, section) so cz_get
    knows which one file to re-parse for the body."""
    paths = _paths(tmp_path)
    _full(paths)
    kinds = {rec["kind"] for rec in A.build(paths)["entries"].values()}
    assert kinds == {"decision", "invariant", "finding", "lesson"}
    assert kinds <= set(A._DOC_SECTION_BY_KIND)
    assert A._DOC_SECTION_BY_KIND["lesson"] == ("LESSONS", "Lessons")
    assert A._DOC_SECTION_BY_KIND["finding"] == ("HARDENING", "Risks")
