# Chat Handoff Index — skill-awareness

> Last updated: 2026-06-22
> Status: Phase 4 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 573

## Ending Protocol

1. `cz_transition_phase` the finished phase to complete.
2. `cz_add_output` each concrete produced value; `cz_add_phase_summary` the recap;
   `cz_add_correction` / `cz_add_lesson` as earned.
3. `cz_transition_status` on touched entities (fires cascade); `cz_resolve_cascade`
   the verdicts.
4. `cz_write_handoff` for the next phase.
5. Run exit verification; report the test count.

## Phase Status Table

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Skill model + SKILLS.md | ✅ COMPLETE | 2026-06-22 | 2026-06-22 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Skill discovery (propose-confirm) | ✅ COMPLETE | 2026-06-22 | 2026-06-22 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Relevance surfacing | ✅ COMPLETE | 2026-06-22 | 2026-06-22 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Curation parity + docs + integration sweep | ✅ COMPLETE | 2026-06-22 | 2026-06-22 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Release 1.0.0rc1 | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-22

Built the skill model as a clean mirror of the lesson architecture (D1). New: markdown/skill_state.py (the single grammar for skill state + the entry fields name/description/source; states active|obsolete|superseded - the supersede-vs-promote divergence from lessons, since skills are already project-level); templates/docs/SKILLS.md (lazy-created from template like LESSONS.md); and the blessed writes mutations.register_skill (S-NN auto-id under a category, idempotent on name so repeat discovery proposals never duplicate) + mutations.obsolete_skill (append-only marker, idempotent). Exposed as cz_register_skill / cz_obsolete_skill via ops.REGISTRY + tools_list.TOOL_NAMES, inserted next to the lesson ops so parity holds. 13 new tests (grammar round-trip incl. mid-text-mention inertness; register/obsolete lifecycle; L-22 idempotency). Full suite 586 passed / 4 skipped / exit 0 - strictly additive, INVARIANT-07 honored. No tracked graph entities touched, so no cascade.

### Phase 1 — completed 2026-06-22

Built read-only skill discovery (D2 propose-confirm). New: src/clauderizer/skill_discovery.py - discover(paths, roots=None) scans default_roots (.claude/skills, ~/.claude/skills, Clauderizer's shipped skills via assets.SKILLS), parses each SKILL.md with markdown.frontmatter, dedups across roots (first wins), diffs against active docs/SKILLS.md entries, and proposes the rest as {name, description, source}. Degrades gracefully on malformed/non-UTF-8 SKILL.md (errors=replace + dir-name fallback, per-file continue), never crashing the scan (L-24). Exposed as cz_discover_skills (writes=False, like cz_curate/cz_mine_failures), appended to REGISTRY + TOOL_NAMES. 7 new tests (good/malformed/duplicate frontmatter fixtures, only-unregistered diff, read-only assertion, real shipped-skill parse). Real CLI smoke via clauderize ops found the 6 clauderizer-* skills from .claude/skills - end-to-end parity (L-05). Suite 593 passed / 4 skipped / exit 0. The full suite caught one L-34 cross-cutting regression - the new docstring leaked .claude into the host-neutral tool surface (D-032 test) - fixed by describing locations neutrally. O-01 resolved.

### Phase 2 — completed 2026-06-22

Wired focused skill surfacing into the two shared pipelines (the L-34 cross-cutting seams). handoff.py: relevant_skill_pointer(paths, query) ranks active SKILLS.md entries by the existing lexical analyzer (analyze.rank_relevant, no ML - D-018), and assemble() renders a '## Skills for This Phase' block - top-k relevant only, or nothing when none overlap (L-35 availability-not-use; rank_relevant already drops zero-overlap entries, so the empty case is free). Deliberate divergence from lessons: skills are a MENU surfaced FOCUSED, not all-carried like lessons (D-009 propagation) - a project may register dozens and dumping them all is noise. status_bundle.py: _memory_gauge counts active_skills + a staleness nudge past ACTIVE_SKILLS_WARN=25 (higher than lessons, since skills surface focused so the concern is pruning stale skills not handoff weight); render_digest shows the skill count when >0. 7 new tests incl. the assemble() integration test (token derived from the real phase query so overlap is guaranteed) + empty/obsolete/no-overlap cases. Suite 600 passed / 4 skipped / exit 0, strictly additive (INVARIANT-07).

### Phase 3 — completed 2026-06-22

Curation scope, docs, dogfooding, and wiring. (1) Amendment A-001 records the honest curation scope cut (L-38): register/obsolete/discover/surface is the complete v1; promote dropped (skills have no gameplan->project tier), consolidate deferred (obsolete+re-register covers a merge), the superseded state ships in the grammar (forward-compatible) but cz_supersede_skill is deferred. (2) Docs swept: README MCP surface 31->38 (also reconciling the L-21 drift - the 4 read-only 0.17.0 loop ops were missing from the list) + a new Skills group; TRUST.md (discovery reads SKILL.md frontmatter only, never executes; register writes only docs/SKILLS.md); SECURITY.md (no execution surface, no network); CHANGELOG [Unreleased]. (3) End-to-end integration test (discover -> confirm -> surfaced in BOTH digest and handoff, then obsolete removes it) across the L-34 seams. (4) Dogfooded for real: confirmed cz_discover_skills' 6 proposals into docs/SKILLS.md (S-01..S-06, Clauderizer's own workflow skills) - the digest now reads '6 skills'. (5) Repaired the drifted wiring with init (explicit --session-host windows-wsl:ubuntu so it did not mis-detect native, the H-08 hazard); doctor 16/16 exit 0 with in-band end-to-end evidence. Suite 601 passed / 4 skipped / exit 0. Named residual for Phase 4: the cold-start restart-validate (G6) needs a real new session.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
