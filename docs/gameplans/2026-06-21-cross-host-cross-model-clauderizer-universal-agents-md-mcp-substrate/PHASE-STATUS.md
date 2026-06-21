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
| 9 | Real-host & cross-model verification (close O-06, O-07; kill engine_stale) | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-9-HANDOFF.md |
| 10 | Adversarial sweep: integration seams & state (codebase-wide) | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-10-HANDOFF.md |
| 11 | Adversarial sweep: concurrency, I/O robustness & failure modes | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-11-HANDOFF.md |
| 12 | Security & trust hardening | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-12-HANDOFF.md |
| 13 | UX completeness, doc truth-up & release gate; close the gameplan | 🟡 IN PROGRESS | 2026-06-21 | — | handoffs/PHASE-13-HANDOFF.md |

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
real_host_consumption: User-confirmed real-host consumption (2026-06-21, WSL Ubuntu). (1) CURSOR (Remote-WSL on ~/cz-hosttest): surfaces the clauderizer MCP PROMPTS (/cz-status, /cz-next-phase) as slash commands from the emitted .cursor/mcp.json — "appear just fine". Since those prompts are unreleased (this branch's P3, "none exist today" at start), their presence proves the config is running the DEV build, not PyPI 0.15.0. = the D-034 Tier-3 path working live. (2) VS CODE / COPILOT: surfaces the clauderizer MCP commands from the emitted .vscode/mcp.json ("sees the mcp"); agent-side invocation gated by an unrelated GitHub/Copilot auth issue (user deferring — does not affect whether VS Code READS the config). Both real hosts read the clauderize-emitted per-host config and register the server = the O-07 consumption proof on 2 hosts. Residual (nicety, non-blocking): a literal /cz-status invocation rendering the [Clauderizer] digest end-to-end not separately reported.
cross_model_adherence: Composer 2.5 Fast (Cursor's own NON-Claude model) drove a full self-created gameplan '2026-06-21-contributing-guide' end-to-end in ~/cz-hosttest — 142 tool calls. ADHERENCE FINDINGS: (1) It NEVER invoked the cz_* MCP tools (0 MCP calls) despite them being available (prompts surfaced in Cursor); it used only Cursor built-ins (Read 48, Shell 47, StrReplace 16, Glob 14, Write 9, Grep 8). (2) It first looked for the tools as FILES (Glob **/mcps/**/tools/cz_*.json), then tried the CLI: bare `clauderize status` failed (command not found — .venv-not-on-PATH), and it RECOVERED on its own by switching to the portable `uvx --from clauderizer clauderize …` form (doctor/status/ops), even introspecting op signatures (`uvx … python -c "inspect.signature(cz_add_decision)"`) to get args right. (3) It DISCOVERED and USED the L-05 CLI fallback `clauderize ops -` with a JSON batch for tracked writes — a real non-Claude model independently validating the 'every tracked write needs a CLI-reachable fallback' design. (4) BUT it ALSO hand-edited tracked docs directly (StrReplace/Write on GAMEPLAN.md x6, PHASE-0-HANDOFF.md, CLAUDE.md, AGENTS.md, ARCHITECTURE.md, .clauderizer/config.toml) — the anti-pattern cz_/ops exist to prevent (frontmatter/graph-corruption risk). Its uvx CLI ran PUBLISHED 0.15.0 while Cursor's ignored MCP server was the dev build. Isolated in the throwaway repo; real repo unaffected.
cross_version_host_target_fragility: Discovered during P9 real-host testing (2026-06-21, ~/cz-hosttest). After Composer 2.5 Fast's session, .clauderizer/config.toml LOST its [host] target line — reverting to the claude-code default. Root cause: the repo was driven with PUBLISHED 0.15.0 via `uvx --from clauderizer` (predates host_target) and/or config.toml was hand-edited during close-out; any engine/edit that rewrites config.toml without the host_target field strips it. Consequence: BOTH the published doctor AND the dev (P10 host-aware) doctor then correctly check CLAUDE-CODE wiring per the defaulted host_target and report drift — MASKING that the actual cursor/copilot wiring (.cursor/mcp.json, .vscode/mcp.json) is fine. So the doctor 'drift' was config-target-LOSS, not graph corruption. `clauderize reindex` rebuilt CLEAN (no frontmatter parse errors → Composer's markdown hand-edits stayed syntactically valid) but found 0 ENTITIES — confirming Composer's close-out claims ('D-001 cascade', 'host profile subsystems') were PROSE, not real tracked graph entities (validates L-33 verify-don't-trust). Implications: (a) the cross-version hazard self-resolves once 0.16.0 ships (the published engine will then preserve host_target through config rewrites); (b) candidate doctor enhancement — when per-host wiring exists but config.host_target==claude-code(default), warn 'host_target may have been stripped by an older engine; re-run clauderize init --host <name>'. Test repo only; real repo unaffected.
```

### Phase 10 Outputs

```
seam_sweep_results: 3 independent reviewers over 6 shared functions. CLEAN: config.py (host_target threaded 14/14 fields through to_toml/load/merge_missing), status_bundle, ops signatures (all 31), graph/index.py (always-rebuild = no stale cache), writer.remove_marker_block. FIXED (2 HIGH hook-dispatcher seams, commit 42140f3): (1) native cross-host event names not aliased -> windsurf pre_user_prompt emitted full digest every prompt; added _EVENT_ALIASES. (2) unhashable hook_event_name raised TypeError vs graceful fallback; coerce non-str -> None. Regression tests at the seam in test_hook_dispatch.py.
```

### Phase 11 Outputs

```
failure_mode_hardening: config.ConfigError (subclasses ValueError) — Config.load wraps its parse, re-raises naming the file; cli.main catches -> actionable msg + exit 1. Fixes doctor/status/reindex crashing on corrupt config.toml. Other parse paths (frontmatter.parse, index.build, index.load_or_rebuild) already graceful — locked by tests. tests/test_failure_modes.py (15 tests): corrupt-config battery, frontmatter/index adversarial inputs, mixed-op (add_lesson+add_decision) concurrency stress. Suite 538. Existing coverage confirmed sufficient for: 8-process lock race (test_locking), L-24 input battery (test_diverse_robustness), hook read-only+exit-0 (test_hook_dispatch).
```

### Phase 12 Outputs

```
security_review_results: Independent security review: 4 threat categories CLEAN (path traversal via host id/config_path — parse_host_target allow-list; config command-injection — hostile host_target re-validated, hooks read-only so cloning doesn't auto-exec; secret leakage — none; uninstall data-loss — preserves docs/foreign servers/foreign hooks, fully reverses). Findings: H-11 HIGH (claude-code .mcp.json/.claude writers skipped path-safety -> machine-path leak on commit) RESOLVED via gitignore-when-machine-specific; H-12 LOW (symlinked skill aborts uninstall) RESOLVED; H-13 LOW (engine writes follow symlinks) OPEN/deferred (needs malicious working tree, content not attacker-controlled). Docs: TRUST.md + SECURITY.md trued-up to P8 reality (uninstall full footprint, claude-code-only hooks, setup-guide filenames). Suite 541.
```

### Phase 13 Outputs

```
ux_and_doc_truthup: clauderize init --list-hosts (cli._print_host_list). Doctor verifies configured host (P10 branch: per-host MCP presence + floor). L-21 doc sweep: README CLI block (+--host/--list-hosts, full-footprint uninstall line), README switch-hosts/uninstall prose, UPGRADING uninstall section (full footprint, manual rm -rf removed), TRUST.md + SECURITY.md (P12), CHANGELOG Unreleased extended P7-P12 with honest wiring-vs-consumption verification note. Lessons L-29 (destructive-op isolation) + L-30 (subagent artifact isolation) promoted to docs/LESSONS.md (16->18). Suite 542.
release_gate_state: ASSEMBLED (automatable): CHANGELOG Unreleased through P7-P12; wiring-contract CI evidence (wiring_contract_sweep green for all auto-write hosts); suite 483->542; branch cross-host-cross-model with per-phase commits. PENDING (irreducibly manual / user's): (1) the four-registry sweep + tag + GitHub Release + PyPI publish (L-08, irreversible — must run release-check + every CI host leg green BEFORE tagging per L-20); (2) real-host consumption evidence + non-Claude-model drive (O-07/O-11, D-032 manual); (3) merge cross-host-cross-model -> main. NOT executed autonomously: the release push is outward-facing/irreversible and the real-host proof needs the user's machine.
host_target_strip_resolution: The P9 cross-version host_target-strip finding is now structurally resolved with two fixes. (1) DETECT (commit on cli.py): doctor's claude-code branch warns 'host_target was likely stripped — re-run clauderize init --host <name>' when per-host wiring exists but host_target defaulted, instead of the misleading bare 're-run init'. (2) PREVENT (commit 3776463): Config.load captures unmodeled keys/sections into Config.extra and to_toml re-emits them, so every config-write path (init, the cz_create_gameplan active_gameplan flip — the smoking gun — and merge_missing) preserves forward/cross-version data; a future engine can no longer silently drop an unrecognized field. Byte-identical when no extras (idempotency safe). Audited all other engine-rewritten files (frontmatter, per-host JSON, .mcp.json/.claude hooks, profile.lock, index.json) — all already preserve unmodeled data; config.toml was the only typed-model surface. The already-stripped 0.15.0 case can't be retro-fixed (the data is gone) but self-heals on `init --host` + is now caught by doctor. Suite 543 -> 548.
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
