# clear the findings backlog to zero and give the register a detector — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-25

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Engine identity — the digest says when it is not the build the working tree describes | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Planning surfaces the lessons that govern planning (H-25) | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-1-HANDOFF.md |
| 2 | The digest nudges on the cost it names, and the register stops being write-only (H-26 + the aging detector) | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Two core-path lows: a symlinked parent directory, and a gameplan that cannot be closed (H-16 + H-21) | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Subsystem docs get an executable seam against their module (H-24) | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Close out and ship 1.14.2 with the backlog at zero | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
DETECTOR: src/clauderizer/engine_identity.py -- tree_package_dir(paths), tree_version(paths) (read as TEXT, since importing would re-import the running module and compare it to itself), serving_build(paths, module_file=None, running_version=None) -> mismatch dict | None with module_file/running_version injectable for testing, describe(mismatch). Wired at status_bundle.compute (bundle['engine_identity']) and render_digest ('⚠ Engine identity: ').
SUITE: 1164 -> 1177 passed, 7 skipped (+13, tests/test_serving_build_identity.py)
```

### Phase 1 Outputs

```
PLAN_TIME_SURFACING: rituals/handoff.plan_lessons(paths, goal_text, k=RELEVANCE_K) -> ranked [{id,title,score}] | []. Wired at ops.cz_create_gameplan, which passes f'{name} {first_phase}' and records telemetry.record_surfaced(phase='plan'). Additive: focus behavior, scaffolding and every existing result key are unchanged, pinned by test_focus_and_scaffold_behavior_is_unchanged.
SUITE: 1177 -> 1184 passed, 7 skipped (+7, tests/test_plan_time_lessons.py)
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
