# Chat Handoff Index — Cross-host & cross-model Clauderizer (universal AGENTS.md + MCP substrate)

> Last updated: 2026-06-21
> Status: Phase 7 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 479

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
| 2 | AGENTS.md canonical substrate & Tier-4 floor | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-2-HANDOFF.md |
| 3 | MCP middle tiers: prompts, auto-load resource & tier routing | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Floor-host wiring emitters (AGENTS.md+MCP hosts) + uninstall & coexistence | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Bespoke-host wiring emitters (native rule formats & deeper integration) | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-5-HANDOFF.md |
| 6 | Cross-host verification execution & release gate | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-6-HANDOFF.md |
| 7 | Server-side session bootstrap (fast-follow; non-gating) | ⬜ NOT STARTED | — | — | handoffs/PHASE-7-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-21

Phase 0 re-derived the per-host capability matrix from primary sources and corrected two load-bearing premises. (1) Lifecycle hooks are NOT Claude-Code-only: ~9 hosts (Copilot, Codex, Gemini CLI, Windsurf, Cline, Amp, plus Claude Code/kimi, possibly Cursor) ship SessionStart/UserPromptSubmit-class hooks, so deterministic Tier-1 injection is broadly reachable - a major upgrade to the lose-nothing goal. (2) No host auto-loads MCP resources, so Tier 2 was retired before any code was written. The ladder was revised (new decision supersedes D-030), the P7 server-side bootstrap promoted to primary automatic fallback for hook-less hosts, and scope cut 13->11 (Roo Code archived, Aider lacks MCP). The zero-dep invariant survives (JSON auto-write; Continue via JSON; TOML hosts guide-only). Deliverables: docs/CROSS-HOST.md (three-axis host model, verified matrix, revised ladder, format audit, verification strategy, release decisions), a CHANGELOG Unreleased stub, and a dogfood fix to the new-gameplan skill (commit-the-plan step 8) for the clean_tree friction hit at this phase own preflight. No engine code changed; baseline remains 446 tests.

### Phase 1 — completed 2026-06-21

Phase 1 built the cross-host injection substrate. New session.py holds the at-most-once delivery signal (INVARIANT-08): a process-global, in-memory, never-persisted flag, plus the host gate (delivers_status_via_hook: the 8 hook hosts vs the rest) and the compact write-first note (D-027). mcp_server._deliver_aware wraps tool registration via functools.wraps so the MCP schemas are byte-identical (a build-guard test proves the wrapped server still constructs - INVARIANT-07); status reads mark the signal, and on a hook-less host a write issued before any status load gets a one-line status note prepended. config.py gained host_target (the third host axis, D-028; default claude-code preserves exact Claude Code behaviour and back-compat). Idempotency/re-entrancy of the real read tools is proven by test (cz_status called repeatedly and with the signal toggled returns identical results). The tool surface was found ALREADY model-neutral (only cz_mine_failures is Claude-specific, legitimately - it mines Claude Code transcripts); no rewrite was needed, and a static guard test locks it (criteria 4/5, D-032). Suite 446 -> 462 (16 new), green. No Claude Code behaviour changed: the gate is off for the default host_target.

### Phase 2 — completed 2026-06-21

Phase 2 made the shared stanza host-neutral and added the Tier-4 floor. The old stanza claimed the SessionStart hook injects status automatically - true only on hook hosts; a Cursor/Continue/Zed agent was told memory had loaded when it had not. The new stanza conditions on whether the [Clauderizer] digest appeared: if it did, the host has a hook and memory is loaded; if not, call cz_status now before anything else. That one host-neutral floor reaches every host that reads AGENTS.md. Mechanism decision D-035: kept the existing single-source dual-write (one template renders both CLAUDE.md and AGENTS.md) rather than the symlink/@import the criteria proposed - symlinks are fragile on the Windows/WSL dogfood host and @import adds a parity dependency, while single-source already gives no-drift (L-16). Strictly additive: Claude Code still gets its digest via the hook (INVARIANT-07 intact). Template + live CLAUDE.md + AGENTS.md synced; a guard test locks the floor presence and neutrality. Suite 462 -> 463. Floor-Release milestone (docs/CROSS-HOST.md sections 4-5) is now real: every AGENTS.md-native host reaches Tier 4 with zero per-host code; full host round-trip verification is P6.

### Phase 3 — completed 2026-06-21

Phase 3 added the Tier-3 prompt mechanism and the tier-routing function. Two MCP prompts (cz-status, cz-next-phase) are registered on the server; on prompt-supporting hosts (Cursor, Copilot, Continue, Gemini, Zed) they surface as /cz-status etc. - a one-shot pull of memory where no hook does it. Invoking one marks the P1 delivery signal so the write-first self-correction and the P7 bootstrap do not double-fire (INVARIANT-08). session.best_tier(host_target) returns the highest reachable tier (1 hook / 3 prompt / 4 floor); Tier-2 (auto-resource) stays retired (D-034). Unknown hosts downgrade safely to the floor; capability is read fresh per call (the stateless server has no stale cache to re-probe). Also fixed forward a brittle P2 guard test that asserted a phrase the template wraps across a line - it shipped RED in 00159ef because P2 was closed on an unreliable ad-hoc shell exit read instead of cz_preflight (correction recorded). Verified this time with cz_preflight, the authoritative gate.

### Phase 4 — completed 2026-06-21

Phase 4 built the per-host wiring emitters. hosttargets.py: HOST_EMITTERS table (verified key/path per host), emit_mcp() writing/merging the clauderizer MCP registration into each host project config NON-DESTRUCTIVELY (preserving every other server, D-031), remove_mcp() for uninstall. Emitted command is the portable uvx form (machine-independent); emit_mcp REFUSES an absolute/venv/wsl.exe command (is_path_safe). Auto-write hosts: cursor, copilot (servers key), continue, zed (context_servers), gemini-cli, cline, amp (amp.mcpServers). Guide-only: codex, windsurf, kimi (TOML/global, O-04). New CLI clauderize uninstall [--host] removes only the clauderizer key. Coexistence two-level: different files per host, other servers survive within a file. Finding: dogfood .mcp.json carries the machine-specific path the emitter prevents (deferred). 9 tests; cz_preflight green.

### Phase 5 — completed 2026-06-21

Phase 5 handled the bespoke hosts - those needing more than AGENTS.md+MCP. Two non-AGENTS.md hosts (Continue, Gemini) get the Tier-4 floor auto-written into their NATIVE instructions file (.continue/rules/clauderizer.md, GEMINI.md) via a marker-block upsert that preserves the user's content and is idempotent. The hook-capable hosts (Copilot, Codex, Windsurf, Cline, Amp - they have SessionStart-class hooks for Tier 1) get a per-host hook SETUP GUIDE rather than an auto-written config: each host's hook config schema differs and is unverified (O-02 residual), so per D-031 we ship a guide (the kimi pattern) with the clauderizer-hook command + the host's event names, rather than emit a config that might be wrong. emit_instructions + hook_setup_guide added to hosttargets.py; 4 tests. Each bespoke host now reaches its best achievable tier: Tier 1 via guided hook wiring, or the native-file floor (Tier 4) plus /cz-status (Tier 3). Verified with cz_preflight.

### Phase 6 — completed 2026-06-21

Phase 6 stood up the verification gate. wiring_contract_sweep() is the in-process host-simulator (D-032): for every auto-write host it emits the config, reads it back, and confirms the clauderizer entry is well-formed, path-safe, and launches clauderizer-mcp - the WIRING CONTRACT. It runs in CI through the test suite, so the gate is green only when every host's emitted config passes. path_safety_audit() scans committed configs for machine-specific absolute paths (catches the O-06 leak). Per D-032 the gate is the wiring contract, not a live launch: actually launching the stdio server to round-trip cz_status, and proving a REAL host reads the config, is consumption proof - irreducibly manual on the ~9 proprietary hosts and deferred to pre-GA (O-07). CHANGELOG Unreleased updated with the cross-host deliverables; the four-registry release sweep (L-20) is a release-time step. 3 tests; suite green via cz_preflight.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

**1.** Verify per-host capabilities from each host own docs before encoding feature-X-is-unique-to-host-Y into architecture; absence of evidence is not evidence of absence. The Phase 0 matrix re-derivation existed precisely to catch this.

**2.** Do not design a delivery tier around an unverified host behavior; confirm the mechanism exists on at least one target host before giving it a phase.

**3.** A new gameplan must be committed before its first do-phase. Fixed: added step 8 (Commit the plan before executing) to clauderizer-new-gameplan source + rendered (L-16), including the rule to separate pre-existing unrelated changes into their own commit.

**5.** Close every phase with cz_preflight (the engine gate that runs AND parses the suite), never an ad-hoc 'pytest > file; EXIT=$?' through wsl.exe - that capture is flaky. And make guard assertions whitespace-robust: normalize with ' '.join(text.split()) before matching a multi-word phrase, because markdown wraps lines.

### Category: Testing

**4.** A neutrality / token-exclusion check false-positives when the product name CONTAINS the forbidden token as a substring: asserting 'Claude' not in text trips on 'Clauderizer'. Strip the product name(s) before the standalone-token check (text.replace('Clauderizer','')). The code was correct (the note says [Clauderizer]); only the test was wrong - a reminder that a guard assertion is itself code that needs the obvious edge case. *(evidence: tests/test_session_signal.py test_session_note_is_host_neutral, P1)*
