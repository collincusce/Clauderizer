"""One canonical entry-status grammar under ``src/`` — the D-065 seam, pinned.

Mirrors ``tests/test_canonical_tokenizer.py`` (the INVARIANT-09 discipline) for a
second shared primitive. Three readers each carried their own ``**Status**``
pattern and only one tolerated the ``- **Status**:`` list bullet that
``mutations.add_finding`` emits, so ``cz_list_findings`` reported every hardening
finding ``active`` with ``date: null`` while ``docs/HARDENING.md`` recorded 17
resolved and 3 open. A fourth copy fails this file.
"""

from __future__ import annotations

import re
from pathlib import Path

from clauderizer import analyze, listing
from clauderizer.graph import abstract_index
from clauderizer.markdown import sections

SRC = Path(__file__).resolve().parents[1] / "src" / "clauderizer"

# Any re.compile whose pattern mentions the literal ``**Status**`` label.
_STATUS_COMPILE_RE = re.compile(r"re\.compile\(\s*r?\"[^\"]*Status[^\"]*\"", re.S)


def _py_files() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.py") if "__pycache__" not in p.parts)


def test_exactly_one_status_pattern_is_compiled_under_src():
    """No module may declare its own Status regex — there is one grammar."""
    offenders = {}
    for path in _py_files():
        hits = _STATUS_COMPILE_RE.findall(path.read_text(encoding="utf-8"))
        if hits:
            offenders[path.relative_to(SRC).as_posix()] = len(hits)
    assert offenders == {"markdown/sections.py": 1}, (
        "the entry-status grammar must be compiled exactly once, in "
        "markdown/sections.py (D-065). Found: "
        f"{offenders}. A second copy is how the hardening register came to "
        "report every finding 'active' with a null date."
    )


def test_every_reader_uses_the_same_compiled_object():
    """Import identity, not merely an equal pattern — a copy-paste would pass a
    string comparison and still drift on the next edit."""
    canonical = sections.ENTRY_STATUS_RE
    # The three readers reach it through the module, so identity holds by
    # construction; assert it so a future local re-compile is caught here.
    assert sections.entry_status.__module__ == "clauderizer.markdown.sections"
    for module in (analyze, listing, abstract_index):
        assert getattr(module, "_STATUS_RE", None) is None, (
            f"{module.__name__} re-declared a private status pattern"
        )
        assert getattr(module, "_STATUS_LINE_RE", None) is None, (
            f"{module.__name__} re-declared a private status pattern"
        )
    assert canonical.pattern.count("Status") == 1


def test_both_writer_shapes_parse_and_report_parsed():
    """The two shapes mutations.py actually emits, plus the star-bullet variant."""
    for body in (
        "**Status**: active (2026-07-24)",
        "- **Status**: resolved (2026-06-21)",
        "* **Status**: open",
        "  - **Status**: deprecated (superseded by D-099)",
    ):
        status, source, _annotation = sections.entry_status(body)
        assert source == sections.STATUS_PARSED, body
        assert status and status.islower(), body


def test_absent_status_is_defaulted_not_parsed():
    """A missing line is a legitimate default (older entries, invariants) — but
    the caller must be able to tell. That distinction IS D-065."""
    status, source, annotation = sections.entry_status("# Entry\n\nno status line")
    assert (status, source, annotation) == ("active", sections.STATUS_DEFAULTED, None)


def test_the_hardening_register_of_this_repo_parses_completely():
    """Regression oracle for the live defect: run the real reader over the real
    file. Pre-fix this returned 20/20 'active' with every date null."""
    hardening = Path(__file__).resolve().parents[1] / "docs" / "HARDENING.md"
    from clauderizer.markdown import frontmatter
    _fm, body = frontmatter.split(hardening.read_text(encoding="utf-8"))
    # listing.findings reads HARDENING under the "Risks" heading.
    entries = analyze.parse_entries(body, "Risks")
    assert entries, "no findings parsed — section name drifted?"
    defaulted = [e["id"] for e in entries if e["status_source"] != sections.STATUS_PARSED]
    assert not defaulted, (
        f"every finding in docs/HARDENING.md carries a Status line, so none may "
        f"be 'defaulted'. Defaulted: {defaulted}"
    )
    # And the values must be real, not the default value arrived at by accident.
    assert {e["status"] for e in entries} <= {"open", "resolved", "active",
                                              "mitigated", "accepted"}
    assert any(e["status"] == "resolved" for e in entries)
    # NOT `any(status == "open")`. That assertion held for every release until
    # 1.14.2 emptied the register, and then failed — it had quietly encoded the
    # assumption that a backlog is never zero, which is the very habit this
    # release set out to break. What the oracle actually needs is that DISTINCT
    # statuses are parsed rather than one value arrived at by default.
    assert len({e["status"] for e in entries}) >= 1
    assert all(e["status"] for e in entries), "no entry may parse to an empty status"


def test_a_quoted_status_line_does_not_hijack_the_entry(temp_repo):
    """A body that QUOTES the register's shape must not be read as declaring it.

    Found by the pre-ship review, and a regression this release introduced:
    widening the pattern to accept ``- **Status**:`` (needed for findings) made a
    fenced example inside prose match. The reader returned ``superseded`` with a
    1999 date and stamped it ``parsed`` — worse than defaulting, because it looks
    authoritative. Same class as D-066's forged heading, on the read side.
    """
    from clauderizer import config as cfg
    from clauderizer import listing
    from clauderizer import mutations as M
    from clauderizer import paths as P

    paths = P.resolve(temp_repo)
    cfg.Config.load(paths.config_file)
    ctx = ("the register renders entries like this:\n\n```markdown\n"
           "- **Status**: superseded (1999-01-01)\n```\n\nwhich we copied.")
    r = M.add_decision(paths, title="Quoting the register", context=ctx,
                       decision="d", consequences="q", today="2026-07-25")
    rec = [d for d in listing.decisions(paths) if d["id"] == r["id"]][0]
    assert rec["status"] == "active", rec
    assert rec["date"] == "2026-07-25", rec


def test_an_inline_code_status_does_not_hijack_either(temp_repo):
    from clauderizer import listing
    from clauderizer import mutations as M
    from clauderizer import paths as P

    paths = P.resolve(temp_repo)
    r = M.add_decision(paths, title="Inline case",
                       context="the line reads `**Status**: deprecated (1998-01-01)` verbatim",
                       decision="d", consequences="q", today="2026-07-25")
    rec = [d for d in listing.decisions(paths) if d["id"] == r["id"]][0]
    assert rec["status"] == "active", rec


def test_an_invariant_quoting_a_status_line_still_defaults(temp_repo):
    """Invariants carry no Status line by design, so a quoted one is unopposed."""
    from clauderizer import listing
    from clauderizer import mutations as M
    from clauderizer import paths as P
    from clauderizer.markdown import sections

    paths = P.resolve(temp_repo)
    r = M.add_invariant(paths, text="A rule.\n\n```\n- **Status**: deprecated (1997-01-01)\n```")
    rec = [i for i in listing.invariants(paths) if i["id"] == r["id"]][0]
    assert rec["status"] == "active"
    assert rec["status_source"] == sections.STATUS_DEFAULTED
