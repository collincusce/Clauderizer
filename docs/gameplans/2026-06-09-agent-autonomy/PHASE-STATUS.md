# agent-autonomy — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-09

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Serialized tracked writes | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-0-HANDOFF.md |
| 1 | CLI write parity: clauderize ops | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Wiring truth: session-host-of-record | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Cold-start breadcrumb hook wrapper | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Stale-engine proof, amendment pointer, 0.7.0 | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
lock_module: src/clauderizer/locking.py — write_lock() over .clauderizer/write.lock (O_EXCL + holder metadata + rename-based stale takeover + post-create nonce verification)
locked_functions: 18/18 public mutations.* via @_locked decorator spanning the full read-modify-write; reentrant (consolidate->add nests); reads lock-free (L-03)
lock_defaults: acquire_timeout 10s, stale_timeout 30s, poll 50ms — module attributes (locking.DEFAULT_*), resolved at call time so tests/embedders can retune
contention_regression: tests/test_locking.py::test_concurrent_writer_processes_lose_nothing — 8 real processes, GO-sentinel start barrier, asserts N sequential ids + N surviving appends
test_count: 148 (baseline 139 + 9 in tests/test_locking.py)
h05_resolution: resolved 2026-06-09 in docs/HARDENING.md; the resolving write itself ran through the locked path in a fresh process (/tmp/resolve_h05.py pattern)
```

### Phase 1 Outputs

```
mcp_less_write_demo: this very registry entry was recorded by `clauderize ops /tmp/dogfood_ops.json` (console script, fresh process, MCP server never spawned) on 2026-06-09 - the L-05 exit-criterion evidence, write serialized on .clauderizer/write.lock
ops_module: src/clauderizer/ops.py — 24 op functions (bodies moved verbatim from mcp_server closures) + REGISTRY (name → Op(fn, writes)) + run_batch executor; mcp_server registers the registry function objects in a loop, so schemas derive from the same callables the CLI executes
cli_verb: clauderize ops <file.json|-> — JSON array (or single object) of {op, args}; utf-8-sig + stdin BOM tolerance; per-op {n, op, ok, result|error} on stdout; exit 0 all-ok / 1 any-failed / 2 unreadable-batch
lock_coverage_extension: Phase 0's deferred residue closed: cz_cascade (non-dry-run), cz_write_handoff, cz_create_gameplan (incl. the active-gameplan config flip) lock in their op bodies; preflight's baseline refresh locks at the write site and skips (self-healing) under contention instead of failing the ritual
test_count: 162 (148 + 14 in tests/test_ops.py: registry/tool-surface equality, MCP-vs-ops read+write parity, batch semantics, CLI exit codes, BOM, cold-process invocation, lock coverage of non-mutation writes, dry-run lock-freedom, baseline contention-skip)
docs_updated: CLAUDE.md stanza names clauderize ops as the no-MCP write fallback (refreshed via marker block); GAMEPLAN-PROCEDURE.md 1.1.0 → 1.2.0 ("Recording Without MCP" Quick Reference section + changelog; shim/stdio-probe patterns retired); PROCEDURE_VERSION constant synced
```

### Phase 2 Outputs

```
hosts_module: src/clauderizer/hosts.py — session-host vocabulary (native | windows-wsl:<distro>; SessionHostError with guidance), detect() (adopt the distro from existing wsl.exe wiring's -d arg, then WSL_DISTRO_NAME, else native), compose() (shim wrap, never double-wraps an explicit wsl.exe run-cmd), spawn_probe() and verify_wiring() returning a 3-state Probe (ok | fail | unverifiable)
config_field: [host] session_host in config.toml — None means "recorded by no init yet" (pre-Phase-2 configs load as None, emit nothing; doctor nudges re-init when wiring is shimmed); resolution precedence in init: --session-host flag > existing config record > adopt-existing-wiring > native
init_guard: init spawn-tests both composed commands (--version, stdin=DEVNULL, 60s) BEFORE any write; fail -> WiringRefused naming command+probe output, nothing written (the H-04 'clauderize clauderizer-mcp' shape now refuses); unverifiable (no interop) -> warn-but-write with the certify-from-host command; CLI: --session-host flag, --no-spawn-test escape hatch; uvx fallback absolutized via which() for non-login PATHs
doctor_surface: 14 checks (was 13): new "session host of record" line (validates the record; nudges re-init when unrecorded but wiring is shimmed) and both launch checks host-aware via hosts.verify_wiring — windows-wsl certifies through a real wsl.exe interop round-trip showing the served version, or prints "? ... unverifiable from this host"; exit codes now 0 ok / 2 drift / 3 ok-but-unverifiable (never a false green); clauderizer-mcp and clauderizer-hook answer --version/--help deterministically (the probe surface)
exit_evidence: clauderize init on this repo (via the PowerShell shim, fresh process): detected windows-wsl:ubuntu from existing wiring, .mcp.json and .claude/settings.json both "kept" (byte-identical regeneration of the hand-maintained wiring), config.toml +1 line (the record); doctor through the same shim: 14/14 green, both launch checks "verified end-to-end via wsl.exe round-trip (clauderizer 0.6.0)", exit 0; H-04 resolved via clauderize ops (fresh process)
test_count: 195 (162 + 33: tests/test_hosts.py — parse/detect/compose matrix, config round-trip incl. apply-twice, real spawn probes incl. the H-04 exit-2 shape refusing init with nothing written, verify_wiring 3-state, init adoption/persistence/idempotency, doctor messaging; test_engine_hardening's _command_runnable tests ported to hosts.verify_wiring)
```

### Phase 3 Outputs

```
wrapper_machinery: hosts.py additions — BREADCRUMB_PREFIX ("[Clauderizer] engine unreachable:"), render_hook_wrapper (sh + cmd variants: capture engine 2>&1, breadcrumb+captured-error on stdout on failure, "$@" forwarding so probes stay transparent, always exit 0), wrapper_engine_argv (parses the "# engine-hook:" line — doctor's freshness anchor), hook_wrapper_invocation (native posix: /bin/sh <repo>/.clauderizer/hook.sh; native win32: cmd /c hook.cmd; windows-wsl: wsl.exe -d <distro> /bin/sh <repo path engine-side>), is_hook_command (shared matcher: clauderizer-hook OR .clauderizer/hook. — init dedup + doctor cannot drift)
init_doctor_integration: init step 11: writes .clauderizer/hook.sh|.cmd (engine-owned rewrite-if-diff, bakes the UNSHIMMED engine argv), spawn-tests the registered wrapper command before touching settings.json (wrapper-specific WiringRefused names the wrapper path; engine reachability still gated pre-write in step 0b so the H-04 nothing-written contract holds); doctor: 16 checks on wrapper repos — "hook wrapper present" (missing = drift exit 2), "hook wrapper freshness" (baked argv vs fresh _resolve_invocation; mismatch = "?" exit 3), direct pre-wrapper wiring gets a "?" re-init nudge; hook launch verdict now certifies the full chain wsl.exe -> /bin/sh -> hook.sh -> engine
h01_closure_evidence: Live demo 2026-06-10 (scratch /tmp/breadcrumb_demo wired windows-wsl:ubuntu, venv clauderizer-hook renamed): pre-D4 direct wiring spawned from PowerShell -> exit 127, stdout EMPTY (error stderr-only = the silent cold start); the registered wrapper command verbatim -> exit 0, stdout = breadcrumb + captured "not found"; binary restored, --version green. H-01 -> resolved via clauderize ops (fresh process). Remaining silent boundary documented in H-01's resolution: wrapper shell itself dead (wsl.exe/distro down = repo unreachable anyway; /bin/sh absent; wrapper file deleted = caught by doctor presence check next run)
test_count: 211 (195 + 16 in tests/test_hook_wrapper.py: template rendering + engine-line round-trip + invocation matrix, REAL /bin/sh executions (dead engine -> verbatim breadcrumb on stdout exit 0 stderr empty; healthy passthrough; --version forwarding through to the real engine), init registration matrix + upgrade dedup + regeneration-on-engine-move + spawn-tested idempotent re-run, doctor present/missing/stale/nudge with exit codes 0/2/3/3); this repo re-inited: only hook.sh + settings.json changed, doctor 16/16 exit 0 through the shim
```

### Phase 4 Outputs

```
identity_check: hosts.served_version (regex on the probe's --version line: both entry points print 'clauderizer <__version__>') + two fail branches in verify_wiring's round-trip success path: missing identity claim (pre-0.6.0 EOF accident, or the D4 wrapper's dead-engine breadcrumb — previously a GREEN hook verdict) and version skew (served != running __version__, message names both + remedies). Scope: the windows-wsl round-trip path; native wiring identity remains covered by the D9 metadata/repo-version checks. Doctor stays 16 checks; healthy wiring on this repo certifies '(clauderizer 0.7.0)' 16/16 exit 0 through the shim.
stale_uvx_demo: D5 evidence captured 2026-06-09 (H-06, resolved): scratch /tmp/stale_uvx_demo wired '~/.local/bin/uvx --from clauderizer[mcp]==0.5.0' by init WITH spawn test on (both 0.5.0 entry points exit 0 — lesson-#4 accident observed live); current 0.7.0 doctor probing through that exact wiring: BOTH launch checks fail identity loudly (MCP: exit-0-no-output; hook: 0.5.0 answered with its old digest — working-but-wrong engine), exit 2. By-name: uvx --from clauderizer → clauderizer 0.6.0 (PyPI latest). Bare pin clauderizer==0.5.0 (no extra) refused at init instead (mcp import exit 1) — guard layering: init catches launch-dead, doctor catches launch-alive-but-stale. Scratch repo deleted after capture; repro steps in H-06.
amendment_pointer_fix: mutations.add_amendment gains amendments_ritual: bool = False (ops layer passes config.ritual_enabled('amendments')): the 'Cascade report' line renders ONLY under the ritual, and as a pending pointer ('run cz_cascade for the affected entities; reports land in _cascade-reports/') — never a per-amendment filename (no code path creates <date>-A-NNN.md under any setting). A-001 in 2026-06-09-engine-structural-robustness healed via entry-anchored line replace under the write lock (/tmp/heal_a001.py, fresh process): now cites _cascade-reports/2026-06-09-subsys.markdown-core.md, the per-entity report that actually notes A-001. Procedure template 1.2.0 → 1.2.1 (format block + changelog); PROCEDURE_VERSION synced; installed copy synced (create_if_absent assets need explicit release-flow sync — lesson #8).
release_0_7_0_state: SUPERSEDED by release_0_8_0_state (2026-06-10): 0.7.0 turned out to be already claimed remotely — a published GitHub Release v0.7.0 at the Phase-0 commit (source 0.6.0) whose PyPI publish had failed as a duplicate (H-07). User chose to retire the number rather than retag; the staged release renumbered to 0.8.0.
restart_validation_observation: UNRESOLVED — needs the next cold start to adjudicate: this session (the first harness session after Phase 3's wrapper registration) received NO [Clauderizer] digest in its SessionStart context (only the output-style hook context appeared), yet the exact registered command run manually from PowerShell emits the digest and exits 0, and doctor certifies the full chain end-to-end. So the command leg is green; the harness-injection leg is unverified. If the digest appears on the next restart, this was a one-off (or a client-config artifact — e.g. project-hook trust in the desktop app); if it does not, the harness-side hook execution is the failure point (candidates: hook stdin JSON handling, timeout, project trust settings) and the v0.7.0 tag stays gated.
thread_hygiene: 0.6.0 post-mortem (engine-structural-robustness) Open Threads all annotated with closure evidence: CLI parity → Phase 1 (24/24, L-05), publish-0.6.0 proof half → H-06 demo, H-01 residue → Phase 3 wrapper, amendment pointer → Phase 4 fix + A-001 heal. Deliberate carry-forwards restated as agent-autonomy Open Items: O1 (ACTIVE_LESSONS_WARN as config) and O2 (project-lesson consolidation past ~20; currently 6) — both explicitly out of any phase's scope, candidates for the next gameplan.
release_0_8_0_state: pyproject + __version__ = 0.8.0 (renumbered from 0.7.0 — that number was already claimed by a broken remote Release, H-07); dist-info refreshed; CHANGELOG: 0.8.0 section (all five phases + the publish gate) with a 0.7.0 'version retired — never published' tombstone explaining the pip-visible hole; publish.yml gains the tag-vs-pyproject gate (fails fast naming both versions); suite 215 green; doctor 16/16 exit 0 via shim certifying '(clauderizer 0.8.0)'. TAG v0.8.0 NOT CUT — still gated on the restart-validated digest; publishing fires on the GitHub Release (gate now guards it). NOTE: origin/main is at the Phase-1 commit — phases 2-4 and this fix are local-only until pushed; the broken v0.7.0 Release/tag remain on GitHub by user choice (retire, don't retag).
```

## Corrections Log

### C-01 — Phase 2

**Phase**: 2
**What gameplan said**: Task 2.3: spawn-test every composed command via a --help probe
**What was actually correct**: Probed with --version instead (entry points handle both): the probe's success output is the engine version the wiring actually serves, so doctor's certification line carries identity evidence ("verified end-to-end via wsl.exe round-trip (clauderizer 0.6.0)") for free. Also added two surfaces the plan didn't name: --no-spawn-test as a loud escape hatch for spawn-restricted sandboxes, and doctor exit code 3 for ok-but-unverifiable.
**Why**: Live probing showed clauderizer-mcp exited 0 on EOF even without argv handling, so any probe arg needed explicit entry-point support anyway — and --version returns a meaningful payload where --help returns prose. The exit-3 distinction keeps scripts from reading "unverifiable" as either green or drift.

### C-02 — Phase 3

**Phase**: 3
**What gameplan said**: D4 / task 3.1: per session host, the wrapper is host-native — .clauderizer/hook.cmd for a Windows session host, hook.sh for POSIX
**What was actually correct**: For windows-wsl the wrapper is WSL-side hook.sh registered as `wsl.exe -d <distro> /bin/sh <repo>/.clauderizer/hook.sh`; hook.cmd ships only for the native-win32 session host (engine installed on Windows)
**Why**: A cmd.exe wrapper spawned in this repo's \\wsl.localhost UNC cwd prints "UNC paths are not supported" into every healthy session's context and resets cwd to C:\Windows (breaking repo detection), while the only failure it additionally covers — wsl.exe dead with cmd alive — implies the UNC repo is unreachable, so no session could start there anyway. The honest layer-below-the-engine for split-host is /bin/sh inside the distro: it spawns whenever wsl.exe+distro are alive, which is exactly when a session on this repo can exist at all.

### C-03 — Phase 4

**Phase**: 4
**What gameplan said**: Task 4.1 / D5: "scratch repo wired uvx --from clauderizer==0.5.0; doctor through that exact wiring must FAIL identity loudly"
**What was actually correct**: Two divergences. (1) The pin needs the extra: clauderizer==0.5.0 bare composes launch-DEAD wiring (0.5.0's clauderizer-mcp exits 1 on the missing 'mcp' import), which init's H-04 spawn guard refuses before anything is written — the demonstrable D5 topology (launches fine, serves stale) is clauderizer[mcp]==0.5.0. (2) "Doctor through that exact wiring" cannot be run literally: a doctor EXECUTED via the pinned wiring is the 0.5.0 doctor, which predates the identity checks and can never fail them. What proves the property is the CURRENT doctor probing THROUGH the exact wiring — its round-trip verdict spawns the wiring's own command and judges the identity the wiring serves. That is what shipped and what the demo recorded.
**Why**: D5's wording conflated the engine that runs doctor with the wiring doctor inspects. The stale-engine trap is precisely that those differ; the guard must therefore live in the inspecting engine's probe of the wiring, not in the (stale) engine behind the wiring. The bare-pin refusal was discovered live when init's spawn test rejected the gameplan's literal pin spec — itself a working demonstration of the H-04 guard layering under the identity guard.

### C-04 — Phase 4

**Phase**: 4
**What gameplan said**: Task 4.4 / exit criteria: "Release 0.7.0 … `clauderize --version` → 0.7.0; tag only after a restart-validated cold start" — and the Phase-4 close-out staged exactly that, believing 0.7.0 was unclaimed
**What was actually correct**: The release ships as 0.8.0. v0.7.0 was already claimed remotely: a published GitHub Release v0.7.0 (2026-06-09T22:24Z) at the Phase-0 commit, cut while the source still declared 0.6.0, whose PyPI publish failed as a duplicate six minutes later — so 0.7.0 exists as a Release page but is installable nowhere (H-07). User chose retire-and-renumber over retagging; CHANGELOG carries a 0.7.0 tombstone; publish.yml now refuses tag/source version skew.
**Why**: The Phase-4 sweep checked source, the gameplan captures, PyPI, and live uvx resolution — all truthfully reporting 0.6.0 — but never enumerated remote tags or GitHub Releases (the tag existed only on origin; local tags end at v0.6.0, and origin/main was three commits behind local, hiding the activity). The uvx by-name result 0.6.0 was read as confirmation when it was actually the symptom of the failed v0.7.0 publish. Lesson #9: a version is a namespace claim across four unsynced registries; sweep all four before claiming one.
