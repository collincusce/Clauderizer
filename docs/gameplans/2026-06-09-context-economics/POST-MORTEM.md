# Context Economics — Post-Mortem

> Author: Claude Code session (claude/clauderizer-feedback-sjk1eu)
> Date: 2026-06-09
> Scope: Full retrospective on phases 0–2, executed 2026-06-09 in a single session.

## Executive Summary

Review finding 5 closed in three phases under ADR D-009 (consolidation pressure,
not caps): `cz_consolidate_lessons` synthesizes overlap within a gameplan,
`cz_promote_lesson` carries enduring lessons into a compact project-level
`docs/LESSONS.md` that rides in every future handoff across gameplans, and the
status digest gained a memory gauge (`Memory: N active lessons, M project
(~K tok handoff)`) that warns past 12 active lessons and names the remedies.
Tests grew 107 → 109 across the gameplan (99 → 109 from its start). Nothing in
the memory is ever deleted; every mechanism marks and redirects.

## What the Gameplan Got Right

### 1. Promotion was exercised on real history, not synthetic data
Phase 1's close-out curated the two *closed* gameplans: four genuinely enduring
lessons (idempotency round-trips, capability-not-presence health checks,
fetch-tools-don't-mutate, round-trip-what-you-write) became L-01..L-04 — and the
very next handoff this gameplan wrote carried them. The cross-gameplan
continuity gap was demonstrated solved in the same session it was built.

### 2. Deciding the cascade policy up front
D6 (entity bumps cascade once, at close) was recorded before Phase 0 wrote any
code, because the same-day report-collision bug was already on the open-threads
list. No reports were overwritten this time.

## What the Gameplan Got Wrong

### 1. The gauge's token estimate needed a guard nobody planned
`compute()` now assembles the next handoff in-memory to size it; that made the
status digest depend on handoff assembly never raising. Wrapped best-effort
(the gauge must never break the digest) — but the dependency was discovered
while writing the code, not the plan.

## Procedure Improvements

- Close-gameplan now has a lesson-curation step. Consider making the coordinator
  checklist mirror it (consolidate → promote → archive) so non-Clauderizer
  adopters of the procedure get the same pressure.

## Open Threads

- `ACTIVE_LESSONS_WARN` as a config knob if real projects need a different line
  (D5 kept it a constant for v1).
- No size pressure yet on `docs/LESSONS.md` itself beyond `L-NN` obsolescence;
  if project lists grow past ~20 active entries, consolidation at project scope
  is the natural extension.
- Still open from the previous gameplan: cascade report filename collision,
  placeholder-aware `next_numbered_id`, blessed writes for the Outputs Registry
  and tracker header lines.
