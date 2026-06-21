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


# --- P5: bespoke native instructions + hook guides -------------------------------

def test_emit_instructions_writes_floor_for_non_agents_hosts(tmp_path):
    p = ht.emit_instructions("continue", tmp_path)
    assert p == tmp_path / ".continue" / "rules" / "clauderizer.md"
    text = p.read_text(encoding="utf-8")
    assert "call `cz_status` first" in text
    assert "clauderizer:start" in text and "clauderizer:end" in text
    assert ht.emit_instructions("gemini-cli", tmp_path) == tmp_path / "GEMINI.md"


def test_emit_instructions_none_for_agents_md_hosts(tmp_path):
    # cursor reads AGENTS.md, so the floor is already there (P2) — no native file
    assert ht.emit_instructions("cursor", tmp_path) is None


def test_emit_instructions_preserves_user_content_and_is_idempotent(tmp_path):
    g = tmp_path / "GEMINI.md"
    g.write_text("# My project rules\nDo the thing.\n", encoding="utf-8")
    ht.emit_instructions("gemini-cli", tmp_path)
    text = g.read_text(encoding="utf-8")
    assert "My project rules" in text            # user content preserved
    assert "call `cz_status` first" in text      # floor appended
    ht.emit_instructions("gemini-cli", tmp_path)  # second emit replaces, not duplicates
    assert g.read_text(encoding="utf-8").count("clauderizer:start") == 1


def test_hook_setup_guide(tmp_path):
    guide = ht.hook_setup_guide("copilot")
    assert "clauderizer-hook" in guide and "SessionStart" in guide
    assert ht.hook_setup_guide("continue") is None   # no hook system
    assert ht.hook_setup_guide("zed") is None


# --- P6: wiring-contract verification (the host-simulator) ------------------------

def test_wiring_contract_sweep_all_green(tmp_path):
    report = ht.wiring_contract_sweep(tmp_path)
    assert report  # non-empty — the auto-write hosts
    for host, (ok, detail) in report.items():
        assert ok, f"{host} failed the wiring contract: {detail}"


def test_path_safety_audit_flags_machine_specific_path(tmp_path):
    cfg = tmp_path / ".cursor" / "mcp.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({"mcpServers": {"clauderizer": {
        "command": "/home/me/.venv/bin/clauderizer-mcp", "args": []}}}), encoding="utf-8")
    offenders = ht.path_safety_audit(tmp_path)
    assert offenders and ".cursor/mcp.json" in offenders[0]


def test_path_safety_audit_clean_after_portable_emit(tmp_path):
    ht.emit_mcp("cursor", tmp_path)
    ht.emit_mcp("zed", tmp_path)
    assert ht.path_safety_audit(tmp_path) == []   # portable commands -> clean
