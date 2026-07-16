"""In-memory, per-process session-delivery signal (INVARIANT-08, P1).

The cross-host injection-parity ladder (D-034, docs/CROSS-HOST.md) must deliver the
Clauderizer status to the model **at most once per session**, across all active
tiers. On hook hosts (Claude Code, Copilot, Codex, ...) the host's own
lifecycle hook delivers it; on hook-less hosts (Cursor-if-governance, Continue,
Zed, kimi — whose injecting hooks are guide-only, not auto-wired, D-050) the MCP
server is the only automatic path — via the write-first self-correction here and
the Phase-7 bootstrap.

This module holds that signal: a process-global flag, **in memory only** — never
persisted, never a config/enable flag (INVARIANT-05/08). It is meaningful only
inside the long-lived MCP server process; the stateless ``clauderize ops`` CLI is
a fresh process per call (flag always False) and never injects, because the gate
below treats a hook host as the default and the CLI is not a model session.

The logic here is deliberately pure and IO-free so it is unit-testable on its own;
the server (mcp_server.py) supplies the live status string and applies the result.
"""

from __future__ import annotations

import os

# Host targets whose own lifecycle hook already delivers the status digest. On
# these the server MUST stay silent — a second delivery would violate INVARIANT-08
# (at most once) and D-027 (trim-first). This is the code form of the
# docs/CROSS-HOST.md capability matrix; per-host hook *context-injection* semantics
# are confirmed when each emitter is built (Phase 4/5, open item O-02 residual).
#
# Grok Build TUI is intentionally ABSENT: it has lifecycle hooks, but passive
# SessionStart stdout is ignored (Hook→ctx=no). Putting "grok" here would
# suppress P7 server bootstrap and leave cold sessions dark (D1 / D-045).
#
# kimi (Kimi Code CLI) is ALSO absent (D-050): its hooks DO inject on exit 0, but
# Clauderizer cannot auto-wire them — its MCP is auto-written to .kimi-code/mcp.json
# while the hooks stay a guide (TOML in ~/.kimi-code/config.toml, zero-dep invariant).
# A default `clauderize init` kimi repo therefore has NO status-delivering hook, so
# the automatic path is the P7 server bootstrap; claiming auto hook-delivery here
# would risk the same dark-session trap as grok if kimi runtime detection is added.
# (Behaviorally inert today: a kimi session sets no marker → effective_host_target →
# "unknown" → bootstrap already fires. This keeps best_tier/delivers_status honest.)
_HOOK_HOSTS = frozenset(
    {
        "claude-code",
        "copilot",
        "codex",
        "gemini-cli",
        "windsurf",
        "cline",
        "amp",
    }
)

DEFAULT_HOST_TARGET = "claude-code"

# Hosts that surface MCP prompts as slash commands (Tier 3) but have no
# status-delivering hook — the prompt is a user-invoked convenience above the floor.
# (Cursor's hooks are governance-only, so it routes here.) docs/CROSS-HOST.md §4.
# Grok is ABSENT: slash sources are builtins + SKILL.md only (no MCP prompts →
# best_tier 4, not 3).
_PROMPT_HOSTS = frozenset({"cursor", "continue", "zed"})

# Module-global: has the status digest reached the model this server session?
_delivered = False


def mark_status_delivered() -> None:
    """Record that the status digest has reached the model this session."""
    global _delivered
    _delivered = True


def status_delivered() -> bool:
    """Whether status has already been delivered this session (read-only)."""
    return _delivered


def reset() -> None:
    """Test-only: clear the signal between cases. Never called in production —
    the flag's whole point is to persist for the life of the server process."""
    global _delivered
    _delivered = False


# --- runtime session-agent detection (D-047) ------------------------------------
# Wiring (which configs exist on disk) is multi-host. Bootstrap routing needs the
# agent driving THIS process. Prefer env markers; when unsure, return None so
# callers use multi-safe hook-less behavior (P7 on) rather than assuming Claude.

def detect_session_agent(env: dict[str, str] | None = None) -> str | None:
    """Best-effort id of the agent tool running this process, or None if unknown.

    Order is specific → general so Claude-compat env vars set by other hosts
    (e.g. Grok's CLAUDE_PROJECT_DIR for hooks) do not mis-route to claude-code.
    """
    e = env if env is not None else os.environ
    # Grok Build TUI
    if e.get("GROK_AGENT") or e.get("GROK_SESSION_ID") or e.get("GROK_WORKSPACE_ROOT"):
        return "grok"
    # Cursor
    if e.get("CURSOR_TRACE_ID") or e.get("CURSOR_AGENT") or e.get("CURSOR_SESSION_ID"):
        return "cursor"
    # OpenAI Codex CLI
    if e.get("CODEX_CI") or e.get("CODEX_THREAD_ID") or (e.get("TERM_PROGRAM") or "") == "codex":
        return "codex"
    # GitHub Copilot / VS Code agent (weak — only when agent-ish markers present)
    if e.get("COPILOT_AGENT") or e.get("GITHUB_COPILOT_TOKEN"):
        return "copilot"
    # Gemini CLI
    if e.get("GEMINI_CLI") or e.get("GEMINI_CLI_SESSION"):
        return "gemini-cli"
    # Claude Code (after Grok — Grok also sets CLAUDE_PROJECT_DIR for hook compat)
    if e.get("CLAUDECODE") or e.get("CLAUDE_CODE_ENTRYPOINT") or e.get("CLAUDE_CODE_SESSION"):
        return "claude-code"
    if e.get("CLAUDE_PROJECT_DIR") and not e.get("GROK_AGENT"):
        # Ambiguous alone (Grok sets it too) — only trust with other Claude signals
        if e.get("ANTHROPIC_API_KEY") or e.get("CLAUDE_CODE"):
            return "claude-code"
    return None


def effective_host_target(
    config_target: str | None = None,
    *,
    env: dict[str, str] | None = None,
) -> str:
    """Host id for injection routing this process (D-047).

    1. Runtime detection wins when confident.
    2. If detection is unknown, return a synthetic multi-safe id that is NOT in
       ``_HOOK_HOSTS`` so P7 bootstrap still fires — never suppress bootstrap
       solely because config.target is claude-code or Claude files exist on disk.
    3. Config target is only used when detection agrees or when an explicit
       non-default override is needed; unknown stays multi-safe.
    """
    detected = detect_session_agent(env)
    if detected:
        return detected
    # Multi-safe default: treat as hook-less (best_tier 4 path).
    # Callers that need the config preference for *display* still read config.
    _ = config_target  # reserved for future explicit session_agent override
    return "unknown"


def delivers_status_via_hook(host_target: str | None) -> bool:
    """True when the host's own lifecycle hook delivers the digest, so the server
    must NOT also inject.

    Unknown / unset hosts are treated as **hook-less** (return False) on purpose:
    the dangerous failure is going *dark* (no status at all), and an extra
    server-side note on a host that also has a hook is merely redundant. The
    default ``host_target`` is ``claude-code`` (a hook host), so an unconfigured
    repo keeps exact Claude Code behaviour — INVARIANT-07."""
    return (host_target or DEFAULT_HOST_TARGET) in _HOOK_HOSTS


def best_tier(host_target: str | None) -> int:
    """Highest injection tier the host supports (D-034 ladder): 1 = lifecycle hook
    (automatic), 3 = MCP prompt slash command (user-invoked), 4 = AGENTS.md floor
    (the universal minimum). Tier 2 (auto-loaded resource) was retired — no host
    has it. Unknown hosts downgrade safely to the floor (4)."""
    ht = host_target or DEFAULT_HOST_TARGET
    if ht in _HOOK_HOSTS:
        return 1
    if ht in _PROMPT_HOSTS:
        return 3
    return 4


def should_inject(host_target: str | None) -> bool:
    """The server-side bootstrap gate (P7): inject a compact status note onto the
    result of the FIRST non-status tool call this session — read OR write — but only
    when the host has no status-delivering hook AND nothing has delivered status yet.
    Idempotent: once delivered it never fires again (INVARIANT-08). The two
    status-delivering reads (cz_status, cz_next_phase_context) deliver status
    directly and just mark the signal, so they never need this."""
    return not delivers_status_via_hook(host_target) and not status_delivered()


def status_note(summary: str) -> str:
    """The compact bootstrap note (D-027: focused, one line, not the full digest).
    Surfaced on the first tool call of a session on a hook-less host — read OR write
    — so the agent is not operating blind. Neutral wording (the trigger may be
    either); points at cz_status for detail rather than dumping it inline."""
    summary = (summary or "").strip()
    tail = f" {summary}" if summary else ""
    return (
        "[Clauderizer] Project status was not loaded yet this session." + tail
        + " Call cz_status for the full picture before continuing."
    )
