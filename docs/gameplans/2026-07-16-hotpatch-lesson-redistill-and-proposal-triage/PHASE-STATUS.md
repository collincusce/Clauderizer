# hotpatch-lesson-redistill-and-proposal-triage — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-16

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Bootstrap | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Re-distill lessons under the 20 threshold | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Triage the no_standing_conditions proposal | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Ship 1.8.1 release | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-3-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
source-of-truth: version=1.8.0 (pyproject.toml); baseline=821 tests (pytest); 34 active project lessons (target <20); 1 pending proposal (no_standing_conditions:3f4873045bf1); promotion candidates L-07, L-21, L-42 (cz_lesson_health).
```

### Phase 1 Outputs

```
redistill-result: docs/LESSONS.md re-distilled 34 → 19 active project lessons (< 20). 7 thematic syntheses added+promoted: L-50 (verification-honesty/eval-discipline), L-51 (release ritual), L-52 (parser round-trip+render), L-53 (self-improving memory loop), L-54 (verify host/model/product reality), L-55 (pin-the-seam integration), L-56 (memory tool-surface contracts). 22 sources obsoleted into them + L-43 obsoleted (absorbed into L-50). 12 distinct high-value survivors retained (incl. high-utility L-07, L-21). 0 redundant pairs, pass_rate 1.0. Append-only preserved (all sources marked, none deleted). Surfaced engine bug H-18 (obsolete-marker parser miscounts reasons containing ')').
```

### Phase 2 Outputs

```
standing-condition-declared: .clauderizer/conditions.2026-06-21-standing-curator-loop-memory-maintenance.toml — one probe lessons_over_threshold: `test $(grep -F '**L-' docs/LESSONS.md | grep -vc '(obsolete') -gt 20`. Resolves proposal no_standing_conditions:3f4873045bf1. cz_modernize pending advisory proposals now 0.
```

### Phase 3 Outputs

```
release-1.8.1: Clauderizer 1.8.1 staged. Real payload: fixed H-18 in src/clauderizer/markdown/lesson_state.py AND its sibling src/clauderizer/markdown/skill_state.py — marker payload tolerates one level of nested parens; regression tests added to both test files. Version single-sourced 1.8.1 across pyproject.toml, __init__.py, CHANGELOG top entry; editable install reinstalled so dist metadata reads 1.8.1. Suite 821 to 823 green, 5 skipped. cz_audit run: 0 release/graph findings. Release commit 72ac7e8. Tag v1.8.1 + push to CI/PyPI pending final origin/main push.
```

## Corrections Log

### C-01 — Phase 1

**Phase**: 1
**What gameplan said**: D1 planned to promote high-utility lessons L-07, L-21, L-42 into docs/LESSONS.md via cz_promote_lesson, then consolidate and obsolete.
**What was actually correct**: L-07/L-21/L-42 were already project lessons in docs/LESSONS.md (cz_promote_lesson is a gameplan→project move, N/A here). The real lever was consolidation: L-07 and L-21 (the two highest-utility) were RETAINED standalone; L-42's content was folded into the new release-ritual synthesis L-51 (content preserved, append-only). Reduction 34→19 came from 7 thematic syntheses (L-50–L-56) + obsoleting 22 sources + 1 situation-specific obsoletion (L-43).
**Why**: cz_lesson_health's 'promotion candidate' flag was read as 'needs promoting' during planning, but these lessons already lived in docs/LESSONS.md; corpus-level re-distill is consolidate+obsolete, not promote. With 0 lexical-duplicate pairs, the honest reduction was thematic synthesis, not merging near-duplicates.
**Lesson**: Corpus re-distill of docs/LESSONS.md is consolidate+obsolete (add synthesis → promote → obsolete sources), never cz_promote_lesson (that is gameplan→project). cz_lesson_health's 'promotion candidate' means high-utility/keep, not 'move it' when it is already a project lesson.
