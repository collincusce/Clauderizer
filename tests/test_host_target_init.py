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


def test_init_default_host_is_claude_code_with_nudge(empty_python_repo):
    report = init(empty_python_repo, spawn_test=False)
    assert report.host_target == "claude-code"
    assert report.host_target_auto is True                  # CLI renders the nudge
    # the nudge is presentation, NOT a wiring warning (existing callers assert
    # report.warnings is empty on a clean init — lesson #6, don't pollute it)
    assert not any("defaulted" in w for w in report.warnings)


def test_init_no_nudge_on_rerun(empty_python_repo):
    init(empty_python_repo, spawn_test=False)
    report2 = init(empty_python_repo, spawn_test=False)     # established repo
    assert report2.host_target_auto is False


def test_cli_init_default_prints_nudge(empty_python_repo, monkeypatch, capsys):
    monkeypatch.chdir(empty_python_repo)
    cli.main(["init", str(empty_python_repo), "--no-spawn-test"])
    assert "defaulted to claude-code" in capsys.readouterr().out


def test_cli_init_list_hosts(capsys):
    code = cli.main(["init", "--list-hosts"])
    out = capsys.readouterr().out
    assert code == 0
    assert "claude-code" in out and "cursor" in out and "codex" in out
    assert "auto-write" in out and "guide-only" in out
    assert ".cursor/mcp.json" in out                        # shows where each lands


def test_cli_init_unknown_host_friendly_error(empty_python_repo, capsys):
    code = cli.main(["init", str(empty_python_repo), "--host", "emacs", "--no-spawn-test"])
    assert code == 1                                          # refused, not a crash
    out = capsys.readouterr().out
    assert "unknown host 'emacs'" in out
    assert "valid hosts" in out


# --- claude-code parity (criterion 3, INVARIANT-07) ------------------------------

def test_init_claude_code_writes_no_foreign_host_files(empty_python_repo):
    init(empty_python_repo, spawn_test=False)
    r = empty_python_repo
    # the default path writes the Claude Code wiring and NOTHING host-specific
    for em in ht.HOST_EMITTERS.values():
        if em.auto_write:
            assert not (r / em.config_path).exists(), em.config_path
    for rel in ht.NATIVE_INSTRUCTIONS.values():
        assert not (r / rel).exists(), rel
    assert not list((r / ".clauderizer").glob("*-hook-setup.md"))
    assert not list((r / ".clauderizer").glob("*-mcp-setup.md"))
    # the claude-code wiring is intact
    assert "clauderizer" in _read(r / ".mcp.json")["mcpServers"]
    assert (r / ".claude" / "settings.json").exists()


def test_init_claude_code_config_target_unchanged(empty_python_repo):
    init(empty_python_repo, spawn_test=False)
    toml = (empty_python_repo / ".clauderizer" / "config.toml").read_text(encoding="utf-8")
    assert 'target = "claude-code"' in toml                   # pre-P8 bytes preserved


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
    assert "cursor MCP config registers clauderizer" in out
    assert "✗" not in out                                     # no failed check


def test_doctor_guide_only_host_notes_manual(empty_python_repo, monkeypatch, capsys):
    init(empty_python_repo, host_target="codex", spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    code = cli.main(["doctor"])
    out = capsys.readouterr().out
    assert code != 2
    assert "guide-only" in out


def test_doctor_warns_on_stripped_host_target(empty_python_repo, monkeypatch, capsys):
    # The cross-version hazard observed live (P9): a pre-host_target engine or a
    # config hand-edit rewrites config.toml without [host] target -> it defaults
    # back to claude-code, but the repo is actually wired for cursor. Doctor must
    # name the RIGHT repair (init --host cursor), not bare init (which would wire
    # Claude Code).
    init(empty_python_repo, spawn_test=False)              # claude-code default
    (empty_python_repo / ".mcp.json").unlink()             # no Claude Code wiring
    ht.emit_mcp("cursor", empty_python_repo)               # but cursor IS wired
    monkeypatch.chdir(empty_python_repo)
    cli.main(["doctor"])
    out = capsys.readouterr().out
    assert "host_target was likely stripped" in out
    assert "init --host cursor" in out                     # the correct repair, named


# --- security review HIGH: claude-code .mcp.json path-safety -----------------------

def test_init_gitignores_machine_specific_mcp_json(empty_python_repo, monkeypatch):
    # a machine-specific .mcp.json command (venv path / wsl shim) is dead on any
    # other machine and leaks the author's path if committed — init must gitignore
    # the clauderizer-owned .mcp.json so it can't leak (O-06 / security review)
    from clauderizer.scaffold import init as scaffold_init
    monkeypatch.setattr(scaffold_init, "_resolve_invocation",
                        lambda run_cmd: (["/abs/venv/bin/clauderizer-mcp"],
                                         ["/abs/venv/bin/clauderizer-hook"]))
    init(empty_python_repo, spawn_test=False)
    gi = (empty_python_repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".mcp.json" in gi
    assert (empty_python_repo / ".mcp.json").exists()      # kept locally, just un-committed


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
