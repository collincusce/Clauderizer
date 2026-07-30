"""The untangle moves engine memory and never touches the human's docs (D-080)."""

from __future__ import annotations

import pathlib
import re
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
    # carries only its high-water sentinel — no real entry
    assert untangle.entry_count(p.docs / "DECISIONS.md") == 1
    assert "D-900000" in stub and "SENTINEL" in stub


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


# --- H-33: an OLD engine writing into a stub ------------------------------

def _old_engine_write(p, name, entry_id_prefix):
    """Simulate an engine too old for the split layout: it resolves the LEGACY
    path and appends there, allocating from whatever ids it finds."""
    from clauderizer.model import next_numbered_id

    legacy = _paths.resolve(p.root)          # how a pre-3.0 engine resolves
    target = legacy.doc(name)
    text = target.read_text(encoding="utf-8")
    new_id = next_numbered_id(text, entry_id_prefix, sep="-", width=3)
    target.write_text(text + f"\n### {new_id} — written by an old engine\n\nbody\n",
                      encoding="utf-8")
    return new_id


def test_the_sentinel_stops_an_old_engines_write_from_COLLIDING(tmp_path):
    """H-33, the live failure: a cz_add_decision through a stale engine landed
    in the stub and numbered itself D-001 while the real register ended at
    D-081 — a duplicate id in an append-only corpus. The sentinel cannot stop
    the write, but it must stop the collision."""
    p, cfg = _repo(tmp_path)
    untangle.apply(p, cfg)
    live = _paths.resolve(p.root, layout=ownership.LAYOUT_SPLIT)
    real_ids = set(re.findall(r"^### (D-\d+)",
                              live.doc("DECISIONS").read_text(encoding="utf-8"),
                              re.M))
    assert real_ids, "fixture must have real decisions"

    orphan = _old_engine_write(p, "DECISIONS", "D")

    assert orphan not in real_ids, (
        f"an old engine allocated {orphan}, colliding with the real corpus — "
        "the sentinel failed")
    assert int(orphan.split("-")[1]) > untangle._SENTINEL_N


def test_a_forked_stub_is_reported_not_silently_tolerated(tmp_path):
    p, cfg = _repo(tmp_path)
    untangle.apply(p, cfg)
    live = _paths.resolve(p.root, layout=ownership.LAYOUT_SPLIT)
    assert untangle.forked_stubs(live) == [], "clean stub must be quiet"

    orphan = _old_engine_write(p, "DECISIONS", "D")

    forked = untangle.forked_stubs(live)
    assert len(forked) == 1
    assert forked[0]["doc"] == "DECISIONS"
    assert orphan in forked[0]["orphan_ids"]
    assert forked[0]["real"].endswith("clauderizer/DECISIONS.md")


def test_forked_stub_detection_is_silent_on_the_legacy_layout(tmp_path):
    """A repo that never migrated has no stubs and must never be reported."""
    p, cfg = _repo(tmp_path)
    assert untangle.forked_stubs(p) == []


def test_report_paths_are_posix_on_every_platform():
    """L-51: the `from`/`to` values are DISPLAY strings — they land in the stub a
    human reads and in the upgrade report — so they must not carry a backslash
    on Windows. Caught by a real red Windows cell, not by inspection."""
    from clauderizer.config import Config as _C
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td) / "repo"
        (root / "docs").mkdir(parents=True)
        (root / ".clauderizer").mkdir()
        p = _paths.resolve(root)
        cfg = _C.for_size("standard")
        p.config_file.write_text(cfg.to_toml(), encoding="utf-8")
        (root / "docs" / "DECISIONS.md").write_text(
            "# D\n\n### D-001 — x\n\nbody\n", encoding="utf-8")
        for a in untangle.plan(p, cfg):
            for key in ("from", "to"):
                v = a.get(key)
                if v:
                    assert "\\" not in v, (
                        f"{a['doc']}.{key} carries a backslash: {v}")
                    assert pathlib.PurePosixPath(v).parts[0] == "docs", v
