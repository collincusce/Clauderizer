# bespoke-auto-write-host-framework — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-17

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Extract host-agnostic MCP-verification + command-composition primitives | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | BespokeHost protocol + registry; port kimi-desktop as first implementation | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Rewire entry points to the registry; offer the handshake to the generic host path | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Extension recipe doc + CHANGELOG + cascade + close-out | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-3-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
extracted-primitive-modules: Two new host-agnostic modules. src/clauderizer/winhost.py: WIN_EXE, WIN_EXE_SUBPATHS, win_path_to_wsl, windows_profile_from_cfg, win_exe_candidates (Windows/WSL command composition). src/clauderizer/mcp_probe.py: PROTOCOL_VERSION, HANDSHAKE_TIMEOUT, init_request, spawn_target, server_info, default_run, handshake_probe (MCP initialize-handshake capability probe; returns dict {status,detail,server_name,server_version}; imports winhost for C:\→/mnt translation). kimidesktop.server_entry now calls winhost.win_exe_candidates/WIN_EXE; cli.cmd_doctor calls mcp_probe.handshake_probe. Tests: tests/test_winhost.py (7), tests/test_mcp_probe.py (9); kimi handshake-primitive tests removed from test_kimidesktop, doctor-integration tests repointed to monkeypatch mcp_probe.handshake_probe. Suite 873→880 passed.
```

### Phase 1 Outputs

```
bespoke-host-framework: src/clauderizer/bespoke_hosts.py: BespokeHost base class (variable members: id, opt_out_env, servers_key, server_name, candidate_configs, compose_entry, setup_guide, unservable_reason; shared lifecycle: detect_config, wire→{status,path,entry,changed,unservable,warnings}, self_heal, remove_registration) + generic merge_entry/remove_entry(servers_key,server_name) + _atomic_write_json + WSL_USERS_DIR/SERVER_NAME + BESPOKE_HOSTS dict registry + register(). kimidesktop.KimiDesktopHost(BespokeHost) is the first impl (id=kimi-desktop, opt_out=CLAUDERIZER_NO_KIMI_DESKTOP, servers_key=mcpServers; overrides call the existing server_entry/candidate_configs/setup_guide/_is_windows_side; UNC_GUIDANCE single-sourced). Module wire/self_heal/detect_config/merge_entry/remove_entry are now thin delegators to _HOST (wire/self_heal add back-compat windows_side via _compat). Tests: test_bespoke_hosts.py (6, incl. a full second-host lifecycle with a different servers_key proving genericity). Suite 880→886.
```

### Phase 2 Outputs

```
entry-points-rewired: init/doctor/status/uninstall now iterate bespoke_hosts.all_hosts() (NOT the raw registry — all_hosts() lazily imports the host impl modules so bootstrap is import-order-independent; a raw-dict iteration left the registry EMPTY in the real CLI, masked by conftest's autouse import → lesson #1). cli.py cmd_status: self_heal each; cmd_doctor: generic loop (self_heal→report→handshake→version-skew→unservable warn) using host.id/host.servers_key/heal['unservable']; scaffold/init.py + uninstall.py: generic wire/guide and remove_registration. O-01 resolved: doctor --deep opt-in handshakes registered HOST_EMITTERS hosts (presence-only by default, L-07). kimidesktop.unservable_reason now gates on _is_windows_side alone (matches old ungated doctor UNC warn). Live-verified: doctor byte-identical (registered/handshake/version-skew/UNC, exit 3), status wipe→restore. Suite 886→888.
```

### Phase 3 Outputs

```
docs-and-closeout: docs/CROSS-HOST.md: "Adding a bespoke auto-write host (D-056)" 4-step recipe (subclass BespokeHost → register + all_hosts import → inherit lifecycle → test); pinned by tests/test_bespoke_hosts.py::test_extension_recipe_names_the_real_api (L-55). CHANGELOG 1.10.0 entry gained a framework bullet (no version bump — folds into unreleased 1.10.0). Cascades resolved: subsys.scaffold-01 (3 deps), subsys.mcp-server-01 (2 deps) — all no-change-needed (behavior-preserving). Suite 889 passed, 5 skipped.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
