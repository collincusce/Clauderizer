# Chat Handoff Index — Cross-host & cross-model Clauderizer (universal AGENTS.md + MCP substrate)

> Last updated: 2026-06-21
> Status: Phase 2 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 446

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
| 0 | Host model, capability audit & parity contract | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Model-agnostic protocol hardening & injection-delivery signal | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-1-HANDOFF.md |
| 2 | AGENTS.md canonical substrate & Tier-4 floor | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | MCP middle tiers: prompts, auto-load resource & tier routing | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Floor-host wiring emitters (AGENTS.md+MCP hosts) + uninstall & coexistence | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Bespoke-host wiring emitters (native rule formats & deeper integration) | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Cross-host verification execution & release gate | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |
| 7 | Server-side session bootstrap (fast-follow; non-gating) | ⬜ NOT STARTED | — | — | handoffs/PHASE-7-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-21

Phase 0 re-derived the per-host capability matrix from primary sources and corrected two load-bearing premises. (1) Lifecycle hooks are NOT Claude-Code-only: ~9 hosts (Copilot, Codex, Gemini CLI, Windsurf, Cline, Amp, plus Claude Code/kimi, possibly Cursor) ship SessionStart/UserPromptSubmit-class hooks, so deterministic Tier-1 injection is broadly reachable - a major upgrade to the lose-nothing goal. (2) No host auto-loads MCP resources, so Tier 2 was retired before any code was written. The ladder was revised (new decision supersedes D-030), the P7 server-side bootstrap promoted to primary automatic fallback for hook-less hosts, and scope cut 13->11 (Roo Code archived, Aider lacks MCP). The zero-dep invariant survives (JSON auto-write; Continue via JSON; TOML hosts guide-only). Deliverables: docs/CROSS-HOST.md (three-axis host model, verified matrix, revised ladder, format audit, verification strategy, release decisions), a CHANGELOG Unreleased stub, and a dogfood fix to the new-gameplan skill (commit-the-plan step 8) for the clean_tree friction hit at this phase own preflight. No engine code changed; baseline remains 446 tests.

### Phase 1 — completed 2026-06-21

Phase 1 built the cross-host injection substrate. New session.py holds the at-most-once delivery signal (INVARIANT-08): a process-global, in-memory, never-persisted flag, plus the host gate (delivers_status_via_hook: the 8 hook hosts vs the rest) and the compact write-first note (D-027). mcp_server._deliver_aware wraps tool registration via functools.wraps so the MCP schemas are byte-identical (a build-guard test proves the wrapped server still constructs - INVARIANT-07); status reads mark the signal, and on a hook-less host a write issued before any status load gets a one-line status note prepended. config.py gained host_target (the third host axis, D-028; default claude-code preserves exact Claude Code behaviour and back-compat). Idempotency/re-entrancy of the real read tools is proven by test (cz_status called repeatedly and with the signal toggled returns identical results). The tool surface was found ALREADY model-neutral (only cz_mine_failures is Claude-specific, legitimately - it mines Claude Code transcripts); no rewrite was needed, and a static guard test locks it (criteria 4/5, D-032). Suite 446 -> 462 (16 new), green. No Claude Code behaviour changed: the gate is off for the default host_target.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

**1.** Verify per-host capabilities from each host own docs before encoding feature-X-is-unique-to-host-Y into architecture; absence of evidence is not evidence of absence. The Phase 0 matrix re-derivation existed precisely to catch this.

**2.** Do not design a delivery tier around an unverified host behavior; confirm the mechanism exists on at least one target host before giving it a phase.

**3.** A new gameplan must be committed before its first do-phase. Fixed: added step 8 (Commit the plan before executing) to clauderizer-new-gameplan source + rendered (L-16), including the rule to separate pre-existing unrelated changes into their own commit.

### Category: Testing

**4.** A neutrality / token-exclusion check false-positives when the product name CONTAINS the forbidden token as a substring: asserting 'Claude' not in text trips on 'Clauderizer'. Strip the product name(s) before the standalone-token check (text.replace('Clauderizer','')). The code was correct (the note says [Clauderizer]); only the test was wrong - a reminder that a guard assertion is itself code that needs the obvious edge case. *(evidence: tests/test_session_signal.py test_session_note_is_host_neutral, P1)*
