# STORM-inspired curation methods — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-18

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Perspective-guided planning and multi-LM guidance | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Gap-finder: graph-adjacency surfacing in cz_analyze | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Provenance on lessons and decisions | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Docs, CHANGELOG, and final cascade | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
new-gameplan skill: src/clauderizer/skills/clauderizer-new-gameplan/SKILL.md (+ .claude mirror, byte-identical) — rewritten to 7 steps: perspective interrogation (step 3, 7 lenses) + multi-LM fan-out note + cz_analyze `adjacent` gap-finder cross-ref; synthesis step (5) routes findings to decisions/phases/open-items.
test command: .venv/bin/python -m pytest (run from ~/Clauderizer in WSL). pytest.ini addopts already sets -q; do NOT pass another -q (becomes -qq and suppresses the summary line). Baseline: 289 passed, 4 skipped.
```

### Phase 1 Outputs

```
gap-finder (cz_analyze adjacent): analyze.adjacent_entities() in src/clauderizer/analyze.py — one-hop graph adjacency (deps + dependents) seeded by entities named in the text and entities introduced_by a surfaced decision; surfaced via ops.cz_analyze (single backend for the MCP tool AND `clauderize ops`), result key `adjacent` = [{id,type,status,via}], gap-aware prompt + summary count. Stdlib only, no new deps, advisory (INVARIANT-05). Live CLI proof: "subsys.rituals" -> [subsys.graph, subsys.markdown-core, subsys.mcp-server].
test count: 294 passed, 4 skipped (was 289/4; +5 tests in tests/test_analyze.py: adjacency hit, exclude-already-named, honest-empty, introduced_by bridge, cz_analyze op surface).
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
