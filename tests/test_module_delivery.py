"""A doc module added to SIZE_MANIFESTS must reach EXISTING repos, not just
fresh inits (L-65 / D-042 tier 1).

The defect these pin was measured on a live 1.13.0 → 2.0.0 upgrade walk: the
refreshed stanza referenced ``docs/ENFORCEMENT.md`` and the shipped fleet skill
referenced ``docs/GLOSSARY.md`` while neither file existed, because
``config.merge_missing`` keeps a repo's existing non-empty ``modules`` list and
``init`` scaffolds from ``config.modules`` alone. ``doctor`` printed
"✓ corpus modernized" over it.
"""

from __future__ import annotations

from clauderizer import assets, modernize
from clauderizer.config import SIZE_MANIFESTS, Config


def _legacy_repo(tmp_path, monkeypatch, modules):
    """A clauderized repo whose config carries an OLDER module list."""
    from clauderizer import paths as _paths

    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / ".clauderizer").mkdir()
    p = _paths.resolve(root)
    cfg = Config.for_size("standard")
    cfg.modules = list(modules)
    cfg.procedure_version = "1.8.0"
    p.config_file.write_text(cfg.to_toml(), encoding="utf-8")
    for m in modules:
        tmpl = assets.doc_template(m)
        if tmpl is not None:
            p.doc(m).write_text(tmpl, encoding="utf-8")
    return p, cfg


def test_manifest_modules_missing_from_an_existing_corpus_are_reported(tmp_path, monkeypatch):
    """The mechanical tier names the gap instead of silently leaving it."""
    full = list(SIZE_MANIFESTS["standard"]["modules"])
    trimmed = [m for m in full if m not in ("GLOSSARY", "ENFORCEMENT")]
    p, cfg = _legacy_repo(tmp_path, monkeypatch, trimmed)

    rep = modernize.report(p, cfg)
    actions = {i["action"] for i in rep["mechanical"]}
    assert "ensure_modules_current" in actions, (
        "a repo missing manifest doc modules must surface a mechanical action")
    detail = next(i["detail"] for i in rep["mechanical"]
                  if i["action"] == "ensure_modules_current")
    assert "GLOSSARY" in detail and "ENFORCEMENT" in detail


def test_apply_delivers_the_modules_and_records_them_in_config(tmp_path, monkeypatch):
    """apply() scaffolds the docs AND updates the module list, so the next
    init/upgrade is a no-op rather than re-proposing forever."""
    full = list(SIZE_MANIFESTS["standard"]["modules"])
    trimmed = [m for m in full if m not in ("GLOSSARY", "ENFORCEMENT")]
    p, cfg = _legacy_repo(tmp_path, monkeypatch, trimmed)

    assert not p.doc("GLOSSARY").exists()
    assert not p.doc("ENFORCEMENT").exists()

    res = modernize.apply(p, cfg)

    assert res["ok"] is True
    assert "ensure_modules_current" in res["applied"]
    assert p.doc("GLOSSARY").exists(), "the module's doc must land on disk"
    assert p.doc("ENFORCEMENT").exists()
    # persisted, not just in-memory
    reread = Config.load(p.config_file)
    assert "GLOSSARY" in reread.modules and "ENFORCEMENT" in reread.modules
    # idempotent: a second pass has nothing left to do
    assert not modernize._missing_manifest_modules(reread)
    rep2 = modernize.report(p, reread)
    assert "ensure_modules_current" not in {i["action"] for i in rep2["mechanical"]}


def test_apply_never_clobbers_an_existing_doc(tmp_path, monkeypatch):
    """INVARIANT-03: a user's own GLOSSARY survives the delivery untouched."""
    full = list(SIZE_MANIFESTS["standard"]["modules"])
    trimmed = [m for m in full if m not in ("GLOSSARY", "ENFORCEMENT")]
    p, cfg = _legacy_repo(tmp_path, monkeypatch, trimmed)
    mine = "# My glossary\n\nHand-written, do not touch.\n"
    p.doc("GLOSSARY").write_text(mine, encoding="utf-8")

    modernize.apply(p, cfg)

    assert p.doc("GLOSSARY").read_text(encoding="utf-8") == mine
    assert p.doc("ENFORCEMENT").exists()
    assert "GLOSSARY" in Config.load(p.config_file).modules


def test_a_current_corpus_reports_no_module_action(tmp_path, monkeypatch):
    """INVARIANT-08 drop-nothing: a repo already carrying the manifest is silent."""
    full = list(SIZE_MANIFESTS["standard"]["modules"])
    p, cfg = _legacy_repo(tmp_path, monkeypatch, full)
    rep = modernize.report(p, cfg)
    assert "ensure_modules_current" not in {i["action"] for i in rep["mechanical"]}


def test_every_size_manifest_module_has_a_shipped_template():
    """The ratchet that makes the whole delivery meaningful: a module named in a
    manifest with no template would scaffold nothing and dangle forever."""
    for size, manifest in SIZE_MANIFESTS.items():
        for m in manifest["modules"]:
            assert assets.doc_template(m) is not None, (
                f"size '{size}' manifest names module {m} with no "
                f"templates/docs/{m}.md — it would never be scaffolded")


def test_engine_referenced_docs_have_a_detector(tmp_path, monkeypatch):
    """L-65's detector: the pointer class is machine-visible, not discipline."""
    full = list(SIZE_MANIFESTS["standard"]["modules"])
    trimmed = [m for m in full if m not in ("GLOSSARY", "ENFORCEMENT")]
    p, cfg = _legacy_repo(tmp_path, monkeypatch, trimmed)

    dangling = modernize.dangling_doc_pointers(p, cfg)
    missing = {doc for _ref, doc in dangling}
    assert "docs/ENFORCEMENT.md" in missing, (
        "the shipped stanza references docs/ENFORCEMENT.md — a repo whose "
        "manifest promises it and does not have it must be detected")
    assert "docs/GLOSSARY.md" in missing, (
        "a shipped skill references docs/GLOSSARY.md")


def test_detector_is_silent_once_the_docs_are_there(tmp_path, monkeypatch):
    full = list(SIZE_MANIFESTS["standard"]["modules"])
    p, cfg = _legacy_repo(tmp_path, monkeypatch, full)
    assert modernize.dangling_doc_pointers(p, cfg) == []


def test_detector_never_flags_an_on_demand_doc(tmp_path, monkeypatch):
    """docs/LESSONS.md is created by cz_add_lesson, not scaffolded — a repo with
    no lessons yet is correct, not broken. The shipped skills reference it."""
    assert "LESSONS" in modernize.engine_doc_references(), (
        "precondition: a shipped skill references docs/LESSONS.md")
    full = list(SIZE_MANIFESTS["standard"]["modules"])
    p, cfg = _legacy_repo(tmp_path, monkeypatch, full)
    assert not p.doc("LESSONS").exists()
    assert modernize.dangling_doc_pointers(p, cfg) == []


def test_detector_ignores_the_users_own_prose(tmp_path, monkeypatch):
    """Only ENGINE-owned wiring is a source — a reference the user wrote in
    their own doc is never second-guessed."""
    full = list(SIZE_MANIFESTS["standard"]["modules"])
    p, cfg = _legacy_repo(tmp_path, monkeypatch, full)
    p.doc("VISION").write_text(
        "See docs/TOTALLY_INVENTED.md for details.\n", encoding="utf-8")
    assert modernize.dangling_doc_pointers(p, cfg) == []


def test_every_engine_referenced_doc_is_deliverable():
    """The CI-time ratchet — this is the check that would have caught 2.0's own
    defect BEFORE release.

    Any ``docs/<NAME>.md`` the shipped stanza or a shipped skill references must
    be something a repo can actually end up with: a doc module in some size
    manifest (scaffolded at init and delivered to existing repos by
    ``ensure_modules_current``), or a declared on-demand doc. A reference to
    anything else is a pointer no repo will ever satisfy.
    """
    manifest_union = set()
    for m in SIZE_MANIFESTS.values():
        manifest_union |= set(m["modules"])
    deliverable = manifest_union | modernize.ON_DEMAND_DOCS
    refs = modernize.engine_doc_references()
    undeliverable = {name: labels for name, labels in refs.items()
                     if name not in deliverable}
    assert not undeliverable, (
        "engine wiring references doc(s) no repo can obtain: "
        + "; ".join(f"docs/{n}.md (from {', '.join(ls)})"
                    for n, ls in sorted(undeliverable.items()))
        + " — add the module to SIZE_MANIFESTS or to ON_DEMAND_DOCS")


def test_this_repos_own_wiring_has_no_dangling_pointers():
    """The self-check: whatever the engine ships must resolve in this repo."""
    from pathlib import Path

    from clauderizer import paths as _paths

    root = Path(__file__).resolve().parent.parent
    cfg = Config.load(root / ".clauderizer" / "config.toml")
    assert modernize.dangling_doc_pointers(_paths.resolve(root), cfg) == []
