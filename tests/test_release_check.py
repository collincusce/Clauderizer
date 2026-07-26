"""harness-truth Phase 3 (O3, D-011): the release preflight ritual.

Two releases were double-claimed in one day by cutting a GitHub Release while
the staged work — including the publish gate itself — was local-only (L-08,
H-07). These tests prove the guard fires on every individual skew (D5: a
guard you haven't seen fail isn't a guard) against REAL git repos with a
local bare origin; the network registries (PyPI, GitHub Releases) are seamed
and patched so the suite stays offline.
"""

import subprocess
from pathlib import Path

import pytest

from clauderizer import release_check
from clauderizer.release_check import GATE_MARKER, run


def _git(cwd: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "-c", "init.defaultBranch=main", *args],
        cwd=str(cwd), capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"git {' '.join(args)}: {r.stderr}"
    return r.stdout.strip()


@pytest.fixture
def staged_repo(tmp_path, monkeypatch):
    """A committed, pushed repo with a version source and clean registries."""
    origin = tmp_path / "origin.git"
    origin.mkdir()
    _git(origin, "init", "--bare", "-q")
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "testpkg"\nversion = "0.1.0"\n', encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "release 0.1.0")
    _git(repo, "remote", "add", "origin", origin.as_posix())
    _git(repo, "push", "-q", "-u", "origin", "main")
    # offline seams: both remote registries report unclaimed, and CI is green.
    # (The CI seam only matters for tests that create .github/workflows/ — the
    # check skips outright when a repo has no workflows at all.)
    monkeypatch.setattr(release_check, "_pypi_claimed", lambda n, v: False)
    monkeypatch.setattr(release_check, "_gh_release_exists", lambda r, t: False)
    monkeypatch.setattr(release_check, "_ci_runs_and_jobs",
                        lambda r, sha: (_RUN_OK, [_job("test (ubuntu-latest, 3.13)")]))
    return repo


# --- CI-at-job-granularity fixtures (H-28) --------------------------------------

#: A run whose own conclusion is `success` — the field this check never trusts.
_RUN_OK = [{"databaseId": 1, "name": "Tests", "status": "completed",
            "conclusion": "success"}]


def _job(name, conclusion="success", workflow="Tests"):
    return {"workflow": workflow, "job": name, "status": "completed",
            "conclusion": conclusion}


@pytest.fixture
def repo_with_ci(staged_repo):
    """A staged repo that HAS workflows, so the CI check engages instead of skipping."""
    wf = staged_repo / ".github" / "workflows" / "test.yml"
    wf.parent.mkdir(parents=True, exist_ok=True)
    wf.write_text("name: Tests\n", encoding="utf-8")
    _git(staged_repo, "add", "-A")
    _git(staged_repo, "commit", "-q", "-m", "add ci")
    _git(staged_repo, "push", "-q", "origin", "main")
    return staged_repo


CI_LABEL = "CI green on this commit"


def _by_label(checks, fragment):
    matches = [c for c in checks if fragment in c.label]
    assert matches, f"no check matching {fragment!r}: {[c.label for c in checks]}"
    return matches[0]


def test_green_path_exit_0(staged_repo):
    code, checks = run(staged_repo)
    assert code == 0
    assert _by_label(checks, "clean tree").status == "ok"
    assert _by_label(checks, "push-then-release").status == "ok"
    assert _by_label(checks, "local tag v0.1.0").status == "ok"
    assert _by_label(checks, "remote tag v0.1.0").status == "ok"
    assert _by_label(checks, "PyPI testpkg==0.1.0").status == "ok"
    assert _by_label(checks, "publish gate").status == "skip"  # no publish.yml


def test_readme_naming_the_ritual_is_ok(staged_repo):
    (staged_repo / "README.md").write_text(
        "Release: run `clauderize release-check` first.\n", encoding="utf-8")
    _git(staged_repo, "add", "-A")
    _git(staged_repo, "commit", "-q", "-m", "readme")
    _git(staged_repo, "push", "-q", "origin", "main")
    code, checks = run(staged_repo)
    assert code == 0
    assert _by_label(checks, "README names the ritual").status == "ok"


def test_readme_drifted_from_ritual_is_red(staged_repo):
    # G7 between sibling docs: a README that documents releasing without the
    # check is exactly how the real README contradicted RELEASING.md.
    (staged_repo / "README.md").write_text(
        "Release: bump the version and cut a GitHub Release.\n", encoding="utf-8")
    _git(staged_repo, "add", "-A")
    _git(staged_repo, "commit", "-q", "-m", "readme")
    _git(staged_repo, "push", "-q", "origin", "main")
    code, checks = run(staged_repo)
    assert code == 2
    c = _by_label(checks, "README names the ritual")
    assert c.status == "fail"
    assert "drifted" in c.detail


def test_unpushed_commit_is_red(staged_repo):
    (staged_repo / "x.txt").write_text("x", encoding="utf-8")
    _git(staged_repo, "add", "-A")
    _git(staged_repo, "commit", "-q", "-m", "local-only work")
    code, checks = run(staged_repo)
    assert code == 2
    c = _by_label(checks, "push-then-release")
    assert c.status == "fail"
    assert "REMOTE head" in c.detail  # names the UI-release mechanism


def test_dirty_tree_is_red(staged_repo):
    (staged_repo / "dirty.txt").write_text("x", encoding="utf-8")
    code, checks = run(staged_repo)
    assert code == 2
    assert _by_label(checks, "clean tree").status == "fail"


def test_local_tag_already_claimed(staged_repo):
    _git(staged_repo, "tag", "v0.1.0")
    code, checks = run(staged_repo)
    assert code == 2
    assert _by_label(checks, "local tag v0.1.0").status == "fail"


def test_remote_only_tag_is_caught(staged_repo):
    # The v0.7.0/v0.8.0 shape: the tag exists on the remote but not locally.
    _git(staged_repo, "tag", "v0.1.0")
    _git(staged_repo, "push", "-q", "origin", "v0.1.0")
    _git(staged_repo, "tag", "-d", "v0.1.0")
    code, checks = run(staged_repo)
    assert code == 2
    assert _by_label(checks, "local tag v0.1.0").status == "ok"
    c = _by_label(checks, "remote tag v0.1.0")
    assert c.status == "fail"
    assert "remote-only" in c.detail


def test_claimed_release_and_pypi_are_red(staged_repo, monkeypatch):
    monkeypatch.setattr(release_check, "_gh_release_exists", lambda r, t: True)
    monkeypatch.setattr(release_check, "_pypi_claimed", lambda n, v: True)
    code, checks = run(staged_repo)
    assert code == 2
    assert _by_label(checks, "GitHub Release v0.1.0").status == "fail"
    assert _by_label(checks, "PyPI testpkg==0.1.0").status == "fail"


def test_unqueryable_registries_are_unverifiable_not_green(staged_repo, monkeypatch):
    monkeypatch.setattr(release_check, "_gh_release_exists", lambda r, t: None)
    monkeypatch.setattr(release_check, "_pypi_claimed", lambda n, v: None)
    code, checks = run(staged_repo)
    assert code == 3  # honest middle — never a false green (D-010)
    assert _by_label(checks, "GitHub Release v0.1.0").status == "unverifiable"
    assert _by_label(checks, "PyPI testpkg==0.1.0").status == "unverifiable"


def test_publish_workflow_without_gate_is_red(staged_repo):
    wf = staged_repo / ".github" / "workflows" / "publish.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text("name: Publish\non:\n  release:\n", encoding="utf-8")
    _git(staged_repo, "add", "-A")
    _git(staged_repo, "commit", "-q", "-m", "add gateless workflow")
    _git(staged_repo, "push", "-q", "origin", "main")
    code, checks = run(staged_repo)
    assert code == 2
    c = _by_label(checks, "publish gate")
    assert c.status == "fail" and "skewed" in c.detail


def test_publish_workflow_with_gate_is_ok(staged_repo):
    wf = staged_repo / ".github" / "workflows" / "publish.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text(f"name: Publish\n# {GATE_MARKER}\n", encoding="utf-8")
    _git(staged_repo, "add", "-A")
    _git(staged_repo, "commit", "-q", "-m", "add gated workflow")
    _git(staged_repo, "push", "-q", "origin", "main")
    code, checks = run(staged_repo)
    assert code == 0
    assert _by_label(checks, "publish gate").status == "ok"


def test_no_version_source_skips_sweep(staged_repo):
    (staged_repo / "pyproject.toml").unlink()
    _git(staged_repo, "add", "-A")
    _git(staged_repo, "commit", "-q", "-m", "drop pyproject")
    _git(staged_repo, "push", "-q", "origin", "main")
    code, checks = run(staged_repo)
    assert code == 0
    assert _by_label(checks, "version source").status == "skip"
    assert not [c for c in checks if "tag v" in c.label]  # sweep skipped


def test_not_a_git_repo_fails(tmp_path):
    code, checks = run(tmp_path)
    assert code == 2
    assert checks[0].status == "fail"


def test_gate_marker_matches_real_publish_workflow():
    # The marker release-check greps for must exist verbatim in OUR workflow —
    # if the step is renamed, this pins the two together (D5: marker drift).
    wf = Path(__file__).parents[1] / ".github" / "workflows" / "publish.yml"
    assert GATE_MARKER in wf.read_text(encoding="utf-8")


# --- H-28: the registries say the VERSION is free; nothing said the CODE passes ---
#
# 0.14.0 and 1.14.2 both shipped with Windows cells red. L-51 sweep (2) named the
# rule ("run the suite on EVERY host leg the CI matrix covers") and it stayed
# discipline, so 1.14.3 verified job granularity by hand because an exit criterion
# said to — nothing in the ritual would have stopped a tag otherwise.
#
# Every test below drives release_check.run() end to end, so each one also pins
# the EXIT CODE: a guard that reports red but exits 0 is not a guard.


def test_ci_all_jobs_green_is_ok(repo_with_ci, monkeypatch):
    monkeypatch.setattr(release_check, "_ci_runs_and_jobs",
                        lambda r, s: (_RUN_OK, [_job("test (ubuntu-latest, 3.13)"),
                                                _job("test (windows-latest, 3.13)"),
                                                _job("fresh-clone")]))
    code, checks = run(repo_with_ci)
    c = _by_label(checks, CI_LABEL)
    assert c.status == "ok", c.detail
    assert "3 job(s)" in c.detail
    assert code == 0


def test_a_skipped_matrix_cell_fails_even_though_the_workflow_says_success(
        repo_with_ci, monkeypatch):
    """THE H-28 case, and the reason this check is per-job.

    GitHub leaves the workflow conclusion `success` when a matrix cell is
    skipped. _RUN_OK carries exactly that `success` — so if this check ever
    consulted the run conclusion it would pass, and the cell that would have
    caught the defect would be invisible at every granularity above the job.
    """
    monkeypatch.setattr(release_check, "_ci_runs_and_jobs",
                        lambda r, s: (_RUN_OK, [_job("test (ubuntu-latest, 3.13)"),
                                                _job("test (windows-latest, 3.13)", "skipped")]))
    code, checks = run(repo_with_ci)
    c = _by_label(checks, CI_LABEL)
    assert c.status == "fail"
    assert "windows-latest" in c.detail and "skipped" in c.detail
    assert "false green" in c.detail          # says WHY, not just what
    assert code == 2


def test_a_failed_job_fails_and_is_named(repo_with_ci, monkeypatch):
    monkeypatch.setattr(release_check, "_ci_runs_and_jobs",
                        lambda r, s: (_RUN_OK, [_job("test (ubuntu-latest, 3.13)"),
                                                _job("test (windows-latest, 3.11)", "failure")]))
    code, checks = run(repo_with_ci)
    c = _by_label(checks, CI_LABEL)
    assert c.status == "fail"
    assert "test (windows-latest, 3.11)" in c.detail and "failure" in c.detail
    assert code == 2


@pytest.mark.parametrize("conclusion",
                         ["cancelled", "timed_out", "action_required", "stale",
                          "startup_failure", "neutral"])
def test_every_non_success_conclusion_fails(repo_with_ci, monkeypatch, conclusion):
    """Green means `success`. Everything else is not-green, per conclusion —
    a guard proven at the granularity it reports (L-25)."""
    monkeypatch.setattr(release_check, "_ci_runs_and_jobs",
                        lambda r, s: (_RUN_OK, [_job("test (macos-latest, 3.12)", conclusion)]))
    code, checks = run(repo_with_ci)
    assert _by_label(checks, CI_LABEL).status == "fail"
    assert code == 2


def test_ci_still_running_fails_rather_than_racing_the_tag(repo_with_ci, monkeypatch):
    running = [{"databaseId": 1, "name": "Tests", "status": "in_progress",
                "conclusion": None}]
    monkeypatch.setattr(release_check, "_ci_runs_and_jobs", lambda r, s: (running, []))
    code, checks = run(repo_with_ci)
    c = _by_label(checks, CI_LABEL)
    assert c.status == "fail"
    assert "still running" in c.detail and "wait" in c.detail
    assert code == 2


def test_no_run_for_this_commit_fails(repo_with_ci, monkeypatch):
    """An unrun commit is not an unverifiable one — the absence of a run is a
    definite fact about the code you are about to tag."""
    monkeypatch.setattr(release_check, "_ci_runs_and_jobs", lambda r, s: ([], []))
    code, checks = run(repo_with_ci)
    c = _by_label(checks, CI_LABEL)
    assert c.status == "fail"
    assert "no workflow run found" in c.detail
    assert code == 2


def test_completed_runs_with_no_jobs_is_unverifiable_not_green(repo_with_ci, monkeypatch):
    monkeypatch.setattr(release_check, "_ci_runs_and_jobs", lambda r, s: (_RUN_OK, []))
    code, checks = run(repo_with_ci)
    c = _by_label(checks, CI_LABEL)
    assert c.status == "unverifiable"
    assert "job granularity" in c.detail
    assert code == 3


def test_unreachable_api_is_unverifiable_never_green(repo_with_ci, monkeypatch):
    """Three-state honesty (D-010): a host that cannot look says so."""
    monkeypatch.setattr(release_check, "_ci_runs_and_jobs", lambda r, s: None)
    code, checks = run(repo_with_ci)
    c = _by_label(checks, CI_LABEL)
    assert c.status == "unverifiable"
    assert "manually" in c.detail
    assert code == 3


def test_a_repo_with_no_workflows_skips(staged_repo):
    """Not every repo has CI; absence is not a failure."""
    code, checks = run(staged_repo)
    c = _by_label(checks, CI_LABEL)
    assert c.status == "skip"
    assert code == 0


def test_a_run_that_cannot_be_opened_is_not_evidence_of_green(monkeypatch, tmp_path):
    """The partial-read trap: `run list` succeeds, `run view` fails. Returning
    the runs we did read would silently certify a matrix we never enumerated."""
    calls = []

    def fake_gh(root, args):
        calls.append(args[1])
        return _RUN_OK if args[1] == "list" else None      # view fails

    monkeypatch.setattr(release_check, "_gh_json", fake_gh)
    assert release_check._ci_runs_and_jobs(tmp_path, "deadbeef") is None
    assert calls == ["list", "view"]


def test_the_check_reads_jobs_not_the_workflow_conclusion(monkeypatch, tmp_path):
    """Structural pin: the run's own `conclusion` must never be consulted.

    A run marked `failure` whose every JOB succeeded still reads green here —
    which is not a judgement about that being desirable, but proof that the
    verdict is computed from the job set alone. The inverse (run `success`,
    job skipped) is the case that actually bites, and is pinned above.
    """
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    runs = [{"databaseId": 1, "name": "Tests", "status": "completed",
             "conclusion": "failure"}]
    monkeypatch.setattr(release_check, "_ci_runs_and_jobs",
                        lambda r, s: (runs, [_job("test (ubuntu-latest, 3.13)")]))
    assert release_check._ci_check(tmp_path, "deadbeef").status == "ok"
