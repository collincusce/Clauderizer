"""Regression tests for the three gameplan-machinery field bugs
(2026-07-02, portfolio authoring via clauderize ops on 1.5.2)."""

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.rituals import _tables

GID = "2026-05-01-bootstrap"


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


# --- bug 1: date-prefix doubling -------------------------------------------------


def test_pre_dated_name_is_not_double_dated(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.create_gameplan(paths, "2026-07-02-backup-and-remotes",
                          today="2026-07-05")
    assert r["gameplan_id"] == "2026-07-02-backup-and-remotes"
    assert (paths.gameplan_dir("2026-07-02-backup-and-remotes") / "GAMEPLAN.md").exists()


def test_undated_name_still_gets_dated(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.create_gameplan(paths, "loop-production-health", today="2026-07-05")
    assert r["gameplan_id"] == "2026-07-05-loop-production-health"


# --- bug 2: unknown gameplan_id must never scaffold a shadow gameplan -------------


def test_add_phase_unknown_gameplan_hard_errors_and_writes_nothing(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_phase(paths, gameplan_id="totally-typo-id", name="X", goal="g")
    assert not r["ok"]
    assert "unknown gameplan" in r["summary"]
    assert GID in r["summary"]  # known ids are listed
    assert not paths.gameplan_dir("totally-typo-id").exists()


def test_sibling_writes_also_guard_unknown_gameplan(temp_repo):
    paths, _ = _ctx(temp_repo)
    calls = [
        lambda: M.add_lesson(paths, gameplan_id="nope", text="t"),
        lambda: M.add_open_item(paths, gameplan_id="nope", text="t"),
        lambda: M.set_exit_criteria(paths, gameplan_id="nope", phase="0",
                                    criteria=["c"]),
        lambda: M.add_correction(paths, gameplan_id="nope", phase="0",
                                 gameplan_said="a", actually="b", why="c"),
        lambda: M.add_amendment(paths, gameplan_id="nope", title="t",
                                affected_sections="s", affected_phases="p",
                                triggered_by="x", what="w", why="y"),
        lambda: M.transition_phase(paths, gameplan_id="nope", phase_n="0",
                                   to_status="in_progress"),
    ]
    for call in calls:
        r = call()
        assert not r["ok"] and "unknown gameplan" in r["summary"]
    assert not paths.gameplan_dir("nope").exists()


# --- bug 3: nonstandard status strings --------------------------------------------


def test_decorated_and_synonym_statuses_normalize():
    cases = {
        "🟡 READY — kickoff scheduled": "ready",
        "⬜ GATED (waiting on remotes)": "blocked",
        "✅ DONE": "complete",
        "IN PROGRESS": "in_progress",
        "⏳ PENDING": "not_started",
        "INCOMPLETE": "unknown",  # word boundary: not COMPLETE
    }
    for raw, want in cases.items():
        assert _tables._normalize_status(raw) == want, raw


def test_transition_works_on_hand_authored_narrow_table(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = M.create_gameplan(paths, "hand-authored", today="2026-07-02")["gameplan_id"]
    status = paths.gameplan_dir(gid) / "PHASE-STATUS.md"
    status.write_text(
        "# Status\n\n## Phase Status\n\n"
        "| # | Phase | Status |\n|---|---|---|\n"
        "| 0 | Kickoff | 🟡 READY — scheduled |\n",
        encoding="utf-8")
    (paths.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md").unlink()
    r = M.transition_phase(paths, gameplan_id=gid, phase_n="0",
                           to_status="in_progress")
    assert r["ok"], r["summary"]
    assert "IN PROGRESS" in status.read_text(encoding="utf-8")


def test_transition_miss_is_diagnostic(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = M.create_gameplan(paths, "diag", today="2026-07-02")["gameplan_id"]
    r = M.transition_phase(paths, gameplan_id=gid, phase_n="9",
                           to_status="in_progress")
    assert not r["ok"]
    assert "tracker rows found" in r["summary"]      # names what IS there
    assert "GATED" in r["summary"]                    # names the vocabulary
