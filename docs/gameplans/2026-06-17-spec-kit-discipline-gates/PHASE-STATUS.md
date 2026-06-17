# spec-kit-discipline-gates — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-17

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Clarify gate: structured open items (O-NN) + judgment-based surfacing | ✅ COMPLETE | 2026-06-17 | 2026-06-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Exit-criteria gate: machine-checkable phase criteria + surfacing at completion | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Analyze gate: surface conflicting invariants/decisions for agent judgment | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Integration & docs: wire gates into rituals/skills/digest, document to code | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
new-tools: cz_add_open_item + cz_resolve_open_item — O-NN open items as **O-NN.** lines in GAMEPLAN.md 'Open Items'; on the shared MCP+CLI registry (test_ops parity green).
advisory-shape: Established result['advisories']=[{kind,ids,message}] in transition_phase: completing a phase surfaces unresolved open items relevant to it (tagged-to-phase or untagged), advisory and non-blocking per INVARIANT-05. Phases 1-2 reuse this shape for unchecked exit-criteria and candidate conflicts.
surfacing-helpers: status_bundle.open_items()/unresolved_open_items(gameplan_dir, phase) parse the section; cz_status bundle gains open_items (unresolved ids) + a digest 'Open items:' line.
test-count: 266 -> 273 (+7 in tests/test_open_items.py), 4 skipped, 0 regressions; registry-parity + MCP-list tests green.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
