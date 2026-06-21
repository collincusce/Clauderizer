"""In-memory, per-process session-delivery signal (INVARIANT-08, P1).

The cross-host injection-parity ladder (D-034, docs/CROSS-HOST.md) must deliver the
Clauderizer status to the model **at most once per session**, across all active
tiers. On hook hosts (Claude Code, kimi, Copilot, Codex, ...) the host's own
lifecycle hook delivers it; on hook-less hosts (Cursor-if-governance, Continue,
Zed) the MCP server is the only automatic path — via the write-first
self-correction here and the Phase-7 bootstrap.

This module holds that signal: a process-global flag, **in memory only** — never
persisted, never a config/enable flag (INVARIANT-05/08). It is meaningful only
inside the long-lived MCP server process; the stateless ``clauderize ops`` CLI is
a fresh process per call (flag always False) and never injects, because the gate
below treats a hook host as the default and the CLI is not a model session.

The logic here is deliberately pure and IO-free so it is unit-testable on its own;
the server (mcp_server.py) supplies the live status string and applies the result.
"""

from __future__ import annotations

# Host targets whose own lifecycle hook already delivers the status digest. On
# these the server MUST stay silent — a second delivery would violate INVARIANT-08
# (at most once) and D-027 (trim-first). This is the code form of the
# docs/CROSS-HOST.md capability matrix; per-host hook *context-injection* semantics
# are confirmed when each emitter is built (Phase 4/5, open item O-02 residual).
_HOOK_HOSTS = frozenset(
    {
        "claude-code",
        "kimi",
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
