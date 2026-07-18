# Chat Handoff Index — bespoke-auto-write-host-framework

> Last updated: 2026-07-17
> Status: All 4 phases complete

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
| 1 | BespokeHost protocol + registry; port kimi-desktop as first implementation | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Rewire entry points to the registry; offer the handshake to the generic host path | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Extension recipe doc + CHANGELOG + cascade + close-out | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-17

Extracted the two genuinely host-agnostic primitives out of `kimidesktop.py` into their own modules, behavior-preserving. `winhost.py` owns Windows/WSL command composition — the `clauderizer-mcp.exe` probing (`win_exe_candidates`, `WIN_EXE`) and the `C:\`↔`/mnt/<drive>` translation (`win_path_to_wsl`, `windows_profile_from_cfg`). `mcp_probe.py` owns the MCP `initialize`-handshake capability probe (`handshake_probe` + `spawn_target`/`server_info`/`default_run`), which takes a generic `{command, args}` entry and imports `winhost` for the cross-OS translation. `kimidesktop.server_entry` now calls `winhost.win_exe_candidates`; `cmd_doctor` calls `mcp_probe.handshake_probe`; the moved code and its now-unused `re`/`subprocess` imports are gone from `kimidesktop`.

Both primitives are now reusable by the coming BespokeHost framework (Phase 1) and by the HOST_EMITTERS per-host doctor path (Phase 2). Tests were reorganized to match the new module boundaries: `test_winhost.py` (7) and `test_mcp_probe.py` (9) unit-test the primitives directly; the doctor-integration tests in `test_kimidesktop.py` were repointed to monkeypatch `clauderizer.mcp_probe.handshake_probe`. Behavior-preservation proven two ways: the full suite stays green (873 → 880 passed, 5 skipped, +7 net), and a live read-only check reproduces the exact composition (`C:\Users\rafaj\...\clauderizer-mcp.exe`, `args:[]`, zero warnings) and a green handshake (serverInfo clauderizer 1.9.1) through the extracted modules. No dangling references to the moved symbols remain in src/.

### Phase 1 — completed 2026-07-17

Introduced the `BespokeHost` framework and ported kimi-desktop onto it as the first implementation, behavior-preserving. `bespoke_hosts.py` holds the base class — the variable parts a host supplies (`candidate_configs`, `compose_entry`, `setup_guide`, optional `unservable_reason`; `id`/`opt_out_env`/`servers_key`) over the shared lifecycle it inherits (`detect_config`, `wire` → a `{status, path, entry, changed, unservable, warnings}` contract, `self_heal`, `remove_registration`), plus the generic non-destructive/atomic/idempotent `merge_entry`/`remove_entry` (parameterized by `servers_key`) and a plain-dict `BESPOKE_HOSTS` registry. `KimiDesktopHost` supplies only the daimon specifics and registers itself; the existing `kimidesktop` module functions became thin delegators to the registered `_HOST`, with `wire`/`self_heal` mapping the generic `unservable` field back to the legacy `windows_side` boolean (`_compat`) so `init`/`doctor` are untouched this phase.

The L-41 identity-default discipline kept this a zero-behavior-change refactor: the full suite went 880 → 886 (only new framework tests added), and a live read-only check reproduced the exact composition (`C:\...\clauderizer-mcp.exe`, idempotent no-op), the `windows_side`/`unservable` back-compat, a green handshake, and the full live `doctor` output. Genericity is proven, not asserted: `test_bespoke_hosts.py` drives a second, test-only `BespokeHost` (a different `servers_key`, no Windows/daimon code) through the entire detect→wire→idempotent-noop→self-heal→remove lifecycle, plus opt-out, unregistrable, and unservable-reason paths. The moved code's `re`/`subprocess`/`json`/`os`/`refuse_if_symlink` imports were dropped from `kimidesktop`; no dangling references remain.

### Phase 2 — completed 2026-07-17

Rewired every entry point off the hardcoded `kimidesktop` calls onto the generic registry: `init`, `doctor`, `status`, and `uninstall` now loop over the bespoke hosts, using `host.id` for the guide filename, `host.servers_key` for the presence check, and the generic `unservable` reason for the "can't-serve-this-repo" guidance — so a second host needs zero new entry-point code. For O-01 (the HOST_EMITTERS handshake), the decided policy is presence-check by default (`verify_wiring` already launch-probes the session host's wiring; a handshake per enabled host is latency for little gain — L-07) with a `clauderize doctor --deep` opt-in that runs the shared `mcp_probe` handshake against each registered auto-write host.

The critical catch: iterating the raw `BESPOKE_HOSTS` dict left it **empty** in the real `clauderize doctor` — the registry is populated by kimidesktop's import side-effect, and doctor no longer imports kimidesktop; the in-process tests masked it because conftest's autouse fixture imports the module (recorded as lesson #1, extending L-23). Fixed with a lazy `all_hosts()` accessor that imports the impl modules on use, plus a fresh-subprocess regression test that imports only the framework and asserts kimi-desktop self-bootstraps. Behavior-preservation re-verified live: `doctor` output is byte-identical (registered ✓, handshake ✓ serverInfo clauderizer, version-skew ?, UNC ?, exit 3) and a live wipe→`status`→restore round-trips the exact `C:\...\clauderizer-mcp.exe` entry through the generic loop. Suite 886 → 888 passed, 5 skipped.

### Phase 3 — completed 2026-07-17

Documented the extension path and closed out. `docs/CROSS-HOST.md` gained a concise 4-step "Adding a bespoke auto-write host" recipe — subclass `BespokeHost` (set `id`/`opt_out_env`/`servers_key`, override `candidate_configs`/`compose_entry`/`setup_guide`/`unservable_reason`), register it and add its module to `all_hosts()`, inherit the detect/merge/self-heal/verify lifecycle, and test against a temp config — pinned to the real API by a doc-content test (L-55) that also asserts each named member exists on the framework. The CHANGELOG's unreleased 1.10.0 entry gained a framework bullet (no new version bump — this folds into the same unreleased release). Cascades over `subsys.scaffold` and `subsys.mcp-server` resolved to "no change needed" (behavior-preserving extraction + generalization).

The D-055 kimi-desktop acceptance criteria were re-verified live throughout the gameplan (composition byte-identical to the user's verified-good entry, self-heal wipe→restore, green `initialize` handshake, UNC guidance, `doctor` exit 3) — all now flowing through the generic registry with no behavior change. Final suite: 889 passed, 5 skipped (from 873 at the gameplan's start; +16 tests across the two new primitive modules, the framework, the second-host lifecycle, the fresh-process bootstrap guard, `--deep`, and the recipe pin).

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** A registry populated by IMPORT SIDE-EFFECTS (module top-level `register(Impl())`) is EMPTY until something imports the implementation module — and an in-process test suite masks the emptiness because a shared fixture imports it (here conftest's autouse `_no_real_kimi_desktop` imports kimidesktop), while the REAL entry point (a `clauderize doctor` that imports only the framework, not the impl) iterates an empty registry and silently does nothing. Two-part fix: (1) iterate through an ACCESSOR that explicitly imports the implementation modules (`all_hosts()` does `from . import kimidesktop` then returns the dict) so bootstrap is order-independent — never iterate the raw registry dict from a caller that may not have imported the impls; a top-level import in the framework module would cycle, so the accessor imports lazily. (2) The masking means an in-process test can't catch it (the fixture already imported the impl) — add a FRESH-PROCESS regression test (`subprocess` running `python -c "from pkg import framework; print(framework.all_hosts())"`, importing ONLY the framework) that fails if the accessor stops bootstrapping. Extends L-23 (the author's/test's environment is not the real execution leg): here the test process' import graph differs from the CLI's. *(evidence: D-056 Phase 2: cmd_doctor rewired to iterate bespoke_hosts.all_hosts(); live `clauderize doctor` showed NO kimi-desktop section (registry empty) until all_hosts() imported kimidesktop; tests/test_bespoke_hosts.py::test_all_hosts_self_bootstraps_in_a_fresh_process is the subprocess guard.)* (promoted 2026-07-17: L-60)
