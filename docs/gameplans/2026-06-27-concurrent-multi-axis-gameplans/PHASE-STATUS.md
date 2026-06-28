# concurrent multi-axis gameplans — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-27

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Bootstrap and back-compat harness | ✅ COMPLETE | 2026-06-27 | 2026-06-27 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Focus model (concurrent gameplans + portfolio) | ✅ COMPLETE | 2026-06-27 | 2026-06-27 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Kinds as real profiles (parse + lexicon) | ✅ COMPLETE | 2026-06-27 | 2026-06-27 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Per-kind / per-gameplan preflight | ✅ COMPLETE | 2026-06-27 | 2026-06-27 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Cross-gameplan dependencies and explicit scoping | ✅ COMPLETE | 2026-06-27 | 2026-06-27 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Docs, dogfood, release | 🟢 READY | — | — | handoffs/PHASE-5-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
baseline_tests_main: 629 passed, 4 skipped (633 collected) on main/v1.1.1; 633 passed after the Phase-0 back-compat harness (+4 tests)
impl_branch: feat/concurrent-multi-axis-gameplans, created off main (44984a7); 0/0 vs main + untracked gameplan dir
golden_harness: tests/test_back_compat_focus.py: frozen single-gameplan digest + bundle snapshot, plus legacy [active_gameplan] load + rewrite round-trip stubs (4 tests, all green)
```

### Phase 5 Outputs

```
dogfood_result: Live isolated-repo dogfood PASSED (fresh clauderize init in a tempdir, L-29): two concurrent axes (driven 'build the tool' + campaign 'launch campaign' created focus=false), portfolio showed both kinds with focus marked, cross-gameplan cz_consumes+transition flagged BOTH axes (cascades:1), campaign focus read in 'stage' vocabulary, per-kind preflight ran campaign QA gates (virality/brand_lint pass, duration skip) NOT pytest, refocus left the campaign untouched. Also captured permanently as tests/test_multi_axis_integration.py.
docs_updated: docs/subsystems/kinds.md (new subsys.kinds), profiles.md cross-ref, GAMEPLAN-PROCEDURE.md (template + repo copy, v1.3.0->1.4.0 + Concurrent-gameplans section), PROCEDURE_VERSION 1.3.0->1.4.0, README (Running several gameplans section + CLI focus/gameplans verbs + MCP surface +cz_focus/cz_gameplans/cz_consumes + count 38->41). doctor: procedure version compatible. Suite 669 passed, 4 skipped.
```

## Corrections Log

### C-01 — Phase 0

**Phase**: 0
**What gameplan said**: Baseline test count is 663; capture it as the source-of-truth value.
**What was actually correct**: The real baseline on the feat/concurrent-multi-axis-gameplans branch (off main, v1.1.1) is 629 passed, 4 skipped (633 collected). 663 was the in-flight abstract-index-fast-retrieval branch's count surfaced in the SessionStart digest.
**Why**: The SessionStart baseline reflected whichever gameplan held focus at session start (abstract-index, phase 6/8, which had added tests). This initiative branches off main where those tests do not exist, so 629 is the correct gate number.
**Lesson**: A SessionStart baseline reflects the focused gameplan's branch, not main; when a new initiative branches off main, re-measure the baseline on that branch rather than trusting the inherited digest figure.
