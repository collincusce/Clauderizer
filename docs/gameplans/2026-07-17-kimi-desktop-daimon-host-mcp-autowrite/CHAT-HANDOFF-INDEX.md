# Chat Handoff Index — kimi-desktop-daimon-host-mcp-autowrite

> Last updated: 2026-07-17
> Status: Phase 3 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 823

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
| 0 | Confirm the daimon runtime contract + design cross-platform detection | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Bespoke kimi-desktop detection + auto-write emitter | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Wire kimi-desktop into init, doctor, uninstall | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Docs, ship 1.9.0, dogfood close | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 1 — completed 2026-07-17

Built the bespoke kimidesktop emitter: cross-platform daimon runtime-home resolution (Windows/macOS/Linux + the WSL->Windows case), detected-only (never creates the app's dirs), non-destructive atomic merge (temp-write + os.replace), and a robust command — uvx resolved absolute, or wsl.exe -d <distro> -e bash -lc 'cd <repo> && uvx …' when init runs inside WSL against a Windows-side config (the user's actual setup). wire() returns a status + loud warnings (missing uvx, unknown distro). Everything injectable so 8 tests run against temp homes, never real per-user dirs (L-29), proving per-platform paths, both-direction detected-only/merge, the WSL wrapper, and surgical remove. Suite 823->831, green fresh venv.

### Phase 2 — completed 2026-07-17

Wired kimi-desktop into init (auto-write on detect, guide on write-failure, silent no-op when absent), doctor (reports registered/unwired/not-detected + loud uvx warning), and uninstall (surgical removal). A live dogfood against the real installed app caught a design flaw (C-01): the per-user config is one file for all repos, so the WSL cd-wrapper was repo-specific and a real init from a temp/test repo overwrote the user's config with a dead pointer. Fixed to a repo-agnostic command (server finds the open repo from the app cwd — the user's verified shape), added the CLAUDERIZER_NO_KIMI_DESKTOP opt-out + an autouse conftest guard so the suite never mutates real per-user state (verified untouched across the run), and cleaned up the real config. Real-machine E2E confirmed idempotent, no-pollution writes. Suite 837 passed, fresh venv.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** A host whose config is a single per-user file (shared across all repos) must get a REPO-AGNOSTIC server command — one that discovers the repo from the host's working directory — never a repo-pinned `cd <repo>` wrapper, or the last init wins and re-init from another repo silently repoints it. And any init/emit step that writes an absolute per-user path (outside the repo) is an L-29 test hazard: guard it behind an env opt-out and an autouse fixture so the suite never mutates real machine state — verify by asserting the real file is untouched after a full run.
