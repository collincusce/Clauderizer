"""Skill discovery (skill-awareness Phase 1) -- read-only propose-confirm.

Discovery scans skill roots, parses SKILL.md frontmatter, diffs against what's
registered in docs/SKILLS.md, and proposes the rest. It never writes and never
crashes on malformed input (L-24).
"""

from clauderizer import mutations as M
from clauderizer import ops
from clauderizer import paths as P
from clauderizer import skill_discovery as D


def _mk_skill(root, name, description, *, with_frontmatter=True):
    d = root / name
    d.mkdir(parents=True)
    if with_frontmatter:
        (d / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
            encoding="utf-8")
    else:
        (d / "SKILL.md").write_text(f"# {name}\n\n{description}\n", encoding="utf-8")
    return d


def test_discover_finds_name_and_description(temp_repo, tmp_path):
    paths = P.resolve(temp_repo)
    root = tmp_path / "skills"
    root.mkdir()
    _mk_skill(root, "frontend-design", "Build distinctive UIs")
    _mk_skill(root, "verify", "Run it for real")
    res = D.discover(paths, roots=[("test", root)])
    assert res["ok"]
    by_name = {p["name"]: p for p in res["proposals"]}
    assert set(by_name) == {"frontend-design", "verify"}
    assert by_name["frontend-design"]["description"] == "Build distinctive UIs"
    assert by_name["frontend-design"]["source"].endswith("frontend-design")


def test_only_unregistered_are_proposed(temp_repo, tmp_path):
    paths = P.resolve(temp_repo)
    root = tmp_path / "skills"
    root.mkdir()
    _mk_skill(root, "alpha", "a")
    _mk_skill(root, "beta", "b")
    M.register_skill(paths, name="alpha", description="a")
    res = D.discover(paths, roots=[("test", root)])
    names = {p["name"] for p in res["proposals"]}
    assert names == {"beta"}
    assert res["registered_count"] == 1


def test_dedup_across_roots_first_wins(temp_repo, tmp_path):
    paths = P.resolve(temp_repo)
    r1 = tmp_path / "r1"
    r1.mkdir()
    _mk_skill(r1, "dup", "from r1")
    r2 = tmp_path / "r2"
    r2.mkdir()
    _mk_skill(r2, "dup", "from r2")
    res = D.discover(paths, roots=[("r1", r1), ("r2", r2)])
    dups = [p for p in res["proposals"] if p["name"] == "dup"]
    assert len(dups) == 1
    assert dups[0]["description"] == "from r1"


def test_malformed_frontmatter_degrades_gracefully(temp_repo, tmp_path):
    paths = P.resolve(temp_repo)
    root = tmp_path / "skills"
    root.mkdir()
    _mk_skill(root, "no-fm", "a body, no frontmatter", with_frontmatter=False)
    (root / "empty").mkdir()
    (root / "empty" / "SKILL.md").write_text("", encoding="utf-8")
    (root / "weird").mkdir()
    (root / "weird" / "SKILL.md").write_bytes(b"\xff\xfe not utf-8 \x00 bytes")
    res = D.discover(paths, roots=[("test", root)])  # must not raise
    assert res["ok"]
    names = {p["name"] for p in res["proposals"]}
    # dir-name fallback keeps real directories discoverable despite bad files
    assert {"no-fm", "empty", "weird"} <= names


def test_discover_never_writes(temp_repo, tmp_path):
    paths = P.resolve(temp_repo)
    sdoc = paths.doc("SKILLS")
    assert not sdoc.exists()
    root = tmp_path / "skills"
    root.mkdir()
    _mk_skill(root, "x", "y")
    D.discover(paths, roots=[("test", root)])
    assert not sdoc.exists()  # discovery is read-only
    assert ops.REGISTRY["cz_discover_skills"].writes is False


def test_discovers_real_shipped_skills(temp_repo):
    """Exit criterion: parses real SKILL.md from the Clauderizer-shipped location."""
    from clauderizer import assets
    paths = P.resolve(temp_repo)
    res = D.discover(paths, roots=[("clauderizer-shipped", assets.SKILLS)])
    names = {p["name"] for p in res["proposals"]}
    assert "clauderizer-cascade" in names
    assert res["proposal_count"] >= 5  # six clauderizer-* skills ship


def test_op_surface_is_read_only_and_registered(temp_repo):
    from clauderizer.tools_list import TOOL_NAMES
    assert "cz_discover_skills" in TOOL_NAMES
    assert list(ops.REGISTRY) == TOOL_NAMES  # parity preserved
    assert ops.REGISTRY["cz_discover_skills"].writes is False
