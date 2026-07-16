# Chat Handoff Index — kimi-code-truth-up-k3-mcp-autowrite

> Last updated: 2026-07-16
> Status: All 4 phases complete

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
| 1 | Flip kimi MCP to auto-write .kimi-code/mcp.json | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Reconcile kimi setup guides and fix stale .kimi paths | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Docs sweep, cascade, and release | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-16

Verified the current Kimi Code CLI contract against upstream docs and corrected the plan's premise. Kimi K3 is served by Kimi Code CLI (kimi-code, npm) — the successor to the legacy Kimi CLI (kimi-cli, pip). MCP is auto-writable via project .kimi-code/mcp.json (mcpServers key, Cursor-identical). Session-start hooks live in ~/.kimi-code/config.toml [[hooks]] with 13 events; the digest-relevant four (SessionStart/UserPromptSubmit/PreCompact/PostCompact) inject stdout on exit 0 — confirming the guide's event set, staying guide-only (TOML). Skills are NOT loaded from .claude/skills on kimi-code (it uses .kimi-code/skills, .agents/skills). Recorded correction C-01: per user decision, repoint the existing `kimi` host id to Kimi Code CLI (.kimi-code) treating legacy Kimi CLI as EOL, and document skills exposure in the setup guide rather than auto-emitting. Resolved open item O-01 (hook contract confirmed).

### Phase 1 — completed 2026-07-16

Repointed the `kimi` HostEmitter to Kimi Code CLI: auto_write=True at .kimi-code/mcp.json under the mcpServers key (Cursor-identical). emit_mcp now writes a real project MCP config non-destructively; remove_mcp, detect_host_target, wiring_contract_sweep, and path_safety_audit all pick kimi up automatically (table-derived). Dropped kimi from the guide-only golden test and added four kimi auto-write/round-trip/detection tests. Suite green at 797 passed / 5 skipped.

### Phase 2 — completed 2026-07-16

Single-sourced the Kimi Code CLI setup guide in hosttargets.kimi_setup_guide() (portable KIMI_HOOK_COMMAND; the four digest-relevant events SessionStart/UserPromptSubmit/PreCompact/PostCompact) and emit it from emit_host_wiring('kimi') as .clauderizer/kimi-setup.md. Removed the dead claude-leg _render_kimi_setup/_KIMI_HOOK_EVENTS. Corrected every stale .kimi path (guide §3 → ~/.kimi-code/config.toml; configure_hints; paths.kimi_setup docstring) and added guide §4 documenting skills exposure (.agents/skills / .kimi-code/skills), since Kimi Code CLI ignores .claude/skills. Only the deliberate 'legacy Kimi CLI used ~/.kimi/' mention remains. Real init smoke confirmed .kimi-code/mcp.json + a correct guide.

### Phase 3 — completed 2026-07-16

Swept the present-tense docs (append-only history left intact per L-21): CROSS-HOST.md kimi row now reads auto (MCP) / guide (hooks TOML) at .kimi-code/mcp.json, with the footnote and §6 TOML table corrected; TRUST.md MCP-locations table repointed kimi to .kimi-code/mcp.json (mcpServers, auto-write); README init-footprint tree and configure-checklist wording updated. Added the CHANGELOG 1.7.0 entry and bumped pyproject 1.6.0 -> 1.7.0. Bumped subsys.scaffold 0.10.0 -> 0.11.0 and resolved the cascade over its three dependents (all additive, ^ pins satisfied). Suite green at 797 passed / 5 skipped. The only remaining ~/.kimi/ mention is D-031's append-only ADR context, which D-049 supersedes.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** When a host's config paths look 'stale', confirm whether the host is one product that moved or two products (predecessor/successor) before renaming — Moonshot's kimi-cli (~/.kimi) and kimi-code (.kimi-code) are distinct tools, and the 'stale' path was correct for the legacy one.
