# skill-awareness — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-22

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Skill model + SKILLS.md | ✅ COMPLETE | 2026-06-22 | 2026-06-22 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Skill discovery (propose-confirm) | ✅ COMPLETE | 2026-06-22 | 2026-06-22 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Relevance surfacing | ✅ COMPLETE | 2026-06-22 | 2026-06-22 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Curation parity + docs + integration sweep | ✅ COMPLETE | 2026-06-22 | 2026-06-22 | handoffs/PHASE-3-HANDOFF.md |
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

### Phase 2 Outputs

```
handoff_surfacing: handoff.relevant_skill_pointer(paths, query) ranks active SKILLS.md entries via analyze.rank_relevant (no ML, D-018); assemble() renders a '## Skills for This Phase' block - top-k relevant only, or nothing when none overlap (rank_relevant drops zero-overlap). Focused-only menu, NOT all-carried like lessons
status_gauge: status_bundle._memory_gauge adds active_skills count + staleness nudge past ACTIVE_SKILLS_WARN=25 (higher than lessons; skills surface focused so it is pruning-stale not handoff-weight); render_digest shows 'N skills' when >0
suite: 600 passed, 4 skipped, exit 0 (was 593; +7 surfacing tests incl. the assemble() L-34 integration test). Strictly additive, INVARIANT-07 honored
```

### Phase 3 Outputs

```
curation_scope: Amendment A-001: register/obsolete/discover/surface is the v1 skill curation surface; promote DROPPED (no gameplan->project tier for skills), consolidate DEFERRED (obsolete+re-register covers merges), the superseded state ships in the grammar (forward-compat) but cz_supersede_skill is deferred. Honest scope cut (L-38), not a faked checkbox
docs_sweep: README MCP surface 31->38 (also added the 4 missing 0.17.0 loop ops - the L-21 drift) + new Skills group; TRUST.md skill read/write scope; SECURITY.md no-execution note; CHANGELOG [Unreleased] entry
dogfood_skills: Registered Clauderizer's own 6 skills into docs/SKILLS.md via the propose-confirm flow (cz_discover_skills proposed, agent confirmed): S-01..S-06 = clauderizer-amend/cascade/close-gameplan/do-phase/new-gameplan/record. Digest now reads '6 skills'
wiring: clauderize init --session-host windows-wsl:ubuntu repaired drifted wiring (2 files written, 21 kept); doctor 16/16 exit 0 with in-band evidence (MCP + SessionStart hook launchable end-to-end via wsl.exe round-trip, identity clauderizer 0.17.0, digest in-band). The cold-start restart-validate (G6) is a named residual, needs a NEW session
suite: 601 passed, 4 skipped, exit 0 (was 600; +1 end-to-end integration test). No engine code changed in Phase 3 (docs + test + SKILLS.md content + wiring only)
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
