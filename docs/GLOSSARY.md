# Clauderizer Glossary

> **Clauderizer's own vocabulary** — engine-owned (D-080), shipped and
> refreshed by the engine. This is not your project's glossary: your domain
> terms belong in `docs/GLOSSARY.md`, which the engine never writes. Two
> glossaries is the intended shape, and they are never merged.
> Each entry points at the doc that owns the full story — prose here is
> descriptive, never normative.

## Core memory vocabulary

- **Gameplan** — a tracked initiative under `docs/gameplans/`, kind `driven`
  (finite phase DAG ending in a post-mortem), `loop` (standing maintenance),
  `campaign` (creative work with deliverables), or a custom kind. Owned by
  `docs/gameplans/GAMEPLAN-PROCEDURE.md`.
- **Phase** — one session-sized unit of a gameplan with a goal, dependencies
  (by technical need, not narrative order), and exit criteria.
- **Exit criteria** — machine-checkable `- [ ]` items authored per phase;
  surfaced (never enforced) at phase completion.
- **Handoff** — the cumulative, self-contained brief for a phase
  (`handoffs/PHASE-N-HANDOFF.md`); agent notes outside the marker block
  survive regeneration.
- **Ending Protocol** — the closing writes of a phase: transition, outputs,
  summary, corrections/lessons, status transitions, next handoff — including
  a "What I did not check" declaration (the negative space of the work).
- **Decision (D-NNN)** — an ADR in `docs/DECISIONS.md`; append-only,
  supersession-linked. **Invariant (INVARIANT-NN)** — a must-hold rule in
  `docs/INVARIANTS.md`. **Lesson (L-NN)** — earned, consolidatable experience
  in `docs/LESSONS.md`. **Finding (H-NN)** — a hardening/audit finding.
- **Open item (O-NN)** — a tracked blocker/question; resolved, never deleted.
- **Cascade** — the dependency walk over the entity graph after a tracked
  change, ending in a resolved report; never hand-edited.
- **Entity graph** — subsystems/features and their `depends_on` edges,
  maintained via `cz_upsert_entity` under `docs/subsystems/`, `docs/features/`.
- **Digest** — the session-start status injection; at most once per session,
  byte-identical on a healthy repo.
- **Discipline gate** — an advisory, judgment-based check (clarify, exit
  criteria, analyze); surfaces candidates, never blocks.
- **Preflight** — the pre-phase check battery (`cz_preflight`), blocking by
  default with per-repo advisory downgrade.
- **Baseline** — the recorded green test count a phase must never regress.
- **Reinforcement** — the blessed alternative to appending a near-duplicate
  lesson: `cz_reinforce_lesson` strengthens the existing entry's trailer;
  strength is curator evidence, never ranking authority.
- **Dream loop** — per-exchange experiential notes (`cz_add_dream`) distilled
  by the dreamer into advisory proposals, then triaged.
- **Curator** — the memory-maintenance loop (consolidate / promote /
  obsolete / reinforce) keeping the lesson corpus compact under coverage gates.
- **Enforcement ladder** — `docs/ENFORCEMENT.md`: which tier
  (hard-NORMALIZE / preflight-blocking / advisory / instructions-floor)
  actually carries each discipline.

## Fleet vocabulary

- **Fleet** — N host-spawned agents working one gameplan concurrently with
  Clauderizer as their shared memory. The **host** spawns and owns every agent
  loop; Clauderizer never spawns anything. Managed by the `clauderizer-fleet`
  skill.
- **Hub** — the single repo checkout whose `docs/` receives **every** tracked
  write of a fleet. Workers reach it via the hub-rooted MCP server or
  `clauderize --repo <hub>` / `CLAUDERIZER_REPO`.
- **Hub-and-spoke law** — memory writes target the hub only. Worktrees may
  hold *code*, never authoritative memory: a worktree's `docs/` copy is never
  written and never merged back (two workers appending in two copies mint
  colliding IDs).
- **Worker** — one spawned agent holding an assignment. A worker closes
  honestly: `complete` only with exit criteria met, else `deferred` with a
  reason — never a laundered "complete". Its completion report ends with a
  "What I did not check" section.
- **Assignment** — the `cz_assign` binding of a phase to a named assignee;
  ownership means one writer per phase. Reviewed with `cz_assignments`.
- **Worker briefing** — the standard prompt block a fleet orchestrator hands
  each worker (assignment, hub coordinates, close-out contract); template
  lives in the `clauderizer-fleet` skill.
