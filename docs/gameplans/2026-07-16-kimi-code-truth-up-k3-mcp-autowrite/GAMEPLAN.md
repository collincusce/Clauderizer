# kimi-code-truth-up-k3-mcp-autowrite Gameplan

> Created: 2026-07-16
> Status: Complete
> Kind: driven
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

_(1–2 paragraphs: what this gameplan accomplishes.)_

## Subsystems Touched

_(list the subsystems/features this gameplan affects.)_

## Source-of-Truth Captures

_(Real values captured from real systems at gameplan start. Authority over the
gameplan body. Account IDs, ARNs, baseline test counts, versions.)_

## Amendments

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

**O-01.** _(phase 0)_ Verify current Kimi Code CLI session-start hook contract before finalizing the setup guide: the legacy kimi-setup guide claims SessionStart/PreCompact/PostCompact/UserPromptSubmit all inject stdout on exit 0, but the 2026-07-16 docs excerpt only confirmed a PreToolUse example and did not state the exit-0 stdout->context injection rule. Confirm the real supported event names and injection semantics for the current Kimi Code CLI; correct the guide's 4-event claim if wrong. _(resolved 2026-07-16: Verified from Kimi Code CLI hooks docs (moonshotai.github.io/kimi-code customization/hooks): 13 hook events exist incl SessionStart, UserPromptSubmit, PreCompact, PostCompact; a hook's stdout is injected into context iff it exits 0 (exit 2 => stderr fed back as correction). The digest-relevant 4-event set the guide wires is therefore correct. Hooks live in ~/.kimi-code/config.toml [[hooks]] (event/command/matcher/timeout) — TOML, so session-start stays guide-only.)_

## Phase Breakdown

### Phase 0: Confirm current Kimi Code CLI contract

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Project MCP config path + top-level key confirmed from Kimi Code CLI docs: .kimi-code/mcp.json, key = mcpServers, entry = {command,args}
- [x] Global vs project config paths confirmed: ~/.kimi-code/config.toml (global) and .kimi-code/local.toml (project)
- [x] Session-start hook event names verified: whether SessionStart/PreCompact/PostCompact/UserPromptSubmit are all supported and whether their stdout injects on exit 0 (correct the guide if the 4-event claim is wrong)
- [x] O-01's blocking unknown (undocumented MCP schema) is confirmed resolved, or a residual open item captures whatever is still unknown

### Phase 1: Flip kimi MCP to auto-write .kimi-code/mcp.json

**Goal**: Change the kimi HostEmitter to auto_write=True at .kimi-code/mcp.json (mcpServers key). Update detect_host_target coverage (kimi now auto-detectable via its unshared config), the golden guide-only test (drop kimi), and add tests: kimi emit_mcp writes .kimi-code/mcp.json non-destructively, uninstall removes only clauderizer, path_safety_audit + wiring_contract_sweep cover kimi.
**Depends on**: Confirm current Kimi Code CLI contract.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] kimi HostEmitter has auto_write=True, config_path='.kimi-code/mcp.json', servers_key='mcpServers'
- [x] emit_mcp('kimi', repo) writes .kimi-code/mcp.json with the portable command, preserving other servers; remove_mcp removes only clauderizer
- [x] test_guide_only_hosts_write_nothing no longer lists kimi; a new test asserts kimi auto-writes and round-trips
- [x] wiring_contract_sweep and path_safety_audit include and pass for kimi; detect_host_target auto-detects a kimi-wired repo
- [x] Full suite green (baseline 793 passed / 5 skipped, plus new kimi tests)

### Phase 2: Reconcile kimi setup guides and fix stale .kimi paths

**Goal**: Correct every stale .kimi -> .kimi-code reference in src (init.py _render_kimi_setup, paths.py kimi_setup, hosttargets configure_hints, HostEmitter note). Reconcile the two drifting guides (kimi-setup.md vs kimi-mcp-setup.md) into one coherent guide that states: MCP is now auto-written, session-start hooks go in ~/.kimi-code/config.toml [[hooks]] with the verified event set. No dead .kimi path remains in src.
**Depends on**: Flip kimi MCP to auto-write .kimi-code/mcp.json.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] grep for '.kimi/' and '~/.kimi/config.toml' in src/ returns no stale references (all -> .kimi-code)
- [x] The two kimi guides are reconciled: one coherent generated guide stating MCP is auto-written and hooks go in ~/.kimi-code/config.toml with the verified event set
- [x] configure_hints and paths.py reference the correct .kimi-code paths and the reconciled guide filename
- [x] Suite green; a test asserts the guide names .kimi-code (not .kimi) and is non-destructive/repo-local

### Phase 3: Docs sweep, cascade, and release

**Goal**: Sweep the non-single-sourced docs (L-21): CROSS-HOST.md kimi row (MCP guide->auto-write, .kimi-code path), TRUST.md, VISION.md, README MCP-surface/host list, CHANGELOG. Resolve open item O-01. Bump subsys.scaffold and run cz_cascade over its dependents, resolving verdicts. Confirm full suite green and version bump.
**Depends on**: Reconcile kimi setup guides and fix stale .kimi paths.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] CROSS-HOST.md kimi row shows MCP=auto-write and the .kimi-code path; TRUST.md/VISION.md/README host+MCP-surface updated; CHANGELOG entry added
- [x] Open item O-01 resolved via cz_resolve_open_item
- [x] subsys.scaffold version bumped; cz_cascade run over its dependents and all verdicts resolved via cz_resolve_cascade
- [x] Version bumped (pyproject.toml) and full suite green
- [x] No stale '.kimi/' reference remains anywhere in docs (except append-only history)
