"""cz_onboard must surface the project's real docs (H-34).

The defect this pins was measured on a 614-commit production repo: onboard
reported ONE candidate against 20 real documents, silently, reading as success.
The cause was ownership inferred from a FILENAME — any name matching a shipped
template was dropped as an engine scaffold, which is exactly the set
(ARCHITECTURE, VISION, REQUIREMENTS, SECURITY...) that ownership.PROJECT_DOCS
declares the project's and that onboarding exists to find.
"""

from __future__ import annotations

from clauderizer import assets, onboard, ownership, paths as _paths


def _repo(tmp_path, docs_rel="docs"):
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / docs_rel).mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text("# readme\n\nreal\n", encoding="utf-8")
    return root, _paths.resolve(root, docs_rel, docs_rel + "/gameplans")


def test_an_authored_doc_at_an_engine_name_is_offered(tmp_path):
    """The headline case: the project wrote 800 lines into ARCHITECTURE.md."""
    root, p = _repo(tmp_path)
    (root / "docs" / "ARCHITECTURE.md").write_text(
        "# Architecture\n\n" + "\n".join(f"Real design paragraph {i}." for i in range(40)),
        encoding="utf-8")
    got = {c["path"] for c in onboard.spec_candidates(p)}
    assert "docs/ARCHITECTURE.md" in got, (
        "a project's authored ARCHITECTURE.md must be offered for onboarding — "
        f"got {sorted(got)}")


def test_an_untouched_scaffold_at_the_same_name_is_not_offered(tmp_path):
    """The other half: name-matching alone must not decide, but content must."""
    root, p = _repo(tmp_path)
    tmpl = assets.doc_template("ARCHITECTURE")
    assert tmpl, "precondition: ARCHITECTURE ships a template"
    (root / "docs" / "ARCHITECTURE.md").write_text(tmpl, encoding="utf-8")
    got = {c["path"] for c in onboard.spec_candidates(p)}
    assert "docs/ARCHITECTURE.md" not in got, (
        "an untouched scaffold is not project knowledge and must stay out")


def test_every_project_owned_name_can_be_offered_when_authored(tmp_path):
    """No PROJECT_DOCS name may be structurally excluded — the ten that were."""
    root, p = _repo(tmp_path)
    for name in sorted(ownership.PROJECT_DOCS):
        (root / "docs" / f"{name}.md").write_text(
            f"# {name}\n\n" + "\n".join(f"Authored line {i}." for i in range(30)),
            encoding="utf-8")
    got = {c["path"] for c in onboard.spec_candidates(p)}
    missing = [n for n in sorted(ownership.PROJECT_DOCS)
               if f"docs/{n}.md" not in got]
    assert not missing, f"project-owned docs still hidden from onboarding: {missing}"


def test_a_custom_docs_root_does_not_hide_the_projects_docs(tmp_path):
    """The attago shape: [paths] docs moved out of the way so the engine cannot
    collide with the project's documentation. The project's docs/ must still be
    scanned, or the engine's own tidiness blinds the onboarding tool."""
    root, p = _repo(tmp_path, docs_rel="docs/clauderizer")
    (root / "docs" / "REQUIREMENTS.md").write_text(
        "# Requirements\n\n" + "\n".join(f"Requirement {i}." for i in range(30)),
        encoding="utf-8")
    (root / "docs" / "clauderizer" / "DECISIONS.md").write_text(
        "# Decisions\n", encoding="utf-8")
    got = {c["path"] for c in onboard.spec_candidates(p)}
    assert "docs/REQUIREMENTS.md" in got, (
        f"a custom engine docs root must not hide docs/ — got {sorted(got)}")


def test_engine_owned_dirs_stay_excluded(tmp_path):
    """Gameplans, features and subsystems are the engine's, not candidates."""
    root, p = _repo(tmp_path)
    for d in ("gameplans", "features", "subsystems"):
        (root / "docs" / d).mkdir(parents=True, exist_ok=True)
        (root / "docs" / d / "thing.md").write_text(
            "# thing\n\n" + "content\n" * 20, encoding="utf-8")
    got = {c["path"] for c in onboard.spec_candidates(p)}
    assert not [g for g in got if "/gameplans/" in g or "/features/" in g
                or "/subsystems/" in g], sorted(got)


def test_no_duplicates_when_roots_overlap(tmp_path):
    """Default layout scans docs/ once, not twice."""
    root, p = _repo(tmp_path)
    (root / "docs" / "SCORING.md").write_text("# Scoring\n\n" + "x\n" * 20,
                                              encoding="utf-8")
    got = [c["path"] for c in onboard.spec_candidates(p)]
    assert len(got) == len(set(got)), got
