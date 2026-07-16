"""The work/release self-audit gate (D-051): deterministic signals (version
single-sourcing, dirty tree, unresolved cascades/open items) + a judgment
checklist, assembled read-only and advisory (INVARIANT-05). The headline signal
is the exact bug this gate exists for — a version bumped in pyproject but not in
the package __version__ — proven to fire on the defect AND stay quiet on health
(L-25: a guard must be verified in both directions)."""

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import ops
from clauderizer import paths as P
from clauderizer.rituals import audit
from clauderizer.tools_list import TOOL_NAMES


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _fresh(paths):
    gid = M.create_gameplan(paths, "Audit Test", today="2026-07-16")["gameplan_id"]
    config = cfg.Config.load(paths.config_file)
    config.active_gameplan = gid
    return gid, config


def _write_pkg(root, *, pyproject_v, dunder_v=None, changelog_v=None):
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "demo"\nversion = "{pyproject_v}"\n', encoding="utf-8")
    if dunder_v is not None:
        pkg = root / "src" / "demo"
        pkg.mkdir(parents=True, exist_ok=True)
        (pkg / "__init__.py").write_text(f'__version__ = "{dunder_v}"\n', encoding="utf-8")
    if changelog_v is not None:
        (root / "CHANGELOG.md").write_text(
            f"# Changelog\n\n## [{changelog_v}] — 2026-07-16\n\n- stuff\n", encoding="utf-8")


def test_release_signal_fires_on_pyproject_vs_dunder_drift(tmp_path):
    # the exact 1.7.0-vs-1.6.0 bug: pyproject bumped, __version__ left stale
    _write_pkg(tmp_path, pyproject_v="1.7.0", dunder_v="1.6.0")
    sigs = audit._release_signals(tmp_path)
    assert any("version drift" in s and "1.7.0" in s and "1.6.0" in s for s in sigs), sigs


def test_release_signal_flags_changelog_drift(tmp_path):
    _write_pkg(tmp_path, pyproject_v="1.7.0", dunder_v="1.7.0", changelog_v="1.6.0")
    sigs = audit._release_signals(tmp_path)
    assert any("CHANGELOG" in s and "1.6.0" in s for s in sigs), sigs


def test_release_signal_quiet_when_versions_agree(tmp_path):
    # the other direction (L-25): a healthy, single-sourced repo produces NO signal
    _write_pkg(tmp_path, pyproject_v="1.7.0", dunder_v="1.7.0", changelog_v="1.7.0")
    assert audit._release_signals(tmp_path) == []


def test_release_signal_skips_missing_sides(tmp_path):
    # non-Python / changelog-less repos degrade gracefully rather than false-firing
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "1.0.0"\n', encoding="utf-8")
    assert audit._release_signals(tmp_path) == []


def test_audit_shape_checklist_and_advisory_prompt(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid, config = _fresh(paths)
    res = audit.audit(paths, config)
    assert res["ok"] and gid in res["scope"]
    for key in ("release", "git", "graph", "checklist", "finding_count", "prompt"):
        assert key in res, key
    # the judgment checks the mechanical signals can't prove are always surfaced
    checks = {c["check"] for c in res["checklist"]}
    assert "clean-environment verification" in checks
    assert "consumer re-audit" in checks
    # advisory, never blocking (INVARIANT-05)
    assert "advisory" in res["prompt"].lower() and "invariant-05" in res["prompt"].lower()


def test_cz_audit_is_registered_and_readonly():
    assert "cz_audit" in TOOL_NAMES
    assert "cz_audit" in ops.REGISTRY
    assert ops.REGISTRY["cz_audit"].writes is False   # read-only gate


def test_shipped_close_skill_invokes_cz_audit():
    # the ritual reaches ALL installs via the close-gameplan skill (D-051): the
    # SHIPPED skill (source of truth for what init copies) must invoke cz_audit.
    from clauderizer import assets
    skill = assets.SKILLS / "clauderizer-close-gameplan" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert "cz_audit" in text, "close-gameplan skill must invoke the self-audit gate"


def test_procedure_template_documents_self_audit_at_current_version():
    # GAMEPLAN-PROCEDURE ships the close procedure; the self-audit step must be
    # present and the stamped version must equal PROCEDURE_VERSION (single-sourced).
    from clauderizer import PROCEDURE_VERSION, assets
    proc = (assets.TEMPLATES / "GAMEPLAN-PROCEDURE.md").read_text(encoding="utf-8")
    assert "cz_audit" in proc and "self-audit" in proc.lower()
    assert f"**Procedure version**: {PROCEDURE_VERSION}" in proc
