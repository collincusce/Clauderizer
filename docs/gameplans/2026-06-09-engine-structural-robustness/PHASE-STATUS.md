# Engine Structural Robustness — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-09

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Structural numbering and table writes | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Collision-proof cascade reports | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Bless the remaining tracked surfaces | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Structural lesson state and 0.6.0 release | 🟡 IN PROGRESS | 2026-06-09 | — | handoffs/PHASE-3-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
BASELINE_AFTER_PHASE: 122 tests
TRACKERS_HEALED: 6 (both closed gameplans' index+status, plus this gameplan's own pair)
```

### Phase 1 Outputs

```
BASELINE_AFTER_PHASE: 127 tests
COLLISION_DEMO: _cascade-reports/2026-06-09-subsys.rituals.md and ...rituals-01.md coexist
```

### Phase 2 Outputs

```
BASELINE_AFTER_PHASE: 134 tests
MCP_TOOLS: 24 (added cz_add_output, cz_add_phase_summary)
DOCTOR_CHECKS: 13, all green incl. the two D9 identity checks
```

## Corrections Log

### C-01 — Phase 0

**Phase**: 0
**What gameplan said**: Pre-flight passes before Phase 0 code (captures: baseline 109, doctor all-green)
**What was actually correct**: The tests check failed with 'pytest: not found': the profile command resolves via shell PATH, and the engine's venv (which contains pytest) is never activated when the engine is launched by absolute path
**Why**: preflight._default_runner inherits the parent environment untouched; engine-environment resolution was assumed but never implemented
**Lesson**: An engine that owns a toolchain must resolve bare profile commands against its own interpreter's bin directory before PATH - shell activation can never be assumed.
