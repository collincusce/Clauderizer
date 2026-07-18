# Chat Handoff Index — bespoke-auto-write-host-framework

> Last updated: 2026-07-17
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 873

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
| 0 | Extract host-agnostic MCP-verification + command-composition primitives | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | BespokeHost protocol + registry; port kimi-desktop as first implementation | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Rewire entry points to the registry; offer the handshake to the generic host path | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Extension recipe doc + CHANGELOG + cascade + close-out | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-17

Extracted the two genuinely host-agnostic primitives out of `kimidesktop.py` into their own modules, behavior-preserving. `winhost.py` owns Windows/WSL command composition — the `clauderizer-mcp.exe` probing (`win_exe_candidates`, `WIN_EXE`) and the `C:\`↔`/mnt/<drive>` translation (`win_path_to_wsl`, `windows_profile_from_cfg`). `mcp_probe.py` owns the MCP `initialize`-handshake capability probe (`handshake_probe` + `spawn_target`/`server_info`/`default_run`), which takes a generic `{command, args}` entry and imports `winhost` for the cross-OS translation. `kimidesktop.server_entry` now calls `winhost.win_exe_candidates`; `cmd_doctor` calls `mcp_probe.handshake_probe`; the moved code and its now-unused `re`/`subprocess` imports are gone from `kimidesktop`.

Both primitives are now reusable by the coming BespokeHost framework (Phase 1) and by the HOST_EMITTERS per-host doctor path (Phase 2). Tests were reorganized to match the new module boundaries: `test_winhost.py` (7) and `test_mcp_probe.py` (9) unit-test the primitives directly; the doctor-integration tests in `test_kimidesktop.py` were repointed to monkeypatch `clauderizer.mcp_probe.handshake_probe`. Behavior-preservation proven two ways: the full suite stays green (873 → 880 passed, 5 skipped, +7 net), and a live read-only check reproduces the exact composition (`C:\Users\rafaj\...\clauderizer-mcp.exe`, `args:[]`, zero warnings) and a green handshake (serverInfo clauderizer 1.9.1) through the extracted modules. No dangling references to the moved symbols remain in src/.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
