# spec-kit-discipline-gates — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-17

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Clarify gate: structured open items (O-NN) + judgment-based surfacing | ✅ COMPLETE | 2026-06-17 | 2026-06-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Exit-criteria gate: machine-checkable phase criteria + surfacing at completion | ✅ COMPLETE | 2026-06-17 | 2026-06-17 | handoffs/PHASE-1-HANDOFF.md |
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

### Phase 1 Outputs

```
new-tools: cz_set_exit_criteria (author/replace a phase's - [ ] list, preserving checked-state of unchanged text) + cz_check_exit_criterion (toggle by substring, idempotent). On the shared MCP+CLI registry; tool surface now 28 (parity green).
surfacing: transition_phase->complete appends a kind:exit_criteria advisory (the phase's unchecked criteria) to result['advisories'] alongside open_items; test-ish criteria (/test|suite|baseline/) auto-link to the measured baseline count. status_bundle.exit_criteria/unchecked_exit_criteria parse the Phase Breakdown blocks and SKIP scaffold placeholders.
test-count: 273 -> 279 (+6 tests/test_exit_criteria.py), 4 skipped, 0 regressions; registry-parity + MCP-list tests green.
```

## Corrections Log

### C-01 — Phase 1

**Phase**: 1
**What gameplan said**: Phase 1: a blessed write toggles an exit criterion (criteria assumed to already exist).
**What was actually correct**: Two writes were needed: cz_set_exit_criteria to AUTHOR/replace a phase's criteria (no blessed write populated them — only the template _(verifiable)_ placeholder existed, and hand-edits are forbidden), plus cz_check_exit_criterion to toggle. Surfacing also had to skip scaffold placeholders so completing a fresh phase does not nag about _(verifiable)_.
**Why**: Criteria-authoring had no blessed path; and adding an always-on surfacing source turned the previously-inert template placeholder into a live unchecked-criterion finding (the Phase 0 suite caught it immediately).
