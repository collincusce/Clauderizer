"""Phase 1: the in-memory session-delivery signal + write-first self-correction.

Covers the new substrate (session.py) and its server seam (mcp_server._deliver_aware):
idempotent/re-entrant by construction, gated off for hook hosts (Claude Code parity,
INVARIANT-07), delivered at most once per session (INVARIANT-08).
"""

from __future__ import annotations

import pytest

from clauderizer import mcp_server, session
from clauderizer.config import Config
from clauderizer.ops import Op


@pytest.fixture(autouse=True)
def _reset_signal():
    session.reset()
    yield
    session.reset()


# --- the signal primitive --------------------------------------------------------

def test_signal_starts_clear_and_marks():
    assert session.status_delivered() is False
    session.mark_status_delivered()
    assert session.status_delivered() is True
    session.reset()
    assert session.status_delivered() is False


def test_hook_host_classification():
    for hooked in ("claude-code", "kimi", "copilot", "codex", "gemini-cli",
                   "windsurf", "cline", "amp"):
        assert session.delivers_status_via_hook(hooked) is True
    for hookless in ("continue", "zed", "cursor-gov", "totally-unknown"):
        assert session.delivers_status_via_hook(hookless) is False
    # unset -> default claude-code -> hook host (Claude Code parity, INVARIANT-07)
    assert session.delivers_status_via_hook(None) is True


def test_should_inject_gate():
    assert session.should_inject_on_write("claude-code") is False   # hook host
    assert session.should_inject_on_write("continue") is True        # hook-less, fresh
    session.mark_status_delivered()
    assert session.should_inject_on_write("continue") is False       # already delivered


def test_status_note_is_compact_one_line_and_points_to_cz_status():
    note = session.status_note("Phase 2 in progress")
    assert "cz_status" in note
    assert "Phase 2 in progress" in note
    assert "\n" not in note          # one line — D-027 trim-first
    assert len(note) < 300


def test_status_note_tolerates_empty_summary():
    note = session.status_note("")
    assert "cz_status" in note
    assert "  " not in note          # no doubled space from an empty tail


# --- the server seam: _deliver_aware --------------------------------------------

def _op(writes: bool):
    return Op(lambda **k: {"ok": True}, writes=writes)


def test_pure_read_passes_through_unwrapped():
    op = _op(writes=False)
    assert mcp_server._deliver_aware("cz_graph_query", op) is op.fn


def test_status_read_marks_delivered():
    wrapped = mcp_server._deliver_aware("cz_status", _op(writes=False))
    assert session.status_delivered() is False
    wrapped()
    assert session.status_delivered() is True


def test_write_first_injects_on_hookless_host(monkeypatch):
    monkeypatch.setattr(mcp_server, "_host_target", lambda: "continue")
    monkeypatch.setattr(mcp_server, "_status_summary", lambda: "Phase 1 in progress")
    wrapped = mcp_server._deliver_aware("cz_add_decision", _op(writes=True))

    result = wrapped(title="x")
    assert result["ok"] is True
    assert "cz_status" in result["clauderizer_status"]

    # idempotent: the second write must NOT re-inject (INVARIANT-08: once)
    assert "clauderizer_status" not in wrapped(title="y")


def test_write_silent_on_hook_host(monkeypatch):
    monkeypatch.setattr(mcp_server, "_host_target", lambda: "claude-code")
    wrapped = mcp_server._deliver_aware("cz_add_decision", _op(writes=True))
    # Claude Code parity — the hook delivers status, the server never does
    assert "clauderizer_status" not in wrapped(title="x")


def test_status_read_suppresses_later_write_injection(monkeypatch):
    monkeypatch.setattr(mcp_server, "_host_target", lambda: "continue")
    monkeypatch.setattr(mcp_server, "_status_summary", lambda: "s")
    read = mcp_server._deliver_aware("cz_status", _op(writes=False))
    write = mcp_server._deliver_aware("cz_add_output", _op(writes=True))
    read()                              # status already seen this session
    assert "clauderizer_status" not in write(phase="0", key="k", value="v")


# --- config: the third host axis -------------------------------------------------

def test_config_roundtrips_host_target(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text(Config(host_target="cursor").to_toml(), encoding="utf-8")
    assert Config.load(p).host_target == "cursor"


def test_config_missing_target_defaults_to_claude_code(tmp_path):
    # a pre-cross-host config (no [host] target) must load as claude-code: the
    # default preserves exact Claude Code behaviour (INVARIANT-07, back-compat).
    p = tmp_path / "config.toml"
    p.write_text('[clauderizer]\nversion = "1"\n[host]\nprofile = "python"\n',
                 encoding="utf-8")
    assert Config.load(p).host_target == "claude-code"


# --- idempotency / re-entrancy of the read tools (exit-criterion 1) --------------

def test_read_tools_idempotent_and_reentrant(temp_repo, monkeypatch):
    monkeypatch.chdir(temp_repo)
    from clauderizer import ops

    # idempotent: repeated calls return identical results (no hidden mutation)
    first = ops.cz_status()
    assert first["ok"] is True
    assert ops.cz_status() == first

    # re-entrant: interleaving other reads in any order does not perturb it, and
    # there is no dependence on hook-injected context (the signal is irrelevant to
    # what a read returns) — reset the signal and the same result still computes.
    ops.cz_graph_query()
    session.mark_status_delivered()
    assert ops.cz_status() == first
    session.reset()
    assert ops.cz_status() == first


# --- model-agnostic surface: no Claude-specific syntax (criteria 4/5, D-032) -----

def test_tool_surface_is_host_neutral():
    """Every cz_* tool description an agent reads must not assume Claude Code, so a
    GPT/Gemini/DeepSeek-driven agent on another host reads the same neutral
    instructions. D-032: the model-agnostic claim is a STATIC check, not a live
    multi-model eval. cz_mine_failures is the one documented exception — it mines
    Claude Code's own transcript format and is inherently host-specific."""
    from clauderizer.ops import REGISTRY

    host_specific_ok = {"cz_mine_failures"}
    leaks = []
    for name, spec in REGISTRY.items():
        if name in host_specific_ok:
            continue
        # strip the product name first — "Clauderizer"/"clauderize" contain
        # "Claude" as a substring and would false-positive.
        doc = (spec.fn.__doc__ or "").replace("Clauderizer", "").replace("clauderize", "")
        for token in ("Claude", "SessionStart", "UserPromptSubmit", ".claude"):
            if token in doc:
                leaks.append(f"{name}: {token!r}")
    assert not leaks, f"Claude-specific syntax in the portable tool surface: {leaks}"


def test_session_note_is_host_neutral():
    # the write-first note an agent sees on ANY host names the product (Clauderizer)
    # but must not name the HOST (Claude Code) — note "Clauderizer" contains
    # "Claude" as a substring, so strip it before the standalone-word check.
    note = session.status_note("Phase 1 in progress")
    assert "Claude Code" not in note
    assert "Claude" not in note.replace("Clauderizer", "")


# --- Tier-4 floor: the shared stanza is host-neutral (P2) ------------------------

def test_stanza_carries_host_neutral_floor():
    """The shared stanza (one template -> CLAUDE.md + AGENTS.md, L-16) must carry the
    Tier-4 floor: tell a hook-less host to call cz_status first, WITHOUT assuming a
    SessionStart hook delivered status (false on most hosts). INVARIANT-07: Claude
    Code still gets its digest via the hook, so this is strictly additive."""
    from pathlib import Path

    import clauderizer

    text = (Path(clauderizer.__file__).parent / "templates" / "claude_stanza.md").read_text(
        encoding="utf-8"
    )
    assert "call `cz_status` now, before anything else" in text   # the floor
    assert "many hosts have no session hook" in text              # host-neutral framing


# --- INVARIANT-07 guard: the wrapped surface still builds ------------------------

def test_wrapped_server_builds():
    pytest.importorskip("mcp")
    # FastMCP derives each tool's schema from the wraps-preserved signature at
    # registration; a wrapper that broke the signature would raise here. The
    # surface must still build with every tool intact.
    server = mcp_server.build_server()
    assert server is not None
