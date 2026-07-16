"""Phase 2 of engine-structural-robustness: blessed writes for the last
hand-edit surfaces (Outputs Registry, Per-Phase Completion Summaries, tracker
header lines — gameplan D7), doctor engine-identity helpers (D9), and the
memory gauge's close-out note (H-03).
"""

from pathlib import Path

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.cli import _engine_repo_version, _metadata_version
from clauderizer.markdown import sections
from clauderizer.rituals import status_bundle


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _fresh(paths, name="Surface Plan"):
    return M.create_gameplan(paths, name, today="2026-06-08")["gameplan_id"]


# --- Outputs Registry (task 2.1) ----------------------------------------------


def test_add_output_replaces_placeholder_and_upserts(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    status_doc = paths.gameplan_dir(gid) / "PHASE-STATUS.md"

    r1 = M.add_output(paths, gameplan_id=gid, phase="0", key="BASELINE", value="122")
    assert r1["ok"] and r1["action"] == "recorded"
    body = sections.get_section(status_doc.read_text(encoding="utf-8"), "Outputs Registry")
    assert "### Phase 0 Outputs" in body
    assert "BASELINE: 122" in body
    assert "_(" not in body  # placeholder gone

    r2 = M.add_output(paths, gameplan_id=gid, phase="0", key="BASELINE", value="127")
    assert r2["action"] == "updated"
    body = sections.get_section(status_doc.read_text(encoding="utf-8"), "Outputs Registry")
    assert "BASELINE: 127" in body and "BASELINE: 122" not in body

    M.add_output(paths, gameplan_id=gid, phase="0", key="TOOLS", value="24")
    M.add_output(paths, gameplan_id=gid, phase="1", key="REPORT", value="x-01.md")
    body = sections.get_section(status_doc.read_text(encoding="utf-8"), "Outputs Registry")
    assert "TOOLS: 24" in body
    assert "### Phase 1 Outputs" in body
    assert body.index("### Phase 0 Outputs") < body.index("### Phase 1 Outputs")


# --- Per-Phase Completion Summaries (task 2.2) ----------------------------------


def test_add_phase_summary_replaces_placeholder_then_its_own_block(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    idx = paths.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md"

    r1 = M.add_phase_summary(paths, gameplan_id=gid, phase="0",
                             text="Shipped the thing.", today="2026-06-08")
    assert r1["ok"] and not r1["replaced"]
    body = sections.get_section(idx.read_text(encoding="utf-8"),
                                "Per-Phase Completion Summaries")
    assert "### Phase 0 — completed 2026-06-08" in body
    assert "_(None yet.)_" not in body

    r2 = M.add_phase_summary(paths, gameplan_id=gid, phase="0",
                             text="Shipped the thing, plus a fix.", today="2026-06-08")
    assert r2["replaced"]
    body = sections.get_section(idx.read_text(encoding="utf-8"),
                                "Per-Phase Completion Summaries")
    assert body.count("### Phase 0") == 1
    assert "plus a fix" in body

    M.add_phase_summary(paths, gameplan_id=gid, phase="1", text="Second.",
                        today="2026-06-08")
    body = sections.get_section(idx.read_text(encoding="utf-8"),
                                "Per-Phase Completion Summaries")
    assert "### Phase 1" in body and body.count("### Phase 0") == 1


# --- tracker header write-backs (task 2.3, D7) ----------------------------------


def test_transition_phase_writes_headers_back(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    gdir = paths.gameplan_dir(gid)

    M.transition_phase(paths, gameplan_id=gid, phase_n="0",
                       to_status="in_progress", today="2026-06-08")
    idx = (gdir / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    assert "> Status: Phase 0 of 1 in progress" in idx
    assert "> Last updated: 2026-06-08" in idx
    gp = (gdir / "GAMEPLAN.md").read_text(encoding="utf-8")
    assert "> Status: Executing" in gp

    M.transition_phase(paths, gameplan_id=gid, phase_n="0",
                       to_status="complete", today="2026-06-08")
    idx = (gdir / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    assert "> Status: All 1 phases complete" in idx
    gp = (gdir / "GAMEPLAN.md").read_text(encoding="utf-8")
    assert "> Status: Complete" in gp
    status_doc = (gdir / "PHASE-STATUS.md").read_text(encoding="utf-8")
    assert "> Last updated: 2026-06-08" in status_doc


def test_add_phase_refreshes_headers(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    M.add_phase(paths, gameplan_id=gid, name="Second", goal="g")
    idx = (paths.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    assert "> Status: Phase 0 ready" in idx  # still planning; ready phase named


# --- doctor identity helpers (task 2.4, D9) -------------------------------------


def test_engine_repo_version_only_fires_on_the_engine_repo(tmp_path):
    assert _engine_repo_version(tmp_path) is None  # no pyproject
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "someapp"\nversion = "9.9.9"\n', encoding="utf-8")
    assert _engine_repo_version(tmp_path) is None  # not the engine
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "clauderizer"\nversion = "0.6.0"\n', encoding="utf-8")
    assert _engine_repo_version(tmp_path) == "0.6.0"


def test_metadata_version_is_string_or_none():
    v = _metadata_version()
    assert v is None or isinstance(v, str)


def test_version_is_single_sourced_with_pyproject():
    # Release guard (the 1.7.0 near-miss): bumping pyproject.toml without bumping
    # clauderizer.__version__ (hardcoded in __init__.py) makes doctor's own
    # version-consistency check fail on every CLEAN install (dist metadata and
    # repo pyproject both disagree with __version__), while a STALE editable venv
    # — whose metadata still equals the old __version__ — stays green and masks it.
    from clauderizer import __version__
    repo_root = Path(__file__).resolve().parents[1]
    # Install-independent: reads the repo's own pyproject directly, so this catches
    # the drift even from a stale venv (the case the doctor tests missed).
    assert _engine_repo_version(repo_root) == __version__, (
        f"pyproject.toml disagrees with clauderizer.__version__ ({__version__}) — "
        f"bump src/clauderizer/__init__.py to match pyproject.toml"
    )
    # Install-consistency: a fresh/CI install's dist metadata must match too.
    meta = _metadata_version()
    if meta is not None:
        assert meta == __version__, (
            f"packaging metadata {meta} != clauderizer.__version__ {__version__} "
            f"— reinstall the editable package, or bump __init__.py to match pyproject"
        )


# --- memory gauge close-out note (task 2.5, H-03) --------------------------------


def test_gauge_explains_missing_size_when_gameplan_complete(temp_repo):
    paths, config = _ctx(temp_repo)
    gid = _fresh(paths)
    M.transition_phase(paths, gameplan_id=gid, phase_n="0",
                       to_status="complete", today="2026-06-08")
    config.active_gameplan = gid
    bundle = status_bundle.compute(paths, config)
    assert bundle["memory"]["handoff_note"] == "n/a: gameplan complete"
    digest = status_bundle.render_digest(bundle)
    assert "(handoff n/a: gameplan complete)." in digest
