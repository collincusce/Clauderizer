"""A superseded gameplan can actually be closed (H-21).

The procedure specifies a disposition the engine never implemented. "Explicitly
deferred" appears in the close ritual and in the status-value table as a
first-class entity status, but the PHASE-ROW vocabulary had no equivalent, and
the portfolio's open/closed derivation reads only phase rows. So the one path the
procedure names for closing an unfinished gameplan was unreachable, and a
superseded gameplan stayed in the open set forever.

Same class as everything else in this release (D-065): the code and the decision
disagreed silently, and both read as correct in isolation.
"""

from __future__ import annotations

import pytest

from clauderizer.rituals import _tables
from clauderizer.rituals import status_bundle as S


@pytest.mark.parametrize("cell,expected", [
    ("⬜ DEFERRED", "deferred"),
    ("DEFERRED (superseded by the 1.15 plan)", "deferred"),
    ("🚫 SUPERSEDED", "deferred"),
    ("ABANDONED", "deferred"),
    ("WONTFIX", "deferred"),
])
def test_the_vocabulary_recognizes_a_dropped_phase(cell, expected):
    rows = _tables.parse_phase_table(
        f"## Phase Status\n\n| Phase | Name | Status |\n|--|--|--|\n| 0 | X | {cell} |\n")
    assert rows[0].status == expected


def test_deferred_is_matched_before_blocked():
    """'DEFERRED (blocked on upstream)' is deferred, not blocked — otherwise the
    disposition silently degrades back into the open set."""
    rows = _tables.parse_phase_table(
        "## Phase Status\n\n| Phase | Name | Status |\n|--|--|--|\n"
        "| 0 | X | DEFERRED (blocked on upstream) |\n")
    assert rows[0].status == "deferred"


def _rows(*statuses):
    body = "".join(f"| {i} | P{i} | {s} |\n" for i, s in enumerate(statuses))
    return _tables.parse_phase_table(
        "## Phase Status\n\n| Phase | Name | Status |\n|--|--|--|\n" + body)


# --- lifecycle and the open set ------------------------------------------------

def test_all_deferred_reads_as_deferred_not_complete():
    """Closed, but never claiming work that was not done."""
    assert S._lifecycle(_rows("DEFERRED", "DEFERRED")) == "deferred"


def test_finished_or_dropped_counts_as_complete():
    assert S._lifecycle(_rows("COMPLETE", "DEFERRED", "COMPLETE")) == "complete"


def test_a_partially_deferred_gameplan_is_still_executing():
    assert S._lifecycle(_rows("COMPLETE", "DEFERRED", "NOT STARTED")) == "executing"


@pytest.mark.parametrize("statuses", [("DEFERRED", "DEFERRED"),
                                      ("COMPLETE", "DEFERRED")])
def test_a_closed_gameplan_leaves_the_open_set(tmp_path, statuses):
    """H-21's actual symptom: it could never leave the portfolio."""
    gdir = tmp_path / "gp"
    gdir.mkdir()
    (gdir / "GAMEPLAN.md").write_text("# G\n\n> Kind: driven\n", encoding="utf-8")
    body = "".join(f"| {i} | P{i} | {s} |\n" for i, s in enumerate(statuses))
    (gdir / "PHASE-STATUS.md").write_text(
        "## Phase Status\n\n| Phase | Name | Status |\n|--|--|--|\n" + body,
        encoding="utf-8")
    card = S.gameplan_card(gdir, focus_id=None)
    assert card["open"] is False, "a deferred gameplan must be closed"


def test_an_ordinary_gameplan_is_unaffected():
    """No regression: the statuses that existed before behave identically."""
    assert S._lifecycle(_rows("COMPLETE", "COMPLETE")) == "complete"
    assert S._lifecycle(_rows("NOT STARTED", "READY")) == "planning"
    assert S._lifecycle(_rows("IN PROGRESS", "NOT STARTED")) == "executing"
    assert S._lifecycle(_rows("BLOCKED", "NOT STARTED")) == "executing"


def test_incomplete_still_does_not_read_as_complete():
    """The word-boundary guard the vocabulary already had, still holding."""
    rows = _tables.parse_phase_table(
        "## Phase Status\n\n| Phase | Name | Status |\n|--|--|--|\n"
        "| 0 | X | INCOMPLETE |\n")
    assert rows[0].status != "complete"
