---
name: clauderizer-fleet
description: Fan out multiple host-spawned agents over one gameplan with Clauderizer as the shared memory hub. Use when the user says "fan out", "fleet", "parallelize this gameplan", "put more agents on it", or asks several phases to be worked concurrently. Orchestrates partitioning (cz_assign), worker briefings, hub-and-spoke memory writes, honest close-out, and dead-worker cleanup.
---

# Run a fleet

A **fleet** is N host-spawned workers over one gameplan, one **hub** (shared
memory). Clauderizer never spawns — spawn through the HOST's own primitives
(Claude Code: the Agent/Workflow tools; other hosts: their subagent facility).
Full vocabulary: `docs/GLOSSARY.md`; law of record: D-071.

**The hub-and-spoke law (non-negotiable):** every tracked write from every
worker targets the hub repo's `docs/` — via the hub-rooted MCP server or
`clauderize --repo <hub>` / `CLAUDERIZER_REPO`. Worktrees may hold *code*,
never memory: a worktree's `docs/` copy is never written, never merged back.
Two workers appending in two copies mint colliding IDs; this is the Fractal
issue-#9 corruption class.

## Procedure

1. **Partition.** Pick genuinely independent work — phases whose `depends_on`
   do not chain (check `cz_phase_detail` / GAMEPLAN.md). One phase = one
   worker. `cz_assign` each phase to a named assignee (`worker-1`…,
   or descriptive names); review with `cz_assignments`. Never fan out phases
   that share a dependency edge — sequence those. Prefer REAL portfolio work
   over seeded toys: production assignments exercise assignment + locking
   under realistic contention, yield honest LockHeld/collision/close figures,
   and often satisfy another phase's criterion as a side effect (D-079's own
   dogfood did).
2. **Brief.** Give each worker the briefing template below, filled in. Workers
   in worktrees get the hub path explicitly.
3. **Spawn** via the host, all workers in parallel. Prefer few well-scoped
   workers over many thin ones: coordination overhead grows with fleet size
   (Fractal's measured outbox tax), and the measured verdict (D-079) is that
   N buys wall-clock, not quality — see Capability notes.
4. **Monitor.** `cz_status` / `cz_assignments` from the orchestrator. Tracked
   writes serialize through the engine lock; workers seeing `LockHeld` retry
   with backoff — it is contention, not failure.
5. **Collect and verify.** When workers report done, trust but verify (L-66):
   reconcile each claim against engine state — `cz_phase_detail` for criteria
   actually checked, `cz_assignments` for ownership, outputs via the phase's
   recorded `cz_add_output` values. Run an independent verification pass over
   the work product itself; fan-out without independent verification is how
   plausible-but-wrong survives (L-33, L-50). A completion report missing its
   **"What I did not check"** section goes back to the worker (or, for a
   vanished worker, the hub writes the section itself from what it can prove)
   — hub judgment, never an engine gate (D-075, INVARIANT-05).
6. **Clean up dead workers.** A phase left `in_progress` by a vanished worker:
   the stranded-state advisory (landed 2.0 phase 1) surfaces it with a
   judgment menu — adopt / continue / close honestly. On an engine without it,
   the degraded path: inspect PHASE-STATUS.md yourself and either adopt the
   phase or close it honestly — `deferred` with a reason (2.0 phase 0
   vocabulary; on older engines, an explicit status note). Never leave a ghost
   `in_progress`, never launder to complete.

## Worker briefing template

```
You are worker <NAME> in a Clauderizer fleet. Hub repo: <HUB_PATH>.
Your assignment: gameplan <GAMEPLAN_ID>, phase <N> "<PHASE_NAME>" (already
bound to you via cz_assign — do not take other phases).
1. Read the phase handoff and cz_next_phase_context; honor CLAUDE.md.
   FIRST ACT in any worktree/clone: verify your branch point against the
   briefed baseline (git merge-base vs the hub's HEAD; run the suite and
   compare the count) — a briefed baseline number is a checkable claim about
   your checkout, and building on a stale branch point builds phase-N work
   on phase-0 code.
2. ALL tracked writes (cz_* / clauderize ops) go to the hub. If you work in a
   worktree, write memory ONLY via `clauderize --repo <HUB_PATH>` or the
   hub-rooted MCP server. NEVER edit any docs/ copy by hand.
3. On LockHeld: retry with backoff — another worker is writing; this is normal.
4. Close honestly: cz_check_exit_criterion what you can PROVE; transition to
   complete ONLY if criteria are met, else deferred with your reason.
   Record concrete outputs via cz_add_output. Your final text must match
   engine state — an unrecorded claim does not exist.
5. Your completion report MUST end with a "What I did not check" section —
   the negative space of your work (D-075): surfaces you never looked at,
   inputs you did not exercise, claims you took on trust. The hub sends back
   reports that lack it.
```

## Capability notes (be honest about what is landed)

Every mechanism below names the phase that landed it and the degraded path
where it is absent (older engine, or dormant pending graduation):

- Always available: portable exclusive locking, `cz_assign`/`cz_assignments`,
  `--repo`/`CLAUDERIZER_REPO` hub decoupling.
- Honest-close vocabulary (`deferred`, landed 2.0 phase 0) — degraded path on
  older engines: an explicit status note instead of a deferred transition.
- Stranded-worker advisory with judgment menu (landed 2.0 phase 1) — degraded
  path: manual PHASE-STATUS.md inspection (procedure step 6).
- Live-state stamps (landed 2.0 phase 2, **env-armed dormant** per
  INVARIANT-10): workers see hub-state figures on tool results only when the
  worker process is armed with `CLAUDERIZER_STATE_STAMP=1` — sanctioned for
  experiment legs, never a persisted toggle; silent by default until the D-064
  matrix graduates it. Degraded/default path: workers poll `cz_status`.
- Fleet spend aggregation via session stints (landed 2.0 phase 2; budgets are
  **declared-dormant** — no filled template default until the matrix verdict).
  Degraded path: no wind-down advisories; watch spend yourself.
- Worktree-edge merge audit (landed 2.0 phase 4, advisory-silent): detects the
  lost-update shape on docs-touching merges after the fact; its squash blind
  spot is stated in its own docs. It does NOT make memory-in-worktrees safe —
  the hub-and-spoke law stands regardless.
- "More agents = better results" is **measured and BOUNDED** (D-079, the
  D-071 fleet-vs-solo matrix leg): on the same seeded three-phase task,
  fleet and solo tied on quality — zero defects in both under independent
  adversarial verification — while the fleet ran 1.57× faster wall-clock at
  ~1.7× total compute, with 0 LockHeld and 0 collisions under the
  hub-and-spoke law. N buys wall-clock on genuinely independent phases,
  never quality; the quality parity came from the fleet DISCIPLINE (disjoint
  assignments, honest closes, independent verification), so the hub's
  verification pass is where fleet quality is actually made. Pick N from the
  number of genuinely independent phases.

## Anti-patterns

- Memory writes in a worktree copy, merged back later (issue-#9 class).
- Fan-out over dependency-chained phases (workers deadlock on each other's
  unfinished prerequisites).
- Unassigned fan-out — two workers, one phase, interleaved half-truths.
- Complete-laundering by a worker that ran out of context: the honest door is
  deferred, and the orchestrator must not "helpfully" flip it.
- Scaling N because more feels better: the measured verdict (D-079) is a
  quality TIE with a wall-clock win — pick N from the number of genuinely
  independent phases, and spend the saved time on the verification pass.
