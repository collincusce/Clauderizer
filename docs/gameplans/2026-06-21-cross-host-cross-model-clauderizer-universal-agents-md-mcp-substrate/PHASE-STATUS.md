# Cross-host & cross-model Clauderizer (universal AGENTS.md + MCP substrate) — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-21

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Host model, capability audit & parity contract | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Model-agnostic protocol hardening & injection-delivery signal | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-1-HANDOFF.md |
| 2 | AGENTS.md canonical substrate & Tier-4 floor | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-2-HANDOFF.md |
| 3 | MCP middle tiers: prompts, auto-load resource & tier routing | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Floor-host wiring emitters (AGENTS.md+MCP hosts) + uninstall & coexistence | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Bespoke-host wiring emitters (native rule formats & deeper integration) | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-5-HANDOFF.md |
| 6 | Cross-host verification execution & release gate | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-6-HANDOFF.md |
| 7 | Server-side session bootstrap (fast-follow; non-gating) | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-7-HANDOFF.md |
| 8 | Wire host_target end-to-end (make cross-host functional via init) | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-8-HANDOFF.md |
| 9 | Real-host & cross-model verification (close O-06, O-07; kill engine_stale) | 🟡 IN PROGRESS | 2026-06-21 | — | handoffs/PHASE-9-HANDOFF.md |
| 10 | Adversarial sweep: integration seams & state (codebase-wide) | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-10-HANDOFF.md |
| 11 | Adversarial sweep: concurrency, I/O robustness & failure modes | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-11-HANDOFF.md |
| 12 | Security & trust hardening | ⬜ NOT STARTED | — | — | handoffs/PHASE-12-HANDOFF.md |
| 13 | UX completeness, doc truth-up & release gate; close the gameplan | ⬜ NOT STARTED | — | — | handoffs/PHASE-13-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
in_scope_hosts: 11: claude-code, kimi, copilot, codex, gemini-cli, windsurf, cline, amp, cursor, continue, zed
dropped_hosts: roo-code (archived 2026-05-15), aider (no native MCP client)
tier1_capable: 9 hosts have context-injecting or candidate lifecycle hooks
tier2_status: RETIRED - no host auto-loads MCP resources
design_doc: docs/CROSS-HOST.md
baseline_tests: 446
agents_md_floor_exceptions: continue (.continue/rules), gemini-cli (GEMINI.md), aider (CONVENTIONS via read:)
```

### Phase 1 Outputs

```
new_module: src/clauderizer/session.py - in-memory delivery signal + host gate + write-first note
config_field: host_target (third host axis, default claude-code) in config.py
server_seam: mcp_server._deliver_aware wraps tool registration; functools.wraps preserves schemas (build-guard test)
hook_hosts: claude-code,kimi,copilot,codex,gemini-cli,windsurf,cline,amp (session._HOOK_HOSTS - the gate)
tests_added: tests/test_session_signal.py (16 tests)
baseline_tests: 462
```

### Phase 2 Outputs

```
floor_instruction: 'call cz_status now, before anything else' (host-neutral) in src/clauderizer/templates/claude_stanza.md
files_synced: claude_stanza.md template + live CLAUDE.md + AGENTS.md (L-16, source first)
stanza_mechanism: single-source dual-write (D-035); no symlink/import
baseline_tests: 463
```

### Phase 3 Outputs

```
prompts: cz-status, cz-next-phase (MCP prompts, Tier-3 slash commands)
tier_fn: session.best_tier(host_target) -> 1 hook / 3 prompt / 4 floor
prompt_hosts: cursor, continue, zed (Tier-3, hook-less)
p2_test_fixed: floor guard test made whitespace-robust (was red in 00159ef)
```

### Phase 4 Outputs

```
module: src/clauderizer/hosttargets.py - emit_mcp/remove_mcp/is_path_safe + HOST_EMITTERS table
auto_write_hosts: cursor, copilot, continue, zed, gemini-cli, cline, amp (project JSON)
guide_only_hosts: codex, windsurf, kimi (TOML/global)
cli_command: clauderize uninstall [--host]
portable_command: uvx --from clauderizer clauderizer-mcp (path-safe, committable)
tests: tests/test_hosttargets.py (9 tests)
```

### Phase 5 Outputs

```
native_floor_hosts: continue (.continue/rules/clauderizer.md), gemini-cli (GEMINI.md) - they do not read AGENTS.md
hook_guide_hosts: copilot, codex, windsurf, cline, amp, gemini-cli (Tier-1 via guided wiring)
functions: hosttargets.emit_instructions + hook_setup_guide
tests: 4 new in tests/test_hosttargets.py
```

### Phase 6 Outputs

```
host_simulator: hosttargets.wiring_contract_sweep + verify_emitted_wiring (D-032 wiring contract)
path_audit: hosttargets.path_safety_audit (catches machine-specific paths, O-06)
ci_gate: test_wiring_contract_sweep_all_green runs the sweep in CI via the suite
tests: 3 new (wiring sweep, path-audit flag, path-audit clean)
```

### Phase 7 Outputs

```
bootstrap: mcp_server._deliver_aware wraps all non-status tools; first call on a hook-less host gets a clauderizer_status note
gate_renamed: session.should_inject_on_write -> should_inject (now gates reads + writes)
dedup: P1 in-memory signal; hook hosts stand down after first call (one lookup, no injection)
tests: 2 new (read bootstrap on hook-less, silent on hook host)
```

### Phase 8 Outputs

```
cli_flag: clauderize init --host <name> (dest=host); resolves flag > config.host_target > hosttargets.detect_host_target > claude-code; persists to config.host_target
new_functions: hosttargets: parse_host_target/valid_host_targets/HostTargetError (friendly validation), detect_host_target (cheap auto-detect), mcp_setup_guide (guide-only hosts), emit_host_wiring + EmitResult (idempotent per-host orchestrator). init branches on host_target==claude-code (byte-identical) else emit_host_wiring.
uninstall_module: src/clauderizer/scaffold/uninstall.py: uninstall(root, host=None) -> UninstallReport. Full footprint = .mcp.json key + .claude hooks + every per-host MCP + CLAUDE.md/AGENTS.md stanzas + native floor blocks + clauderizer-* skills + .clauderizer/ + gitignore line. --host scopes to one. Preserves docs/ and unrelated entries. Uses new markdown.remove_marker_block (sections.py+writer.py).
baseline_tests: 507 (was 484; +23 in tests/test_host_target_init.py). Commit 91561ed.
```

### Phase 9 Outputs

```
o06_fix: .mcp.json + .claude/settings.json git rm --cached + gitignored (machine-path leak removed from version control; dogfood keeps them locally for its editable-engine build). path_safety_audit made gitignore-aware (hosttargets._is_git_ignored). Audit clean on real repo. Commit on cross-host-cross-model branch.
live_server_verification: Launched clauderizer-mcp over real stdio MCP client (mcp SDK ClientSession): serves P3 prompts [cz-next-phase, cz-status], 31 tools, cz-status prompt returns live [Clauderizer] digest, cz_status tool round-trips. CI-pinned: test_mcp_tools.py::test_server_serves_prompts + test_server_bootstrap_injects_only_on_hookless_host (P7 bootstrap fires for cursor, silent for claude-code). engine_stale for THIS session is unrelated to correctness — the running server holds pre-edit modules; clears on session restart (user action).
```

### Phase 10 Outputs

```
seam_sweep_results: 3 independent reviewers over 6 shared functions. CLEAN: config.py (host_target threaded 14/14 fields through to_toml/load/merge_missing), status_bundle, ops signatures (all 31), graph/index.py (always-rebuild = no stale cache), writer.remove_marker_block. FIXED (2 HIGH hook-dispatcher seams, commit 42140f3): (1) native cross-host event names not aliased -> windsurf pre_user_prompt emitted full digest every prompt; added _EVENT_ALIASES. (2) unhashable hook_event_name raised TypeError vs graceful fallback; coerce non-str -> None. Regression tests at the seam in test_hook_dispatch.py.
```

### Phase 11 Outputs

```
failure_mode_hardening: config.ConfigError (subclasses ValueError) — Config.load wraps its parse, re-raises naming the file; cli.main catches -> actionable msg + exit 1. Fixes doctor/status/reindex crashing on corrupt config.toml. Other parse paths (frontmatter.parse, index.build, index.load_or_rebuild) already graceful — locked by tests. tests/test_failure_modes.py (15 tests): corrupt-config battery, frontmatter/index adversarial inputs, mixed-op (add_lesson+add_decision) concurrency stress. Suite 538. Existing coverage confirmed sufficient for: 8-process lock race (test_locking), L-24 input battery (test_diverse_robustness), hook read-only+exit-0 (test_hook_dispatch).
```

## Corrections Log

### C-01 — Phase 0

**Phase**: 0
**What gameplan said**: Claude Code hook-driven auto-injection has no clean cross-tool equivalent; Tier 1 is effectively Claude-Code/kimi-only (D-029/D-030, open item O-02).
**What was actually correct**: Primary-source verification (2026-06-21) found ~9 hosts ship SessionStart/UserPromptSubmit-class lifecycle hooks: GitHub Copilot/VS Code, Codex CLI, Gemini CLI, Windsurf, Cline (POSIX-only), Amp (TS plugins), plus Claude Code and kimi; Cursor has governance hooks (context-injection TBD). Tier 1 is broadly reachable.
**Why**: The first deep-research pass could not verify per-host hook support and inferred Claude-only from absence of evidence; per-host primary docs overturned it.
**Lesson**: Verify per-host capabilities from each host own docs before encoding feature-X-is-unique-to-host-Y into architecture; absence of evidence is not evidence of absence. The Phase 0 matrix re-derivation existed precisely to catch this.

### C-02 — Phase 0

**Phase**: 0
**What gameplan said**: Tier 2 = an auto-loaded MCP resource is the portable substitute for hook injection (D-030 ladder).
**What was actually correct**: No verified host auto-loads MCP resources into context. Across Cursor, Copilot, Continue, Gemini, Windsurf, Cline, and Zed (no resources at all), resources are model-requested or manual @-mention only. Tier 2 is RETIRED.
**Why**: MCP resources are user/model-controlled by spec; the auto-load assumption had no primary-source basis.
**Lesson**: Do not design a delivery tier around an unverified host behavior; confirm the mechanism exists on at least one target host before giving it a phase.

### C-03 — Phase 0

**Phase**: 0
**What gameplan said**: (implicit) running clauderizer-do-phase right after clauderizer-new-gameplan proceeds cleanly.
**What was actually correct**: The first cz_preflight of a fresh gameplan FAILS clean_tree, because creating the gameplan writes uncommitted docs (DECISIONS/INVARIANTS/gameplan dir/config pointer) and nothing commits the plan.
**Why**: new-gameplan had no commit step; do-phase preflight clean_tree guard then trips on the plan own creation artifacts.
**Lesson**: A new gameplan must be committed before its first do-phase. Fixed: added step 8 (Commit the plan before executing) to clauderizer-new-gameplan source + rendered (L-16), including the rule to separate pre-existing unrelated changes into their own commit.

### C-04 — Phase 3

**Phase**: 3
**What gameplan said**: P2 was reported green (suite 463) and committed (00159ef).
**What was actually correct**: P2 actually shipped with the floor guard test RED: it asserted the contiguous phrase 'before anything else' but the template wraps it across a line break ('before anything' + newline + 'else'). cz_preflight at P3-start (the authoritative gate) caught it; the ad-hoc pytest-to-file + EXIT read through wsl.exe had reported a misleading exit 0.
**Why**: P2 was closed on an ad-hoc shell exit-code read (unreliable through the wsl.exe layer - summary lines are carriage-return-eaten and exit codes mis-captured) instead of cz_preflight, and the guard assertion was brittle to markdown line-wrapping.
**Lesson**: Close every phase with cz_preflight (the engine gate that runs AND parses the suite), never an ad-hoc 'pytest > file; EXIT=$?' through wsl.exe - that capture is flaky. And make guard assertions whitespace-robust: normalize with ' '.join(text.split()) before matching a multi-word phrase, because markdown wraps lines.
