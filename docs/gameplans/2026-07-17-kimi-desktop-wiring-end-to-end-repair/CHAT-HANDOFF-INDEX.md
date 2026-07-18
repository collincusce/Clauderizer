# Chat Handoff Index — kimi-desktop-wiring-end-to-end-repair

> Last updated: 2026-07-17
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 840

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
| 0 | --repo / CLAUDERIZER_REPO repo decoupling in clauderizer-mcp | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Windows-native command composition (clauderizer-mcp.exe) | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Self-healing registration on every entry point | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Doctor MCP initialize-handshake smoke-test | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | WSL-hosted-repo UNC guidance instead of dead registration | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Docs + release close-out | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-17

Decoupled repo discovery from the process cwd — the primitive the whole gameplan needs. `ops.repo_ctx()` now resolves the served repo from `$CLAUDERIZER_REPO` when set (walking up to the `.clauderizer/config.toml` marker like cwd discovery does), else falls back to `Path.cwd()`; a non-clauderized override raises a RuntimeError that names the source and points at `clauderize init`. `clauderizer-mcp` gained a `--repo <path>` flag (`_parse_repo`, last-wins, `--repo X` and `--repo=X` forms) that `main()` exports into `$CLAUDERIZER_REPO` before building the server, so the CLI flag beats an inherited env var. The `--version`/`--help` deterministic probe path (D3) is preserved and `--help` documents the new flag.

This lets a host that cannot set the repo as its spawn cwd — a Windows desktop serving a `\\wsl.localhost` UNC repo it can't `cd` into (D-054/D-055) — still point the stateless server at the right repo, and lets Phase 3's doctor smoke-test spawn from a non-repo cwd. Scope kept tight: the transcripts-dir discovery (ops.py ~979, a separate telemetry concern) was intentionally left on cwd. 7 new tests in tests/test_repo_override.py; suite 840 → 847 passed, 5 skipped; verified end-to-end from /tmp.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
