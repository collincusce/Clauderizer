"""Tests for the engine-hardening fixes surfaced by real-world dogfooding:

- #1 doctor checks command *executability*, not just registration presence
- #2 profile.lock.toml is read back as a per-project command override
- #4 init hook wiring is idempotent across a changed invocation (no duplicates)
- #6 cz_next_phase_context / handoff.assemble(write=False) is side-effect-free
- #8 the first real entry replaces a scaffold placeholder instead of stacking
"""
import json
import sys
from pathlib import Path

from clauderizer import cli
from clauderizer import config as cfg
from clauderizer import paths as P
from clauderizer.markdown import sections as S
from clauderizer.profiles import detect
from clauderizer.rituals import handoff
from clauderizer.scaffold import init as scaffold_init
from clauderizer.scaffold.init import _register_hook, _resolve_invocation


# --- #8 placeholder replacement ----------------------------------------------

def test_append_replaces_scaffold_placeholder():
    body = "## Risks\n\n_(Add risks here. Each: context, severity, mitigation.)_\n"
    out = S.append_to_section(body, "Risks", "### H-01 — first")
    assert "_(Add risks here" not in out
    assert "### H-01 — first" in out
    # subsequent entries accumulate; the first is not dropped
    out2 = S.append_to_section(out, "Risks", "### H-02 — second")
    assert "### H-01 — first" in out2 and "### H-02 — second" in out2


# --- #2 profile.lock overlay -------------------------------------------------

def test_load_for_repo_overlays_lock(tmp_path):
    lock = tmp_path / "profile.lock.toml"
    lock.write_text('profile = "python"\n[commands]\ntest = "pytest -q --maxfail=1"\n', encoding="utf-8")
    prof = detect.load_for_repo("python", lock)
    assert prof.command("test") == "pytest -q --maxfail=1"  # project override wins
    # no lock -> packaged default
    assert detect.load_for_repo("python", tmp_path / "absent.toml").command("test") == "pytest -q"


def test_load_for_repo_ignores_empty_overrides(tmp_path):
    lock = tmp_path / "profile.lock.toml"
    lock.write_text('profile = "python"\n[commands]\ntest = ""\nlint = "ruff check src"\n', encoding="utf-8")
    prof = detect.load_for_repo("python", lock)
    assert prof.command("test") == "pytest -q"        # empty value ignored -> default kept
    assert prof.command("lint") == "ruff check src"   # non-empty value applied


# --- #6 read-only context fetch ----------------------------------------------

def test_assemble_write_false_is_side_effect_free(temp_repo):
    paths = P.resolve(temp_repo)
    config = cfg.Config.load(paths.config_file)
    res = handoff.assemble(paths, config, "2026-05-01-bootstrap", "99", write=False)
    assert res["written"] is False
    assert res["path"] is None
    # the merged view opens with the engine's marker block (D-008)
    assert res["handoff_md"].startswith("<!-- clauderizer:handoff:start -->")
    assert "# Phase 99 Handoff" in res["handoff_md"]
    handoff_file = paths.gameplan_dir("2026-05-01-bootstrap") / "handoffs" / "PHASE-99-HANDOFF.md"
    assert not handoff_file.exists()  # nothing written


def test_assemble_write_true_still_writes(temp_repo):
    paths = P.resolve(temp_repo)
    config = cfg.Config.load(paths.config_file)
    res = handoff.assemble(paths, config, "2026-05-01-bootstrap", "98")  # write defaults True
    assert res["written"] is True
    assert Path(res["path"]).exists()


# --- #4 init wiring idempotency + resolution ---------------------------------

def test_register_hook_replaces_on_invocation_change(tmp_path):
    settings = tmp_path / "settings.json"
    _register_hook(settings, ["uvx", "--from", "clauderizer", "clauderizer-hook"])
    _register_hook(settings, ["/venv/bin/clauderizer-hook"])  # re-run, different invocation
    data = json.loads(settings.read_text(encoding="utf-8"))
    cmds = [h["command"] for g in data["hooks"]["SessionStart"] for h in g["hooks"]]
    clauderizer = [c for c in cmds if "clauderizer-hook" in c]
    assert clauderizer == ["/venv/bin/clauderizer-hook"]  # replaced, not duplicated


def test_register_hook_preserves_others_and_is_idempotent(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps(
        {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "other-tool"}]}]}}
    ), encoding="utf-8")
    assert _register_hook(settings, ["clauderizer-hook"]) is True
    assert _register_hook(settings, ["clauderizer-hook"]) is False  # second run = no-op
    cmds = [h["command"] for g in json.loads(settings.read_text(encoding="utf-8"))["hooks"]["SessionStart"]
            for h in g["hooks"]]
    assert "other-tool" in cmds
    assert cmds.count("clauderizer-hook") == 1


def test_resolve_invocation_explicit_prefix():
    mcp, hook = _resolve_invocation(["uvx", "--from", "clauderizer"])
    assert mcp == ["uvx", "--from", "clauderizer", "clauderizer-mcp"]
    assert hook == ["uvx", "--from", "clauderizer", "clauderizer-hook"]


def test_resolve_invocation_prefers_scripts_next_to_interpreter(monkeypatch, tmp_path):
    # scripts sitting next to the running interpreter win — the reliable venv hit,
    # even when shutil.which would miss (bin dir off PATH).
    (tmp_path / "clauderizer-mcp").write_text("")
    (tmp_path / "clauderizer-hook").write_text("")
    monkeypatch.setattr(scaffold_init.sys, "executable", str(tmp_path / "python"))
    monkeypatch.setattr(scaffold_init.shutil, "which", lambda name: None)  # PATH misses
    mcp, hook = _resolve_invocation(None)
    assert mcp == [str(tmp_path / "clauderizer-mcp")]
    assert hook == [str(tmp_path / "clauderizer-hook")]


def test_resolve_invocation_falls_back_to_path_then_uvx(monkeypatch, tmp_path):
    # nothing next to the interpreter -> PATH lookup, then uvx.
    monkeypatch.setattr(scaffold_init.sys, "executable", str(tmp_path / "python"))
    monkeypatch.setattr(scaffold_init.shutil, "which", lambda name: f"/venv/bin/{name}")
    assert _resolve_invocation(None)[0] == ["/venv/bin/clauderizer-mcp"]
    monkeypatch.setattr(scaffold_init.shutil, "which", lambda name: None)
    assert _resolve_invocation(None)[0] == ["uvx", "-q", "--from", "clauderizer",
                                            "clauderizer-mcp"]


# --- #1 doctor command executability -----------------------------------------
# (the boolean _command_runnable grew into hosts.verify_wiring's three-state
# verdict in agent-autonomy Phase 2; the native branch keeps these semantics)

def test_native_verify_wiring_detects_missing_and_present():
    from clauderizer import hosts

    assert hosts.verify_wiring([sys.executable], "native").ok is True  # absolute, executable
    bad = hosts.verify_wiring(["definitely-not-a-real-binary-xyz123"], "native")
    assert bad.ok is False and "not found" in bad.detail
    assert hosts.verify_wiring(None, "native").ok is False
    assert hosts.verify_wiring(None, None).ok is False  # unrecorded host -> native rules


def test_mcp_and_hook_command_extraction(tmp_path):
    from clauderizer import hosts

    mcp_json = tmp_path / ".mcp.json"
    mcp_json.write_text(json.dumps(
        {"mcpServers": {"clauderizer": {"command": "uvx", "args": ["--from", "clauderizer", "clauderizer-mcp"]}}}
    ), encoding="utf-8")
    assert hosts.read_wiring(mcp_json) == ["uvx", "--from", "clauderizer", "clauderizer-mcp"]
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps(
        {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "uvx --from clauderizer clauderizer-hook"}]}]}}
    ), encoding="utf-8")
    assert cli._hook_command(settings) == ["uvx", "--from", "clauderizer", "clauderizer-hook"]
