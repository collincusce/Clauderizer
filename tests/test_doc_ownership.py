"""Doc ownership is structural (D-080), and introducing it changes NOTHING.

The load-bearing property of this phase is the identity default (L-41): every
doc must resolve exactly where it resolved before ownership existed, so a
breaking relocation can land in stages with a byte-identical digest at every
step. The tests that matter here are the ones asserting *no change*.
"""

from __future__ import annotations

from pathlib import Path

from clauderizer import ownership, paths as _paths
from clauderizer.config import SIZE_MANIFESTS, Config


# --- the map itself -------------------------------------------------------

def test_every_templated_doc_has_an_explicit_owner():
    """No templated name may fall through to the unknown-name default by
    accident — the taxonomy is a decision, and silence is not one."""
    from clauderizer import assets

    templated = {p.stem for p in (assets.TEMPLATES / "docs").glob("*.md")}
    classified = ownership.ENGINE_DOCS | ownership.PROJECT_DOCS | ownership.PRODUCT_DOCS
    unclassified = templated - classified
    assert not unclassified, (
        f"templated doc(s) with no recorded owner: {sorted(unclassified)} — "
        "add each to ENGINE_DOCS or PROJECT_DOCS in ownership.py (D-080)")


def test_an_unknown_doc_belongs_to_the_project():
    """The default is deliberate: a doc the engine does not recognize is the
    human's, and the engine keeps its hands off it."""
    assert ownership.owner_of("FILM-PROCEDURE") == ownership.PROJECT
    assert ownership.owner_of("VOICE-CASTING-PROCEDURE.md") == ownership.PROJECT
    assert not ownership.is_engine_owned("CONPTY")


def test_the_measured_collisions_are_project_owned():
    """The names that actually collided in the field survey."""
    for name in ("SECURITY", "ARCHITECTURE", "VISION", "TESTING", "SCHEMA",
                 "DEPLOYMENT", "REQUIREMENTS", "INCIDENTS"):
        assert ownership.owner_of(name) == ownership.PROJECT, name
        assert not ownership.is_engine_owned(name), name


def test_the_working_memory_corpus_is_engine_owned():
    for name in ("DECISIONS", "INVARIANTS", "LESSONS", "HARDENING", "SKILLS",
                 "ENFORCEMENT"):
        assert ownership.is_engine_owned(name), name


def test_gameplan_procedure_is_product_and_never_relocates():
    """O-02: it is the file _procedure_drift reads, so moving it would destroy
    the one loud signal an older engine trips on a migrated repo."""
    assert ownership.owner_of("GAMEPLAN-PROCEDURE") == ownership.PRODUCT
    assert not ownership.is_engine_owned("GAMEPLAN-PROCEDURE")


def test_glossary_is_engine_owned_and_declared_a_split_name():
    """Two glossaries is the shape: the engine's Clauderizer-vocabulary glossary
    relocates; the project's domain glossary keeps docs/GLOSSARY.md."""
    assert ownership.is_engine_owned("GLOSSARY")
    assert "GLOSSARY" in ownership.SPLIT_NAMES


# --- the identity default: nothing moves ----------------------------------

def test_legacy_layout_resolves_every_doc_exactly_where_it_always_did(tmp_path):
    p = _paths.resolve(tmp_path)
    assert p.engine_docs is None, "legacy layout must leave engine_docs unset"
    for name in ("DECISIONS", "INVARIANTS", "LESSONS", "HARDENING", "SKILLS",
                 "ENFORCEMENT", "GLOSSARY", "ARCHITECTURE", "VISION", "TESTING",
                 "SECURITY", "ANYTHING-ELSE"):
        assert p.doc(name) == p.docs / f"{name}.md", name


def test_legacy_layout_keeps_entity_dirs_where_they_were(tmp_path):
    p = _paths.resolve(tmp_path)
    assert p.features_dir == p.docs / "features"
    assert p.subsystems_dir == p.docs / "subsystems"


def test_default_config_is_legacy_and_writes_no_layout_key(tmp_path):
    """INVARIANT-08 drop-nothing: an untouched repo's config stays byte-identical
    — the layout key appears only once a repo has left the legacy layout."""
    cfg = Config.for_size("standard")
    assert cfg.docs_layout == ownership.LAYOUT_LEGACY
    assert "docs_layout" not in cfg.to_toml()


# --- the split layout: engine docs move, project docs do not --------------

def test_split_layout_moves_only_engine_owned_docs(tmp_path):
    p = _paths.resolve(tmp_path, layout=ownership.LAYOUT_SPLIT)
    ns = p.docs / ownership.ENGINE_NAMESPACE
    assert p.engine_docs == ns
    # engine memory relocates
    for name in ("DECISIONS", "INVARIANTS", "LESSONS", "HARDENING", "SKILLS",
                 "ENFORCEMENT", "GLOSSARY"):
        assert p.doc(name) == ns / f"{name}.md", name
    # the project's docs do NOT
    for name in ("ARCHITECTURE", "VISION", "TESTING", "SECURITY",
                 "FILM-PROCEDURE"):
        assert p.doc(name) == p.docs / f"{name}.md", name


def test_split_layout_never_moves_the_procedure_file(tmp_path):
    legacy = _paths.resolve(tmp_path)
    split = _paths.resolve(tmp_path, layout=ownership.LAYOUT_SPLIT)
    assert split.procedure_file == legacy.procedure_file
    assert split.gameplans == legacy.gameplans


def test_split_layout_round_trips_through_config(tmp_path):
    cfg = Config.for_size("standard")
    cfg.docs_layout = ownership.LAYOUT_SPLIT
    toml = cfg.to_toml()
    assert 'docs_layout = "split"' in toml
    (tmp_path / "config.toml").write_text(toml, encoding="utf-8")
    assert Config.load(tmp_path / "config.toml").docs_layout == ownership.LAYOUT_SPLIT


# --- the phase's real exit criterion --------------------------------------

def test_no_manifest_claims_a_name_in_the_projects_namespace():
    """P2: `modules` is what the engine scaffolds and manages, so every entry
    must be engine-owned. A project-owned name in a manifest is the defect this
    whole gameplan exists to remove."""
    for size, m in SIZE_MANIFESTS.items():
        claimed = [d for d in m["modules"] if not ownership.is_engine_owned(d)]
        assert not claimed, (
            f"size '{size}' manifest claims project-owned name(s) {claimed} in "
            f"`modules` — they belong in `project_seeds` (D-080)")


def test_project_seeds_are_offered_never_claimed():
    """The generic names are still AVAILABLE, just not taken by default."""
    for size, m in SIZE_MANIFESTS.items():
        for d in m.get("project_seeds", ()):
            assert ownership.owner_of(d) == ownership.PROJECT, (size, d)
            assert d not in m["modules"], (size, d)
    # the collision names specifically are seeds, not modules
    assert "SECURITY" in SIZE_MANIFESTS["saas"]["project_seeds"]
    assert "ARCHITECTURE" in SIZE_MANIFESTS["standard"]["project_seeds"]


def test_this_repo_still_resolves_its_own_corpus(tmp_path):
    """The engine's own repo is on the legacy layout and must keep resolving."""
    root = Path(__file__).resolve().parent.parent
    p = _paths.resolve(root)
    assert p.doc("DECISIONS").exists()
    assert p.doc("INVARIANTS").exists()
    assert p.subsystems_dir.is_dir()
