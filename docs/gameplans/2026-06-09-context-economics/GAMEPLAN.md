# Context Economics Gameplan

> Created: 2026-06-09
> Status: Planning
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

Close review finding 5: Clauderizer's memory is append-only and handoffs are
cumulative by design, but nothing pushes back — a long gameplan's handoff carries
every lesson forever, lessons die with the gameplan at close (or bloat the next
one), and nothing measures the bundle. A memory system that eventually crowds out
the working context recreates the intra-session limit it was built to escape.

Three mechanisms, all blessed writes (per the discipline-seams pattern):
**consolidate** (N gameplan lessons → 1 synthesized lesson), **promote** (enduring
lessons → a compact project-level docs/LESSONS.md that future gameplans' handoffs
carry), and a **memory gauge** in the status digest that makes bloat visible and
nudges toward the first two. Never auto-delete; the audit trail stays intact.

## Subsystems Touched

- `src/clauderizer/mutations.py` — consolidate_lessons, promote_lesson, obsolete_lesson scope extension
- `src/clauderizer/rituals/handoff.py` — distilled project lessons in the bundle; prune promoted
- `src/clauderizer/rituals/status_bundle.py` — memory gauge + digest warning
- `src/clauderizer/mcp_server.py` + `tools_list.py` — cz_consolidate_lessons, cz_promote_lesson
- `src/clauderizer/templates/docs/LESSONS.md` — new on-demand project doc
- `src/clauderizer/skills/clauderizer-close-gameplan/` — promotion step at close

## Source-of-Truth Captures

Captured 2026-06-09 from the live repo:

- **Baseline test count**: 99 passing (now self-healing via preflight write-back)
- **Engine version**: 0.4.0; MCP tool count: 20
- **Lesson volume evidence**: the closed v1-bootstrap gameplan accumulated 12
  lessons in one gameplan; the discipline-seams gameplan added 5 more in a day —
  none promoted anywhere, all dead weight for the next gameplan
- **Roll-up prune markers today**: lines containing `(obsolete` or `~~` (handoff.collect_lessons)
- **On-demand doc precedent**: HARDENING.md is created from its template at first
  write (_ensure_doc), without appearing in a size manifest
- **Config is a strict dataclass** — no free-form sections, so the gauge threshold
  ships as a documented constant in v1, not a config knob

## Amendments

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

### D3 — Promotion marker prunes like obsolescence

**Context**: A promoted lesson must not appear twice in a handoff (gameplan section + project section).
**Decision**: promote_lesson marks the source line '(promoted <date>: L-NN)'; collect_lessons prunes '(promoted' exactly like '(obsolete'. The project section is the single carrier from then on.
**Consequences**: Roll-up counting stays simple; the source line remains in the gameplan log for the audit trail.

### D4 — LESSONS.md is on-demand, not in size manifests

**Context**: Adding LESSONS to SIZE_MANIFESTS would change init output for every new repo and require config migration for existing ones.
**Decision**: docs/LESSONS.md follows the HARDENING precedent: created from its template at first promote_lesson write, regardless of size dial.
**Consequences**: Zero init churn; repos that never promote never grow the file.

### D5 — Gauge threshold is a documented constant in v1

**Context**: Config is a strict dataclass with no free-form sections; a [memory] table means schema + emitter + merge churn for one number.
**Decision**: ACTIVE_LESSONS_WARN = 12 ships as a module constant in status_bundle with a docstring; a config knob can follow if real projects need different lines.
**Consequences**: v1 stays small; the constant is trivially overridable in code and documented where it lives.

## Open Items

_(O1, O2, … — blockers and cross-phase questions.)_

## Phase Breakdown

### Phase 0: Lesson consolidation

**Goal**: N overlapping lessons can be synthesized into one through a blessed
write, shrinking every future handoff without deleting anything.
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | `mutations.consolidate_lessons(gameplan_id, numbers, text, category)`: validates sources exist and aren't already obsolete/promoted; adds the synthesized lesson; marks each source `(obsolete <date>: consolidated into #N)` | 2h |
| 0.2 | Expose `cz_consolidate_lessons`; add to tools_list | 1h |
| 0.3 | Tests: consolidation round-trip, roll-up shrinks, invalid/duplicate sources rejected, idempotency | 2h |

**Exit criteria**:
- [ ] Consolidating 3 lessons into 1 drops handoff roll-up count by 2; all 3 source lines remain in the log, marked
- [ ] Consolidating an already-consolidated lesson is rejected with a clear error
- [ ] Full suite passes; baseline grows from 99

### Phase 1: Lesson promotion & project LESSONS.md

**Goal**: Enduring lessons outlive their gameplan: promoted into a compact
project-level `docs/LESSONS.md` (L-NN) that every future handoff carries, while
the gameplan copy is marked and stops rolling up individually.
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | `templates/docs/LESSONS.md` + `mutations.promote_lesson(gameplan_id, number, text_override)`: appends `**L-NN.** text *(from <gameplan-id>)*` under the category in docs/LESSONS.md (created on demand); marks the source `(promoted <date>: L-NN)` | 2h |
| 1.2 | `handoff.collect_lessons` prunes `(promoted` lines; `assemble` adds a "Project Lessons (distilled)" section from docs/LESSONS.md inside the marker block when the doc exists | 2h |
| 1.3 | `obsolete_lesson` accepts `L-NN` ids so the project list can be curated too (cz_obsolete_lesson number becomes a string) | 1h |
| 1.4 | Expose `cz_promote_lesson`; tools_list; close-gameplan skill gains the promotion step | 1h |
| 1.5 | Tests: promote round-trip, no duplication in handoff (promoted absent from gameplan section, present in project section), L-NN obsolescence, on-demand doc creation | 2h |

**Exit criteria**:
- [ ] A promoted lesson appears exactly once in an assembled handoff (project section), and survives into a *different* gameplan's handoff
- [ ] docs/LESSONS.md entries carry provenance and can be obsoleted via the same tool
- [ ] Full suite passes

### Phase 2: Memory gauge

**Goal**: The status digest measures the memory instead of letting it grow
silently — count + size, with a nudge toward consolidate/promote/obsolete when
it crosses the line.
**Depends on**: Phases 0–1 (the remedies the warning points at must exist).

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | status_bundle.compute gains a `memory` block: active/obsolete/promoted gameplan lessons, project lessons, and the assembled-handoff size (~tokens, len/4) | 2h |
| 2.2 | render_digest prints `Memory: N active lessons, M project (~K tok handoff)` and a ⚠ nudge past ACTIVE_LESSONS_WARN (12, documented constant) | 1h |
| 2.3 | README tool list (also catching up 0.4.0's tools), CHANGELOG 0.5.0, version bump | 1h |
| 2.4 | Tests: memory block math, warning threshold on/off, digest rendering | 2h |

**Exit criteria**:
- [ ] A gameplan with >12 active lessons produces the ⚠ nudge naming the three remedies; ≤12 stays quiet
- [ ] This repo's own digest shows the memory line (dogfood)
- [ ] CHANGELOG/README updated; full suite passes
