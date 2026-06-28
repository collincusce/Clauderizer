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


def test_unwired_gate_warns_not_silent_skip(temp_repo):
    """#6a false-green fix: a kind-declared QA gate with no wired command must NOT
    read as a clean green — it WARNS (it did not run), but does not hard-fail
    (the engine ships the mechanism, never the QA logic)."""
    paths, config = _make_campaign(temp_repo)  # no preflight.campaign.toml written
    result = preflight.run(paths, config, Profile(name="python", commands={}),
                           runner=_fake_runner({"git status --porcelain": (0, "")}))
    vir = next(c for c in result.checks if c.name == "virality")
    assert vir.status == "warn"                    # loud, not a silent skip
    assert "did NOT run" in vir.detail
    assert "preflight.campaign.toml" in vir.detail  # actionable hint
    assert result.passed is True                   # advisory: warn never hard-fails
    # but the verdict must surface the warning so it can't be misread as all-clear
    summary = result.to_dict()["summary"]
    assert "WARNINGS" in summary and "warned" in summary


def test_shipped_campaign_preflight_example_is_inert():
    """#6a (b): an example wiring file ships for discoverability, but it must be
    INERT (the `.example` suffix, gates commented out) so it can never itself
    create a false-green by exit-0 placeholder commands."""
    import tomllib
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    example = repo_root / ".clauderizer" / "preflight.campaign.toml.example"
    assert example.exists(), "the example campaign preflight wiring should ship"
    data = tomllib.loads(example.read_text(encoding="utf-8"))
    # no active gate commands -> the engine's _load_preflight_gates would yield {}
    assert not data.get("gates"), "example gates must be commented out (inert)"


def test_command_gate_runs_a_real_subprocess(temp_repo):
    """#3 (b): exercise the command-gate via the REAL runner (a true subprocess,
    not the fake) — exit-code -> status mapping, output capture, and the
    wired/unwired/advisory ordering, all in one check list.

    Two real runs over the same campaign:
      A) no advisory -> a non-zero gate FAILS preflight, its detail carries the exit
         code (output is captured), wired-pass passes, unwired WARNS;
      B) the same failing gate marked advisory -> it downgrades to warn, passed=True.
    """
    import sys

    py = sys.executable
    pass_cmd = f'"{py}" -c "import sys; sys.exit(0)"'
    fail_cmd = f'"{py}" -c "import sys; sys.exit(7)"'

    paths, config = _make_campaign(temp_repo)
    # virality wired-pass, brand_lint wired-fail; duration left UNWIRED. Written with
    # TOML literal (single-quoted) strings since the commands contain double quotes.
    (paths.clauderizer_dir / "preflight.campaign.toml").write_text(
        "[gates]\n" f"virality = '{pass_cmd}'\n" f"brand_lint = '{fail_cmd}'\n",
        encoding="utf-8")
    profile = Profile(name="python", commands={})

    # --- run A: real subprocess, no advisory --------------------------------------
    result = preflight.run(paths, config, profile)  # no runner= -> _default_runner
    by = {c.name: c for c in result.checks}
    # ordering follows the kind's enabled list
    assert [c.name for c in result.checks] == ["clean_tree", "virality", "brand_lint", "duration"]
    assert by["virality"].status == "pass"                  # exit 0 -> pass
    assert by["brand_lint"].status == "fail"                # exit 7 -> fail
    assert "exit 7" in by["brand_lint"].detail             # output/exit captured
    assert by["duration"].status == "warn"                  # declared but unwired (#6a)
    assert result.passed is False                           # a real failing gate fails preflight

    # --- run B: same failing gate, now advisory -> downgraded on the real path -----
    config.preflight_advisory = ["brand_lint"]
    result2 = preflight.run(paths, config, profile)
    by2 = {c.name: c for c in result2.checks}
    assert by2["brand_lint"].status == "warn" and "(advisory)" in by2["brand_lint"].detail
    assert result2.passed is True                           # advisory failure never hard-fails


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
