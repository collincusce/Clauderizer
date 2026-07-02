# engine-1.5.0-onboarding — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-01

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Plan, baselines & commit | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Detector + cz_onboard assembly tool | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Surfacing — init advisory + modernize proposal | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Skill + docs + version bumps | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Dogfood & ship 1.5.0 | 🟡 IN PROGRESS | 2026-07-01 | — | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 1 Outputs

```
phase1_suite: 761 passed, 5 skipped (+6 tests/test_onboard.py); surface 45 (cz_onboard read-only, CLI parity verified); onboard.py: spec_candidates (root files + docs/*.md minus owned set, cap 25, ≤2MB, paths+bytes only) + unseeded_docs (meaningful-lines ⊆ template — drift-proof) + report/prompt
```

### Phase 2 Outputs

```
phase2_suite: 763 passed, 5 skipped (+2); InitReport gains advisories[] printed by cmd_init as "→"; init step 6b fires only when unseeded docs AND spec candidates coexist; modernize tier-2 unseeded_docs proposal with the same predicate, clears when a doc gains real prose (both tested both ways)
```

### Phase 3 Outputs

```
phase3_versions: engine 1.5.0 (pyproject + __init__), PROCEDURE_VERSION 1.6.0 with template changelog + "Onboarding an Existing Project" section; clauderizer-onboard skill (7th packaged skill, init-drop tested); CHANGELOG 1.5.0 names both version lines with carries phrasing; README init section onboarding sentence; JARGON_CLEAN; suite 764 (+1 skill test)
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
