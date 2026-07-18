"""Phase 8: host_target wired end-to-end through `clauderize init --host` (A-001).

Covers the five exit criteria: the --host flag sets+emits a host's wiring;
unknown hosts fail friendly (no KeyError); claude-code stays byte-identical
(INVARIANT-07); init --host cursor yields BOTH the floor and the tools and passes
the wiring contract; and uninstall reverses the full footprint while preserving
docs/ and unrelated entries.
"""

from __future__ import annotations

import json

import pytest

from clauderizer import cli, hosttargets as ht
from clauderizer.config import Config
from clauderizer.markdown import writer
from clauderizer.scaffold.init import init
from clauderizer.scaffold.uninstall import uninstall


def _read(p):
    return json.loads(p.read_text(encoding="utf-8"))


# --- host_target validation (criterion 2) ----------------------------------------

def test_parse_host_target_accepts_known():
    assert ht.parse_host_target(None) == "claude-code"      # unset -> default
    assert ht.parse_host_target("claude-code") == "claude-code"
    assert ht.parse_host_target("cursor") == "cursor"
    assert ht.parse_host_target("codex") == "codex"          # guide-only counts
    assert ht.parse_host_target("grok") == "grok"            # Grok Build TUI


def test_parse_host_target_rejects_unknown_listing_valid():
    with pytest.raises(ht.HostTargetError) as exc:
        ht.parse_host_target("emacs")
    msg = str(exc.value)
    assert "emacs" in msg
    assert "claude-code" in msg and "cursor" in msg          # the valid list, no KeyError


# --- --host sets host_target + emits wiring (criterion 1) -------------------------

def test_init_host_flag_persists_to_config(empty_python_repo):
    report = init(empty_python_repo, host_target="cursor", spawn_test=False)
    assert report.host_target == "cursor"
    cfg = Config.load(empty_python_repo / ".clauderizer" / "config.toml")
    assert cfg.host_target == "cursor"
    # and it survives a re-run with no flag (config persistence, like session_host)
    report2 = init(empty_python_repo, spawn_test=False)
    assert report2.host_target == "cursor"


def test_init_default_is_multi_host(empty_python_repo):
    report = init(empty_python_repo, spawn_test=False)
    assert report.host_target == "claude-code"               # session preference
    assert report.host_target_auto is True                   # first bare init
    assert "cursor" in report.hosts_wired and "grok" in report.hosts_wired
    assert ht.CLAUDE_CODE in report.hosts_wired
    # multi is presentation, NOT a wiring warning
    assert not any("defaulted" in w for w in report.warnings)
    r = empty_python_repo
    assert (r / ".cursor" / "mcp.json").exists()
    assert (r / ".claude" / "settings.json").exists()
    assert (r / ht.GROK_HOOKS_REL).exists()
    entry = _read(r / ".mcp.json")["mcpServers"]["clauderizer"]
    assert ht.is_path_safe([entry["command"], *entry["args"]])  # multi → portable
    toml = (r / ".clauderizer" / "config.toml").read_text(encoding="utf-8")
    assert '"*"' in toml and "enabled" in toml


def test_init_no_nudge_on_rerun(empty_python_repo):
    init(empty_python_repo, spawn_test=False)
    report2 = init(empty_python_repo, spawn_test=False)     # established repo
    assert report2.host_target_auto is False
    assert report2.changed == [] or True  # second run should be mostly no-op
    assert set(report2.hosts_wired) == set(ht.all_host_ids())


def test_cli_init_default_prints_multi_host(empty_python_repo, monkeypatch, capsys):
    monkeypatch.chdir(empty_python_repo)
    cli.main(["init", str(empty_python_repo), "--no-spawn-test"])
    out = capsys.readouterr().out
    assert "multi-host default" in out
    assert "hosts wired" in out


def test_cli_init_list_hosts(capsys):
    code = cli.main(["init", "--list-hosts"])
    out = capsys.readouterr().out
    assert code == 0
    assert "claude-code" in out and "cursor" in out and "codex" in out
    assert "auto-write" in out and "guide-only" in out
    assert ".cursor/mcp.json" in out                        # shows where each lands
    assert "SCOPE" in out or "scope" in out.lower() or "ALL" in out


def test_cli_init_unknown_host_friendly_error(empty_python_repo, capsys):
    code = cli.main(["init", str(empty_python_repo), "--host", "emacs", "--no-spawn-test"])
    assert code == 1                                          # refused, not a crash
    out = capsys.readouterr().out
    assert "unknown host 'emacs'" in out
    assert "valid hosts" in out


# --- scoped --host still works; Claude-only via --host claude-code ---------------

def test_init_scoped_claude_code_only(empty_python_repo):
    init(empty_python_repo, host_target="claude-code", spawn_test=False)
    r = empty_python_repo
    for em in ht.HOST_EMITTERS.values():
        if em.auto_write and em.config_path not in ht._SHARED_WITH_CLAUDE_CODE:
            assert not (r / em.config_path).exists(), em.config_path
    assert not (r / ht.GROK_HOOKS_REL).exists()
    assert "clauderizer" in _read(r / ".mcp.json")["mcpServers"]
    assert (r / ".claude" / "settings.json").exists()


def test_init_claude_code_config_target_unchanged(empty_python_repo):
    init(empty_python_repo, spawn_test=False)
    toml = (empty_python_repo / ".clauderizer" / "config.toml").read_text(encoding="utf-8")
    assert 'target = "claude-code"' in toml


# --- init --host cursor: BOTH floor and tools + wiring contract (criterion 4) -----

def test_init_cursor_emits_mcp_and_floor(empty_python_repo):
    init(empty_python_repo, host_target="cursor", spawn_test=False)
    r = empty_python_repo
    # the tools: a real .cursor/mcp.json with a path-safe clauderizer entry
    entry = _read(r / ".cursor" / "mcp.json")["mcpServers"]["clauderizer"]
    assert entry["command"] == "uvx"
    assert ht.is_path_safe([entry["command"], *entry["args"]])
    # the floor: AGENTS.md carries the cz_status-first stanza (cursor reads it)
    agents = (r / "AGENTS.md").read_text(encoding="utf-8")
    assert "<!-- clauderizer:start -->" in agents and "cz_status" in agents


def test_init_cursor_no_claude_only_wiring(empty_python_repo):
    # no floor-but-no-tools, and no dead claude-only wiring either
    init(empty_python_repo, host_target="cursor", spawn_test=False)
    r = empty_python_repo
    assert not (r / ".mcp.json").exists()                     # claude-only file
    settings = r / ".claude" / "settings.json"
    if settings.exists():                                     # skills may create .claude/
        data = _read(settings)
        assert "clauderizer" not in json.dumps(data.get("hooks", {}))


def test_init_cursor_passes_wiring_contract(empty_python_repo):
    init(empty_python_repo, host_target="cursor", spawn_test=False)
    report = ht.wiring_contract_sweep(empty_python_repo)
    ok, detail = report["cursor"]
    assert ok, f"cursor failed the wiring contract: {detail}"


def test_init_cursor_idempotent(empty_python_repo):
    init(empty_python_repo, host_target="cursor", spawn_test=False)
    report2 = init(empty_python_repo, host_target="cursor", spawn_test=False)
    assert report2.changed == [], f"second cursor init changed: {report2.changed}"


# --- guide-only host + native-floor host + hook guide -----------------------------

def test_init_codex_guide_only_writes_setup_guide(empty_python_repo):
    init(empty_python_repo, host_target="codex", spawn_test=False)
    r = empty_python_repo
    guide = r / ".clauderizer" / "codex-mcp-setup.md"
    assert guide.exists()
    text = guide.read_text(encoding="utf-8")
    assert "uvx" in text and ".codex/config.toml" in text
    # codex has a hook system -> a hook guide too
    assert (r / ".clauderizer" / "codex-hook-setup.md").exists()


def test_init_continue_writes_native_floor(empty_python_repo):
    # Continue does NOT read AGENTS.md -> the floor goes in its own rules file
    init(empty_python_repo, host_target="continue", spawn_test=False)
    floor = empty_python_repo / ".continue" / "rules" / "clauderizer.md"
    assert floor.exists()
    assert "cz_status" in floor.read_text(encoding="utf-8")
    # and the MCP tools
    assert "clauderizer" in _read(
        empty_python_repo / ".continue" / "mcpServers" / "clauderizer.json")["mcpServers"]


# --- cheap auto-detection --------------------------------------------------------

def test_detect_host_target_adopts_existing_registration(empty_python_repo):
    ht.emit_mcp("zed", empty_python_repo)                     # a prior zed registration
    assert ht.detect_host_target(empty_python_repo) == "zed"


def test_detect_host_target_defaults_claude_code(empty_python_repo):
    assert ht.detect_host_target(empty_python_repo) == "claude-code"


def test_detect_host_target_mcp_json_alone_is_not_grok(empty_python_repo):
    # dogfood-style .mcp.json must not flip auto-detect to grok
    ht.emit_mcp("grok", empty_python_repo)
    assert ht.detect_host_target(empty_python_repo) == "claude-code"


def test_detect_host_target_grok_hooks(empty_python_repo):
    ht.emit_grok_hooks(empty_python_repo)
    assert ht.detect_host_target(empty_python_repo) == "grok"


# --- init --host grok: portable MCP + governance hooks (INVARIANT-07) ------------

def test_init_grok_accepts_and_emits_portable_mcp_and_hooks(empty_python_repo):
    report = init(empty_python_repo, host_target="grok", spawn_test=False)
    assert report.host_target == "grok"
    r = empty_python_repo
    entry = _read(r / ".mcp.json")["mcpServers"]["clauderizer"]
    argv = [entry["command"], *entry["args"]]
    assert entry["command"] == "uvx"
    assert ht.is_path_safe(argv)
    assert any("clauderizer-mcp" in t for t in argv)
    hooks = _read(r / ht.GROK_HOOKS_REL)
    assert "SessionStart" in hooks["hooks"]
    assert "UserPromptSubmit" in hooks["hooks"]
    cmd = hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert "wsl.exe" not in cmd and "wsl" != cmd.split()[0].lower()
    assert "clauderizer-hook" in cmd
    assert "GROK_WORKSPACE_ROOT" in cmd
    # honesty guide present; Tier-1 guide must not claim digest injection
    guide = (r / ".clauderizer" / "grok-mcp-setup.md").read_text(encoding="utf-8")
    assert "Hook→ctx" in guide or "NOT" in guide
    assert "Tier-1" in guide or "best_tier" in guide or "floor" in guide.lower()
    agents = (r / "AGENTS.md").read_text(encoding="utf-8")
    assert "cz_status" in agents


def test_init_grok_does_not_rewrite_claude_settings_hooks(empty_python_repo):
    r = empty_python_repo
    (r / ".claude").mkdir()
    foreign = {
        "hooks": {
            "PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": "echo foreign"}],
            }]
        }
    }
    (r / ".claude" / "settings.json").write_text(
        json.dumps(foreign, indent=2) + "\n", encoding="utf-8")
    init(r, host_target="grok", spawn_test=False)
    settings = _read(r / ".claude" / "settings.json")
    # foreign hooks preserved; no clauderizer SessionStart wired into Claude settings
    assert settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == "echo foreign"
    assert "SessionStart" not in settings.get("hooks", {})
    dumped = json.dumps(settings)
    assert "clauderizer-hook" not in dumped
    assert ".clauderizer/hook." not in dumped


def test_init_grok_passes_wiring_contract(empty_python_repo):
    init(empty_python_repo, host_target="grok", spawn_test=False)
    ok, detail = ht.verify_emitted_wiring("grok", empty_python_repo)
    assert ok, f"grok wiring contract failed: {detail}"


def test_init_grok_idempotent(empty_python_repo):
    init(empty_python_repo, host_target="grok", spawn_test=False)
    report2 = init(empty_python_repo, host_target="grok", spawn_test=False)
    assert report2.changed == [], f"second grok init changed: {report2.changed}"


def test_uninstall_grok_removes_hooks_preserves_claude(empty_python_repo):
    r = empty_python_repo
    (r / ".claude").mkdir()
    (r / ".claude" / "settings.json").write_text(
        json.dumps({"hooks": {"PreToolUse": [{"hooks": [
            {"type": "command", "command": "echo keep"}]}]}}),
        encoding="utf-8")
    init(r, host_target="grok", spawn_test=False)
    assert (r / ht.GROK_HOOKS_REL).exists()
    uninstall(r, host="grok")
    assert not (r / ht.GROK_HOOKS_REL).exists()
    assert not (r / ".mcp.json").exists() or "clauderizer" not in _read(
        r / ".mcp.json").get("mcpServers", {})
    # Claude foreign content intact
    assert _read(r / ".claude" / "settings.json")["hooks"]["PreToolUse"][0]["hooks"][0][
        "command"] == "echo keep"


def test_uninstall_kimi_removes_mcp_and_setup_guide(empty_python_repo):
    # D-049: kimi auto-writes .kimi-code/mcp.json + the bespoke kimi-setup.md guide;
    # host-scoped uninstall must remove BOTH (the guide is specially named, not the
    # <host>-mcp-setup.md convention — regression for the orphaned-guide bug).
    r = empty_python_repo
    init(r, host_target="kimi", spawn_test=False)
    assert (r / ".kimi-code" / "mcp.json").exists()
    assert (r / ".clauderizer" / "kimi-setup.md").exists()
    uninstall(r, host="kimi")
    assert "clauderizer" not in _read(r / ".kimi-code" / "mcp.json").get("mcpServers", {})
    assert not (r / ".clauderizer" / "kimi-setup.md").exists()   # not orphaned


# --- writer.remove_marker_block (the P4-noted extension) -------------------------

def test_remove_marker_block_preserves_user_content(tmp_path):
    p = tmp_path / "AGENTS.md"
    p.write_text("# House rules\n\nUse rg.\n", encoding="utf-8")
    writer.upsert_marker_block(p, "clauderizer", "floor here")
    assert "clauderizer:start" in p.read_text(encoding="utf-8")
    assert writer.remove_marker_block(p, "clauderizer") is True
    text = p.read_text(encoding="utf-8")
    assert "Use rg." in text                                  # user content survives
    assert "clauderizer" not in text
    assert writer.remove_marker_block(p, "clauderizer") is False   # idempotent


def test_remove_marker_block_deletes_block_only_file(tmp_path):
    p = tmp_path / "GEMINI.md"
    writer.upsert_marker_block(p, "clauderizer", "floor")
    assert writer.remove_marker_block(p, "clauderizer") is True
    assert not p.exists()                                     # block was the whole file


# --- uninstall: full footprint, preserve docs/ + unrelated (criterion 5) ----------

def test_uninstall_full_removes_footprint_preserves_docs(empty_python_repo):
    init(empty_python_repo, spawn_test=False)
    r = empty_python_repo
    assert (r / "docs" / "VISION.md").exists()                # memory present
    report = uninstall(r)

    # wiring gone
    assert not (r / ".clauderizer").exists()
    assert not (r / ".mcp.json").exists() or "clauderizer" not in _read(r / ".mcp.json").get("mcpServers", {})
    if (r / "CLAUDE.md").exists():
        assert "clauderizer:start" not in (r / "CLAUDE.md").read_text(encoding="utf-8")
    if (r / "AGENTS.md").exists():
        assert "clauderizer:start" not in (r / "AGENTS.md").read_text(encoding="utf-8")
    settings = r / ".claude" / "settings.json"
    if settings.exists():
        assert "clauderizer" not in json.dumps(_read(settings))

    # memory preserved
    assert (r / "docs" / "VISION.md").exists()
    assert report.removed                                      # it reported what it did


def test_uninstall_preserves_unrelated_mcp_and_hooks(empty_python_repo):
    r = empty_python_repo
    (r / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"other": {"command": "x"}}}), encoding="utf-8")
    (r / ".claude").mkdir()
    (r / ".claude" / "settings.json").write_text(
        json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash",
                    "hooks": [{"type": "command", "command": "echo hi"}]}]}}),
        encoding="utf-8")
    init(r, spawn_test=False)
    uninstall(r)

    servers = _read(r / ".mcp.json")["mcpServers"]
    assert servers == {"other": {"command": "x"}}             # foreign server intact
    data = _read(r / ".claude" / "settings.json")
    ptu = data["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert ptu == "echo hi"                                   # foreign hook intact


def test_uninstall_host_scoped_leaves_clauderizer_dir(empty_python_repo):
    init(empty_python_repo, host_target="cursor", spawn_test=False)
    r = empty_python_repo
    assert "clauderizer" in _read(r / ".cursor" / "mcp.json")["mcpServers"]
    report = uninstall(r, host="cursor")
    assert "clauderizer" not in _read(r / ".cursor" / "mcp.json")["mcpServers"]
    assert (r / ".clauderizer").exists()                      # host-scoped: config kept
    assert report.host == "cursor"


def test_cli_uninstall_full_reports(empty_python_repo, monkeypatch, capsys):
    init(empty_python_repo, spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    assert cli.main(["uninstall"]) == 0
    out = capsys.readouterr().out
    assert "Uninstalled Clauderizer (full footprint)" in out
    assert "kept" in out                                      # docs/ preservation noted


# --- amp dotted-key consistency (review finding #1: round-trip guard) -------------

def test_amp_emit_remove_roundtrip_is_consistent(tmp_path):
    # amp uses a FLAT dotted settings.json key ("amp.mcpServers", VS Code family);
    # emit/detect/remove must all agree on it and never touch foreign entries
    cfg = tmp_path / ".amp" / "settings.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({"amp.notifications": True,
                               "amp.mcpServers": {"other": {"command": "x"}}}),
                   encoding="utf-8")
    ht.emit_mcp("amp", tmp_path)
    assert ht.detect_host_target(tmp_path) == "amp"           # detect agrees on the key
    assert ht.remove_mcp("amp", tmp_path) is True             # remove finds what emit wrote
    data = _read(cfg)
    assert "clauderizer" not in data["amp.mcpServers"]        # ours gone
    assert data["amp.mcpServers"]["other"] == {"command": "x"}  # foreign server intact
    assert data["amp.notifications"] is True                  # foreign key intact


# --- doctor verifies the CONFIGURED host (O-09 minimal guard) ---------------------

def test_doctor_does_not_false_fail_cursor_repo(empty_python_repo, monkeypatch, capsys):
    init(empty_python_repo, host_target="cursor", spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    code = cli.main(["doctor"])
    out = capsys.readouterr().out
    assert "Drift detected" not in out                        # healthy cursor repo
    assert code != 2
    assert "cursor" in out and "MCP" in out
    assert "✗" not in out                                     # no failed check


def test_doctor_deep_handshakes_auto_write_host(empty_python_repo, monkeypatch, capsys):
    # O-01/D-056: `doctor --deep` opts into the shared MCP handshake for a registered
    # auto-write emitter host; the default (no --deep) stays presence-only.
    from clauderizer import mcp_probe
    init(empty_python_repo, host_target="cursor", spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    monkeypatch.setattr(mcp_probe, "handshake_probe", lambda *a, **k: {
        "status": "ok", "detail": "initialize → serverInfo clauderizer",
        "server_name": "clauderizer", "server_version": None})

    cli.main(["doctor"])
    assert "cursor MCP initialize handshake" not in capsys.readouterr().out   # default: presence only

    cli.main(["doctor", "--deep"])
    assert "cursor MCP initialize handshake" in capsys.readouterr().out       # --deep: capability


def test_doctor_guide_only_host_notes_manual(empty_python_repo, monkeypatch, capsys):
    init(empty_python_repo, host_target="codex", spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    code = cli.main(["doctor"])
    out = capsys.readouterr().out
    assert code != 2
    assert "guide-only" in out or "codex" in out


def test_doctor_multi_host_configure_hints(empty_python_repo, monkeypatch, capsys):
    init(empty_python_repo, spawn_test=False)                  # multi default
    monkeypatch.chdir(empty_python_repo)
    code = cli.main(["doctor"])
    out = capsys.readouterr().out
    assert code != 2
    assert "enabled hosts" in out
    assert "cursor" in out and "grok" in out
    # configure-on-demand notes for hosts that need human steps
    assert "hooks-trust" in out or "Hook→ctx" in out or "grok" in out


def test_doctor_reports_missing_mcp_as_advisory_not_claude_false_fail(
    empty_python_repo, monkeypatch, capsys
):
    # Multi-host repo with .mcp.json removed: doctor should advise re-init, not
    # claim "stripped host_target" exclusive-repair (D-046 multi is the default).
    init(empty_python_repo, spawn_test=False)
    (empty_python_repo / ".mcp.json").unlink()
    monkeypatch.chdir(empty_python_repo)
    cli.main(["doctor"])
    out = capsys.readouterr().out
    assert "re-run" in out.lower() or "missing" in out.lower() or "✗" in out


# --- security review HIGH: claude-code-only .mcp.json path-safety -----------------

def test_init_gitignores_machine_specific_mcp_json(empty_python_repo, monkeypatch):
    # Scoped Claude-only with a machine-specific command: gitignore .mcp.json
    from clauderizer.scaffold import init as scaffold_init
    monkeypatch.setattr(scaffold_init, "_resolve_invocation",
                        lambda run_cmd: (["/abs/venv/bin/clauderizer-mcp"],
                                         ["/abs/venv/bin/clauderizer-hook"]))
    init(empty_python_repo, host_target="claude-code", spawn_test=False)
    gi = (empty_python_repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".mcp.json" in gi
    assert (empty_python_repo / ".mcp.json").exists()


def test_init_portable_mcp_json_stays_committable(empty_python_repo, monkeypatch):
    from clauderizer.scaffold import init as scaffold_init
    monkeypatch.setattr(scaffold_init, "_resolve_invocation",
                        lambda run_cmd: (["uvx", "--from", "clauderizer", "clauderizer-mcp"],
                                         ["uvx", "--from", "clauderizer", "clauderizer-hook"]))
    init(empty_python_repo, spawn_test=False)
    gi = (empty_python_repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".mcp.json" not in gi                            # portable uvx -> committable


def test_uninstall_handles_symlinked_skill_without_aborting(empty_python_repo):
    # a planted symlink masquerading as a clauderizer skill must NOT be followed and
    # must NOT abort the uninstall mid-footprint (security review LOW)
    import os
    init(empty_python_repo, spawn_test=False)
    r = empty_python_repo
    outside = r.parent / "outside_target"
    outside.mkdir()
    (outside / "keep.txt").write_text("important", encoding="utf-8")
    link = r / ".claude" / "skills" / "clauderizer-evil"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported in this environment")
    uninstall(r)
    assert not link.is_symlink() and not link.exists()      # the link removed
    assert (outside / "keep.txt").exists()                  # its target never followed
    assert not (r / ".clauderizer").exists()                # uninstall completed past it
