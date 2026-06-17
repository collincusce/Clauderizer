# Chat Handoff Index — spec-kit-discipline-gates

> Last updated: 2026-06-17
> Status: Phase 3 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 273

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
| 0 | Clarify gate: structured open items (O-NN) + judgment-based surfacing | ✅ COMPLETE | 2026-06-17 | 2026-06-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Exit-criteria gate: machine-checkable phase criteria + surfacing at completion | ✅ COMPLETE | 2026-06-17 | 2026-06-17 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Analyze gate: surface conflicting invariants/decisions for agent judgment | ✅ COMPLETE | 2026-06-17 | 2026-06-17 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Integration & docs: wire gates into rituals/skills/digest, document to code | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-17

Phase 0 shipped the clarify gate: structured open items. Two blessed mutations — add_open_item (auto-numbered O-NN appended to the GAMEPLAN 'Open Items' section via next_numbered_id + append_to_section, with an optional phase tag) and resolve_open_item (idempotent in-place _(resolved date: ...)_ marker, never deletes) — exposed as cz_add_open_item / cz_resolve_open_item on the shared MCP+CLI registry (parity test green). cz_status now reports unresolved open items (bundle['open_items'] + a digest line), and transition_phase to complete surfaces the unresolved items relevant to that phase in a new result['advisories']=[{kind,ids,message}] field: advisory and non-blocking per INVARIANT-05, and the shared surfacing shape Phases 1-2 reuse. All per D-015 (no config flags, judgment-based) and D1 (reuse existing markdown conventions, no new schema). Suite 266 -> 273 (+7), 4 skipped, zero regressions.

### Phase 1 — completed 2026-06-17

Phase 1 shipped the exit-criteria gate. cz_set_exit_criteria authors/replaces a phase's exit criteria as machine-checkable - [ ] items (preserving the checked state of unchanged text); cz_check_exit_criterion toggles one by substring (idempotent). Both operate on the GAMEPLAN 'Phase Breakdown' blocks (D1: reuse existing checkboxes) and ride the shared MCP+CLI registry (parity green). cz_transition_phase to complete now appends a kind:exit_criteria advisory listing the phase's unchecked criteria, alongside Phase 0's open_items advisory in the shared result['advisories'] shape — advisory and non-blocking (INVARIANT-05); test-ish criteria auto-link to the measured baseline count (the D-015 'be intelligent' bit). status_bundle parsers skip scaffold placeholders so a fresh phase never nags about the _(verifiable)_ template line. Suite 273 -> 279 (+6), 4 skipped, zero regressions.

### Phase 2 — completed 2026-06-17

Phase 2 shipped the analyze gate — spec-kit's /analyze adapted to Clauderizer's judgment-based grain (D-016). New module analyze.py surfaces the existing decisions/invariants most relevant to a piece of text by lexical overlap (keyword + entity-id, ADR boilerplate stopped, ranked + capped top-k) — no embeddings, no new dependency (L-14, resolving O-01 as gameplan decision D2). cz_analyze (read-op, parallel to cz_graph_query) returns candidates + a verdict prompt; cz_add_decision now enriches its result with related/possibly-superseded entries so a conflict is noticed at write time. Both are advisory and judgment-based — the engine surfaces, the agent rules; never a deterministic contradiction-detector (D-016), never blocking (INVARIANT-05). Registry 29 tools (parity green). Phase 2's own exit criteria (machine-checkable since Phase 1) were checked off with cz_check_exit_criterion and the phase completed clean — the three gates dogfooding one another. Suite 279 -> 283 (+4), 4 skipped, zero regressions.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

**1.** When an exploration subagent maps an unfamiliar codebase to ground a plan, treat its file:line claims as leads to verify, not facts. The spec-kit-gates map asserted tests/test_blessed_surfaces.py held the MCP/CLI parity test; it was actually tests/test_ops.py (test_registry_is_exactly_the_tool_surface), so editing on the map alone would have changed the wrong test. Fan-out exploration locates code fast; confirm which file does what at the point of edit.

### Category: Design

**2.** An always-on advisory that reads existing markdown must exclude scaffold placeholders (_(...)_), or every fresh gameplan surfaces its template placeholder as a real finding. Adding a new surfacing source turns previously-inert scaffold into live input — the existing suite caught this the moment exit-criteria surfacing landed (write→read→rewrite tests earn their keep on cross-feature interactions, not just the happy path).
