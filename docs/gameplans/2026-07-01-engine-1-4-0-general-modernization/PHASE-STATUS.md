# engine-1.4.0-general-modernization — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-01

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Baselines, design decisions & plan commit | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Scoped memory — write path & near-dup parity | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Scoped memory — read path & curator grouping | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Approval gates — hash-bound exit criteria | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Deliverable-matrix campaigns | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Standing conditions + consumes surfacing | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-5-HANDOFF.md |
| 6 | Corpus modernization framework | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-6-HANDOFF.md |
| 7 | Docs & procedure 1.5.0 & version bump | ⬜ NOT STARTED | — | — | handoffs/PHASE-7-HANDOFF.md |
| 8 | Dogfood & live verification | ⬜ NOT STARTED | — | — | handoffs/PHASE-8-HANDOFF.md |
| 9 | Ship 1.4.0 — release ritual & close-out | ⬜ NOT STARTED | — | — | handoffs/PHASE-9-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
baseline_versions: engine 1.3.1 (pyproject.toml, main @ clean tree 2026-07-01); PROCEDURE_VERSION 1.4.0 (src/clauderizer/__init__.py:12); tool surface 42 (ops.py REGISTRY == tools_list.TOOL_NAMES, test_ops.py:56)
target_versions: engine 1.4.0; PROCEDURE_VERSION 1.5.0; tool surface 44 (+cz_approve_gate, +cz_modernize); new CLI subcommand: clauderize upgrade
baseline_suite: 716 passed (cz_preflight green 2026-07-01 on feat/engine-1.4.0-general-modernization @ d0b3068; profile python, build skip)
```

### Phase 1 Outputs

```
phase1_suite: 725 passed, 5 skipped (716 baseline + 9 new in tests/test_scoped_memory.py); abstract_index SCHEMA_VERSION 1→2; near-dup advisory verified live on the verbatim logo-invariant pair at Jaccard ≥ 0.40 (O-02 evidence)
```

### Phase 2 Outputs

```
phase2_suite: 730 passed, 5 skipped (+5 read-path tests); analyze.scope_filter + handoff audience threading + telemetry same-audience pairing guards; cz_next_phase_context gains audience param (read-only view); written handoff never filtered (C-01)
```

### Phase 3 Outputs

```
phase3_suite: 737 passed, 5 skipped (+7 in tests/test_approval_gates.py); surface 43 (cz_approve_gate, CLI parity verified live); approval staleness is COMPUTED at parse time (no auto-write); preflight appends approval_gates check only when the current phase declares approvals
```

### Phase 4 Outputs

```
phase4_suite: 742 passed, 5 skipped (+5 in tests/test_deliverable_matrix.py); Kind.lifecycle from [lifecycle] statuses; campaign = concept/spec-approved/produced/assembled/qa/shipped; cz_gameplans(gameplan_id=...) detail view with matrix_md; digest rollup ≤1 line only when deliverables exist
```

### Phase 5 Outputs

```
phase5_suite: 748 passed, 5 skipped (+6 in tests/test_standing_conditions.py); rituals/conditions.py probes (30s cap, exit 0 = met); compute(conditions=True) only from cz_status/cz_preflight/cz_loop_step — hook path structurally probe-free; consumes rendering verified end-to-end + version display added (C-02)
```

### Phase 6 Outputs

```
phase6_suite: 754 passed, 5 skipped (+6 tests/test_modernize.py, +1 golden deliberately updated to model a modernized corpus); surface 44 (cz_modernize); live: fresh init stamps 1.4.0, doctor shows advisory line, upgrade --report on THIS repo correctly finds unstamped config + missing kinds dir + proposes standing conditions for the curator loop; discovered pre-existing defect: the 1.3.1 preflight hint referenced a preflight.<kind>.toml.example nothing ever shipped — modernize now actually scaffolds it
```

## Corrections Log

### C-01 — Phase 2

**Phase**: 2
**What gameplan said**: Phase 2 applies audience filtering to both cz_next_phase_context and cz_write_handoff ("cz_next_phase_context/cz_write_handoff with audience=X drop other-audience lessons").
**What was actually correct**: Audience filtering lands on cz_next_phase_context (read-only bundle) only; cz_write_handoff always writes the full unfiltered canonical handoff. handoff.assemble takes the audience param but cz_write_handoff never passes it, and a regression test pins the written file as never-filtered.
**Why**: The handoff FILE is the self-contained cross-session artifact — the module's founding anti-pattern (#2, incomplete lesson propagation) is precisely "a later session missed a lesson because the carrier dropped it." A role-filtered file would silently become the next session's truncated truth. Read-time filtering gives roles their view without ever thinning the durable record (D-043 is filtering at READ time; D-009 propagation stands).

### C-02 — Phase 5

**Phase**: 5
**What gameplan said**: Consumes surfacing must be ADDED: "cz_next_phase_context/handoff renders the gameplan's declared consumed entities … so cross-gameplan consequences are visible where work starts."
**What was actually correct**: handoff.assemble has rendered a "Consumes (Cross-Gameplan)" section with per-entity status since 1.2.0 (_consumes_section), and cz_next_phase_context shares that assembly. Phase 5 verified it end to end with a new test (declare → render → cross-axis transition → pending cross-ref on the portfolio card) and enriched the rendering with the consumed entity's version.
**Why**: The feature brief (GR-8) claimed the surfacing was absent, and the plan inherited that claim without re-checking the 1.2.0 changelog. The code recon during Phase 2 falsified it — the gap was evidence (no test) and a missing version display, not a missing feature.
