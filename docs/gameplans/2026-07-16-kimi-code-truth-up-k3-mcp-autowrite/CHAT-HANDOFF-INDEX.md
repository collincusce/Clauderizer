# Chat Handoff Index — kimi-code-truth-up-k3-mcp-autowrite

> Last updated: 2026-07-16
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 793

## Ending Protocol

1. `cz_transition_phase` the finished phase to complete.
2. `cz_add_output` each concrete produced value; `cz_add_phase_summary` the recap;
   `cz_add_correction` / `cz_add_lesson` as earned.
3. `cz_transition_status` on touched entities (fires cascade); `cz_resolve_cascade`
   the verdicts.
4. `cz_write_handoff` for the next phase.
5. Run exit verification; report the test count.

## Phase Status Table

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Confirm current Kimi Code CLI contract | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Flip kimi MCP to auto-write .kimi-code/mcp.json | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Reconcile kimi setup guides and fix stale .kimi paths | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Docs sweep, cascade, and release | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-16

Verified the current Kimi Code CLI contract against upstream docs and corrected the plan's premise. Kimi K3 is served by Kimi Code CLI (kimi-code, npm) — the successor to the legacy Kimi CLI (kimi-cli, pip). MCP is auto-writable via project .kimi-code/mcp.json (mcpServers key, Cursor-identical). Session-start hooks live in ~/.kimi-code/config.toml [[hooks]] with 13 events; the digest-relevant four (SessionStart/UserPromptSubmit/PreCompact/PostCompact) inject stdout on exit 0 — confirming the guide's event set, staying guide-only (TOML). Skills are NOT loaded from .claude/skills on kimi-code (it uses .kimi-code/skills, .agents/skills). Recorded correction C-01: per user decision, repoint the existing `kimi` host id to Kimi Code CLI (.kimi-code) treating legacy Kimi CLI as EOL, and document skills exposure in the setup guide rather than auto-emitting. Resolved open item O-01 (hook contract confirmed).

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** When a host's config paths look 'stale', confirm whether the host is one product that moved or two products (predecessor/successor) before renaming — Moonshot's kimi-cli (~/.kimi) and kimi-code (.kimi-code) are distinct tools, and the 'stale' path was correct for the legacy one.
