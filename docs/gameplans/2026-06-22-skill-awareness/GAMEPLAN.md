# skill-awareness Gameplan

> Created: 2026-06-22
> Status: Executing
> Kind: driven
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

_(1–2 paragraphs: what this gameplan accomplishes.)_

## Subsystems Touched

_(list the subsystems/features this gameplan affects.)_

## Source-of-Truth Captures

_(Real values captured from real systems at gameplan start. Authority over the
gameplan body. Account IDs, ARNs, baseline test counts, versions.)_

## Amendments

### A-001 — Skill curation v1 = register/obsolete/discover/surface; promote/consolidate dropped, supersede-tool deferred

- **Date**: 2026-06-22
- **Affected sections in GAMEPLAN.md**: Phase 3 exit criteria (curation parity); D1
- **Affected phases**: 3
- **Triggered by**: Phase 3 design review: promote/consolidate do not map onto skills
- **What changed**: v1 ships register + obsolete + discover + relevance-surfacing as the complete skill-awareness surface. cz_promote_skill is DROPPED: promotion is the lessons' gameplan->project tier, and skills are already project-level, so there is no tier to promote across. cz_consolidate_skills is DEFERRED: low value, since cz_obsolete_skill + re-register already covers merging a near-duplicate. The 'superseded' state ships in markdown/skill_state (parsed, tested, forward-compatible) but the cz_supersede_skill tool is deferred to a future gameplan.
- **Why**: An honest scope cut over a faked parity checkbox (L-38). Forcing promote/consolidate onto skills would add awkward, low-value surface to a 1.0 release candidate. register/obsolete/discover/surface is the coherent, complete v1; the grammar leaves a clean seam for cz_supersede_skill later.

## Decisions

### D1 — Skills mirror the lesson architecture (line-entries, not graph entities)

**Context**: Lessons are the closest existing analog to a curated, surfaced knowledge inventory: stored as line-entries in docs/LESSONS.md with a lesson_state grammar, not as frontmatter graph entities. Skill-awareness needs the same shape - a compact, append-only, ranked-and-surfaced inventory.
**Decision**: v1 stores skills as line-entries in docs/SKILLS.md with a markdown/skill_state.py grammar mirroring lesson_state.py; register/obsolete/promote/consolidate mirror the lesson mutations. Skills are NOT graph entities with frontmatter in v1.
**Consequences**: Maximal reuse of the analyze ranker, handoff rollup, status gauge, and parity tests; minimal new seams. If skills later need dependency edges (supersedes/requires), graduate to entities then.
**Status**: active (2026-06-22)

### D2 — Skill-awareness is propose-confirm, never auto-mutating (INVARIANT-05)

**Context**: The user explicitly rejected auto-opening PRs. The project constitution (INVARIANT-05, L-37, the curator) is autonomous-in-cadence, supervised-in-mutation.
**Decision**: Discovery SURFACES skills read-only (like cz_curate/cz_mine_failures); the agent records them via blessed writes (cz_register_skill). No auto-registration, no PR-opening, no network fetch.
**Consequences**: Awareness without surprise writes; aligns with the existing read-only advisory ops and their tests.
**Status**: active (2026-06-22)

### D3 — v1 scope = skills already present in the project environment; external ingestion deferred

**Context**: The original idea included noticing PUBLIC skills (nvidia/skills) and PRing them. The user dropped the PR/ingestion path.
**Decision**: v1 makes a project aware of skills already available in its environment (local skill dirs + Clauderizer's own shipped skills). Ingesting external/public skills and any PR-opening are explicitly OUT of scope (deferred).
**Consequences**: Smaller, safer surface; no network/license/foreign-instruction-trust burden in v1. A future gameplan can add a read-only external catalog if wanted.
**Status**: active (2026-06-22)

### D4 — Release as 1.0.0rc1 to exercise the documented 1.0 gates

**Context**: RELEASING.md defines 1.0 readiness gates G1-G7; G6 carries a named residual (a literal native-harness cold-start restart observation). The user asked to ship 1.0 release candidate 1.
**Decision**: Cut version 1.0.0rc1 (PEP 440) via the standard release ritual. The rc is the vehicle to exercise G1-G7 in the wild and retire the G6 residual before a final 1.0.
**Consequences**: A real-world rc on PyPI; the four-registry sweep + release-check + restart-validate still gate it; final 1.0 follows once the rc proves the residual.
**Status**: active (2026-06-22)

## Open Items

**O-01.** _(phase 1)_ Discovery host-coverage: exactly which skill locations are scanned (.claude/skills, ~/.claude/skills, Clauderizer's shipped src skills, plugin skill dirs) and which hosts are covered vs named-residual. _(resolved 2026-06-22: Discovery scans 3 default roots (skill_discovery.default_roots): repo .claude/skills, ~/.claude/skills, and Clauderizer's shipped skills (assets.SKILLS), deduped by name (first root wins). Named residual: plugin skill dirs + non-Claude hosts (kimi/codex) not yet scanned, documented in default_roots docstring. Real smoke found 6 clauderizer-* skills from .claude/skills.)_

**O-02.** _(phase 4)_ Is 0.17.0 fully published on PyPI (so 1.0.0rc1 is the clean next four-registry claim), or mid-flight? Resolve via a fresh four-registry sweep before the release phase.

## Phase Breakdown

### Phase 0: Skill model + SKILLS.md

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] docs/SKILLS.md template exists under src/clauderizer/templates/docs/ and renders as valid markdown
- [x] markdown/skill_state.py parses active/obsolete/superseded and round-trips (apply-twice == apply-once)
- [x] cz_register_skill and cz_obsolete_skill are in REGISTRY and tools_list.TOOL_NAMES (parity test green)
- [x] new tests for the skill model pass and the full suite stays green

### Phase 1: Skill discovery (propose-confirm)

**Goal**: A read-only cz_discover_skills that scans known local skill locations, parses SKILL.md frontmatter, and PROPOSES unregistered skills for the agent to confirm (INVARIANT-05) - never auto-registers.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_discover_skills is read-only (writes=False) and returns proposals with name+description+source for unregistered SKILL.md files
- [x] discovery parses real SKILL.md frontmatter from at least the .claude/skills and Clauderizer-shipped locations
- [x] it proposes only unregistered skills (diffs against docs/SKILLS.md) and never writes
- [x] tests cover discovery with fixtures incl. malformed/duplicate frontmatter; suite green

### Phase 2: Relevance surfacing

**Goal**: Registered skills surface in the handoff and status digest, ranked by relevance to the current phase via the existing lexical analyzer - closing the L-35 availability-not-use gap.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] registered skills roll up into the cumulative handoff, ranked by relevance to the phase via the existing analyzer
- [x] cz_status/status_bundle reports an active-skill count (and a bloat nudge past a threshold, mirroring lessons)
- [x] a phase with no relevant skills surfaces nothing (no noise); tests assert ranking + the empty case; suite green

### Phase 3: Curation parity + docs + integration sweep

**Goal**: Promote/consolidate skills to lesson parity; sweep reference docs (README MCP surface, TRUST/SECURITY skill-scan note, CHANGELOG, procedure); add a cross-cutting integration test at the status/handoff seam (L-34); repair + restart-validate the dogfood wiring.
**Depends on**: 0, 1, 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_promote_skill/cz_consolidate_skills reach lesson parity (or a recorded amendment explains the scope cut)
- [x] README MCP-surface tool list, TRUST.md (what discovery reads), SECURITY.md scope line, and CHANGELOG updated; procedure mentions skills if needed
- [x] a cross-cutting integration test exists at the status_bundle/handoff seam (L-34)
- [x] clauderize doctor exits 0 on the dogfood repo after init-repair; suite green

### Phase 4: Release 1.0.0rc1

**Goal**: Verify the 1.0 readiness gates (G1-G7) hold or amend with named residuals; full suite green on every host leg (L-31); cut 1.0.0rc1 via the release ritual; post-mortem + close.
**Depends on**: 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] 1.0 gates G1-G7 each verified-holding or amended with a named residual
- [ ] full suite green on every host leg the CI matrix covers (L-31/L-20) before any tag
- [ ] fresh four-registry sweep confirms 1.0.0rc1 is unclaimed; clauderize release-check exits 0 BEFORE tagging
- [ ] 1.0.0rc1 tagged on the pushed commit, GitHub Release cut, Publish-to-PyPI green, uvx --refresh resolves 1.0.0rc1
- [ ] restart-validate: a real cold start shows the [Clauderizer] digest; POST-MORTEM written and gameplan closed
