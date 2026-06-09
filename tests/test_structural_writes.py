"""Phase 0 of engine-structural-robustness: anchored ID numbering and
table-aware tracker writes (gameplan D3; findings C-01/H-02; amendment A-001).

Every scenario here was first observed live on this repo: decisions numbering
D3..D9 with a phantom D6 gap, tracker tables fractured by paragraph appends,
and preflight failing to find the venv's own pytest.
"""

import os
import sys
from pathlib import Path

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.markdown import sections, tables
from clauderizer.model import next_numbered_id
from clauderizer.rituals.preflight import _command_env


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


# --- task 0.1: numbering anchors ---------------------------------------------


def test_numbering_ignores_scaffold_placeholder_prose():
    doc = "## Decisions\n\n_(Gameplan-internal decisions D1, D2, … appended here.)_\n"
    assert next_numbered_id(doc, "D", sep="", width=0) == "D1"


def test_numbering_ignores_cross_references_in_entry_text():
    # The live bug: this gameplan's own decisions skipped D6 because one
    # decision's text cited another gameplan's D6.
    doc = (
        "### D3 — Per-phase cascade resumes\n\n"
        "**Context**: reverses context-economics D6; D9 there is unrelated.\n"
    )
    assert next_numbered_id(doc, "D", sep="", width=0) == "D4"


def test_numbering_counts_heading_anchors():
    doc = "### D-001 — a\n\nprose mentioning D-007 doesn't count\n\n### D-002 — b\n"
    assert next_numbered_id(doc, "D") == "D-003"


def test_numbering_counts_bold_entry_anchors():
    doc = (
        "**L-01.** first *(from x)*\n\n"
        "**L-02.** mentions a marker (promoted 2026-06-09: L-07) mid-line\n"
    )
    assert next_numbered_id(doc, "L", width=2) == "L-03"


def test_numbering_empty_doc_starts_at_one():
    assert next_numbered_id("", "C", width=2) == "C-01"


def test_fresh_gameplan_decisions_number_from_d1(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.create_gameplan(paths, "Fresh Plan", today="2026-06-08")
    gid = r["gameplan_id"]
    d1 = M.add_decision(paths, scope="gameplan", gameplan_id=gid,
                        title="first", context="c", decision="d", consequences="q")
    assert d1["id"] == "D1"
    d2 = M.add_decision(paths, scope="gameplan", gameplan_id=gid,
                        title="second", context="cites another gameplan's D6",
                        decision="d", consequences="q")
    assert d2["id"] == "D2"


# --- tasks 0.2/0.3: table block writes ----------------------------------------

BROKEN = (
    "| Phase | Name | Status | Started | Completed | Handoff |\n"
    "|-------|------|--------|---------|-----------|---------|\n"
    "| 0 | Alpha | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-0-HANDOFF.md |\n"
    "\n"
    "**Status legend**: ⬜ NOT STARTED · ✅ COMPLETE\n"
    "\n"
    "| 1 | Beta | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-1-HANDOFF.md |\n"
    "\n"
    "| 2 | Gamma | 🟡 IN PROGRESS | 2026-06-09 | — | handoffs/PHASE-2-HANDOFF.md |"
)


def test_normalize_heals_fractured_table():
    healed = tables.normalize(BROKEN)
    lines = healed.splitlines()
    assert lines[2].startswith("| 0 |")
    assert lines[3].startswith("| 1 |")
    assert lines[4].startswith("| 2 |")
    # the legend survives, after the block, exactly one gap
    assert "**Status legend**" in healed
    assert healed.count("\n\n") == 1


def test_normalize_is_idempotent():
    once = tables.normalize(BROKEN)
    assert tables.normalize(once) == once


def test_upsert_row_appends_then_replaces_by_key():
    sec = tables.normalize(BROKEN)
    grown = tables.upsert_row(sec, "| 3 | Delta | ⬜ NOT STARTED | — | — | h |")
    assert grown.splitlines()[5].startswith("| 3 |")
    replaced = tables.upsert_row(grown, "| 1 | Beta | 🔴 FAILED | 2026-06-09 | — | h |")
    assert "🔴 FAILED" in replaced
    assert sum(1 for ln in replaced.splitlines() if ln.startswith("| 1 |")) == 1


def test_add_phase_rows_stay_contiguous(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = M.create_gameplan(paths, "Tables Plan", today="2026-06-08")["gameplan_id"]
    M.add_phase(paths, gameplan_id=gid, name="Second", goal="g")
    M.add_phase(paths, gameplan_id=gid, name="Third", goal="g")
    idx = paths.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md"
    sec = sections.get_section(idx.read_text(encoding="utf-8"), "Phase Status Table")
    lines = sec.splitlines()
    i1 = next(i for i, ln in enumerate(lines) if ln.startswith("| 1 |"))
    assert lines[i1 + 1].startswith("| 2 |")
    legend = next(i for i, ln in enumerate(lines) if "Status legend" in ln)
    assert legend > i1 + 1  # prose lives after the table block


def test_transition_phase_heals_a_fractured_tracker(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = M.create_gameplan(paths, "Heal Plan", today="2026-06-08")["gameplan_id"]
    M.add_phase(paths, gameplan_id=gid, name="Second", goal="g")
    idx = paths.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md"
    fractured = idx.read_text(encoding="utf-8").replace("\n| 1 |", "\n\n| 1 |")
    idx.write_text(fractured, encoding="utf-8")
    assert "\n\n| 1 |" in idx.read_text(encoding="utf-8")
    # a same-status transition is enough of a blessed touch to heal the table
    r = M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                           to_status="not_started", today="2026-06-08")
    assert r["ok"]
    healed = idx.read_text(encoding="utf-8")
    assert "\n\n| 1 |" not in healed


def test_set_phase_row_unchanged_on_healthy_same_status(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = M.create_gameplan(paths, "Noop Plan", today="2026-06-08")["gameplan_id"]
    r = M.transition_phase(paths, gameplan_id=gid, phase_n="0",
                           to_status="ready", today="2026-06-08")
    assert r["ok"]
    # same status again on a healthy table: a true no-op
    r2 = M.transition_phase(paths, gameplan_id=gid, phase_n="0",
                            to_status="ready", today="2026-06-08")
    assert not r2["ok"]


# --- task 0.6 (A-001): profile commands resolve in the engine's environment ---


def test_profile_commands_resolve_in_engine_environment():
    env = _command_env()
    first = env["PATH"].split(os.pathsep)[0]
    assert Path(first) == Path(sys.executable).parent
