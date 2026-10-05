"""Pilot-benchmark field fixes for the node profile's preflight gates.

1. A Node project with no `build` script made `npm run build` exit non-zero, the
   build gate FAILED, and the procedure stopped the phase to ask — so an
   unattended agent never started work. A missing package.json script now
   SKIPS (did not run, listed in gates_unrun) instead of failing.
2. The baseline test count only matched mocha's "N passing"; node:test (spec
   and TAP), jest and vitest output now parse too."""

import json
import re

from clauderizer import config as cfg
from clauderizer import paths as P
from clauderizer.profiles.detect import Profile, load
from clauderizer.rituals import preflight


def _ctx(repo, checks):
    paths = P.resolve(repo)
    config = cfg.Config.load(paths.config_file)
    config.preflight_checks = checks
    return paths, config


def _node_profile():
    return Profile(name="node", commands={"test": "npm test", "build": "npm run build"},
                   baseline_test_regex=load("node").baseline_test_regex)


def _pkg(repo, scripts):
    (repo / "package.json").write_text(json.dumps({"name": "x", "scripts": scripts}), encoding="utf-8")


def _recording_runner(calls, out=""):
    def _run(cmd, cwd):
        calls.append(cmd)
        return 0, out
    return _run


def test_missing_build_script_skips_instead_of_failing(temp_repo):
    _pkg(temp_repo, {"test": "node --test"})
    paths, config = _ctx(temp_repo, ["tests", "build"])
    calls = []
    d = preflight.run(paths, config, _node_profile(), runner=_recording_runner(calls)).to_dict()
    build = next(c for c in d["checks"] if c["name"] == "build")
    assert build["status"] == "skip"
    assert 'no "build" script' in build["detail"]
    assert "npm run build" not in calls          # never executed
    assert d["passed"] is True
    assert "build" in d["gates_unrun"]           # honest: it did not run


def test_existing_build_script_still_runs_and_can_fail(temp_repo):
    _pkg(temp_repo, {"test": "node --test", "build": "tsc"})
    paths, config = _ctx(temp_repo, ["build"])
    d = preflight.run(paths, config, _node_profile(),
                      runner=lambda cmd, cwd: (2, "error")).to_dict()
    build = next(c for c in d["checks"] if c["name"] == "build")
    assert build["status"] == "fail"
    assert d["passed"] is False


def test_unreadable_package_json_runs_the_command_as_before(temp_repo):
    (temp_repo / "package.json").write_text("{not json", encoding="utf-8")
    assert preflight._missing_npm_script(temp_repo, "npm run build") is None


def test_missing_npm_script_matcher(tmp_path):
    _pkg(tmp_path, {"test": "x"})
    assert preflight._missing_npm_script(tmp_path, "npm run build") == "build"
    assert preflight._missing_npm_script(tmp_path, "npm run-script lint") == "lint"
    assert preflight._missing_npm_script(tmp_path, "npm test") is None
    assert preflight._missing_npm_script(tmp_path, "make build") is None
    assert preflight._missing_npm_script(tmp_path, "npm run build && npm run x") is None
    _pkg(tmp_path, {})
    assert preflight._missing_npm_script(tmp_path, "npm test") == "test"


def test_node_baseline_regex_parses_common_runners():
    rx = load("node").baseline_test_regex
    count = lambda out: next((g for g in re.search(rx, out).groups() if g), None)
    assert count("  12 passing (40ms)") == "12"                       # mocha
    assert count("ℹ tests 3\nℹ suites 0\nℹ pass 3") == "3"            # node:test spec
    assert count("1..3\n# tests 3\n# pass 3") == "3"                  # node:test TAP
    assert count("Tests:       7 passed, 7 total") == "7"             # jest
    assert count(" Test Files  1 passed (1)\n      Tests  5 passed (5)") == "5"  # vitest


def test_node_test_count_recorded_in_preflight(temp_repo):
    _pkg(temp_repo, {"test": "node --test"})
    paths, config = _ctx(temp_repo, ["tests"])
    res = preflight.run(paths, config, _node_profile(),
                        runner=lambda cmd, cwd: (0, "ℹ tests 3\nℹ pass 3\nℹ fail 0"))
    assert res.baseline_tests == "3"
