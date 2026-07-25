# clear the findings backlog to zero and give the register a detector — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-25

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Engine identity — the digest says when it is not the build the working tree describes | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Planning surfaces the lessons that govern planning (H-25) | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-1-HANDOFF.md |
| 2 | The digest nudges on the cost it names, and the register stops being write-only (H-26 + the aging detector) | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Two core-path lows: a symlinked parent directory, and a gameplan that cannot be closed (H-16 + H-21) | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Subsystem docs get an executable seam against their module (H-24) | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-4-HANDOFF.md |
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

### Phase 2 Outputs

```
TOKEN_NUDGE_AND_AGING: status_bundle.PROJECT_LESSON_TOKENS_WARN=5000 with memory['project_lesson_tokens'] reported whether or not it fires; _findings_by_age(open_findings, today=None) -> {oldest_id, oldest_days, stale_ids} | None with FINDING_STALE_DAYS=30, surfaced as bundle['findings_age'] and appended to the existing Open findings digest line. Live at close: project lessons ~6168 tok across 20 entries (fires); oldest open finding H-16 at 32d.
SUITE: 1184 -> 1194 passed, 7 skipped (+10). tests/test_rituals.py::test_memory_gauge_honors_configured_thresholds updated deliberately to the new token contract — a golden update, not a loosened assertion.
```

### Phase 3 Outputs

```
TWO_CORE_LOWS: H-16: markdown/writer.refuse_if_symlink walks path.parents (existing dirs only, stops at fs root). H-21: _tables._STATUS_WORDS gains DEFERRED/SUPERSEDED/ABANDONED/WONTFIX -> 'deferred' ahead of GATED/BLOCKED; status_bundle._lifecycle, gameplan_card['open'] and the completion branch all updated together. SUITE 1194 -> 1213.
```

### Phase 4 Outputs

```
DOC_SEAM_RATCHET: tests/test_subsystem_doc_seam.py + tests/fixtures/subsystem_doc_baseline.json. Ratchet 1: undocumented_per_subsystem, actual must equal baseline (fails BOTH ways -- growth is rot, improvement must be locked in). Ratchet 2: modules_with_no_subsystem_doc, may only shrink. Guards on the map: every doc resolves to code, no stale alias, baseline covers exactly the checkable set. Frozen debt: 79 undocumented callables across 7 subsystems + 32 unmapped modules -- visible, not laundered.
```

### Phase 5 Outputs

```
RELEASE_GATES_CAUGHT_TWO: Both caught by CI on the release commit, before any tag existed -- which is the entire argument for L-51 sweep 2. (1) The Quickstart published-MCP probe was a COIN FLIP, not a check: it piped all three JSON-RPC messages and closed stdin, so the server could see EOF and exit before answering tools/list. Green on 1.14.1's release commit, red on 1.14.2's, green again on a bare re-run -- with the published server proven healthy at 67 tools throughout, verified locally by holding stdin open. Fixed to drive the server as a real client does. A flaky release gate is worse than none because it teaches you to re-run red. (2) THREE Windows cells red on a path assertion: `"uv/archive-v0" in serving_path` asserts a SEPARATOR, and Windows renders `uv\archive-v0`. This is L-51 sweep 2 verbatim, down to the cell count -- '0.14.0 shipped with 3 Windows cells red on such an assertion' -- and the lesson was in the surfaced set at the time I wrote it.
RESUME_TO_SHIP_1142: STATE: phases 0-4 complete, all six findings resolved, OPEN FINDINGS = 0 of 27 in the register. Suite 1232 passed / 7 skipped. Version 1.14.2 single-sourced across pyproject, __version__, the top CHANGELOG entry and the refreshed editable dist-info. origin/main == caf96fb. v1.14.2 unclaimed on local tag, remote tag, GitHub Releases and PyPI. Two release-gate defects already fixed in-flight: the flaky published-MCP probe (e4fb082) and the Windows path assertion (f9f8343). TO FINISH, in order and never reordered (L-51 sweep 2): (1) wait for CI on caf96fb -- the docs-only commit that followed the tag candidate -- and require 10/10 at JOB granularity, 9 matrix cells plus fresh-clone, since a workflow-level green hides a failed cell; (2) re-run `clauderize release-check` and require all nine green; (3) tag v1.14.2 on the pushed commit, push the tag; (4) cut the GitHub Release from the 1.14.2 CHANGELOG section (rn text at scratchpad/rn-1142.md) -- publishing fires on release:published via trusted publishing, not on the tag; (5) read the publish job log for IN-BAND upload evidence, since the PyPI index lags and a fresh negative is unproven rather than failed; (6) prove by handshake: hold stdin OPEN (the fire-and-close probe is the bug just fixed) and require serverInfo clauderizer 1.14.2 with 67 tools; (7) NEW for this release -- re-run the H-27 deployment check by restarting a session and confirming cz_status no longer needs `clauderize ops`, i.e. the served build is 1.14.2; (8) write POST-MORTEM.md answering whether a register emptied to zero STAYS at zero; (9) transition phase 5 to complete.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
