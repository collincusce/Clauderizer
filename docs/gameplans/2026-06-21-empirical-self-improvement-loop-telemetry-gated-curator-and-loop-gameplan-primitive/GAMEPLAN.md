# Empirical self-improvement loop - telemetry-gated curator and loop-gameplan primitive Gameplan

> Created: 2026-06-21
> Status: Executing
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

_(1–2 paragraphs: what this gameplan accomplishes.)_

## Subsystems Touched

_(list the subsystems/features this gameplan affects.)_

## Source-of-Truth Captures

_(Real values captured from real systems at gameplan start. Authority over the
gameplan body. Account IDs, ARNs, baseline test counts, versions.)_

## Amendments

### A-001 — EC2 typed-edge scope: redundant auto-detected, alternative agent-assignable (D-018)

- **Date**: 2026-06-21
- **Affected sections in GAMEPLAN.md**: Phase 3 exit criteria
- **Affected phases**: 3
- **Triggered by**: D-018 (deterministic, no-ML/no-embeddings constraint)
- **What changed**: cz_analyze now labels each suggested edge with a kind: redundant (lexical near-duplicate, shared/min-tokens >= 0.8, auto-detected) or related (a plausible depends_on). 'alternative' (same goal, different mechanism) is NOT auto-detected - it remains an agent-assignable kind in the typed-edge vocabulary.
- **Why**: D-018 forbids ML/embeddings; 'alternative' is a semantic relation that is not lexically decidable, so auto-emitting it would be a false signal. Honest scope: the engine auto-detects the two lexically-decidable kinds and leaves the semantic one to the agent's judgment (INVARIANT-05).

## Decisions

### D1 — Telemetry is a deterministic append-only signal log, never ML or auto-mutation

**Context**: The keystone gap (verified twice against the engine) is the absence of any persisted empirical signal: nothing records which lessons/invariants were surfaced or whether the phase then passed. Without it, utility/failure-rate scoring and any 'did memory help' claim are impossible. But INVARIANT-05/D-018 forbid ML and auto-mutation.
**Decision**: Add a deterministic, stdlib-only, append-only telemetry log (INVARIANT-03) recording surfacing events (from the existing relevance ranker) and phase outcomes (from exit-criteria checks). It SURFACES signal only; it never decides, ranks by ML, or writes to the corpus.
**Consequences**: Enables usage-driven scoring while upholding the constitution. Adds an on-disk log plus read-only cz_corpus_health/cz_lesson_health surfaces. Telemetry must be derivable from blessed events already happening (cz_write_handoff, cz_transition_phase).
**Status**: active (2026-06-21)

### D2 — The Curator PROPOSES; the agent confirms every mutation through a blessed cz_* write

**Context**: Frontier systems (SkillOps/AutoSkill) auto-mutate skill libraries in a background curator. Clauderizer's constitution (D-015/INVARIANT-05: engine surfaces, agent decides; no enable/disable flags) forbids silent rewriting of memory, which the literature also flags as the top drift/audit risk.
**Decision**: cz_curate is read-only and PROPOSES a batch of maintenance actions with evidence, exactly like cz_mine_failures. Consolidate/obsolete/promote are applied only via the existing blessed cz_* tools the agent invokes, preserving the append-only audit trail.
**Consequences**: Reconciles autonomy with auditability: the loop is autonomous in cadence, supervised in mutation. No new write authority is created; every change stays traceable and reversible.
**Status**: active (2026-06-21)

### D3 — Loop gameplans are autonomous-in-cadence, supervised-in-mutation, and interlock with driven gameplans

**Context**: The user asks whether to build a system that creates autonomous loop gameplans distinct from typical driven gameplans. A driven gameplan is a finite phase DAG with a terminal post-mortem; maintenance/curation is a standing, recurring cycle with different lifecycle semantics.
**Decision**: Introduce a loop gameplan as a first-class type: a standing gameplan whose phases are recurring iterations with a trigger, a per-iteration exit, and a convergence metric tracked over time. Driven gameplans FEED the loop (their lessons/failures are its input); the loop SPAWNS driven gameplans when it detects structural work too big for a maintenance pass.
**Consequences**: Two complementary types: driven = build new capability (completes); loop = continuously distill and maintain the corpus (standing). The loop never auto-mutates beyond the propose-confirm boundary of the curator decision.
**Status**: active (2026-06-21)

### D4 — No phase may claim improvement without a before/after metric on a held-out eval

**Context**: The user's explicit requirement is verifiable improvement, test and retest. Reflexion-style loops are bounded by reliable success/failure signals; a self-improvement system that cannot measure its own delta is unfalsifiable.
**Decision**: Every phase claiming a memory-quality improvement must show a baseline captured at gameplan start and a measured delta on a held-out eval (the 0.15.0 focused-vs-full agent-eval is the template), plus a green test suite. Exit criteria are machine-checkable.
**Consequences**: Forces the telemetry+eval harness early (Phase 0/1) as a prerequisite; makes the initiative falsifiable; intentionally slows any phase that lacks a metric.
**Status**: active (2026-06-21)

### D5 — Loop-iteration exit follows the Loop Engineering /goal triad; Routines is the O-03 cadence candidate

**Context**: rari's 'Loop Engineering' (the named 2026 discipline; Osmani/Cherny/Steinberger) defines a good autonomous goal as three parts - an explicit end state, a runnable check, and a guardrail - and ships cadence via Claude Code Routines (a cloud schedule that runs while the laptop is closed). Practitioners already bolt a GitHub repo on as the loop's 'memory/notepad'; Clauderizer is the engineered version of that substrate.
**Decision**: Each loop-gameplan iteration's per-iteration exit (Phase 4) is authored as the /goal triad: (1) an explicit end state, (2) a machine-runnable check (cz_check_exit_criterion and/or a cz_corpus_health delta), (3) a guardrail (max-iterations + scope pin). Claude Code Routines is the leading cadence mechanism for the standing loop, evaluated in O-03 against the SessionStart-nudge and CI-cron alternatives.
**Consequences**: Phase 4 inherits a concrete exit template and a cadence shortlist; the loop stays autonomous-in-cadence, supervised-in-mutation (D2). The shape is validated against the field, not invented.
**Evidence**: Loop Engineering (Addy Osmani, Jun 2026); sabrina.dev /goal+Routines guide; rari @0xwhrrari article 2065524169517785088
**Status**: active (2026-06-21)

## Open Items

**O-01.** _(phase 0)_ Minimum telemetry to compute utility reliably: which fields (lesson id, phase id, surfaced?, passed?), what recency window, and is the signal dense enough on a real project to be meaningful rather than noisy?

**O-02.** _(phase 2)_ Is ANY Curator action safe to auto-apply within bounds (e.g. a provably reversible dedup of byte-identical lessons) versus always agent-confirm? Where exactly is the auto-apply line that still honors INVARIANT-05? _(resolved 2026-06-21: Resolved by Phase 2 design: cz_curate is strictly propose-only (read-only, like cz_mine_failures) - NO action auto-applies. Every mutation routes through an agent-confirmed blessed cz_* write (D2 / INVARIANT-05). The auto-apply line is: none for now - autonomy lives in cadence and proposal, never in mutation; a bounded future auto-apply (e.g. byte-identical dedup) stays out of scope behind the propose-confirm boundary.)_

**O-03.** _(phase 4)_ Cadence wiring for the standing loop: SessionStart 'curator due' nudge vs CI/cron propose-pass that opens a confirm queue vs purely manual invocation - which cadence is both autonomous and constitution-safe? _(resolved 2026-06-21: Addressed by Phase 4 + D5: the iteration engine is cz_loop_step (agent-invoked today). Documented cadence options: Claude Code Routines (cloud cron, runs while the laptop is closed), a SessionStart 'curator due' nudge, or manual invocation. The loop is autonomous-in-cadence once wired to any trigger; wiring a specific cadence is a deployment choice for the operator, not an engine requirement - so it does not block the primitive.)_

## Phase Breakdown

### Phase 0: Telemetry substrate & baseline

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] A telemetry record is appended on cz_write_handoff (which lessons/invariants were surfaced) and on cz_transition_phase->complete (which exit criteria checked/passed) - deterministic, stdlib-only, append-only (INVARIANT-03/D-018)
- [x] cz_corpus_health returns a deterministic metric (active-lesson count, lexical-redundancy estimate, never-surfaced count) with zero ML / third-party deps
- [x] Baseline corpus-health snapshot AND test count recorded in PHASE-STATUS Outputs Registry as source-of-truth
- [x] New tests cover telemetry round-trip + metric determinism; full suite green at >= baseline count

### Phase 1: Utility & failure-risk scoring (advisory)

**Goal**: Compute per-lesson utility (recent-success fraction), failure-risk, and time-decay from Phase 0 telemetry and SURFACE them read-only; validate the score against held-out judgment on a labeled sample.
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_lesson_health surfaces per-lesson utility (recent-success fraction), failure-risk, and time-decay - deterministic, advisory only (performs no writes)
- [x] An agent-eval shows the score agrees with held-out judgment on a labeled sample at an agreed threshold (the 0.15.0 focused-vs-full eval is the template)
- [x] Parity / INVARIANT-05 test confirms cz_lesson_health is read-only (writes=False in REGISTRY)
- [x] Full suite green

### Phase 2: The Curator - propose-confirm maintenance pass

**Goal**: A read-only cz_curate op that, from health scores plus lexical redundancy, PROPOSES consolidate/obsolete/promote/flag actions the agent confirms via blessed cz_* writes; A/B it against judgment-only on the corpus-health metric.
**Depends on**: Phase 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_curate proposes consolidate/obsolete/promote/flag actions with evidence, read-only (PROPOSE-only, exactly like cz_mine_failures)
- [x] A/B vs judgment-only baseline shows corpus-health improves by an agreed delta with NO recall@k regression on the handoff relevance eval
- [x] Every applied change routes through the existing blessed cz_* writes (audit trail intact; no new write authority)
- [x] Full suite green

### Phase 3: Empirical-gated promotion & typed-edge risk surfacing

**Goal**: Gate promotion suggestions on empirical recurrence (Darwin-Godel style) and extend analyze/cascade with redundant/alternative typed-edge suggestions plus preemptive risk flags on dependents of shaky upstream entities.
**Depends on**: Phase 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Promotion suggestions require empirical recurrence evidence (surfaced across >= N phases and correlated with passing) - the agent still decides
- [x] cz_analyze emits typed redundant/alternative edge suggestions (extending the existing edge_suggester); cz_cascade preemptively flags dependents of a shaky upstream entity
- [x] Deterministic (no ML, D-018) and advisory (no auto-write, INVARIANT-05) - verified by test
- [x] Full suite green

### Phase 4: The loop-gameplan primitive

**Goal**: Generalize the Curator into a first-class loop-gameplan type (trigger, iteration body, per-iteration exit, convergence metric, spawn-driven-gameplan escape hatch); document it in GAMEPLAN-PROCEDURE.md; prove K-iteration convergence.
**Depends on**: Phase 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] A loop gameplan can be created (kind=loop), runs one curator iteration, records a convergence metric across iterations, and spawns a driven gameplan when it detects out-of-scope structural work
- [x] A K-iteration test shows proposals converge to 0 and corpus-health is monotone non-decreasing on a seeded corpus
- [x] GAMEPLAN-PROCEDURE.md bumped (MINOR) documenting the loop-gameplan type
- [x] Full suite green

### Phase 5: Close-out, dogfood & ship

**Goal**: Consolidate and promote enduring lessons, write the post-mortem with procedure improvements, bump version and release-check, and flip the bootstrap into a standing loop gameplan maintaining Clauderizer's own corpus.
**Depends on**: Phase 4.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Close-out consolidation done; enduring lessons promoted to LESSONS.md; post-mortem written with procedure improvements
- [ ] Suite green, doctor green, release-check exit 0; version bumped (target 0.17.0)
- [ ] The standing loop gameplan is active and maintaining Clauderizer's own corpus (dogfood)
