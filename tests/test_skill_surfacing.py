"""Skill relevance surfacing (skill-awareness Phase 2).

Registered skills surface FOCUSED into the handoff (top-k by relevance to the
phase, or nothing when none overlap - L-35) and the status gauge reports an
active-skill count + a staleness nudge. The handoff integration test exercises
the cross-cutting assemble() seam (L-34).
"""

from clauderizer import analyze
from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.rituals import handoff, status_bundle

GID = "2026-05-01-bootstrap"


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def test_relevant_skill_pointer_ranks_only_overlapping(temp_repo):
    paths, _ = _ctx(temp_repo)
    M.register_skill(paths, name="oauth-login",
                     description="Implement OAuth authentication and session tokens")
    M.register_skill(paths, name="canvas-art",
                     description="Generate static visual posters and designs")
    md = handoff.relevant_skill_pointer(
        paths, "we need to implement oauth authentication for the login flow")
    assert md is not None
    assert "oauth-login" in md
    assert "canvas-art" not in md  # no lexical overlap with the auth query


def test_relevant_skill_pointer_empty_cases(temp_repo):
    paths, _ = _ctx(temp_repo)
    # no SKILLS.md yet
    assert handoff.relevant_skill_pointer(paths, "implement an authentication flow") is None
    M.register_skill(paths, name="frontend", description="build polished user interfaces")
    # no query
    assert handoff.relevant_skill_pointer(paths, "") is None
    # a query that overlaps nothing surfaces nothing (honest negative)
    assert handoff.relevant_skill_pointer(paths, "quokka zeppelin obscure xyzzy") is None


def test_obsolete_skill_drops_from_surfacing(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.register_skill(paths, name="oauth-login",
                         description="Implement OAuth authentication and session tokens")
    q = "implement oauth authentication login"
    assert "oauth-login" in (handoff.relevant_skill_pointer(paths, q) or "")
    M.obsolete_skill(paths, skill_id=r["id"])
    assert handoff.relevant_skill_pointer(paths, q) is None  # obsolete -> not surfaced


def test_assemble_surfaces_relevant_skill_block(temp_repo):
    """L-34 seam: registered, phase-relevant skills appear in the assembled handoff."""
    paths, config = _ctx(temp_repo)
    gtext = (paths.gameplan_dir(GID) / "GAMEPLAN.md").read_text(encoding="utf-8")
    query = handoff._phase_query(gtext, "1")
    toks = sorted(analyze._tokens(query))
    assert toks, "fixture phase 1 must have rankable text"
    word = toks[0]
    M.register_skill(paths, name="phase-helper", description=f"Assists with {word} tasks")
    M.register_skill(paths, name="zzz-unrelated", description="quokka zeppelin xyzzy obscure")
    res = handoff.assemble(paths, config, GID, "1", write=False)
    md = res["handoff_md"]
    assert "## Skills for This Phase" in md
    assert "phase-helper" in md
    assert "zzz-unrelated" not in md  # zero overlap -> not surfaced


def test_assemble_omits_block_when_no_skills(temp_repo):
    paths, config = _ctx(temp_repo)
    res = handoff.assemble(paths, config, GID, "1", write=False)
    assert "## Skills for This Phase" not in res["handoff_md"]


def test_gauge_counts_skills_and_nudges_past_threshold(temp_repo):
    paths, config = _ctx(temp_repo)
    idx = (paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    assert status_bundle._memory_gauge(paths, config, idx)["active_skills"] == 0
    for i in range(status_bundle.ACTIVE_SKILLS_WARN + 1):
        M.register_skill(paths, name=f"skill-{i:02d}", description=f"does thing number {i}")
    g = status_bundle._memory_gauge(paths, config, idx)
    assert g["active_skills"] == status_bundle.ACTIVE_SKILLS_WARN + 1
    assert g["warning"] and "registered skills" in g["warning"]


def test_digest_renders_skill_count(temp_repo):
    paths, config = _ctx(temp_repo)
    M.register_skill(paths, name="alpha", description="does alpha work")
    M.register_skill(paths, name="beta", description="does beta work")
    bundle = status_bundle.compute(paths, config)
    assert bundle["memory"]["active_skills"] == 2
    assert "2 skills" in status_bundle.render_digest(bundle)
