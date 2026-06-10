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
    # offline seams: both remote registries report unclaimed
    monkeypatch.setattr(release_check, "_pypi_claimed", lambda n, v: False)
    monkeypatch.setattr(release_check, "_gh_release_exists", lambda r, t: False)
    return repo


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
    assert c.status == "fail" and "H-07" in c.detail


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
