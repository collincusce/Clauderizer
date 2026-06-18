# Chat Handoff Index — STORM-inspired curation methods

> Last updated: 2026-06-18
> Status: All 4 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 300

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
| 2 | Provenance on lessons and decisions | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Docs, CHANGELOG, and final cascade | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-18

Imported STORM's perspective-guided question-asking (#1) and multi-LM cost-split (#5) into the clauderizer-new-gameplan skill — a pure skill rewrite, zero engine change. The skill now interrogates a goal from seven named lenses (security/data, performance/scale, ops/release, testing, cost/dependencies, failure-modes, prerequisite-chains) before phases are drafted, runs them as a cheap fan-out with the strong model reserved for synthesis, vets against recorded memory with cz_analyze, and forward-references the `adjacent` gap-finder built in Phase 1. Source was edited first then mirrored byte-identical to .claude/ (L-16); the only skill test (existence check in test_init) is unaffected. Full suite green: 289 passed, 4 skipped.

### Phase 1 — completed 2026-06-18

Built the gap-finder (D-018): analyze.adjacent_entities() surfaces one-hop graph neighbors of what a text touches but hasn't named — seeded by entities named verbatim in the text and by entities introduced_by a keyword-surfaced decision (the introduced_by bridge from the flat-doc ADR world into the graph). It excludes seeds and already-named ids, returns {id,type,status,via}, and is honestly empty when nothing relates. Surfaced through ops.cz_analyze — the single backend shared by the MCP tool and `clauderize ops` — with a gap-aware prompt and a "+N adjacent" summary count. Pure stdlib, zero new deps, advisory only (INVARIANT-05). Live CLI run on this repo: "a change to subsys.rituals" returned adjacent [subsys.graph, subsys.markdown-core, subsys.mcp-server]. Tests +5 (adjacency hit, exclude-named, empty, introduced_by bridge, ops surface); full suite 294 passed, 4 skipped.

### Phase 2 — completed 2026-06-18

Added optional provenance/citation (D-017, STORM #4): an `evidence` argument on cz_add_lesson and cz_add_decision recording where a lesson/decision came from. Lessons render it inline as *(evidence: ...)* — placed so lesson_state never misreads it as an obsolete/promoted marker — so it survives every handoff rollup unchanged; decisions render an **Evidence**: field. Both are additive and backward-compatible (omitted produces byte-identical output to today) and flow through mutations + markdown/writer.py (INVARIANT-02); the MCP tool schema auto-derives the new param from the function signature (test_ops parity updated, confirming the surface). Verified end-to-end: dogfooded live via `clauderize ops` (a fresh build, since this session's MCP server is pinned to the pre-edit engine) — gameplan lesson #2 was recorded with evidence and rolled into the Phase 3 handoff with its marker intact. Tests +6 (tests/test_provenance.py); full suite 300 passed, 4 skipped.

### Phase 3 — completed 2026-06-18

Closed out the gameplan: documented all three surfaces and staged the release. CHANGELOG gained a [0.12.0] entry (gap-finder, provenance, perspective-planning) in the repo's versioned-entry convention; pyproject + __init__ bumped 0.11.0 -> 0.12.0 (MINOR, additive). The editable install was reinstalled so doctor's dist-info/source identity check stays green — it caught the un-synced metadata immediately (7 doctor tests went red on the source-only bump, then 300 passed after the reinstall: the identity-check lineage doing its job). ARCHITECTURE.md now describes the analyze `adjacent` gap-finder and a Provenance subsection; subsys.mutations bumped to 0.6.0 with its cascade to subsys.mcp-server resolved non-breaking. No release performed (no tag/push) — that is the gated release-check ritual. Full suite 300 passed, 4 skipped; all four phases complete.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

### Category: Design

**1.** Decisions and invariants are flat-doc entries (### D-NNN in DECISIONS.md), not graph nodes — so to walk the project graph from a keyword-surfaced decision you must bridge through a node's `introduced_by` frontmatter, the only structural link from an ADR into the graph. The gap-finder (D-018) keyword-ranks decisions, then bridges + walks one hop. Structural graph adjacency is the embedding-free way to surface "related but not yet connected" (the complement to keyword-overlap relevance).

**2.** When adding an inline marker to a line another parser also reads, place it where it cannot be mistaken for that parser's grammar, and prove both readers still work. Provenance (D-017) appends *(evidence: ...)* to a lesson line; lesson_state reads an (obsolete|promoted ...) marker only at line-end, so the evidence marker parses as ACTIVE and a real state marker still appends after it. Sibling to L-06: one writer, many readers - satisfy every reader's grammar. *(evidence: src/clauderizer/markdown/lesson_state.py + tests/test_provenance.py::test_evidence_marker_is_not_a_lesson_state_marker; recorded live via `clauderize ops` because this session's MCP server is pinned to the pre-edit build)*
