"""The untangle moves engine memory and never touches the human's docs (D-080)."""

from __future__ import annotations

import subprocess

from clauderizer import assets, ownership, paths as _paths, untangle
from clauderizer.config import Config


def _repo(tmp_path, *, seeded_glossary: str | None = None, git: bool = True):
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / ".clauderizer").mkdir()
    if git:
        for cmd in (["init", "-q"], ["config", "user.email", "t@t.t"],
                    ["config", "user.name", "t"]):
            subprocess.run(["git", "-C", str(root), *cmd], check=True,
                           capture_output=True)
    p = _paths.resolve(root)
    cfg = Config.for_size("standard")
    p.config_file.write_text(cfg.to_toml(), encoding="utf-8")
    # engine scaffolds at the legacy paths
    for name in ("DECISIONS", "INVARIANTS", "HARDENING", "ENFORCEMENT", "GLOSSARY"):
        (root / "docs" / f"{name}.md").write_text(
            assets.doc_template(name) or f"# {name}\n", encoding="utf-8")
    # a seeded register: real engine entries
    (root / "docs" / "DECISIONS.md").write_text(
        "# Decisions\n\n### D-001 — first\n\nbody\n\n### D-002 — second\n\nbody\n",
        encoding="utf-8")
    # the project's own doc at a name the engine does not use
    (root / "docs" / "FILM-PROCEDURE.md").write_text(
        "# Film procedure\n\nOurs.\n", encoding="utf-8")
    if seeded_glossary is not None:
        (root / "docs" / "GLOSSARY.md").write_text(seeded_glossary, encoding="utf-8")
    if git:
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True,
                       capture_output=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "seed"],
                       check=True, capture_output=True)
    return p, cfg


def test_plan_names_every_file_and_its_verdict_before_writing(tmp_path):
    p, cfg = _repo(tmp_path)
    actions = untangle.plan(p, cfg)
    assert actions, "a legacy repo must have a plan"
    by_doc = {a["doc"]: a for a in actions}
    assert by_doc["DECISIONS"]["verdict"] == untangle.MOVE
    assert by_doc["DECISIONS"]["entries"] == 2
    for a in actions:
        assert a["why"], f"{a['doc']} has no stated reason"
    # dry run wrote nothing
    assert not (p.docs / ownership.ENGINE_NAMESPACE).exists()


def test_engine_memory_moves_and_the_project_doc_never_does(tmp_path):
    p, cfg = _repo(tmp_path)
    res = untangle.apply(p, cfg)
    ns = p.docs / ownership.ENGINE_NAMESPACE
    assert res["ok"]
    assert (ns / "DECISIONS.md").exists()
    assert "D-001" in (ns / "DECISIONS.md").read_text(encoding="utf-8")
    # the human's doc is untouched, at its original path
    film = p.docs / "FILM-PROCEDURE.md"
    assert film.exists()
    assert film.read_text(encoding="utf-8") == "# Film procedure\n\nOurs.\n"
    assert not (ns / "FILM-PROCEDURE.md").exists()


def test_a_seeded_project_glossary_is_left_byte_identical(tmp_path):
    """The two-glossary case: their content stays put, ours is written fresh
    alongside. Nothing is split or merged."""
    mine = "# Glossary\n\n- **Dailies** — the day's footage.\n- **Blocking** — staging.\n"
    p, cfg = _repo(tmp_path, seeded_glossary=mine)
    actions = {a["doc"]: a for a in untangle.plan(p, cfg)}
    assert actions["GLOSSARY"]["verdict"] == untangle.LEAVE_AND_CREATE

    untangle.apply(p, cfg)
    assert (p.docs / "GLOSSARY.md").read_text(encoding="utf-8") == mine
    engine_g = p.docs / ownership.ENGINE_NAMESPACE / "GLOSSARY.md"
    assert engine_g.exists()
    assert engine_g.read_text(encoding="utf-8") != mine
    assert "Gameplan" in engine_g.read_text(encoding="utf-8")


def test_entries_are_conserved(tmp_path):
    p, cfg = _repo(tmp_path)
    before = untangle._corpus_entries(p.docs)
    res = untangle.apply(p, cfg)
    assert res["entries_conserved"] is True
    assert res["entries_after"] >= before
    assert untangle.entry_count(
        p.docs / ownership.ENGINE_NAMESPACE / "DECISIONS.md") == 2


def test_history_survives_the_move(tmp_path):
    """git mv STAGES a rename; history is preserved when that rename is
    committed. So the property to assert is that git recorded a rename (R),
    not a delete+add — the latter is what loses history."""
    p, cfg = _repo(tmp_path)
    res = untangle.apply(p, cfg)
    moved = [a for a in res["applied"] if a["doc"] == "DECISIONS"][0]
    assert moved["history_preserved"] is True, "git should have handled the move"
    r = subprocess.run(["git", "-C", str(p.root), "status", "--porcelain",
                        "--find-renames"], capture_output=True, text=True)
    renames = [ln for ln in r.stdout.splitlines() if ln.startswith("R")]
    assert any(f"{ownership.ENGINE_NAMESPACE}/DECISIONS.md" in ln
               for ln in renames), (
        f"expected a staged RENAME for DECISIONS.md, got:\n{r.stdout}")

    # and once committed, --follow reaches the pre-migration history
    subprocess.run(["git", "-C", str(p.root), "add", "-A"], check=True,
                   capture_output=True)
    subprocess.run(["git", "-C", str(p.root), "commit", "-qm", "untangle"],
                   check=True, capture_output=True)
    log = subprocess.run(
        ["git", "-C", str(p.root), "log", "--follow", "--oneline", "--",
         f"docs/{ownership.ENGINE_NAMESPACE}/DECISIONS.md"],
        capture_output=True, text=True)
    assert len(log.stdout.strip().splitlines()) >= 2, (
        "--follow must reach the commit that predates the move")


def test_a_legacy_stub_is_left_at_every_vacated_path(tmp_path):
    """D-081: the stub is the compat contract, not a courtesy."""
    p, cfg = _repo(tmp_path)
    untangle.apply(p, cfg)
    stub = (p.docs / "DECISIONS.md").read_text(encoding="utf-8")
    assert "moved" in stub.lower()
    assert f"docs/{ownership.ENGINE_NAMESPACE}/DECISIONS.md" in stub
    assert "uv tool install" in stub
    # inert: contributes no entries
    assert untangle.entry_count(p.docs / "DECISIONS.md") == 0


def test_the_stub_stops_the_old_engines_harmful_advice(tmp_path):
    """dangling_doc_pointers must go quiet, because its 'run upgrade to
    scaffold them' advice would recreate empty legacy files on an old engine."""
    from clauderizer import modernize

    p, cfg = _repo(tmp_path)
    untangle.apply(p, cfg)
    legacy_view = _paths.resolve(p.root)          # how an OLD engine resolves
    dangling = modernize.dangling_doc_pointers(legacy_view, cfg)
    missing = {doc for _ref, doc in dangling}
    assert "docs/DECISIONS.md" not in missing
    assert "docs/ENFORCEMENT.md" not in missing


def test_apply_is_idempotent(tmp_path):
    p, cfg = _repo(tmp_path)
    untangle.apply(p, cfg)
    again = untangle.apply(p, cfg)
    assert again["applied"] == []
    assert "nothing to untangle" in again["summary"]
    assert untangle.plan(p, cfg) == []


def test_the_layout_is_recorded_so_paths_resolve_after(tmp_path):
    p, cfg = _repo(tmp_path)
    untangle.apply(p, cfg)
    reread = Config.load(p.config_file)
    assert reread.docs_layout == ownership.LAYOUT_SPLIT
    live = _paths.resolve(p.root, layout=reread.docs_layout)
    assert live.doc("DECISIONS").exists()
    assert live.doc("DECISIONS").parent.name == ownership.ENGINE_NAMESPACE
    assert untangle.entry_count(live.doc("DECISIONS")) == 2


def test_entity_dirs_travel_with_the_corpus(tmp_path):
    p, cfg = _repo(tmp_path)
    (p.docs / "subsystems").mkdir()
    (p.docs / "subsystems" / "thing.md").write_text(
        "---\nid: subsys.thing\ntype: subsystem\n---\n\n# Thing\n", encoding="utf-8")
    untangle.apply(p, cfg)
    ns = p.docs / ownership.ENGINE_NAMESPACE
    assert (ns / "subsystems" / "thing.md").exists()


def test_works_without_git(tmp_path):
    """A non-git repo still migrates; only history preservation is lost."""
    p, cfg = _repo(tmp_path, git=False)
    res = untangle.apply(p, cfg)
    assert res["ok"]
    assert (p.docs / ownership.ENGINE_NAMESPACE / "DECISIONS.md").exists()
