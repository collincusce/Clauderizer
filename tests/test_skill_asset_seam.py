"""Dual-copy skill seam (L-65, A-001 phase 7): src assets == installed renders.

Every shipped skill exists twice: the wheel source under src/clauderizer/skills/
and the installed render under .claude/skills/ (init refreshes render from
source). This repo is clauderized by its own engine, so the two copies must
stay byte-identical and cover the same set — an edit that lands on one side
only is exactly the drift a future `clauderize init` silently clobbers.
Read-only against the real repo (no mutation — L-29).
"""

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src" / "clauderizer" / "skills"
INSTALLED = REPO / ".claude" / "skills"


def _src_names() -> set[str]:
    return {d.name for d in SRC.iterdir() if d.is_dir()}


def _installed_clauderizer_names() -> set[str]:
    # Only clauderizer-owned dirs: users may install foreign skills beside ours
    # and uninstall.py's footprint uses the same prefix rule.
    return {d.name for d in INSTALLED.iterdir()
            if d.is_dir() and d.name.startswith("clauderizer-")}


def test_shipped_and_installed_skill_sets_match():
    """Set equality both directions: nothing ships un-installed, nothing
    clauderizer-owned exists repo-local-only (it would vanish from fresh
    inits and drift from the wheel)."""
    assert _src_names() == _installed_clauderizer_names()


def test_fleet_skill_is_shipped():
    """A-001's productization pin: clauderizer-fleet is a wheel asset, not a
    repo-local file."""
    assert "clauderizer-fleet" in _src_names()


def test_every_shipped_skill_file_byte_identical():
    """init copies each top-level file of each skill dir; the render must be
    byte-identical to the source in both directions (same contract as
    scaffold.init step 9)."""
    for d in sorted(SRC.iterdir()):
        if not d.is_dir():
            continue
        for src_file in sorted(d.iterdir()):
            if not src_file.is_file():
                continue
            dest = INSTALLED / d.name / src_file.name
            assert dest.exists(), f"{d.name}/{src_file.name} not installed"
            assert dest.read_bytes() == src_file.read_bytes(), (
                f"{d.name}/{src_file.name} drifted between src and installed "
                f"copies — edit the source, re-run init (or copy), commit both")
    for d in sorted(INSTALLED.iterdir()):
        if not d.is_dir() or not d.name.startswith("clauderizer-"):
            continue
        for inst_file in sorted(d.iterdir()):
            if not inst_file.is_file():
                continue
            assert (SRC / d.name / inst_file.name).exists(), (
                f"{d.name}/{inst_file.name} exists installed-only — a future "
                f"init will not ship it; add the src copy")


def test_glossary_referenced_from_doc_listings():
    """L-65 sweep pin (phase 7): the canonical vocabulary doc exists and the
    non-single-sourced doc listings reach it."""
    assert (REPO / "docs" / "GLOSSARY.md").exists()
    assert "GLOSSARY.md" in (REPO / "README.md").read_text(encoding="utf-8")
    assert "GLOSSARY.md" in (REPO / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
