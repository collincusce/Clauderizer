# Chat Handoff Index — 2026-07-09-multi-host-default-wiring

> Last updated: 2026-07-09
> Status: All 4 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 790

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
| 0 | Model: wiring set vs session routing | ✅ COMPLETE | 2026-07-09 | 2026-07-09 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Config + emit multi-host default | ✅ COMPLETE | 2026-07-09 | 2026-07-09 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Runtime session-agent detection + bootstrap safety | ✅ COMPLETE | 2026-07-09 | 2026-07-09 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Doctor configure-on-demand + uninstall/docs/ship | ✅ COMPLETE | 2026-07-09 | 2026-07-09 | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-09

Locked multi-host model: bare init wires all project-level hosts; --host scopes; runtime detect for bootstrap; configure-on-demand advisories. O-01–O-03 resolved. D-046/D-047/D-048 already project-scoped.

### Phase 1 — completed 2026-07-09

Config.enabled_hosts + bare init multi-emit; --host scopes; multi uses portable [mcp] .mcp.json; Claude hooks retained; suite green.

### Phase 2 — completed 2026-07-09

session.detect_session_agent + effective_host_target; mcp_server uses effective; multi-safe unknown never suppresses P7.

### Phase 3 — completed 2026-07-09

Doctor multi-host + configure checklist; README/docs teach multi default; CHANGELOG; full suite green. Ship version deferred (user).

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

### Category: Cross-host

**1.** Exclusive --host is the wrong default for multi-AI repos: wire all project-level hosts by default (enabled=["*"]), keep --host as a scope filter, detect the running agent for bootstrap, and surface configure-on-demand steps in doctor — never hard-block. Multi-host .mcp.json must be portable (clauderizer[mcp]); session_host-composed wsl.exe wiring stays Claude-only scoped dogfood. *(evidence: gameplan 2026-07-09-multi-host-default-wiring; D-046/D-047/D-048)* (promoted 2026-07-09: L-48)
