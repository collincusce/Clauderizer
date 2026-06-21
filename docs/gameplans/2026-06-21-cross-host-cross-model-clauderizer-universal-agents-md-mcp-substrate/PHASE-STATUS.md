# Cross-host & cross-model Clauderizer (universal AGENTS.md + MCP substrate) — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-21

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Host model, capability audit & parity contract | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Model-agnostic protocol hardening & injection-delivery signal | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-1-HANDOFF.md |
| 2 | AGENTS.md canonical substrate & Tier-4 floor | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | MCP middle tiers: prompts, auto-load resource & tier routing | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Floor-host wiring emitters (AGENTS.md+MCP hosts) + uninstall & coexistence | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Bespoke-host wiring emitters (native rule formats & deeper integration) | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Cross-host verification execution & release gate | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |
| 7 | Server-side session bootstrap (fast-follow; non-gating) | ⬜ NOT STARTED | — | — | handoffs/PHASE-7-HANDOFF.md |

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
