import json
from pathlib import Path

from clauderizer.config import Config
from clauderizer.scaffold.init import init


def _snapshot(root: Path) -> dict[str, str]:
    snap = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and ".git/" not in str(p):
            snap[str(p.relative_to(root))] = p.read_text(encoding="utf-8", errors="replace")
    return snap


def test_init_creates_expected_layout(empty_python_repo):
    report = init(empty_python_repo, size="standard")
    assert report.host_profile == "python"
    r = empty_python_repo
    assert (r / ".clauderizer" / "config.toml").exists()
    assert (r / ".clauderizer" / "profile.lock.toml").exists()
    assert (r / "docs" / "gameplans" / "GAMEPLAN-PROCEDURE.md").exists()
    for doc in ("VISION", "ARCHITECTURE", "DECISIONS", "INVARIANTS", "TESTING", "HARDENING"):
        assert (r / "docs" / f"{doc}.md").exists(), doc
    assert (r / "CLAUDE.md").exists()
    assert "<!-- clauderizer:start -->" in (r / "CLAUDE.md").read_text(encoding="utf-8")
    assert (r / ".mcp.json").exists()
    assert (r / ".claude" / "settings.json").exists()
    assert (r / ".claude" / "skills" / "clauderizer-do-phase" / "SKILL.md").exists()
    assert ".clauderizer/index.json" in (r / ".gitignore").read_text(encoding="utf-8")

    cfg = Config.load(r / ".clauderizer" / "config.toml")
    assert cfg.size == "standard"
    assert cfg.host_profile == "python"
    assert cfg.ritual_enabled("cascade") is True


def test_init_is_idempotent(empty_node_repo):
    init(empty_node_repo, size="standard")
    snap1 = _snapshot(empty_node_repo)
    report2 = init(empty_node_repo, size="standard")
    snap2 = _snapshot(empty_node_repo)
    assert snap1 == snap2, "second init produced diffs"
    assert report2.changed == [], f"second run changed: {report2.changed}"


def test_init_detects_node(empty_node_repo):
    report = init(empty_node_repo)
    assert report.host_profile == "node"
    cfg = Config.load(empty_node_repo / ".clauderizer" / "config.toml")
    assert cfg.host_profile == "node"


def test_init_preserves_existing_claude_md(empty_python_repo):
    claude = empty_python_repo / "CLAUDE.md"
    claude.write_text("# My Project\n\nImportant human notes.\n", encoding="utf-8")
    init(empty_python_repo)
    text = claude.read_text(encoding="utf-8")
    assert "Important human notes." in text
    assert "<!-- clauderizer:start -->" in text


def test_init_preserves_other_mcp_servers(empty_python_repo):
    mcp = empty_python_repo / ".mcp.json"
    mcp.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}}), encoding="utf-8")
    init(empty_python_repo)
    data = json.loads(mcp.read_text(encoding="utf-8"))
    assert "other" in data["mcpServers"]
    assert "clauderizer" in data["mcpServers"]


def test_init_pet_size_is_minimal(empty_python_repo):
    init(empty_python_repo, size="pet")
    r = empty_python_repo
    cfg = Config.load(r / ".clauderizer" / "config.toml")
    assert cfg.ritual_enabled("cascade") is False
    # pet ships VISION but not HARDENING/INVARIANTS
    assert (r / "docs" / "VISION.md").exists()
    assert not (r / "docs" / "HARDENING.md").exists()


def test_init_with_gameplan(empty_python_repo):
    init(empty_python_repo, gameplan="First Initiative")
    cfg = Config.load(empty_python_repo / ".clauderizer" / "config.toml")
    assert cfg.active_gameplan and cfg.active_gameplan.endswith("first-initiative")
    gp = empty_python_repo / "docs" / "gameplans" / cfg.active_gameplan / "GAMEPLAN.md"
    assert gp.exists()
