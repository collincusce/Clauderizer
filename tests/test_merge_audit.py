"""Merge-integrity audit (2.0 P4) — the whole safety envelope.

Pins the vetting conditions: git evidence only (no ledger, no persisted
state — findings self-clear from history), O(1) subprocess cost per compute,
the squash blind spot (a squash commit is INVISIBLE, asserted, and the shared
wording says so to the user), quoted-marker/fenced-block exemption, and
byte-identical healthy digests. All fixtures are REAL git repos built with
real merges — the audit's ground truth is git, so the tests' is too.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from clauderizer import config as cfg
from clauderizer import paths as P
from clauderizer.rituals import merge_audit


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                       text=True, check=True)
    return r.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "r"
    (repo / "docs").mkdir(parents=True)
    _git(repo.parent, "init", "-q", "-b", "main", str(repo))
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / "docs" / "A.md").write_text("a0\n", encoding="utf-8")
    (repo / "docs" / "B.md").write_text("b0\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    return repo


def _commit_on_branch(repo: Path, branch: str, path: str, text: str) -> str:
    _git(repo, "checkout", "-qb", branch, "main")
    (repo / path).write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", f"{branch}: {path}")
    return _git(repo, "rev-parse", "HEAD")


def _merge_keeping(repo: Path, keep: str, other: str) -> str:
    """A TRUE merge commit whose tree is exactly `keep`'s — the second parent's
    change is silently discarded (the lost-update construction, built with
    commit-tree so it is deterministic)."""
    tree = _git(repo, "rev-parse", f"{keep}^{{tree}}")
    merge = _git(repo, "commit-tree", tree, "-p", keep, "-p", other,
                 "-m", "merge")
    _git(repo, "checkout", "-q", "main")
    _git(repo, "reset", "-q", "--hard", merge)
    return merge


def test_quiet_when_no_merges_and_quiet_off_git(tmp_path):
    repo = _repo(tmp_path)
    assert merge_audit.compute(P.resolve(repo)) is None      # linear history
    bare = tmp_path / "no-git"
    (bare / "docs").mkdir(parents=True)
    assert merge_audit.compute(P.resolve(bare)) is None      # not a repo


def test_lost_update_on_a_true_merge_is_found_and_self_clears(tmp_path):
    repo = _repo(tmp_path)
    a = _commit_on_branch(repo, "side-a", "docs/A.md", "a1\n")
    b = _commit_on_branch(repo, "side-b", "docs/A.md", "a2\n")
    _merge_keeping(repo, a, b)                # b's change to A.md discarded
    found = merge_audit.compute(P.resolve(repo))
    assert found is not None
    kinds = {f["kind"] for f in found["findings"]}
    assert kinds == {"lost_update"}
    assert any(f["path"] == "docs/A.md" for f in found["findings"])
    assert "silently discarded" in found["findings"][0]["detail"]
    # no persisted state anywhere: the finding derives from history alone, so
    # a follow-up commit restoring the change makes it self-clear
    (repo / "docs" / "A.md").write_text("a1+a2 reconciled\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "reconcile")
    assert merge_audit.compute(P.resolve(repo)) is not None  # merge still latest
    # ... the finding clears only when history's latest docs merge is clean:
    c = _commit_on_branch(repo, "side-c", "docs/A.md", "a3\n")
    d = _commit_on_branch(repo, "side-d", "docs/B.md", "b1\n")
    _git(repo, "checkout", "-q", "main")
    _git(repo, "reset", "-q", "--hard", c)
    _git(repo, "merge", "-q", d)              # clean true merge, disjoint files
    assert merge_audit.compute(P.resolve(repo)) is None


def test_clean_merge_of_disjoint_docs_changes_is_quiet(tmp_path):
    repo = _repo(tmp_path)
    a = _commit_on_branch(repo, "side-a", "docs/A.md", "a1\n")
    b = _commit_on_branch(repo, "side-b", "docs/B.md", "b1\n")
    _git(repo, "checkout", "-q", "main")
    _git(repo, "reset", "-q", "--hard", a)
    _git(repo, "merge", "-q", b)
    assert merge_audit.compute(P.resolve(repo)) is None


def test_squash_is_invisible_by_construction(tmp_path):
    """The blind spot is a stated property, not a bug: a squash has one parent,
    so even a squash that flattened away a docs change raises nothing."""
    repo = _repo(tmp_path)
    _commit_on_branch(repo, "side-b", "docs/A.md", "a2\n")
    _git(repo, "checkout", "-q", "main")
    _git(repo, "merge", "-q", "--squash", "side-b")
    (repo / "docs" / "A.md").write_text("a0\n", encoding="utf-8")  # flatten away
    (repo / "docs" / "C.md").write_text("c0\n", encoding="utf-8")  # keep non-empty
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "squash that dropped the change")
    assert merge_audit.compute(P.resolve(repo)) is None
    # and the user-facing wording admits it
    assert "squash merges are invisible" in merge_audit.describe(
        [{"kind": "lost_update", "path": "docs/A.md", "merge": "x"}])


def test_committed_conflict_markers_found_but_fenced_quotes_exempt(tmp_path):
    repo = _repo(tmp_path)
    triad = "<<<<<<< ours\na1\n=======\na2\n>>>>>>> theirs\n"
    a = _commit_on_branch(repo, "side-a", "docs/A.md", triad)
    b = _commit_on_branch(repo, "side-b", "docs/B.md",
                          "quoting markers:\n```\n" + triad + "```\n")
    _merge_keeping(repo, a, b)
    found = merge_audit.compute(P.resolve(repo))
    assert found is not None
    marker_paths = {f["path"] for f in found["findings"]
                    if f["kind"] == "conflict_markers"}
    assert marker_paths == {"docs/A.md"}       # fenced quote in B.md is exempt
    assert not merge_audit._unfenced_triad("```\n" + triad + "```\n")
    assert merge_audit._unfenced_triad(triad)
    # a lone ======= banner is never a marker
    assert not merge_audit._unfenced_triad("title\n=======\nbody\n")


def test_subprocess_count_is_constant(tmp_path, monkeypatch):
    """O(1) per compute — pinned. The lost-update repo with many docs files
    must not grow the call count: blob resolution is one batched ls-tree per
    commit, never per-file."""
    repo = _repo(tmp_path)
    for i in range(25):
        (repo / "docs" / f"F{i}.md").write_text(f"f{i}\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "many docs")
    a = _commit_on_branch(repo, "side-a", "docs/A.md", "a1\n")
    b = _commit_on_branch(repo, "side-b", "docs/A.md", "a2\n")
    _merge_keeping(repo, a, b)
    calls = []
    real = merge_audit._git
    monkeypatch.setattr(merge_audit, "_git",
                        lambda root, *args: (calls.append(args), real(root, *args))[1])
    assert merge_audit.compute(P.resolve(repo)) is not None
    assert len(calls) <= 8, [c[0] for c in calls]


def test_digest_and_preflight_surface_only_when_findings_exist(tmp_path):
    """Conditional emission on both remaining surfaces (INVARIANT-07/08): a
    healthy history renders byte-identically; a bad merge speaks with the ONE
    shared wording on digest, preflight and cz_audit alike."""
    import shutil

    from clauderizer.rituals import audit as audit_mod
    from clauderizer.rituals import status_bundle as S

    src = Path(__file__).parent / "fixtures" / "sample_repo"
    repo = tmp_path / "repo"
    shutil.copytree(src, repo)
    paths = P.resolve(repo)
    config = cfg.Config.load(paths.config_file)
    _git(repo.parent, "init", "-q", "-b", "main", str(repo))
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    healthy = S.render_digest(S.compute(paths, config))
    assert "Merge integrity" not in healthy
    a = _commit_on_branch(repo, "side-a", "docs/DECISIONS.md",
                          (repo / "docs" / "DECISIONS.md").read_text(encoding="utf-8") + "a\n")
    b = _commit_on_branch(repo, "side-b", "docs/DECISIONS.md",
                          (repo / "docs" / "DECISIONS.md").read_text(encoding="utf-8") + "b\n")
    _merge_keeping(repo, a, b)
    bundle = S.compute(paths, config)
    assert bundle.get("merge_audit")
    wording = merge_audit.describe(bundle["merge_audit"]["findings"])
    assert f"⚠ Merge integrity: {wording}" in S.render_digest(bundle)
    assert "squash merges are invisible" in wording
    config.preflight_checks = ["deps_spotcheck"]
    from clauderizer.profiles.detect import Profile
    from clauderizer.rituals import preflight as preflight_mod
    profile = Profile(name="generic", commands={}, baseline_test_regex="")
    res = preflight_mod.run(paths, config, profile,
                            runner=lambda c, w: (0, "")).to_dict()
    warn = [c for c in res["checks"] if c["name"] == "merge_integrity"]
    assert warn and warn[0]["status"] == "warn" and warn[0]["detail"] == wording
    assert res["passed"] is True               # warn, never fail (D-024 intact)
    got = audit_mod.audit(paths, config)
    assert wording in got["merge_integrity"]
