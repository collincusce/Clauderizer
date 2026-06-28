"""Phase 3 of concurrent-multi-axis-gameplans: per-kind / per-gameplan preflight.

The check LIST comes from the focus gameplan's kind; tests/build and campaign-style
gates (virality, brand_lint, …) are one command-gate primitive whose command
resolves from .clauderizer/preflight.<kind>.toml else the host profile; unwired
gates skip-with-hint. Clauderizer ships the mechanism, never the QA logic.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from clauderizer import config as cfg
from clauderizer import ops
from clauderizer import paths as P
from clauderizer.profiles.detect import Profile
from clauderizer.rituals import preflight


@contextmanager
def _chdir(path: Path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _fake_runner(responses):
    def run(cmd, cwd):
        for key, val in responses.items():
            if key in cmd:
                return val
        return (0, "")
    return run


def _make_campaign(repo: Path) -> tuple:
    """Create a campaign gameplan (becomes focus) and return (paths, reloaded config)."""
    with _chdir(repo):
        ops.cz_create_gameplan("spring promo", kind="campaign")
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _wire_gates(paths: P.RepoPaths, kind: str, **gates: str) -> None:
    body = "[gates]\n" + "".join(f'{k} = "{v}"\n' for k, v in gates.items())
    (paths.clauderizer_dir / f"preflight.{kind}.toml").write_text(body, encoding="utf-8")


# --- the check list comes from the kind ---------------------------------------


def test_campaign_check_list_comes_from_kind(temp_repo):
    paths, config = _make_campaign(temp_repo)
    _wire_gates(paths, "campaign", virality="run-vir", brand_lint="run-bl", duration="run-dur")
    result = preflight.run(paths, config, Profile(name="python", commands={"test": "pytest"}),
                           runner=_fake_runner({"git status --porcelain": (0, "")}))
    names = [c.name for c in result.checks]
    # the campaign kind's list — NOT config's (branch_base/tests/build/...)
    assert names == ["clean_tree", "virality", "brand_lint", "duration"]
    assert "tests" not in names and "branch_base" not in names


def test_driven_preflight_unchanged(temp_repo):
    # focus is the fixture's driven gameplan; enabled still comes from config and
    # tests/build still resolve from the host profile, with baseline parsing.
    paths, config = P.resolve(temp_repo), cfg.Config.load(P.resolve(temp_repo).config_file)
    config.preflight_checks = ["clean_tree", "tests"]
    profile = Profile(name="python", commands={"test": "pytest -q"},
                      baseline_test_regex=r"(\d+) passed")
    result = preflight.run(paths, config, profile, runner=_fake_runner({
        "git status --porcelain": (0, ""), "pytest": (0, "42 passed in 1s")}))
    names = {c.name: c.status for c in result.checks}
    assert names == {"clean_tree": "pass", "tests": "pass"}
    assert result.baseline_tests == "42"  # tests gate still parses the count


# --- command-gate behavior -----------------------------------------------------


def test_wired_gate_passes_and_fails_by_exit_code(temp_repo):
    paths, config = _make_campaign(temp_repo)
    _wire_gates(paths, "campaign", virality="run-vir", brand_lint="run-bl", duration="run-dur")
    result = preflight.run(paths, config, Profile(name="python", commands={}),
                           runner=_fake_runner({
                               "git status --porcelain": (0, ""),
                               "run-vir": (0, "ok"),
                               "run-bl": (1, "brand violation"),
                               "run-dur": (0, "ok"),
                           }))
    st = {c.name: c.status for c in result.checks}
    assert st["virality"] == "pass" and st["duration"] == "pass"
    assert st["brand_lint"] == "fail"
    assert result.passed is False  # a failed gate fails preflight


def test_unwired_gate_skips_with_hint(temp_repo):
    paths, config = _make_campaign(temp_repo)  # no preflight.campaign.toml written
    result = preflight.run(paths, config, Profile(name="python", commands={}),
                           runner=_fake_runner({"git status --porcelain": (0, "")}))
    vir = next(c for c in result.checks if c.name == "virality")
    assert vir.status == "skip"
    assert "preflight.campaign.toml" in vir.detail  # actionable hint
    assert result.passed is True  # a skip never fails preflight


def test_gate_failure_downgraded_by_advisory(temp_repo):
    paths, config = _make_campaign(temp_repo)
    config.preflight_advisory = ["brand_lint"]
    _wire_gates(paths, "campaign", virality="run-vir", brand_lint="run-bl", duration="run-dur")
    result = preflight.run(paths, config, Profile(name="python", commands={}),
                           runner=_fake_runner({
                               "git status --porcelain": (0, ""),
                               "run-vir": (0, ""), "run-bl": (1, "x"), "run-dur": (0, ""),
                           }))
    bl = next(c for c in result.checks if c.name == "brand_lint")
    assert bl.status == "warn" and "(advisory)" in bl.detail
    assert result.passed is True  # advisory failure does not fail preflight
