# STORM self-critique gate — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-18

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Synthesis-quality skill refinements | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Self-critique rubric gate (cz_critique) | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Docs, CHANGELOG, cascade, and close | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-2-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
skill refinements: new-gameplan SKILL.md step 3 now also derives lenses from related graph entities (cz_graph_query), not only the fixed lens list. close-gameplan SKILL.md post-mortem step and do-phase SKILL.md handoff-notes step now prescribe outline-before-synthesize. All edits source-first then mirrored; diff -rq src/clauderizer/skills vs .claude/skills = identical.
```

### Phase 1 Outputs

```
cz_critique gate: src/clauderizer/rituals/critique.py + ops.cz_critique (appended to REGISTRY + tools_list TOOL_NAMES; order-sensitive parity test unchanged). Reference-free Coverage/Coherence/Grounding rubric for target = phase | gameplan | handoff, composing status_bundle signals (open items, exit criteria, drift, pending cascades) + lessons-without-evidence (D-017). Read-only, advisory (INVARIANT-05), stdlib. Live CLI: cz_critique gameplan -> 12 Coverage gaps, Coherence/Grounding clean.
test count: 304 passed, 4 skipped (was 300/4; +4 in tests/test_critique.py: structure, coverage-flags, coverage-clears, grounding-flags-and-clears).
```

### Phase 2 Outputs

```
docs + graph: CHANGELOG [0.12.0] extended with cz_critique + the skill refinements (Suite 289 -> 304). ARCHITECTURE: cz_critique added as the 4th discipline gate (D-019). subsys.rituals 0.5.0 -> 0.6.0 (owns rituals/critique.py); cascade to subsys.mcp-server resolved non-breaking. Zero pending cascades.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
