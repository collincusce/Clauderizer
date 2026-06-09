# Discipline Seams — Post-Mortem

> Author: Claude Code session (claude/clauderizer-feedback-sjk1eu)
> Date: 2026-06-09
> Scope: Full retrospective on phases 0–2, executed 2026-06-09 in a single session.

## Executive Summary

All three review findings closed in three phases: cascade resolution and lesson
obsolescence got blessed writes (`cz_resolve_cascade`, `cz_obsolete_lesson`),
handoff regeneration became marker-protected so agent enrichment survives
(D-008), and the baseline test count is now written back by preflight while
completed gameplans report success instead of a dead end. Tests grew 84 → 99.
The gameplan also caught two real bugs it wasn't looking for — the invalid-TOML
lock file and the `-qq` flag doubling — both found because Phase 2's exit
criterion demanded the *live* repo demonstrate the write-back, not just the
test suite.

## What the Gameplan Got Right

### 1. "Demonstrate on the live repo" as an exit criterion
Task 2.3 (dogfood the write-back on this repo) is what exposed the lock-file
TOML bug and the `-qq` interplay. The unit tests alone would have passed
against a fiction.

### 2. Using the new tool in its own close-out
`cz_resolve_cascade`'s first real use was resolving the cascade from Phase 0's
own version bumps. Every later phase resolved its cascades the same way; no
hand-edited report exists in this gameplan.

## What the Gameplan Got Wrong

### 1. Assumed the baseline pipeline already worked
**Cost**: an extra debugging loop mid-Phase 2.
**Root cause**: `to_lock_toml` wrote unescaped backslashes (invalid TOML) and
`load_for_repo` swallowed the parse error silently — so the "measured count"
the plan relied on had never actually been measured on this repo (C-02).
**Lesson**: every file the engine writes must round-trip through its own parser
in tests; silent fallback on config parse errors is a footgun.

### 2. Decision numbering started at D3
**Cost**: cosmetic, but permanent in the record.
**Root cause**: `next_numbered_id` counted the template placeholder prose
"D1, D2, …" as existing IDs (C-01).

## Procedure Improvements

- Cascade report filenames are date+entity; two same-day cascades of one
  entity silently overwrite the earlier report. `report_filename` needs a time
  or sequence component (lesson #5; candidate next fix).
- Auto-numbering should not count IDs that appear only in scaffold placeholder
  prose (lesson #1).

## Open Threads

- **Review finding 5 (context economics)** — deliberately deferred: pruning
  pressure on cumulative memory (e.g. close-gameplan promoting lessons into a
  compact project doc). `cz_obsolete_lesson` is the mechanism; the policy is
  future work.
- Tracked-doc surfaces that still lack a blessed write: the Outputs Registry
  and Per-Phase Completion Summaries sections, and the `> Status:` /
  `> Last updated:` header lines of tracker docs (this file's gameplan still
  says "Phase 0 ready" in its index header).
- `report_filename` collision fix, and placeholder-aware `next_numbered_id`.
