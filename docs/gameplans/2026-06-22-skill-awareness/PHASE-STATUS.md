# skill-awareness — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-22

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Skill model + SKILLS.md | ✅ COMPLETE | 2026-06-22 | 2026-06-22 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Skill discovery (propose-confirm) | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Relevance surfacing | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Curation parity + docs + integration sweep | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Release 1.0.0rc1 | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
new_tools: cz_register_skill, cz_obsolete_skill (writes=True), inserted after cz_promote_lesson in ops.REGISTRY + tools_list.TOOL_NAMES; parity test green
new_modules: src/clauderizer/markdown/skill_state.py (parse_state/is_active/mark/format_entry/parse_entry; states active|obsolete|superseded; EMDASH=U+2014); src/clauderizer/templates/docs/SKILLS.md (lazy-created via _ensure_doc)
mutations: mutations.register_skill (S-NN auto-id under a category, idempotent on name) + mutations.obsolete_skill (append-only marker, idempotent), mirroring promote_lesson/obsolete_lesson
suite: 586 passed, 4 skipped, exit 0 (was 573 baseline; +13 skill tests: test_skill_state.py x7, test_skills.py x6)
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
