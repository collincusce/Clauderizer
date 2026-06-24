# critique-bias-hardening — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-24

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | CALM self-enhancement + authority checks | ✅ COMPLETE | 2026-06-24 | 2026-06-24 | handoffs/PHASE-0-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
detection_result: Principled classifiers: 100% detection (17/17) of planted bias the PRIOR rubric scored clean; 0 false-positives on 15 sound cases (precision 100%). Beats a naive strawman on 6/7 adversarial near-misses (naive 20-50% FP, det as low as 67%). Prior rubric: 0% detection (no bias axis existed). Per-axis: authority 7/7, hollow-resolution 6/6, overclaim 4/4.
fixture_and_harness: docs/gameplans/2026-06-24-critique-bias-hardening/_experiments/ : fixture.json (32 labeled cases across 3 axes, with adversarial near-misses), measure.py (principled vs naive-strawman vs prior detectors), results.json (machine-readable verdict). Kept as provenance.
suite_after_change: 626 passed / 630 collected, 4 skipped, 0 failures (620 passed baseline + 6 new critique tests). No regression; benchmarks untouched.
verdict: KEEP. CALM self-enhancement + authority axes added to src/clauderizer/rituals/critique.py (3 pure classifiers + 2 integration helpers + 2 advisory dimensions). Deterministic, stdlib-re only, no new dependency, no enable/disable flag, advisory (agent grades). Ready for review/merge on branch experiment/critique-bias-hardening.
```

## Corrections Log

### C-01 — Phase 0

**Phase**: 0
**What gameplan said**: Full suite green (baseline 624 tests)
**What was actually correct**: The real green baseline is 620 passed / 624 collected (4 skipped, platform-conditional). Post-change: 626 passed / 630 collected, 0 failures (+6 new critique tests).
**Why**: The exit-criterion wording used the collected count; recording the passed count keeps the no-regression judgment honest against the right number.
