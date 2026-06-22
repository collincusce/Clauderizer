# skill-awareness — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-22

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Skill model + SKILLS.md | ✅ COMPLETE | 2026-06-22 | 2026-06-22 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Skill discovery (propose-confirm) | ✅ COMPLETE | 2026-06-22 | 2026-06-22 | handoffs/PHASE-1-HANDOFF.md |
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

### Phase 1 Outputs

```
discovery: src/clauderizer/skill_discovery.py: discover(paths, roots=None) read-only; default_roots = .claude/skills, ~/.claude/skills, clauderizer-shipped; parses SKILL.md via markdown.frontmatter; dedups across roots; diffs vs active SKILLS.md entries; degrades on bad bytes (errors=replace) + dir-name fallback
new_tool: cz_discover_skills (writes=False), appended after cz_loop_step in REGISTRY + TOOL_NAMES; host-neutral docstring (passes test_tool_surface_is_host_neutral / D-032)
cli_smoke: clauderize ops cz_discover_skills on the dogfood repo: scanned 3 roots, 2 present, 6 proposals (clauderizer-* from .claude/skills); read-only; end-to-end CLI parity (L-05)
suite: 593 passed, 4 skipped, exit 0 (was 586; +7 discovery tests). The full suite caught + I fixed one L-34 regression: the cz_discover_skills docstring leaked .claude into the host-neutral surface
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
