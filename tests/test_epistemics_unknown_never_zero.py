"""2.0-alpha Phase 0 — unknowable-never-zero epistemics (D-070, D-065/D-069 lineage).

A reading that could not be measured is a DIFFERENT CLAIM from a measured
zero/unmet/pass. Four residual conflation sites get their missing arms, and the
tests here are the detectors (D-069):

1. ``conditions.evaluate``: a probe that could not RUN (timeout / OS error) is
   ``unevaluable`` — distinct from evaluated-unmet. ``met`` stays a boolean and
   the new field is additive, so external ``if c.get("met")`` consumers are
   untouched (INVARIANT-07).
2. preflight ``standing_conditions``: an armed guard whose probe cannot run
   "cannot trip" — WARN, never a silent "none met".
3. preflight command gates: a runner that RAISES is UNKNOWN, not pass and not a
   preflight crash — the other checks survive, the verdict lowers to
   PASS WITH WARNINGS, ``passed`` stays True.
4. curator consolidation: an unmeasured utility is never coerced to 0.0 — the
   keep/drop evidence names what was measured and what was not.

Plus the working-time disclosure: staleness ages gain a hedged "~N active
day(s)" ONLY when a stale set exists (healthy repos: no git call, byte-identical
digest — INVARIANT-08); any git failure means NO claim, never a fabricated one.
"""

from __future__ import annotations

import subprocess

import pytest

from clauderizer import config as cfg
from clauderizer import paths as P
from clauderizer import telemetry
from clauderizer.rituals import conditions, preflight, status_bundle

GID = "2026-05-01-bootstrap"


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _declare(paths, gid, body):
    p = paths.clauderizer_dir / f"conditions.{gid}.toml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def _stub_profile(commands=None):
    from clauderizer.profiles.detect import Profile

    return Profile(name="generic", commands=commands or {}, baseline_test_regex="")


def _ok_runner(cmd, cwd):
    return 0, ""


# --- 1. probe arms: could-not-run is unevaluable, not unmet -------------------

def test_probe_timeout_is_unevaluable_not_unmet(temp_repo, monkeypatch):
    paths, _ = _ctx(temp_repo)
    _declare(paths, GID, '[conditions]\nslow = "sleep 999"\n')

    def _boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="sleep 999", timeout=30)

    monkeypatch.setattr(conditions.subprocess, "run", _boom)
    (row,) = conditions.evaluate(paths, GID)
    assert row["met"] is False
    assert row["unevaluable"] is True
    assert "timed out" in row["detail"]


def test_probe_oserror_is_unevaluable_not_unmet(temp_repo, monkeypatch):
    paths, _ = _ctx(temp_repo)
    _declare(paths, GID, '[conditions]\nbroken = "whatever"\n')

    def _boom(*a, **k):
        raise OSError("no such device")

    monkeypatch.setattr(conditions.subprocess, "run", _boom)
    (row,) = conditions.evaluate(paths, GID)
    assert row["met"] is False
    assert row["unevaluable"] is True
    assert "no such device" in row["detail"]


def test_probe_that_ran_nonzero_is_evaluated_unmet_not_unevaluable(temp_repo):
    """A probe that RAN and exited nonzero (including a 127 from a missing
    binary under shell=True) was EVALUATED — unmet is a measured reading."""
    paths, _ = _ctx(temp_repo)
    _declare(paths, GID, '[conditions]\nunmet = "exit 7"\n')
    (row,) = conditions.evaluate(paths, GID)
    assert row["met"] is False
    assert not row.get("unevaluable")


def test_met_stays_boolean_truthiness_contract(temp_repo, monkeypatch):
    """External clauderize-ops JSON consumers rely on `if c.get("met")` — the
    unevaluable arm must not flip met to a third state (INVARIANT-07)."""
    paths, _ = _ctx(temp_repo)
    _declare(paths, GID, '[conditions]\na = "exit 0"\nb = "exit 1"\n')
    for row in conditions.evaluate(paths, GID):
        assert isinstance(row["met"], bool)

    def _boom(*a, **k):
        raise OSError("gone")

    monkeypatch.setattr(conditions.subprocess, "run", _boom)
    for row in conditions.evaluate(paths, GID):
        assert isinstance(row["met"], bool) and row["met"] is False


# --- 2. preflight: an armed guard that cannot run cannot trip -----------------

def test_preflight_warns_cannot_trip_when_probe_unevaluable(temp_repo, monkeypatch):
    paths, config = _ctx(temp_repo)
    config.preflight_checks = ["clean_tree"]
    _declare(paths, config.active_gameplan, '[conditions]\nguard = "x"\n')

    def _boom(*a, **k):
        raise OSError("probe binary vanished")

    monkeypatch.setattr(conditions.subprocess, "run", _boom)
    res = preflight.run(paths, config, _stub_profile(), runner=_ok_runner)
    d = res.to_dict()
    gate = next(c for c in d["checks"] if c["name"] == "standing_conditions")
    assert gate["status"] == "warn"
    assert "cannot trip" in gate["detail"]
    assert d["passed"] is True
    assert "PASS WITH WARNINGS" in d["summary"]


def test_preflight_all_ran_none_met_stays_quiet_pass(temp_repo):
    paths, config = _ctx(temp_repo)
    config.preflight_checks = ["clean_tree"]
    _declare(paths, config.active_gameplan, '[conditions]\ndue = "exit 1"\n')
    res = preflight.run(paths, config, _stub_profile(), runner=_ok_runner).to_dict()
    gate = next(c for c in res["checks"] if c["name"] == "standing_conditions")
    assert gate["status"] == "pass"
    assert "none met" in gate["detail"]


# --- 3. command gates: UNKNOWN is contained, named, and not a pass ------------

def _raising_runner(gate_cmd):
    def _runner(cmd, cwd):
        if cmd == gate_cmd:
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=600)
        return 0, ""

    return _runner


def test_command_gate_unknown_contained_and_named(temp_repo):
    paths, config = _ctx(temp_repo)
    config.preflight_checks = ["clean_tree", "tests"]
    profile = _stub_profile({"test": "run-the-suite"})
    res = preflight.run(paths, config, profile,
                        runner=_raising_runner("run-the-suite"))
    d = res.to_dict()
    # every other check survived the raise (degrade, don't crash — O-03)
    assert any(c["name"] == "clean_tree" for c in d["checks"])
    gate = next(c for c in d["checks"] if c["name"] == "tests")
    assert gate["status"] == "unknown"
    assert "UNKNOWN, not pass" in gate["detail"]
    assert d["passed"] is True
    assert d["verdict"] == "PASS WITH WARNINGS"
    assert d["gates_unrun"] == ["tests"]
    assert "unknown" in d["summary"]


def test_verdict_field_mirrors_summary_across_matrix(temp_repo):
    paths, config = _ctx(temp_repo)
    config.preflight_checks = ["clean_tree", "tests"]
    profile = _stub_profile({"test": "suite"})
    ok = preflight.run(paths, config, profile, runner=_ok_runner).to_dict()
    assert ok["verdict"] == "PASS" and "PASS:" in ok["summary"]
    assert ok["gates_unrun"] == []

    def _fail_runner(cmd, cwd):
        return (1, "boom") if cmd == "suite" else (0, "")

    bad = preflight.run(paths, config, profile, runner=_fail_runner).to_dict()
    assert bad["verdict"] == "FAIL" and bad["passed"] is False


def test_unwired_declared_gate_counts_as_unrun(temp_repo):
    """The #6a warn (declared-but-unwired) is also an unrun gate — the additive
    gates_unrun field makes 'which QA never executed' machine-readable."""
    paths, config = _ctx(temp_repo)
    config.preflight_checks = ["clean_tree", "virality_qa"]
    res = preflight.run(paths, config, _stub_profile(), runner=_ok_runner).to_dict()
    gate = next(c for c in res["checks"] if c["name"] == "virality_qa")
    assert gate["status"] == "warn"
    assert "virality_qa" in res["gates_unrun"]


# --- 4. curator: unmeasured utility is never a measured zero ------------------

def _bare_repo_with_lessons(tmp_path, lines):
    repo = tmp_path / "repo"
    doc = repo / "docs" / "LESSONS.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("## Lessons\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return P.resolve(repo)


REDUNDANT = [
    "**L-01.** always run the full pytest suite before any irreversible release *(from g)*",
    "**L-02.** always run the full pytest suite before every irreversible release step *(from g)*",
]


def test_curate_names_the_unmeasured_side_instead_of_coercing(tmp_path):
    paths = _bare_repo_with_lessons(tmp_path, REDUNDANT)
    telemetry.record_surfaced(paths.telemetry_file, gameplan="g", phase="1",
                              lessons=["L-01"], invariants=[],
                              gameplan_lessons=[], today="2026-06-21")
    telemetry.record_outcome(paths.telemetry_file, gameplan="g", phase="1",
                             status="complete", criteria_total=1,
                             criteria_checked=1, today="2026-06-21")
    props = telemetry.curate_proposals(paths)
    (cons,) = [p for p in props["proposals"] if p["action"] == "consolidate"]
    assert cons["suggested_args"]["number"] == "L-02"      # keep the measured one
    assert "unmeasured" in cons["note"]
    assert ">= utility" not in cons["note"]                # no fake comparison


def test_curate_makes_no_ranked_claim_when_neither_measured(tmp_path):
    paths = _bare_repo_with_lessons(tmp_path, REDUNDANT)
    props = telemetry.curate_proposals(paths)
    (cons,) = [p for p in props["proposals"] if p["action"] == "consolidate"]
    assert "unmeasured for both" in cons["note"]
    assert "content, not score" in cons["note"]
    assert ">= utility" not in cons["note"]


# --- working-time disclosure: hedged, stale-gated, no-claim-on-failure --------

def _fake_git_dates(dates_stdout):
    class _Proc:
        returncode = 0
        stdout = dates_stdout

    def _run(*a, **k):
        return _Proc()

    return _run


def test_findings_age_gains_hedged_active_days_when_git_answers(tmp_path, monkeypatch):
    monkeypatch.setattr(status_bundle.subprocess, "run",
                        _fake_git_dates("2026-07-01\n2026-07-01\n2026-07-20\n"))
    age = status_bundle._findings_by_age(
        [{"id": "H-01", "date": "2026-05-01"}], today="2026-07-26", root=tmp_path)
    assert age["oldest_id"] == "H-01"
    assert age["oldest_active_days"] == 2          # distinct dates, dupes folded


def test_findings_age_makes_no_claim_when_git_fails(tmp_path, monkeypatch):
    def _boom(*a, **k):
        raise OSError("git vanished")

    monkeypatch.setattr(status_bundle.subprocess, "run", _boom)
    age = status_bundle._findings_by_age(
        [{"id": "H-01", "date": "2026-05-01"}], today="2026-07-26", root=tmp_path)
    assert age is not None
    assert "oldest_active_days" not in age         # no claim, never a fake 0


def test_no_stale_findings_means_no_git_call_at_all(tmp_path, monkeypatch):
    calls = []

    def _spy(*a, **k):
        calls.append(a)
        raise AssertionError("git must not run for a healthy register")

    monkeypatch.setattr(status_bundle.subprocess, "run", _spy)
    age = status_bundle._findings_by_age(
        [{"id": "H-01", "date": "2026-07-25"}], today="2026-07-26", root=tmp_path)
    assert age is None and calls == []


def test_digest_line_carries_the_hedge_only_when_measured():
    line_with = status_bundle._findings_age_phrase(
        {"oldest_id": "H-01", "oldest_days": 64, "stale_ids": ["H-01"],
         "oldest_active_days": 14})
    assert "oldest H-01 at 64d (~14 active day(s))" in line_with
    line_without = status_bundle._findings_age_phrase(
        {"oldest_id": "H-01", "oldest_days": 64, "stale_ids": ["H-01"]})
    assert "active day" not in line_without
    assert "oldest H-01 at 64d" in line_without


# --- digest: unevaluable line is tool-path-only and quiet-by-construction -----

def test_digest_surfaces_unevaluable_guard_on_tool_path_only(temp_repo, monkeypatch):
    paths, config = _ctx(temp_repo)
    _declare(paths, config.active_gameplan, '[conditions]\nguard = "x"\n')

    def _boom(*a, **k):
        raise OSError("gone")

    monkeypatch.setattr(conditions.subprocess, "run", _boom)
    # hook shape: never evaluates, never mentions conditions (INVARIANT-06)
    hook_digest = status_bundle.render_digest(status_bundle.compute(paths, config))
    assert "unevaluable" not in hook_digest
    # tool shape: the armed-but-unrunnable guard is disclosed
    tool_digest = status_bundle.render_digest(
        status_bundle.compute(paths, config, conditions=True))
    assert "Standing condition unevaluable: guard" in tool_digest
    assert "cannot trip" in tool_digest


def test_digest_byte_identical_when_all_probes_run(temp_repo):
    paths, config = _ctx(temp_repo)
    _declare(paths, config.active_gameplan, '[conditions]\ndue = "exit 1"\n')
    d = status_bundle.render_digest(status_bundle.compute(paths, config, conditions=True))
    assert "unevaluable" not in d and "cannot trip" not in d
