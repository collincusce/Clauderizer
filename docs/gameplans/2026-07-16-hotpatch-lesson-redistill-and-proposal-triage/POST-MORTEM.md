# Post-Mortem — hotpatch-lesson-redistill-and-proposal-triage (1.8.1)

> Closed: 2026-07-17 · Kind: driven · Phases: 4/4 complete · Outcome: shipped

## Overview

A "minor hotpatch" to clear two standing items surfaced at session start: the
project-lesson corpus had drifted to **34** active lessons (`docs/LESSONS.md`
rides every handoff across all gameplans, so >20 is portfolio-wide bloat), and
one advisory `no_standing_conditions` proposal was pending for the
standing-curator loop. What began as memory housekeeping turned into a genuine
**1.8.1 patch release** when dogfooding surfaced a real parser bug (H-18).

Outcome: lessons **34 → 19** (kept lean even after close: 20 with one promotion);
curator loop now self-arms on lesson drift; H-18 fixed in two sibling parsers;
suite **821 → 823**; **1.8.1 live on PyPI**, verified from a fresh install.

## What worked

- **Measure-before-acting (dogfooding L-50).** Every risky step was probed first:
  the standing-condition shell probe was run before it was declared; the published
  1.8.1 wheel was fresh-installed and asserted to carry the H-18 fix before the
  gameplan closed. No step was declared done on assumption.
- **The audit's consumer re-check earned its keep.** `cz_audit`'s "re-audit every
  consumer" prompt is what turned up `skill_state.py` — the exact same paren bug
  as `lesson_state.py`. Fixing only the lesson parser would have shipped a
  half-fix.
- **Honest release scoping.** Rather than cut a code-identical 1.8.1, we stopped,
  surfaced that no shipped code had changed, and folded in the H-18 fix so the
  release carried a real payload (amendment A-001).
- **Append-only discipline held.** All 22 consolidated lessons + L-43 were marked,
  never deleted (INVARIANT-03); the full audit trail survives.

## What didn't — and the root cause each time

- **H-18: marker parser mis-read reasons containing `)`.** The obsolete/promoted
  marker regex used `[^()]*`, so a reason like `(obsolete …: superseded (see L-50))`
  failed to match and the lesson read as **active** — silently kept riding every
  handoff. Found only because our *own* re-distill wrote such a reason (L-43) and
  the count came out one high. Root cause: an end-anchored structured-marker regex
  that forbade delimiters its own free-text payload could contain. Fixed in both
  `lesson_state.py` and `skill_state.py` (one level of nested parens tolerated,
  end-anchor + `\b` keep mid-text mentions inert); regression tests added.
- **Stale editable-install metadata turned 11 tests red.** Bumping the source to
  1.8.1 left the installed `.dist-info` at 1.8.0, so `importlib.metadata.version()`
  and doctor's version check disagreed — 11 doctor/version tests went red until
  `pip install -e .` refreshed the metadata. Root cause: exactly the L-51
  clean-environment failure mode; the working install is not the artifact.
- **D1 planned the wrong mechanism.** The plan said "promote L-07/L-21/L-42 via
  `cz_promote_lesson`," but those were already project lessons — promotion is a
  gameplan→project move, a no-op here. The real lever was consolidate + obsolete.
  Recorded as correction C-01; promoted as L-57. Root cause: read
  `cz_lesson_health`'s "promotion candidate" (= high-utility, keep) as "move it."

## Procedure improvements

- **Add "reinstall the editable package after a version bump" to the release
  checklist** (before running the suite) — it deterministically prevents the
  11-red-tests detour. L-51 covers the registry sweep; this is the local-env
  companion step.
- **Marker-reason hygiene is now enforced by code, not care.** With H-18 fixed,
  `(resolved …)` / `(obsolete …)` reasons may contain parentheses safely; before
  the fix we had to hand-avoid them (and did, per H-18 in the resolution notes).
- **Corpus re-distill guidance is now a promoted lesson (L-57)**: consolidate +
  obsolete, never promote-the-sources; 0 duplicate pairs ⇒ thematic synthesis, not
  near-duplicate merging. Directly serves the recurring curator-loop work the new
  standing condition will trigger.

## Open threads

- **Stashed WIP (`stash@{0}`)** — the kimi-code integration + procedure 1.7 bump
  the session started with, parked to keep the hotpatch tree clean. On restore,
  `cz_modernize` will re-offer the procedure-stamp mechanical updates (they came
  from that stash). Not owned by this gameplan.
- **No new code debt.** H-18's fix is complete across both parsers; the finding is
  resolved. No deferred sub-tasks.

## Metrics

| | Before | After |
|---|---|---|
| Active project lessons | 34 | 19 (20 post-close promotion) |
| Test suite | 821 | 823 |
| Pending advisory proposals | 1 | 0 |
| Open findings | H-18 open | H-18 resolved |
| Version | 1.8.0 | 1.8.1 (live on PyPI) |
