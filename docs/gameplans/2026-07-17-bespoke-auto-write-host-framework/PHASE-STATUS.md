# bespoke-auto-write-host-framework — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-17

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Extract host-agnostic MCP-verification + command-composition primitives | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | BespokeHost protocol + registry; port kimi-desktop as first implementation | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Rewire entry points to the registry; offer the handshake to the generic host path | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Extension recipe doc + CHANGELOG + cascade + close-out | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
extracted-primitive-modules: Two new host-agnostic modules. src/clauderizer/winhost.py: WIN_EXE, WIN_EXE_SUBPATHS, win_path_to_wsl, windows_profile_from_cfg, win_exe_candidates (Windows/WSL command composition). src/clauderizer/mcp_probe.py: PROTOCOL_VERSION, HANDSHAKE_TIMEOUT, init_request, spawn_target, server_info, default_run, handshake_probe (MCP initialize-handshake capability probe; returns dict {status,detail,server_name,server_version}; imports winhost for C:\→/mnt translation). kimidesktop.server_entry now calls winhost.win_exe_candidates/WIN_EXE; cli.cmd_doctor calls mcp_probe.handshake_probe. Tests: tests/test_winhost.py (7), tests/test_mcp_probe.py (9); kimi handshake-primitive tests removed from test_kimidesktop, doctor-integration tests repointed to monkeypatch mcp_probe.handshake_probe. Suite 873→880 passed.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
