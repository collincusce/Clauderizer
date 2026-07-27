# Glossary

> Canonical vocabulary for this project. A term enters this file through a
> decision (D-NNN) or a gameplan that defines it; each entry points at the doc
> that owns the full story. Prose here is descriptive, never normative — the
> owning doc and the decision log are the authorities.

## Core memory vocabulary

- **Gameplan** — a tracked initiative under `docs/gameplans/`, kind `driven`
  (finite phase DAG ending in a post-mortem), `loop` (standing maintenance), or
  a custom kind. Owned by `docs/gameplans/GAMEPLAN-PROCEDURE.md`.
- **Phase** — one session-sized unit of a gameplan with a goal, dependencies
  (by technical need, not narrative order — L-11), and exit criteria.
- **Exit criteria** — machine-checkable `- [ ]` items authored per phase;
  surfaced (never enforced — INVARIANT-05) at phase completion.
- **Handoff** — the cumulative, self-contained brief for a phase
  (`handoffs/PHASE-N-HANDOFF.md`); agent notes outside the marker block
  survive regeneration.
- **Ending Protocol** — the closing writes of a phase: transition, outputs,
  summary, corrections/lessons, status transitions, next handoff.
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
  byte-identical on a healthy repo (INVARIANT-08).
- **Discipline gate** — an advisory, judgment-based check (clarify, exit
  criteria, analyze); surfaces candidates, never blocks (INVARIANT-05).
- **Preflight** — the pre-phase check battery (`cz_preflight`), blocking by
  default per D-024 with per-repo advisory downgrade.
- **Baseline** — the recorded green test count a phase must never regress.
- **Dream loop** — per-exchange experiential notes (`cz_add_dream`) distilled
  by the dreamer into advisory proposals, then triaged (D-058/D-059).
- **Curator** — the memory-maintenance loop (consolidate / promote / obsolete)
  keeping the lesson corpus compact under coverage gates (L-67).

## Fleet vocabulary (D-071, A-001)

- **Fleet** — N host-spawned agents working one gameplan concurrently with
  Clauderizer as their shared memory. The **host** spawns and owns every agent
  loop; Clauderizer never spawns anything (the D-070 memory-layer boundary).
  Managed by the `clauderizer-fleet` skill.
- **Hub** — the single repo checkout whose `docs/` receives **every** tracked
  write of a fleet. Workers reach it via the hub-rooted MCP server or
  `clauderize --repo <hub>` / `CLAUDERIZER_REPO` (D-055).
- **Hub-and-spoke law** — memory writes target the hub only. Worktrees may
  hold *code*, never authoritative memory: a worktree's `docs/` copy is never
  written and never merged back. (Per-node memory merge-back is the corruption
  class Fractal's issue #9 documents; the phase-4 merge-integrity audit
  *detects* that damage, it does not make the pattern safe.)
- **Worker** — one spawned agent holding an assignment. A worker closes
  honestly: `complete` only with exit criteria met, else `deferred` with a
  reason — never a laundered "complete".
- **Assignment** — the `cz_assign` binding of a phase to a named assignee;
  ownership means one writer per phase. Reviewed with `cz_assignments`.
- **Worker briefing** — the standard prompt block a fleet orchestrator hands
  each worker (assignment, hub coordinates, close-out contract); template
  lives in the `clauderizer-fleet` skill.

*Status (2026-07-26):* the fleet substrate ships today — portable exclusive
locking (`locking.py`), assignments, `--repo` hub decoupling. The 2.0-alpha
gameplan strengthens it: dead-worker detection (phase 1), live-state stamps
and fleet spend aggregation (phase 2), the worktree-edge audit (phase 4).
"More agents = better results" is a **hypothesis under test** — D-071
pre-names the fleet-vs-solo matrix signal; the phase-5 verdict, whatever it
is, updates the skill's guidance.
