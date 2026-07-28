"""Reserve-window wind-down budgets: declared, derived, dormant (D-072).

Pins the binding conditions: two tiers only, spend denominated in DISTINCT
RECORDED DATES (proc tags never the unit), WIND_DOWN derived at read time with
a module-constant reserve, phase-aware advisory wording ("IN the final
budgeted stint" vs "exceeds"), UNTRACKED-never-zero epistemics, live re-read
(raising the budget in markdown IS the retune), byte-identical surfaces for
undeclared repos, and the pre_compact convergence (L-68 clause 1).
"""

from __future__ import annotations

import pytest

from clauderizer import config as cfg
from clauderizer import telemetry
from clauderizer import paths as P
from clauderizer.rituals import budgets, preflight
from clauderizer.rituals import status_bundle as S

GID = "2026-05-01-bootstrap"


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _declare_gameplan_budget(paths, n="4"):
    gp = paths.gameplan_dir(GID) / "GAMEPLAN.md"
    text = gp.read_text(encoding="utf-8")
    gp.write_text(text.replace("> Status:", f"> Budget: {n} sessions\n> Status:", 1),
                  encoding="utf-8")


def _stint(paths, date, phase="1", proc="aaaa0000"):
    telemetry._append(paths.telemetry_file, {
        "kind": "stint", "date": date, "gameplan": GID,
        "phase": phase, "proc": proc})


# --- declarations -------------------------------------------------------------

def test_undeclared_is_dormant_everywhere(temp_repo):
    paths, config = _ctx(temp_repo)
    assert budgets.assess(paths, GID, "1") == []
    bundle = S.compute(paths, config)
    assert "budgets" not in bundle
    assert "Wind-down" not in S.render_digest(bundle)


@pytest.mark.parametrize("raw", ["twelve", "0", "-3"])
def test_malformed_declaration_is_surfaced_never_raised(temp_repo, raw):
    paths, _ = _ctx(temp_repo)
    _declare_gameplan_budget(paths, raw)
    (rec,) = budgets.assess(paths, GID, "1")
    assert rec["state"] == "malformed"
    assert "positive integer" in budgets.describe(rec)


def _declare_phase_budget(paths, n="2"):
    """Insert the Budget line into the fixture's EXISTING '### Phase 1' block
    (an appended duplicate block would never be parsed — first match wins)."""
    gp = paths.gameplan_dir(GID) / "GAMEPLAN.md"
    text = gp.read_text(encoding="utf-8")
    assert "### Phase 1" in text
    idx = text.index("### Phase 1")
    eol = text.index("\n", idx)
    gp.write_text(text[:eol + 1] + f"\n**Budget**: {n} sessions\n" + text[eol + 1:],
                  encoding="utf-8")


def test_phase_tier_declaration_parses(temp_repo):
    paths, _ = _ctx(temp_repo)
    _declare_phase_budget(paths, "2")
    decl = budgets.declarations(paths, GID, "1")
    assert decl["phase"] == 2 and decl["gameplan"] is None


# --- reserve math and the derived latch ---------------------------------------

def test_reserve_math_and_windows(temp_repo):
    paths, _ = _ctx(temp_repo)
    assert budgets.reserve(10) == 1
    assert budgets.reserve(3) == 1
    assert budgets.reserve(1) == 1
    _declare_gameplan_budget(paths, "3")
    _stint(paths, "2026-07-01")
    (rec,) = budgets.assess(paths, GID, "1")
    assert rec["state"] == "ok" and rec["spent"] == 1
    _stint(paths, "2026-07-02")
    (rec,) = budgets.assess(paths, GID, "1")
    assert rec["state"] == "wind_down"        # 2 >= 3 - 1
    _stint(paths, "2026-07-03")
    (rec,) = budgets.assess(paths, GID, "1")
    assert rec["state"] == "wind_down" and rec["spent"] == 3
    _stint(paths, "2026-07-04")
    (rec,) = budgets.assess(paths, GID, "1")
    assert rec["state"] == "over"


def test_budget_of_one_the_first_stint_is_the_ending(temp_repo):
    paths, _ = _ctx(temp_repo)
    _declare_gameplan_budget(paths, "1")
    _stint(paths, "2026-07-01")
    (rec,) = budgets.assess(paths, GID, "1")
    assert rec["state"] == "wind_down"


# --- the spend unit: distinct DATES, never proc tags --------------------------

def test_spend_is_distinct_dates_not_proc_tags(temp_repo):
    paths, _ = _ctx(temp_repo)
    _declare_gameplan_budget(paths, "5")
    _stint(paths, "2026-07-01", proc="aaaa0000")
    _stint(paths, "2026-07-01", proc="bbbb1111")   # second session, same date
    _stint(paths, "2026-07-01", proc="cccc2222")   # third — still one date
    (rec,) = budgets.assess(paths, GID, "1")
    assert rec["spent"] == 1


def test_phase_tier_counts_only_its_phase(temp_repo):
    paths, _ = _ctx(temp_repo)
    _declare_phase_budget(paths, "2")
    _stint(paths, "2026-07-01", phase="0")
    _stint(paths, "2026-07-02", phase="1")
    (rec,) = budgets.assess(paths, GID, "1")
    assert rec["tier"] == "phase" and rec["spent"] == 1


# --- epistemics: untracked is never zero --------------------------------------

def test_declared_but_unrecorded_reads_untracked_never_ok(temp_repo):
    paths, _ = _ctx(temp_repo)
    _declare_gameplan_budget(paths, "4")
    (rec,) = budgets.assess(paths, GID, "1", phase_in_flight=True)
    assert rec["state"] == "untracked"
    text = budgets.describe(rec)
    assert "UNTRACKED, not zero" in text or "UNTRACKED" in text
    assert "O-01" in text


# --- live re-read: markdown is the retune -------------------------------------

def test_raising_the_budget_in_markdown_is_the_retune(temp_repo):
    paths, _ = _ctx(temp_repo)
    _declare_gameplan_budget(paths, "2")
    _stint(paths, "2026-07-01")
    (rec,) = budgets.assess(paths, GID, "1")
    assert rec["state"] == "wind_down"
    gp = paths.gameplan_dir(GID) / "GAMEPLAN.md"
    gp.write_text(gp.read_text(encoding="utf-8")
                  .replace("> Budget: 2 sessions", "> Budget: 8 sessions"),
                  encoding="utf-8")
    (rec,) = budgets.assess(paths, GID, "1")
    assert rec["state"] == "ok"               # nothing persisted the old state


# --- wording: phase-aware, one voice ------------------------------------------

def test_wind_down_and_over_speak_different_sentences(temp_repo):
    paths, _ = _ctx(temp_repo)
    _declare_gameplan_budget(paths, "2")
    _stint(paths, "2026-07-01")
    (rec,) = budgets.assess(paths, GID, "1")
    wd = budgets.describe(rec)
    assert "IN the final budgeted stint" in wd
    assert "land the Ending Protocol" in wd
    _stint(paths, "2026-07-02")
    _stint(paths, "2026-07-03")
    (rec,) = budgets.assess(paths, GID, "1")
    over = budgets.describe(rec)
    assert "exceeds budget" in over and "IN the final" not in over
    for text in (wd, over):
        assert "never blocks" in text or "nothing blocks" in text


# --- surfacing: digest, preflight recorder, pre_compact convergence -----------

def test_digest_one_line_when_wound_down_and_shared_wording(temp_repo):
    paths, config = _ctx(temp_repo)
    _declare_gameplan_budget(paths, "2")
    _stint(paths, "2026-07-01")
    bundle = S.compute(paths, config)
    (rec,) = bundle["budgets"]
    digest = S.render_digest(bundle)
    assert f"⏳ Wind-down: {budgets.describe(rec)}" in digest


def test_ok_state_emits_zero_bytes(temp_repo):
    paths, config = _ctx(temp_repo)
    _declare_gameplan_budget(paths, "9")
    _stint(paths, "2026-07-01")
    digest = S.render_digest(S.compute(paths, config))
    assert "Wind-down" not in digest


def test_the_op_is_the_recorder_and_the_library_run_is_write_free(temp_repo):
    """The stint writer is cz_preflight (the OP, writes=True) — never the
    library run(): tests, embedders, and read-only fixtures calling run()
    directly must stay byte-free of telemetry (the sample_repo fixture is the
    motivating casualty this pins against)."""
    paths, config = _ctx(temp_repo)
    config.preflight_checks = ["deps_spotcheck"]
    from clauderizer.profiles.detect import Profile
    profile = Profile(name="generic", commands={}, baseline_test_regex="")
    preflight.run(paths, config, profile, runner=lambda c, w: (0, ""))
    assert not [e for e in telemetry.read_events(paths.telemetry_file)
                if e.get("kind") == "stint"]
    preflight.record_run_stint(paths, config)
    preflight.record_run_stint(paths, config)
    stints = [e for e in telemetry.read_events(paths.telemetry_file)
              if e.get("kind") == "stint"]
    assert len(stints) == 2                   # raw appends, both recorded
    _declare_gameplan_budget(paths, "9")
    (rec,) = budgets.assess(paths, GID, stints[0]["phase"])
    assert rec["spent"] == 1                  # deduped to one DATE at read


def test_the_cz_preflight_op_calls_the_recorder(temp_repo, monkeypatch):
    monkeypatch.chdir(temp_repo)
    from clauderizer import ops as O
    calls = []
    monkeypatch.setattr(O.preflight, "run",
                        lambda *a, **k: preflight.PreflightResult())
    monkeypatch.setattr(O.preflight, "record_run_stint",
                        lambda paths, config: calls.append(config.active_gameplan))
    O.run_op("cz_preflight")
    assert calls == [GID]


def test_pre_compact_carries_the_wind_down_convergence(temp_repo, monkeypatch):
    paths, config = _ctx(temp_repo)
    _declare_gameplan_budget(paths, "2")
    _stint(paths, "2026-07-01")
    monkeypatch.chdir(temp_repo)
    from clauderizer.hook import handlers
    msg = handlers.pre_compact({})
    assert msg is not None
    assert "IN the final budgeted stint" in msg
    # quiet repo: the reminder exists but carries no budget note
    gp = paths.gameplan_dir(GID) / "GAMEPLAN.md"
    gp.write_text(gp.read_text(encoding="utf-8")
                  .replace("> Budget: 2 sessions", "> Budget: 9 sessions"),
                  encoding="utf-8")
    msg2 = handlers.pre_compact({})
    assert msg2 is not None and "budgeted stint" not in msg2


def test_next_phase_context_attaches_wind_down(temp_repo, monkeypatch):
    paths, _ = _ctx(temp_repo)
    _declare_gameplan_budget(paths, "2")
    _stint(paths, "2026-07-01")
    monkeypatch.chdir(temp_repo)
    from clauderizer import ops
    res = ops.run_op("cz_next_phase_context")
    assert res.get("wind_down")
    assert "IN the final budgeted stint" in res["wind_down"][0]["advisory"]
