"""2.0-alpha Phase 0 — honest terminal vocabulary (D-070).

``deferred`` becomes the honest terminal DOOR for the write path (the read
side has understood it since H-21): a phase deliberately stopped short of its
goal transitions to deferred-with-reason instead of laundering into complete.

Pins, in order:
- the positional status matcher: the ENGINE-OWNED leading token classifies the
  cell; trailing free text ("…call it done…") can no longer reclassify a row
  (the laundering path), and classification is independent of vocabulary
  declaration order;
- the write vocabulary: deferred + aliases (exited/abandoned/superseded/… map
  INTO deferred — no fourth terminal status, ratcheted);
- reason sanitization: table-safe, engine token leads, no crash on empty;
- tracker headers agree with status_bundle._lifecycle on what "closed" means
  (the runtime-demonstrated COMPLETE+DEFERRED -> "Executing" divergence);
- advisories: completing over unchecked criteria names the deferred
  alternative; the deferred door itself never nags (INVARIANT-05, no flags);
- telemetry: deferred is a terminal outcome, reason carried;
- the corpus sweep ratchet: on THIS repo's real trackers, the positional
  matcher only ever moves a row toward open/deferred — never toward complete.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import ops, telemetry
from clauderizer import paths as P
from clauderizer.rituals import _tables
from clauderizer.rituals import status_bundle as S

REPO_ROOT = Path(__file__).resolve().parents[1]


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _cell(text):
    rows = _tables.parse_phase_table(
        f"## Phase Status\n\n| Phase | Name | Status |\n|--|--|--|\n| 0 | X | {text} |\n")
    return rows[0].status


def _gameplan(paths, n_extra_phases=1):
    gid = M.create_gameplan(paths, "Honest close", today="2026-07-26")["gameplan_id"]
    for i in range(n_extra_phases):
        M.add_phase(paths, gameplan_id=gid, name=f"P{i + 1}", goal="g")
    return gid


def _row(paths, gid, n):
    idx = paths.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md"
    rows = _tables.parse_phase_table_full(idx.read_text(encoding="utf-8"))
    return next(r for r in rows if r.number == str(n))


# --- positional matcher: the engine token leads -------------------------------

@pytest.mark.parametrize("cell,expected", [
    ("DEFERRED (call it done for now)", "deferred"),
    ("DEFERRED — complete enough for 1.15", "deferred"),
    ("FAILED (tests done but red)", "failed"),
    ("READY (done planning)", "ready"),
    ("IN PROGRESS — nearly complete", "in_progress"),
    ("BLOCKED — deferred until upstream ships", "blocked"),
    ("⏸️ DEFERRED — done for now, resume in 1.16", "deferred"),
    ("INCOMPLETE", "unknown"),
])
def test_leading_token_wins_over_trailing_free_text(cell, expected):
    assert _cell(cell) == expected


def test_classification_is_declaration_order_independent(monkeypatch):
    cells = ["DEFERRED (call it done)", "✅ COMPLETE", "FAILED (done trying)",
             "DEFERRED (blocked on X)", "🟡 IN PROGRESS", "NOT STARTED"]
    before = [_cell(c) for c in cells]
    reversed_vocab = dict(reversed(list(_tables._STATUS_WORDS.items())))
    monkeypatch.setattr(_tables, "_STATUS_WORDS", reversed_vocab)
    assert [_cell(c) for c in cells] == before


def test_tie_at_same_offset_longest_word_wins():
    # NOT STARTED and (nothing else) start at 0; COMPLETED vs COMPLETE overlap.
    assert _cell("NOT STARTED") == "not_started"
    assert _cell("COMPLETED") == "complete"


# --- write vocabulary: deferred and its aliases, no fourth status -------------

def test_transition_writes_deferred_with_sanitized_reason(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    res = M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                             to_status="deferred",
                             reason="scope cut | resume in 1.16\nsecond line",
                             today="2026-07-26")
    assert res["ok"] is True and res["to_status"] == "deferred"
    row = _row(paths, gid, 1)
    assert row.status == "deferred"
    assert "|" not in row.raw_status.replace("", "")  # cell is table-safe
    assert "scope cut / resume in 1.16" in row.raw_status
    assert "second line" not in row.raw_status
    assert row.raw_status.startswith("⏸️ DEFERRED — ")  # engine token leads
    assert row.completed == "2026-07-26"               # closed phases get a date
    assert row.started is None                          # no fabricated start


def test_empty_and_whitespace_reasons_do_not_crash(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths, n_extra_phases=2)
    for phase, reason in (("1", ""), ("2", "  \n\n  ")):
        res = M.transition_phase(paths, gameplan_id=gid, phase_n=phase,
                                 to_status="deferred", reason=reason,
                                 today="2026-07-26")
        assert res["ok"] is True
        assert _row(paths, gid, phase).raw_status.strip() == "⏸️ DEFERRED"


def test_long_reason_is_capped(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                       to_status="deferred", reason="x" * 400, today="2026-07-26")
    assert len(_row(paths, gid, 1).raw_status) < 130


@pytest.mark.parametrize("alias", ["exited", "exit", "abandon", "abandoned",
                                   "superseded", "wontfix", "defer", "scope_cut"])
def test_aliases_map_into_deferred_never_a_new_status(temp_repo, alias):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    res = M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                             to_status=alias, today="2026-07-26")
    assert res["ok"] is True and res["to_status"] == "deferred"


def test_no_fourth_terminal_status_ratchet():
    """ABANDONED/EXITED are doors INTO deferred, never statuses of their own —
    a process-death status has no writer in a memory layer."""
    assert set(M._PHASE_DISPLAY) == {
        "not_started", "ready", "in_progress", "complete", "blocked",
        "failed", "deferred"}
    assert set(M._PHASE_ALIASES.values()) <= set(M._PHASE_DISPLAY)


def test_reject_message_names_deferred(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    res = M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                             to_status="nonsense", today="2026-07-26")
    assert res["ok"] is False and "deferred" in res["summary"]


# --- tracker headers: closed means what _lifecycle says it means --------------

def test_complete_plus_deferred_is_closed_not_executing(temp_repo):
    """The runtime-demonstrated divergence: header said 'Executing' while the
    portfolio said complete."""
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)  # phases 0 and 1
    M.transition_phase(paths, gameplan_id=gid, phase_n="0",
                       to_status="complete", today="2026-07-26")
    M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                       to_status="deferred", reason="scope cut", today="2026-07-26")
    gp = (paths.gameplan_dir(gid) / "GAMEPLAN.md").read_text(encoding="utf-8")
    m = re.search(r"> Status:\s*(.+)", gp)
    assert m and m.group(1).strip() == "Complete"
    idx = (paths.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    assert "All 2 phases closed (1 deferred)" in idx
    assert S._lifecycle(_tables.parse_phase_table(idx)) == "complete"


def test_all_deferred_reads_deferred_everywhere(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    for n in ("0", "1"):
        M.transition_phase(paths, gameplan_id=gid, phase_n=n,
                           to_status="deferred", today="2026-07-26")
    gp = (paths.gameplan_dir(gid) / "GAMEPLAN.md").read_text(encoding="utf-8")
    m = re.search(r"> Status:\s*(.+)", gp)
    assert m and m.group(1).strip() == "Deferred"
    idx = (paths.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    assert "All 2 phases deferred" in idx
    assert S._lifecycle(_tables.parse_phase_table(idx)) == "deferred"


def test_mixed_open_still_executes(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                       to_status="deferred", today="2026-07-26")
    gp = (paths.gameplan_dir(gid) / "GAMEPLAN.md").read_text(encoding="utf-8")
    m = re.search(r"> Status:\s*(.+)", gp)
    assert m and m.group(1).strip() == "Executing"


# --- advisories: the honest door never nags (INVARIANT-05) --------------------

def _with_unchecked_criteria(paths, gid, phase="1"):
    M.set_exit_criteria(paths, gameplan_id=gid, phase=phase,
                        criteria=["thing one", "thing two"])


def test_completing_over_unchecked_criteria_names_the_deferred_alternative(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    _with_unchecked_criteria(paths, gid)
    res = M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                             to_status="complete", today="2026-07-26")
    assert res["ok"] is True  # advisory, never a block
    adv = next(a for a in res["advisories"] if a["kind"] == "exit_criteria")
    assert "deferred" in adv["message"]
    assert "goal" in adv["message"]


def test_deferring_never_nags_about_unchecked_criteria(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    _with_unchecked_criteria(paths, gid)
    res = M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                             to_status="deferred", reason="stopping short",
                             today="2026-07-26")
    assert res["ok"] is True
    for adv in res.get("advisories", []):
        assert adv["kind"] != "exit_criteria"
        assert "verify each" not in adv.get("message", "")
    # context is still recorded honestly — checked/total, no imperative
    kinds = [a["kind"] for a in res.get("advisories", [])]
    assert "exit_criteria_context" in kinds
    ctx = next(a for a in res["advisories"] if a["kind"] == "exit_criteria_context")
    assert "0/2" in ctx["message"]


# --- telemetry: deferred is a terminal outcome, reason carried ----------------

def test_deferred_outcome_reaches_telemetry_with_reason(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    res = M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                             to_status="deferred", reason="scope cut for a1",
                             today="2026-07-26")
    assert res.get("telemetry") == "outcome"
    events = [e for e in telemetry.read_events(paths.telemetry_file)
              if e.get("kind") == "outcome"]
    assert events[-1]["status"] == "deferred"
    assert events[-1]["reason"] == "scope cut for a1"


def test_complete_outcome_shape_unchanged(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                       to_status="complete", today="2026-07-26")
    events = [e for e in telemetry.read_events(paths.telemetry_file)
              if e.get("kind") == "outcome"]
    assert events[-1]["status"] == "complete"
    assert "reason" not in events[-1]


# --- tool surface: one source for CLI and MCP (schemas derive from ops) -------

def test_ops_surface_documents_the_three_way_closeout():
    sig = inspect.signature(ops.cz_transition_phase)
    assert "reason" in sig.parameters
    doc = ops.cz_transition_phase.__doc__ or ""
    assert "deferred" in doc and "reason" in doc


# --- corpus sweep ratchet: flips only ever move toward open/deferred ----------

def _old_order_normalize(raw: str) -> str:
    """The pre-positional matcher, replicated: dict order wins."""
    up = raw.upper()
    for word, norm in _tables._STATUS_WORDS.items():
        if re.search(rf"(?<![A-Z]){re.escape(word)}(?![A-Z])", up):
            return norm
    return "unknown"


def test_corpus_sweep_no_row_flips_toward_complete():
    trackers = sorted(REPO_ROOT.glob("docs/gameplans/*/PHASE-STATUS.md")) + \
        sorted(REPO_ROOT.glob("docs/gameplans/*/CHAT-HANDOFF-INDEX.md"))
    assert trackers, "sweep must run against the real corpus"
    flips = []
    for t in trackers:
        for row in _tables.parse_phase_table(t.read_text(encoding="utf-8")):
            old = _old_order_normalize(row.raw_status)
            if row.status != old:
                flips.append((t.name, row.number, old, row.status))
                # the laundering direction is forbidden
                assert row.status != "complete", (
                    f"{t}: phase {row.number} flipped {old} -> complete")
                # a previously-classified row must not vanish into unknown
                assert row.status != "unknown" or old == "unknown"
    # flips are allowed (that is the point) but only toward honesty
    for _, _, old, new in flips:
        assert new in {"deferred", "not_started", "ready", "in_progress",
                       "blocked", "failed"}
