# Chat Handoff Index — STORM self-critique gate

> Last updated: 2026-06-18
> Status: Phase 2 ready

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
| 0 | Synthesis-quality skill refinements | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Self-critique rubric gate (cz_critique) | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Docs, CHANGELOG, cascade, and close | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-18

Imported STORM's remaining skill-level refinements. The new-gameplan skill now derives interrogation lenses from related graph entities via cz_graph_query (STORM's perspective-discovery-from-related-articles, adapted to the dependency graph), not only the fixed lens list. The close-gameplan (post-mortem) and do-phase (handoff Phase Notes) skills now prescribe outline-before-synthesize for long-form writing — STORM treats the outline as a separable, quality-predictive stage. Pure skill edits: source edited first, then mirrored byte-identical to .claude/ (L-16), verified by diff -rq across the whole skills tree (ALL-SKILLS-IDENTICAL). No engine change; suite 300 passed, 4 skipped.

### Phase 1 — completed 2026-06-18

Built cz_critique (D-019), the STORM reference-free self-critique gate: a read-only, advisory tool that assembles a Coverage/Coherence/Grounding rubric for a target (phase, gameplan, or handoff) by composing signals the engine already computes — unresolved open items + unchecked exit criteria (Coverage), graph drift + pending cascades (Coherence), and lessons lacking provenance (Grounding, the D-017 tie-in) — and surfaces it with a grading prompt for the agent. Lives in rituals/critique.py; wired into the shared ops REGISTRY + tools_list (registry parity unchanged — appended to both in the same position). Stdlib only, no embeddings, never scores or blocks (INVARIANT-05). Proven live via clauderize ops on this gameplan (12 Coverage gaps, Coherence/Grounding clean — accurately flagging the then-incomplete phases). A test bug surfaced and fixed: mutations.create_gameplan does not flip active_gameplan (the ops layer does), so the helper must point config at the fresh gameplan. Tests +4; full suite 304 passed, 4 skipped.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** A blessed-write helper can split responsibility across layers: mutations.create_gameplan scaffolds the gameplan, but the ops wrapper (ops.cz_create_gameplan) is what flips config.active_gameplan. A caller that drives the mutation layer directly gets a gameplan that is NOT active, so it silently operates on whatever gameplan was active before (in tests, the fixture's). Exercise the layer that owns the side effect, or set the state the wrapper would. Sibling to L-15: verify a layer's real behavior at the point of use. *(evidence: tests/test_critique.py _fresh helper + ops.py line 232 (config.active_gameplan = result gameplan_id); surfaced as 3 failing critique tests before the fix)*
