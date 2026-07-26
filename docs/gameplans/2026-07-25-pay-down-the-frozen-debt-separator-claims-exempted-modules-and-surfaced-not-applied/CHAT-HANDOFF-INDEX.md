# Chat Handoff Index — pay down the frozen debt — separator claims, exempted modules, and surfaced-not-applied

> Last updated: 2026-07-25
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 1232

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
| 0 | Triage the 24 separator-shaped assertions and make the class machine-rejectable | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Pay down the 32 exempted modules | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Close out and ship 1.14.3 with both ratchets tighter | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-25

Triaged every separator-shaped assertion in the repo and turned the class into a machine check. The first finding was that the phase's own premise was off: the "24" came from grepping `assert "…/…" in …`, and an AST scan over src/, tests/ and scripts/ found 40 (33 distinct file+literal keys) — grep cannot see single-quoted literals, a second literal on one line, the non-first arms of an `or` chain, or `not in` forms. Recorded as C-01, because the count is load-bearing: the ratchet is pinned at the post-triage number, and pinning it at 24 would have left 16 sites permanently outside the guard while reading as complete. The second finding was that all 40 are message assertions — zero platform claims survive, because commit f9f8343 had already fixed the only real instance in 1.14.2's aftermath. Exit criterion 3 is therefore satisfied vacuously, and that is stated rather than dressed up as repair work.

The deliverable is `tests/test_separator_claims.py` (21 tests) plus `tests/fixtures/separator_claims_baseline.json`, which carries the written classification of every site — the reason each slash holds on Windows, not a count. The detector flags two shapes the source itself gives evidence for: Rule A, where the compared-against value announces itself a path (`m["serving_path"]`, or a bare `str()`, with `.as_posix()` exempt as the sanctioned fix), and Rule B, where the literal is a fragment of an absolute-path literal in the same module. Rule B exists because the 1.14.2 fix commit had to change *two* lines, and the second (`assert "uv/archive-v0" in digest`) announces nothing — a check that caught only the criterion's named line would have missed half the actual regression. The behavioral oracle was run against the real pre-fix blob at `f9f8343^` using only `ast` and the filesystem: both lines flagged, 2 of 2. The false-positive floor is asserted, not asserted-to: 11 message-assertion shapes are parametrized (a fraction, `n/a`, cmd.exe `/b` and `/d` flags, a slash command, an XML tag, authored .gitignore lines, HostEmitter constants, an f-string slash, an `.as_posix()` producer) and the whole real 40-site corpus is checked to stay unflagged. The guard was arm-tested by injecting the regression into a scratch module: both the class check and the untriaged-site ratchet went red, green again on removal. The module states its own scope limit plainly — a path-valued expression that neither declares itself nor traces to a path literal is not statically decidable, and the inventory ratchet is the backstop that cannot classify such a site but can refuse to let it appear unclassified. Suite 1232 → 1253 passed, 7 skipped, zero failures.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** Never scope a defect class by a grep count when the class is defined syntactically — count it with the same instrument that will enforce it, or the ratchet inherits the blind spot.
