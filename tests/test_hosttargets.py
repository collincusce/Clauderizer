"""Phase 4: per-host wiring emitters — portable, non-destructive, reversible."""

from __future__ import annotations

import json

import pytest

from clauderizer import hosttargets as ht


def _read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def test_emit_writes_portable_config(tmp_path):
    path = ht.emit_mcp("cursor", tmp_path)
    assert path == tmp_path / ".cursor" / "mcp.json"
    data = _read(path)
    entry = data["mcpServers"]["clauderizer"]
    # machine-independent uvx form — no absolute path, no wsl.exe shim (D-031)
    assert entry["command"] == "uvx"
    assert "clauderizer" in entry["args"]
    assert ht.is_path_safe([entry["command"], *entry["args"]])


def test_host_specific_keys(tmp_path):
    # each host's own key/path (verified 2026-06-21) — locked so drift is caught
    assert "servers" in _read(ht.emit_mcp("copilot", tmp_path))          # VS Code
    assert "context_servers" in _read(ht.emit_mcp("zed", tmp_path))       # Zed
    assert "amp.mcpServers" in _read(ht.emit_mcp("amp", tmp_path))        # Amp dotted key


def test_emit_is_non_destructive(tmp_path):
    # a user's pre-existing server in the same file must survive (D-031)
    cfg = tmp_path / ".cursor" / "mcp.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({"mcpServers": {"playwright": {"command": "npx"}}}),
                   encoding="utf-8")
    ht.emit_mcp("cursor", tmp_path)
    servers = _read(cfg)["mcpServers"]
    assert servers["playwright"] == {"command": "npx"}   # untouched
    assert "clauderizer" in servers                       # added alongside


def test_coexistence_across_hosts(tmp_path):
    # the top config-safety risk: a second host must not clobber the first
    ht.emit_mcp("cursor", tmp_path)
    ht.emit_mcp("copilot", tmp_path)
    assert "clauderizer" in _read(tmp_path / ".cursor" / "mcp.json")["mcpServers"]
    assert "clauderizer" in _read(tmp_path / ".vscode" / "mcp.json")["servers"]


def test_emit_refuses_machine_specific_command(tmp_path):
    with pytest.raises(ValueError):
        ht.emit_mcp("cursor", tmp_path,
                    ["/home/me/.venv/bin/clauderizer-mcp"])   # absolute -> refused
    with pytest.raises(ValueError):
        ht.emit_mcp("cursor", tmp_path,
                    ["wsl.exe", "-d", "ubuntu", "clauderizer-mcp"])  # shim -> refused


def test_guide_only_hosts_write_nothing(tmp_path):
    for host in ("codex", "windsurf", "kimi"):       # TOML / global -> guide-only
        assert ht.emit_mcp(host, tmp_path) is None
    assert not any(tmp_path.rglob("*.json"))         # nothing auto-written


def test_uninstall_removes_only_clauderizer(tmp_path):
    cfg = tmp_path / ".cursor" / "mcp.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({"mcpServers": {
        "playwright": {"command": "npx"}, "clauderizer": {"command": "uvx"}}}),
        encoding="utf-8")
    assert ht.remove_mcp("cursor", tmp_path) is True
    servers = _read(cfg)["mcpServers"]
    assert "clauderizer" not in servers
    assert servers["playwright"] == {"command": "npx"}   # everything else intact


def test_is_path_safe():
    assert ht.is_path_safe(ht.PORTABLE_COMMAND) is True
    assert ht.is_path_safe(["/abs/path/clauderizer-mcp"]) is False
    assert ht.is_path_safe(["C:\\Users\\me\\mcp.exe"]) is False
    assert ht.is_path_safe(["wsl.exe", "-d", "ubuntu", "x"]) is False


def test_cli_uninstall_removes_only_clauderizer(tmp_path, monkeypatch):
    from clauderizer import cli

    (tmp_path / ".git").mkdir()
    ht.emit_mcp("cursor", tmp_path)
    cfg = tmp_path / ".cursor" / "mcp.json"
    data = _read(cfg)
    data["mcpServers"]["other"] = {"command": "x"}
    cfg.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    assert cli.main(["uninstall", "--host", "cursor"]) == 0

    servers = _read(cfg)["mcpServers"]
    assert "clauderizer" not in servers
    assert servers["other"] == {"command": "x"}
