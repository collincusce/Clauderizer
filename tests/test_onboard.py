"""Onboarding an existing project (D-044): detector + cz_onboard.

The engine detects spec candidates and unseeded scaffold docs and prompts; the
agent reads and seeds. Everything here is read-only.
"""

from clauderizer import assets, onboard
from clauderizer import paths as P

GID = "2026-05-01-bootstrap"


def _paths(repo):
    return P.resolve(repo)


# --- spec candidates ----------------------------------------------------------


def test_candidates_include_root_and_docs_but_never_owned(temp_repo):
    paths = _paths(temp_repo)
    (temp_repo / "README.md").write_text("# Proj\n\nA real readme.\n", encoding="utf-8")
    (temp_repo / "DESIGN.md").write_text("design notes\n", encoding="utf-8")
    (paths.docs / "studio.md").write_text("how the studio works\n", encoding="utf-8")
    (paths.docs / "VISION.md").write_text("# Vision\n\nreal vision\n", encoding="utf-8")
    got = {c["path"] for c in onboard.spec_candidates(paths)}
    assert "README.md" in got and "DESIGN.md" in got
    assert "docs/studio.md" in got
    assert "docs/VISION.md" not in got  # engine-owned name
    assert not any(p.startswith("docs/gameplans/") for p in got)  # owned dir
    assert all(set(c) == {"path", "bytes"} for c in onboard.spec_candidates(paths))


def test_candidates_skip_empty_and_oversized_and_cap(temp_repo):
    paths = _paths(temp_repo)
    (temp_repo / "README.md").write_text("", encoding="utf-8")  # empty -> skipped
    (temp_repo / "SPEC.md").write_bytes(b"x" * (onboard.MAX_CANDIDATE_BYTES + 1))
    for i in range(onboard.CANDIDATE_CAP + 10):
        (paths.docs / f"note-{i:02d}.md").write_text(f"note {i}\n", encoding="utf-8")
    got = onboard.spec_candidates(paths)
    assert len(got) == onboard.CANDIDATE_CAP
    names = {c["path"] for c in got}
    assert "README.md" not in names and "SPEC.md" not in names


# --- unseeded docs -------------------------------------------------------------


def test_unseeded_detects_scaffold_and_clears_on_prose(temp_repo):
    paths = _paths(temp_repo)
    vision = paths.doc("VISION")
    vision.parent.mkdir(parents=True, exist_ok=True)
    vision.write_text(assets.doc_template("VISION"), encoding="utf-8")
    assert "docs/VISION.md" in onboard.unseeded_docs(paths)
    vision.write_text("# Vision\n\n## What & Why\n\nA real product vision.\n",
                      encoding="utf-8")
    assert "docs/VISION.md" not in onboard.unseeded_docs(paths)


def test_unseeded_is_robust_to_template_wording_drift(temp_repo):
    paths = _paths(temp_repo)
    vision = paths.doc("VISION")
    vision.parent.mkdir(parents=True, exist_ok=True)
    # An OLDER template's scaffold: same structure (headings + placeholders),
    # different placeholder wording than today's template ships.
    vision.write_text("# Vision\n\n## What & Why\n\n_(fill this in later)_\n",
                      encoding="utf-8")
    assert "docs/VISION.md" in onboard.unseeded_docs(paths)


def test_append_only_logs_are_never_onboarding_targets(temp_repo):
    paths = _paths(temp_repo)
    assert all(not d.endswith(("DECISIONS.md", "INVARIANTS.md", "LESSONS.md",
                               "HARDENING.md"))
               for d in onboard.unseeded_docs(paths))


# --- the bundle -----------------------------------------------------------------


def test_report_shape_and_prompt(temp_repo):
    paths = _paths(temp_repo)
    vision = paths.doc("VISION")
    vision.parent.mkdir(parents=True, exist_ok=True)
    vision.write_text(assets.doc_template("VISION"), encoding="utf-8")
    (temp_repo / "README.md").write_text("# Proj\n\nreal spec content\n",
                                         encoding="utf-8")
    rep = onboard.report(paths)
    assert rep["ok"]
    assert "docs/VISION.md" in rep["unseeded"]
    assert any(c["path"] == "README.md" for c in rep["candidates"])
    for needle in ("cz_upsert_entity", "cz_add_decision", "cz_add_invariant",
                   "never seeds"):
        assert needle in rep["prompt"]
