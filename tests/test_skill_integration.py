"""End-to-end skill-awareness integration (skill-awareness Phase 3).

Exercises the whole loop across the cross-cutting seams (L-34): a SKILL.md on
disk -> read-only discovery proposes -> the agent confirms (register) -> the
skill surfaces in BOTH the status digest (status_bundle) and the phase handoff
(handoff). One test that fails if any seam regresses.
"""

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer import skill_discovery as D
from clauderizer.rituals import handoff, status_bundle

GID = "2026-05-01-bootstrap"


def test_discover_confirm_surface_end_to_end(temp_repo, tmp_path):
    paths = P.resolve(temp_repo)
    config = cfg.Config.load(paths.config_file)

    # 1. a SKILL.md exists in a local skill directory
    sk = tmp_path / "skills" / "oauth-login"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text(
        "---\nname: oauth-login\n"
        "description: Implement OAuth authentication and session tokens\n---\n# x\n",
        encoding="utf-8")

    # 2. discovery proposes it and writes NOTHING (read-only)
    res = D.discover(paths, roots=[("test", tmp_path / "skills")])
    prop = next(p for p in res["proposals"] if p["name"] == "oauth-login")
    assert not paths.doc("SKILLS").exists()

    # 3. the agent confirms the proposal -> register (the blessed write)
    M.register_skill(paths, name=prop["name"], description=prop["description"],
                     source=prop["source"])

    # 4. it surfaces in the status digest...
    bundle = status_bundle.compute(paths, config)
    assert bundle["memory"]["active_skills"] == 1
    assert "1 skills" in status_bundle.render_digest(bundle)

    # 5. ...and in a phase handoff whose query overlaps its trigger
    md = handoff.relevant_skill_pointer(paths, "implement oauth authentication and login")
    assert md and "oauth-login" in md

    # 6. obsoleting it removes it from both surfaces (append-only marker)
    M.obsolete_skill(paths, skill_id="S-01")
    bundle2 = status_bundle.compute(paths, config)
    assert bundle2["memory"]["active_skills"] == 0
    assert handoff.relevant_skill_pointer(
        paths, "implement oauth authentication and login") is None
