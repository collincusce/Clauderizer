# Post-Mortem — 2026-06-21-empirical-self-improvement-loop

> Author: Opus 4.8 session (driven autonomously after CEO go-ahead)
> Date: 2026-06-21
> Scope: Phases 0–4 built, tested, and committed on `feat/empirical-self-improvement-loop`;
> Phase 5 local close-out done. **Ship of 0.17.0 (merge → push → tag → PyPI) is the one
> remaining step, deliberately paused for human authorization (irreversible/public).**

## Executive Summary

Built the empirical self-improvement loop that the deep-research pass + the user's
"Loop Engineering" sources pointed at — and did it *under Clauderizer's own constitution*
rather than around it. The keystone was the one verified gap: **no persisted empirical
signal**. Phase 0 added an append-only telemetry log (which memory a handoff SURFACED;
whether the phase then PASSED); Phases 1–4 turned that signal into per-lesson health
scoring, a propose-only curator, empirical-gated promotion + typed-edge/risk surfacing,
and finally the **loop-gameplan primitive** (`cz_loop_step` + `kind=loop`). Tool surface
31 → 35, suite 548 → 573, every phase gated on a green suite and a measurable delta
(D-026). The loop is **autonomous in cadence, supervised in mutation**: every new op is
read-only and advisory (INVARIANT-05); all mutation still routes through the existing
blessed writes the agent confirms.

## What the gameplan got right

1. **Telemetry-first sequencing.** Making the empirical signal Phase 0 meant every later
   phase had a real metric to verify against. The before/after on the live repo
   (never_surfaced 20→15, pass_rate null→1.0 from the loop feeding itself) proved the
   substrate end-to-end, not just in tests.
2. **The constitution as a design asset, not a constraint.** "Engine surfaces, agent
   decides" (INVARIANT-05) + "no ML" (D-018) forced the propose-confirm curator — which
   independently matches the practitioner best-practice ("start read-only") and sidesteps
   the documented auto-mutation drift risk. The `cz_analyze` gate even auto-confirmed the
   gameplan's own decisions aligned with existing canon (D-026, D-023, D-013).
3. **Verifiability discipline held.** Every phase shipped with new tests and a green suite;
   no phase claimed improvement without a number. The one over-specified criterion
   (auto-detecting a semantic "alternative" edge under no-ML) was handled by an honest
   amendment (A-001), not a faked checkbox.

## What didn't (root causes)

1. **A genuinely-flaky timing test surfaced mid-run.** `test_locking.py::test_crashed_holder_blocks_at_most_stale_timeout`
   went red once (`waited=0.103` vs `>=0.4`) then green on re-run — the documented
   `test_locking` load-sensitivity, unrelated to this work. Cost: one extra suite run.
   Flagged as a follow-up (de-flake with a tolerance or a deterministic clock).
2. **Driving the engine from a Windows host is quote/space-fragile.** Git-Bash `bash -lc`
   mangled slash args (H-08 family); long PowerShell `-lc` strings and `$(...)`-bearing
   commands truncated output mid-space repeatedly. The reliable lane was the clean-arg form
   `wsl.exe --cd <repo> -- ./.venv/bin/<prog> <args>` + Write-tool JSON batches through
   `clauderize ops` (L-05 earned its place again, this time for a Claude session, not just
   a cross-model one).

## Procedure improvements

1. **Loop Gameplans are now a documented first-class type** (GAMEPLAN-PROCEDURE.md
   v1.2.1 → v1.3.0, both the bundled template and the repo copy): trigger / iteration body /
   per-iteration `/goal`-triad exit / convergence metric / spawn-driven escape hatch.
2. **Telemetry is the missing rung under D-026's "empirical gain-gate."** D-026 demanded
   measurable benefit; until now there was no persisted signal to measure memory utility
   over time. Future memory features should report against `cz_corpus_health` /
   `cz_lesson_health` deltas, not one-shot evals alone.

## Open threads

- **Ship 0.17.0** (the paused step): commit Phase 5 → merge to main → push → release-check
  exit 0 → tag → `gh release` → PyPI. Awaiting human authorization.
- **Cadence wiring (O-03, resolved-as-deployment-choice):** wire the standing loop to a
  trigger — Claude Code Routines (cloud cron), a SessionStart "curator due" nudge, or
  manual. Not an engine requirement; an operator decision.
- **De-flake `test_locking`** timing assertion (tolerance or injected clock).
- **Telemetry persistence policy:** currently machine-local (gitignored). Whether to commit
  aggregates / sync across machines is a deferred decision (noted in `.gitignore`).
- **Curator on a mature corpus:** the never-surfaced signal is only meaningful once
  telemetry has history; on a fresh corpus the agent must (and did) decline premature
  obsoletion — a real-world test of the propose-confirm boundary.
