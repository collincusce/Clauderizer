# Chat Handoff Index — Clauderizer v1 Bootstrap

> Last updated: 2026-05-30
> Status: Phase 0 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 0

## Ending Protocol

1. Update PHASE-STATUS.md (status + outputs + corrections).
2. `cz_add_lesson` for anything new.
3. `cz_transition_status` on touched entities (fires cascade).
4. `cz_write_handoff` for the next phase.
5. Run exit verification; report the test count.

## Phase Status Table

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Bootstrap | ⬜ READY | — | — | handoffs/PHASE-0-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

_(None yet.)_

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

**3.** Markdown round-trip idempotency (apply-twice==apply-once) is the load-bearing test for every mutation.

**4.** Make init idempotent via marker blocks, key-scoped JSON merges, and exists-checks — never clobber user content.

**12.** Real-world dogfooding found every high-severity gap in integration/observability, not the core model — keep validating the drop-in on non-native-Linux happy paths.

### Category: Build

**1.** Keep the core dependency-free: a vendored frontmatter parser beats a PyYAML dep for a drop-in.

**2.** FastMCP may not structure deeply-nested tool returns — keep returns shallow; write big artifacts to disk.

**5.** Prefer vendoring a tiny parser over a dependency when portability is the point.

### Category: Observability

**6.** Health checks must verify capability, not just presence: `doctor` now probes that the MCP/hook command is actually executable — a green check on a non-launchable setup is worse than no check.

**11.** Hook failures must surface where the agent can see them: the SessionStart hook now prints errors to stdout (session context), never silently to stderr.

### Category: Integration

**7.** Write-only config is a silent footgun: profile.lock.toml was written but never read; per-project command overrides now overlay the packaged profile via detect.load_for_repo.

**8.** Drop-in wiring must fit non-uvx installs: init now prefers installed console scripts (venv/pipx) and only falls back to uvx, fixing the Windows->WSL/venv path.

**9.** Idempotency must hold across changed inputs, not just identical re-runs: re-running init with a different invocation now REPLACES the SessionStart hook instead of appending a duplicate.

### Category: Design

**10.** Name tools by their effect: a 'context fetch' must not mutate the tree. cz_next_phase_context now assembles the handoff in-memory (write=False) and only cz_write_handoff persists.
