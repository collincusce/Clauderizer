# STORM-inspired curation methods — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-18

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Perspective-guided planning and multi-LM guidance | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Gap-finder: graph-adjacency surfacing in cz_analyze | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Provenance on lessons and decisions | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Docs, CHANGELOG, and final cascade | ✅ COMPLETE | 2026-06-18 | 2026-06-18 | handoffs/PHASE-3-HANDOFF.md |

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

### Phase 2 Outputs

```
provenance (evidence field): Optional `evidence` arg on cz_add_lesson (renders inline *(evidence: ...)*, survives handoff rollup) and cz_add_decision (renders an **Evidence**: field). Additive/backward-compatible (omitted = byte-identical to today); written via mutations + markdown/writer.py (INVARIANT-02). MCP schema auto-derives the param from the function signature (test_ops parity updated). Dogfooded live via `clauderize ops` -> gameplan lesson #2 carries evidence into the Phase 3 handoff.
test count: 300 passed, 4 skipped (was 294/4; +6 in tests/test_provenance.py; tests/test_ops.py schema spot-check updated to include the new evidence param).
```

### Phase 3 Outputs

```
release staged (not released): Version 0.11.0 -> 0.12.0 in pyproject.toml + src/clauderizer/__init__.py (MINOR, additive). CHANGELOG [0.12.0] entry added (versioned-entry convention). Editable install reinstalled (`pip install -e . --no-deps`) to sync dist-info, which doctor's identity check requires. NOT released: no tag/push — release is the gated `clauderize release-check` ritual, left to the user.
docs + graph: ARCHITECTURE.md: analyze gate gains the `adjacent` gap-finder (D-018) + a new Provenance (D-017) subsection. subsys.mutations 0.5.0 -> 0.6.0; cascade to dependent subsys.mcp-server resolved non-breaking (0.6.0 satisfies ^0.1.0; evidence param optional). cz_status: zero pending cascades, no drift.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
