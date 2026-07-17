# Chat Handoff Index — kimi-desktop-unc-recovery-playbook

> Last updated: 2026-07-17
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 0

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
| 0 | Agent-recovery guide + doctor warning for the WSL/UNC combo | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Ship 1.9.1, dogfood close, release | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-17

Shipped the agent-recovery playbook (D-054). Expanded the kimi-desktop setup guide with a 'shell/tools failing' section — the UNC-cwd cause, how to keep working via file tools + docs/, and the two real fixes (repo on Windows / Kimi Code CLI in WSL). init now emits that guide into .clauderizer/ whenever it detects the WSL-repo + Windows-desktop combo (so a spawn-broken agent can read its way out), plus a loud warning; doctor warns for the same combo. Fixed a stale module-docstring claim and f-string backslash escaping. Live-verified on this WSL+desktop machine: doctor printed the UNC warning, init emitted the 9-keyword playbook. Suite 837->840, fresh venv.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
