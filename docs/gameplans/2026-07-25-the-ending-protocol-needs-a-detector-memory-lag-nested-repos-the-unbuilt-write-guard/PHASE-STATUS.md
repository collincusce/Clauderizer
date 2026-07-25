# the ending protocol needs a detector — memory lag, nested repos, the unbuilt write guard — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-25

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Memory-lag detection so a session cannot silently drift from the repo | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Nested clauderized repos stop contradicting each other | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Build the write guard 1.14.0 specified and did not ship | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Close the graph drop gap and the init spawn-test carried from 1.14.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Close out and ship 1.14.1 | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
DETECTOR: src/clauderizer/rituals/memory_lag.py — public API: tracker_anchor(paths, gid) -> (short_sha, iso_date) | None; work_commits_since(paths, anchor) -> int (-1 = git could not answer); detect(paths, gid, target, status) -> lag dict | None; describe(lag) -> the single shared sentence. Wired at status_bundle.compute (bundle["memory_lag"]), status_bundle.render_digest ("⚠ Memory lag: " line), preflight.run (check_memory_lag, appended only when lag exists).
SUITE: 1074 -> 1085 passed, 7 skipped (+11, all in tests/test_memory_lag.py)
RED_BEFORE_GREEN_HARNESS: git clone --local --no-checkout <repo> <tmp> then checkout --detach efdf210 (an isolated CLONE, not a worktree — nothing writes the real .git, so the isolation is structural per L-29), run with PYTHONPATH=<tmp>/src. Reuse for every remaining 1.14.1 phase. Measured RED on efdf210 for Phase 0: bundle["memory_lag"]=None, "Memory lag" in digest=False, preflight memory_lag check=None, verdict "preflight PASS" — against a fixture whose tracker read NOT STARTED with a src/ commit past it. Post-fix on the same fixture: lag={'phase':'1','commits':1,'anchor':'b324de5'}, line present, check ('memory_lag','warn'), verdict "PASS WITH WARNINGS".
HISTORICAL_CHECK: The 1.14.0 drift window, measured: anchor 54290e2 "close(P4)" 2026-07-25 04:01:34 was the last tracker write, leaving phases 5 and 6 NOT STARTED; the tracker was not touched again until ef196aa 15:25:31 — 11h24m later. Non-docs commits in that window: 1 at eac1c9a (the criterion-7 commit; touches src/hosttargets.py, modernize.py, ops.py, scaffold/init.py, tests/), rising to 4 by f42f73d, and 8 total between the anchor and efdf210. tests/test_memory_lag.py::test_historical_1_14_0_drift_would_have_fired parses the phase state FROM the tracker as it stood at eac1c9a (nothing hand-fed) and asserts the detector fires.
LIVE_DOGFOOD: In-band evidence (L-07): after committing 61317f5 with this gameplan's phase 0 still reading READY, `clauderize status` on this repo emitted — ⚠ Memory lag: phase 0 "Memory-lag detection so a session cannot silently drift from the repo" still reads ready, but 1 non-docs commit landed since the tracker was last written (efdf210, 2026-07-25). The detector caught its own author.
```

### Phase 1 Outputs

```
OWNERSHIP_MODULE: src/clauderizer/nesting.py — is_clauderized(d); owner_of(cwd) -> nearest clauderized ancestor | None; outranked_by(anchored_root, session_cwd) -> the nested owner that should speak instead | None; nested_installs(root, max_depth=4) -> descendants, pruned (does not descend into a found install, skips dot/vendor dirs, ~0.24s on a real home dir); clauderized_ancestors(root); describe_nested / describe_ancestors. Wired at hook/handlers.repo_paths_config(payload) — threaded through session_start, pre_compact, post_compact and user_prompt_submit — plus cli.cmd_doctor and scaffold.init.
SUITE: 1085 -> 1101 passed, 7 skipped (+16, all in tests/test_nested_installs.py)
LIVE_NESTED_SCAN: /home/ccusce holds TEN nested clauderized installs, found in 0.24s: Clauderizer, arena-security-audit, clauderizer-site, cz-dogfood-pet, cz-dogfood-saas, cz-dogfood-standard, cz-hosttest, marketing-studio, phasekeep, viderizer. Every one of them was being narrated over by the outer install, because /home/ccusce/.claude/settings.json IS the per-user settings file — initializing Clauderizer in $HOME makes its hook global to every session on the machine. That is the root cause behind H-23 and it is worth stating plainly: the outer install is not merely "an ancestor", it is wired globally.
DEPLOYMENT_GAP: /home/ccusce/.clauderizer/hook.sh runs `uvx -q --from clauderizer clauderizer-hook` — the PUBLISHED engine, currently 1.14.0. The nesting fix therefore does NOT reach the outer install until 1.14.1 is on PyPI and uvx's cache refreshes. Phase 4 must re-run the live two-digest check AFTER publish (`uvx --refresh`) to confirm the repair actually lands where the pathology lives; until then the live green is for the mechanism, not the deployment.
```

### Phase 2 Outputs

```
WRITE_GUARD: src/clauderizer/mutations.py::_strip_toolcall_markup, applied inside _safe_body and _one_line — the D-066 render boundary every cz_* write already flows through. Two signals: (1) _TOOLCALL_TAG_RE matches the vocabulary parameter|invoke|function_calls|function_results, bare or antml:-prefixed, opening or closing; (2) an UNBALANCED closing tag, i.e. _CLOSE_TAG_RE match whose name has no _OPEN_TAG_RE opener in the visible value. _code_segments skips fenced blocks and inline code (read-side parity with sections._without_code_spans). Fast path returns unchanged when the value has no "<".
SUITE: 1101 -> 1127 passed, 7 skipped (+26, all in tests/test_toolcall_write_guard.py)
RED_EVIDENCE: Substantive RED at efdf210: cz_add_decision fed the exact live shapes wrote them straight to docs/DECISIONS.md — "**Context**: User confusion, this session.</context>" followed by "<parameter name=\"context\">User confusion (real, this session)." — byte-for-byte the corruption at docs/DECISIONS.md:381-382. Same probe on the fixed tree: all three markers neutralized, every word of prose preserved. Acceptance corpus is read OFF DISK (not synthesized): tests parse D-052/D-062/H-19/H-23 out of the live registers, assert the stray tag is still present (a guard against retro-editing), then assert the guard cleans it.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
