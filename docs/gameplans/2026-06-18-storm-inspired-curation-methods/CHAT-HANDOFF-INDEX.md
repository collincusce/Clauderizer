# Chat Handoff Index — STORM-inspired curation methods

> Last updated: 2026-06-18
> Status: Phase 2 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 289

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
| 0 | Perspective-guided planning and multi-LM guidance | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Gap-finder: graph-adjacency surfacing in cz_analyze | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Provenance on lessons and decisions | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Docs, CHANGELOG, and final cascade | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-18

Imported STORM's perspective-guided question-asking (#1) and multi-LM cost-split (#5) into the clauderizer-new-gameplan skill — a pure skill rewrite, zero engine change. The skill now interrogates a goal from seven named lenses (security/data, performance/scale, ops/release, testing, cost/dependencies, failure-modes, prerequisite-chains) before phases are drafted, runs them as a cheap fan-out with the strong model reserved for synthesis, vets against recorded memory with cz_analyze, and forward-references the `adjacent` gap-finder built in Phase 1. Source was edited first then mirrored byte-identical to .claude/ (L-16); the only skill test (existence check in test_init) is unaffected. Full suite green: 289 passed, 4 skipped.

### Phase 1 — completed 2026-06-18

Built the gap-finder (D-018): analyze.adjacent_entities() surfaces one-hop graph neighbors of what a text touches but hasn't named — seeded by entities named verbatim in the text and by entities introduced_by a keyword-surfaced decision (the introduced_by bridge from the flat-doc ADR world into the graph). It excludes seeds and already-named ids, returns {id,type,status,via}, and is honestly empty when nothing relates. Surfaced through ops.cz_analyze — the single backend shared by the MCP tool and `clauderize ops` — with a gap-aware prompt and a "+N adjacent" summary count. Pure stdlib, zero new deps, advisory only (INVARIANT-05). Live CLI run on this repo: "a change to subsys.rituals" returned adjacent [subsys.graph, subsys.markdown-core, subsys.mcp-server]. Tests +5 (adjacency hit, exclude-named, empty, introduced_by bridge, ops surface); full suite 294 passed, 4 skipped.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

### Category: Design

**1.** Decisions and invariants are flat-doc entries (### D-NNN in DECISIONS.md), not graph nodes — so to walk the project graph from a keyword-surfaced decision you must bridge through a node's `introduced_by` frontmatter, the only structural link from an ADR into the graph. The gap-finder (D-018) keyword-ranks decisions, then bridges + walks one hop. Structural graph adjacency is the embedding-free way to surface "related but not yet connected" (the complement to keyword-overlap relevance).
