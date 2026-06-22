"""Skill registration + obsolete lifecycle (skill-awareness Phase 0).

Mirrors the lesson lifecycle: register lazily creates docs/SKILLS.md from the
template, assigns S-NN under a category, and is idempotent on name; obsolete
marks in place (append-only) and is idempotent. Both round-trip (L-22).
"""

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.markdown import skill_state as SS


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def test_register_creates_doc_and_assigns_ids(temp_repo):
    paths, _ = _ctx(temp_repo)
    sdoc = paths.doc("SKILLS")
    assert not sdoc.exists()  # lazily created from the template on first write
    r = M.register_skill(paths, name="frontend-design",
                         description="Build distinctive UIs",
                         source=".claude/skills/frontend-design")
    assert r["ok"] and r["id"] == "S-01"
    assert sdoc.exists()
    text = sdoc.read_text(encoding="utf-8")
    assert "**S-01.** frontend-design" in text
    assert "Build distinctive UIs" in text
    assert "_(none yet)_" not in text  # placeholder stripped

    r2 = M.register_skill(paths, name="systematic-debugging",
                          description="Root-cause first", category="Testing")
    assert r2["id"] == "S-02"
    assert "### Category: Testing" in sdoc.read_text(encoding="utf-8")


def test_register_is_idempotent_on_name(temp_repo):
    paths, _ = _ctx(temp_repo)
    r1 = M.register_skill(paths, name="verify", description="run it for real")
    r2 = M.register_skill(paths, name="VERIFY", description="a different description")
    assert r1["id"] == "S-01"
    assert r2.get("already_registered") is True and r2["id"] == "S-01"
    text = paths.doc("SKILLS").read_text(encoding="utf-8")
    assert text.count("**S-01.**") == 1
    assert "**S-02.**" not in text


def test_obsolete_marks_in_place_and_is_idempotent(temp_repo):
    paths, _ = _ctx(temp_repo)
    M.register_skill(paths, name="old-skill", description="legacy")
    r = M.obsolete_skill(paths, skill_id="S-01", reason="removed upstream",
                         today="2026-06-22")
    assert r["ok"] and not r["already_obsolete"]
    text = paths.doc("SKILLS").read_text(encoding="utf-8")
    assert "(obsolete 2026-06-22: removed upstream)" in text
    assert "**S-01.** old-skill" in text  # append-only: entry kept, just marked

    r2 = M.obsolete_skill(paths, skill_id="S-01", today="2026-06-22")
    assert r2["already_obsolete"]

    # an obsolete name frees up for a fresh registration (new id)
    r3 = M.register_skill(paths, name="old-skill", description="back again")
    assert r3["id"] == "S-02"


def test_obsolete_unknown_skill_fails(temp_repo):
    paths, _ = _ctx(temp_repo)
    M.register_skill(paths, name="x", description="y")
    assert M.obsolete_skill(paths, skill_id="S-99")["ok"] is False


def test_register_round_trip_idempotent(temp_repo):
    """L-22: register-twice (same name) == register-once; the doc is stable."""
    paths, _ = _ctx(temp_repo)
    M.register_skill(paths, name="a", description="d1", category="Testing")
    once = paths.doc("SKILLS").read_text(encoding="utf-8")
    M.register_skill(paths, name="a", description="d1", category="Testing")
    twice = paths.doc("SKILLS").read_text(encoding="utf-8")
    assert once == twice


def test_registered_skill_parses_back_via_grammar(temp_repo):
    paths, _ = _ctx(temp_repo)
    M.register_skill(paths, name="canvas-design", description="Static visual art",
                     source="anthropic-skills/canvas-design")
    body = paths.doc("SKILLS").read_text(encoding="utf-8")
    entries = [SS.parse_entry(ln) for ln in body.splitlines()]
    entries = [e for e in entries if e]
    assert len(entries) == 1
    assert entries[0]["name"] == "canvas-design"
    assert entries[0]["source"] == "anthropic-skills/canvas-design"
    assert entries[0]["state"] == "active"
