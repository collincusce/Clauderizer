# pay down the frozen debt — separator claims, exempted modules, and surfaced-not-applied — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-25

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Triage the 24 separator-shaped assertions and make the class machine-rejectable | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Pay down the 32 exempted modules | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Close out and ship 1.14.3 with both ratchets tighter | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
separator_shaped_assertions_total: 40 sites across 33 distinct `<file>::<literal>` keys (AST scan of src/, tests/, scripts/). The gameplan's "24" was a grep undercount — see C-01. Ratcheted both directions in tests/fixtures/separator_claims_baseline.json.
platform_claims_remaining: 0. All 40 are message assertions. The only real instance of the class (`assert "uv/archive-v0" in m["serving_path"]` plus its sibling `... in digest`) was already fixed by commit f9f8343 in 1.14.2's aftermath, so exit criterion 3 is satisfied vacuously and honestly.
guard_artifacts: tests/test_separator_claims.py (21 tests) + tests/fixtures/separator_claims_baseline.json (the written triage, machine-read by the ratchet). Detector = Rule A (RHS trailing identifier is path/dir/file/root/home, or a bare str() coercion; .as_posix() exempt) OR Rule B (literal is a fragment of an absolute-path literal in the same module).
suite_after_phase_0: 1253 passed, 7 skipped (was 1232 passed at preflight; +21 from tests/test_separator_claims.py). Zero failures.
```

## Corrections Log

### C-01 — Phase 0

**Phase**: 0
**What gameplan said**: There are 24 separator-shaped assertions to triage, found by the pattern `assert "…/…" in …`, and the phase's job is to classify those 24 and fix the ones that are platform claims.
**What was actually correct**: The real class is 40 sites (33 distinct file+literal keys). The 24 was a grep artifact: a text pattern over `assert "…/…" in …` cannot see single-quoted literals, a second literal on the same line (test_init.py:269 has two), the non-first arms of an `or` chain (test_init.py:265/266/267 — grep saw only 265), `not in` forms (5 of them), or a literal whose line differs from the `assert` keyword's. An AST scan over src/, tests/ and scripts/ found all 40. Separately, ZERO of the 40 turned out to be platform claims — every one is a message assertion, because commit f9f8343 had already fixed the only real instance of the class in 1.14.2's aftermath. So the "fix every platform claim" criterion was satisfied vacuously, and the deliverable is the triage plus the guard, not a set of repairs.
**Why**: The phase was scoped by counting with the same kind of tool the defect class hides from. Grep counts text; the class is a property of syntax. Recording this matters because the count itself was load-bearing — the ratchet is pinned at the post-triage number, and pinning it at 24 would have left 16 sites permanently outside the guard while reading as complete.
**Lesson**: Never scope a defect class by a grep count when the class is defined syntactically — count it with the same instrument that will enforce it, or the ratchet inherits the blind spot.
