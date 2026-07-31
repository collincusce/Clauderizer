"""A repo with no gameplan can still record a lesson (H-35).

Found while onboarding a 614-commit production repo: its SECURITY.md held a
textbook lesson and cz_add_lesson refused it with "unknown gameplan None".
Onboarding is precisely the moment a project has the most earned experience and
the least in-flight work, so the category was unreachable exactly when it
mattered. cz_add_decision already accepted scope="project" without a gameplan;
this closes that asymmetry.
"""

from __future__ import annotations

from clauderizer import mutations, paths as _paths
from clauderizer.config import Config


def _repo(tmp_path):
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / ".clauderizer").mkdir()
    p = _paths.resolve(root)
    p.config_file.write_text(Config.for_size("standard").to_toml(), encoding="utf-8")
    return p


def test_no_gameplan_records_a_project_lesson(tmp_path):
    p = _repo(tmp_path)
    r = mutations.add_lesson(p, gameplan_id="", text="Rotation is not erasure.",
                             category="Security", evidence="SECURITY.md")
    assert r["ok"], r
    assert r["id"] == "L-01" and r["scope"] == "project"
    body = p.doc("LESSONS").read_text(encoding="utf-8")
    assert "Rotation is not erasure." in body
    assert "evidence: SECURITY.md" in body
    assert "recorded directly" in body, "provenance must say it did not arrive by promotion"


def test_ids_keep_allocating_from_the_project_register(tmp_path):
    p = _repo(tmp_path)
    for _ in range(3):
        mutations.add_lesson(p, gameplan_id="", text="x" * 20, category="Process")
    ids = [ln.split("**")[1].rstrip(".") for ln in
           p.doc("LESSONS").read_text(encoding="utf-8").splitlines()
           if ln.startswith("**L-")]
    assert ids == ["L-01", "L-02", "L-03"], ids


def test_explicit_project_scope_works_even_with_a_gameplan(tmp_path):
    """scope='project' is an explicit choice, not only a no-gameplan fallback."""
    p = _repo(tmp_path)
    r = mutations.create_gameplan(p, "some work")
    gid = r["gameplan_id"]
    out = mutations.add_lesson(p, gameplan_id=gid, text="Enduring rule." * 3,
                               category="Process", scope="project")
    assert out["ok"] and out["scope"] == "project"
    assert "Enduring rule." in p.doc("LESSONS").read_text(encoding="utf-8")


def test_the_gameplan_scoped_default_is_unchanged(tmp_path):
    """The existing loop must not shift: with a gameplan and no scope, the
    lesson is gameplan-scoped and promotion still governs the project register."""
    p = _repo(tmp_path)
    gid = mutations.create_gameplan(p, "some work")["gameplan_id"]
    out = mutations.add_lesson(p, gameplan_id=gid, text="Local lesson body here.",
                               category="Process")
    assert out["ok"]
    assert out.get("scope") != "project"
    assert "number" in out or "n" in out or out.get("id") is None, out
    idx = (p.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    assert "Local lesson body here." in idx
    lessons = p.doc("LESSONS")
    assert not lessons.exists() or "Local lesson body here." not in lessons.read_text(
        encoding="utf-8"), "a gameplan lesson must not leak into the project register"
