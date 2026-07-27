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
   that share a dependency edge — sequence those.
2. **Brief.** Give each worker the briefing template below, filled in. Workers
   in worktrees get the hub path explicitly.
3. **Spawn** via the host, all workers in parallel. Prefer few well-scoped
   workers over many thin ones: coordination overhead grows with fleet size
   (Fractal's measured outbox tax), and the "more agents = better" thesis is
   under test (D-071), not proven.
4. **Monitor.** `cz_status` / `cz_assignments` from the orchestrator. Tracked
   writes serialize through the engine lock; workers seeing `LockHeld` retry
   with backoff — it is contention, not failure.
5. **Collect and verify.** When workers report done, trust but verify (L-66):
   reconcile each claim against engine state — `cz_phase_detail` for criteria
   actually checked, `cz_assignments` for ownership, outputs via the phase's
   recorded `cz_add_output` values. Run an independent verification pass over
   the work product itself; fan-out without independent verification is how
   plausible-but-wrong survives (L-33, L-50).
6. **Clean up dead workers.** A phase left `in_progress` by a vanished worker:
   with 2.0-alpha phase 1 landed, the stranded-state advisory surfaces it with
   a judgment menu (adopt / continue / close honestly). Until then: inspect
   PHASE-STATUS.md yourself and either adopt the phase or close it honestly —
   `deferred` with a reason (2.0-alpha phase 0; before that, an explicit
   status note). Never leave a ghost `in_progress`, never launder to complete.

## Worker briefing template

```
You are worker <NAME> in a Clauderizer fleet. Hub repo: <HUB_PATH>.
Your assignment: gameplan <GAMEPLAN_ID>, phase <N> "<PHASE_NAME>" (already
bound to you via cz_assign — do not take other phases).
1. Read the phase handoff and cz_next_phase_context; honor CLAUDE.md.
2. ALL tracked writes (cz_* / clauderize ops) go to the hub. If you work in a
   worktree, write memory ONLY via `clauderize --repo <HUB_PATH>` or the
   hub-rooted MCP server. NEVER edit any docs/ copy by hand.
3. On LockHeld: retry with backoff — another worker is writing; this is normal.
4. Close honestly: cz_check_exit_criterion what you can PROVE; transition to
   complete ONLY if criteria are met, else deferred with your reason.
   Record concrete outputs via cz_add_output. Your final text must match
   engine state — an unrecorded claim does not exist.
```

## Capability notes (be honest about what is landed)

- Works today: locking, `cz_assign`/`cz_assignments`, `--repo` hub decoupling.
- 2.0-alpha phase 0 adds the `deferred` honest-close vocabulary; phase 1 the
  stranded-worker advisory; phase 2 live-state stamps (workers see hub changes
  on their next tool result) and fleet spend aggregation; phase 4 the
  worktree merge audit. Where a mechanism is not landed, use the degraded
  path named above — do not describe unbuilt behavior to workers as present.

## Anti-patterns

- Memory writes in a worktree copy, merged back later (issue-#9 class).
- Fan-out over dependency-chained phases (workers deadlock on each other's
  unfinished prerequisites).
- Unassigned fan-out — two workers, one phase, interleaved half-truths.
- Complete-laundering by a worker that ran out of context: the honest door is
  deferred, and the orchestrator must not "helpfully" flip it.
- Scaling N because more feels better: pick N from the number of genuinely
  independent phases, then let the D-071 matrix verdict tune the guidance.
