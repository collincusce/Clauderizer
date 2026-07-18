# bespoke-auto-write-host-framework — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-17

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Extract host-agnostic MCP-verification + command-composition primitives | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | BespokeHost protocol + registry; port kimi-desktop as first implementation | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Rewire entry points to the registry; offer the handshake to the generic host path | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Extension recipe doc + CHANGELOG + cascade + close-out | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
extracted-primitive-modules: Two new host-agnostic modules. src/clauderizer/winhost.py: WIN_EXE, WIN_EXE_SUBPATHS, win_path_to_wsl, windows_profile_from_cfg, win_exe_candidates (Windows/WSL command composition). src/clauderizer/mcp_probe.py: PROTOCOL_VERSION, HANDSHAKE_TIMEOUT, init_request, spawn_target, server_info, default_run, handshake_probe (MCP initialize-handshake capability probe; returns dict {status,detail,server_name,server_version}; imports winhost for C:\→/mnt translation). kimidesktop.server_entry now calls winhost.win_exe_candidates/WIN_EXE; cli.cmd_doctor calls mcp_probe.handshake_probe. Tests: tests/test_winhost.py (7), tests/test_mcp_probe.py (9); kimi handshake-primitive tests removed from test_kimidesktop, doctor-integration tests repointed to monkeypatch mcp_probe.handshake_probe. Suite 873→880 passed.
```

### Phase 1 Outputs

```
bespoke-host-framework: src/clauderizer/bespoke_hosts.py: BespokeHost base class (variable members: id, opt_out_env, servers_key, server_name, candidate_configs, compose_entry, setup_guide, unservable_reason; shared lifecycle: detect_config, wire→{status,path,entry,changed,unservable,warnings}, self_heal, remove_registration) + generic merge_entry/remove_entry(servers_key,server_name) + _atomic_write_json + WSL_USERS_DIR/SERVER_NAME + BESPOKE_HOSTS dict registry + register(). kimidesktop.KimiDesktopHost(BespokeHost) is the first impl (id=kimi-desktop, opt_out=CLAUDERIZER_NO_KIMI_DESKTOP, servers_key=mcpServers; overrides call the existing server_entry/candidate_configs/setup_guide/_is_windows_side; UNC_GUIDANCE single-sourced). Module wire/self_heal/detect_config/merge_entry/remove_entry are now thin delegators to _HOST (wire/self_heal add back-compat windows_side via _compat). Tests: test_bespoke_hosts.py (6, incl. a full second-host lifecycle with a different servers_key proving genericity). Suite 880→886.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
