import json
from pathlib import Path

from clauderizer.config import Config
from clauderizer.scaffold import init as scaffold_init
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


# --- invocation resolution: never wire a uvx ephemeral env -----------------------
# (stranger-readiness Phase 0: `uvx --from clauderizer clauderize init` wired
# uv-cache paths into .mcp.json and the wrapper; `uv cache clean` then killed
# the MCP wiring and every digest until a re-init.)


def _fake_uvx_env(tmp_path, monkeypatch, *, cache_env=True):
    cache = tmp_path / "cache" / "uv"
    bindir = cache / "archive-v0" / "AbCd1234" / "bin"
    bindir.mkdir(parents=True)
    for name in ("clauderizer-mcp", "clauderizer-hook"):
        (bindir / name).write_text("", encoding="utf-8")
    if cache_env:
        monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    else:
        monkeypatch.delenv("UV_CACHE_DIR", raising=False)
    monkeypatch.setattr(scaffold_init.sys, "executable", str(bindir / "python"))
    monkeypatch.setattr(
        scaffold_init.shutil, "which",
        lambda n: str(bindir / n) if n.startswith("clauderizer")
        else ("/opt/tools/uvx" if n == "uvx" else None))
    return bindir


def test_resolve_invocation_refuses_uv_cache_paths(tmp_path, monkeypatch):
    _fake_uvx_env(tmp_path, monkeypatch, cache_env=True)
    mcp, hook = scaffold_init._resolve_invocation(None)
    assert mcp == ["/opt/tools/uvx", "-q", "--from", "clauderizer", "clauderizer-mcp"]
    assert hook == ["/opt/tools/uvx", "-q", "--from", "clauderizer", "clauderizer-hook"]


def test_resolve_invocation_archive_marker_alone_suffices(tmp_path, monkeypatch):
    # no UV_CACHE_DIR in the environment: the archive-v0 path component is
    # still recognized (uvx ephemeral envs live there on every platform)
    _fake_uvx_env(tmp_path, monkeypatch, cache_env=False)
    mcp, hook = scaffold_init._resolve_invocation(None)
    assert mcp[0] == "/opt/tools/uvx"
    assert hook[-1] == "clauderizer-hook"


def test_resolve_invocation_venv_scripts_still_preferred(tmp_path, monkeypatch):
    # a real venv bindir (not under any uv cache) keeps the existing behavior
    bindir = tmp_path / "venv" / "bin"
    bindir.mkdir(parents=True)
    for name in ("clauderizer-mcp", "clauderizer-hook"):
        (bindir / name).write_text("", encoding="utf-8")
    monkeypatch.delenv("UV_CACHE_DIR", raising=False)
    monkeypatch.setattr(scaffold_init.sys, "executable", str(bindir / "python"))
    mcp, hook = scaffold_init._resolve_invocation(None)
    assert mcp == [str(bindir / "clauderizer-mcp")]
    assert hook == [str(bindir / "clauderizer-hook")]
