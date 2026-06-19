# Chat Handoff Index — headroom-borrowed-ideas

> Last updated: 2026-06-19
> Status: All 5 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 352

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
| 0 | Baseline & methodology | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Idea 1 — Prefix-stability (CacheAligner analog) | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Idea 2 — Relevance-ranked handoff (IntelligentContext analog) | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Idea 3 — Failure-miner (headroom learn analog) | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Consolidate survivors & close | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-19

Established the experimental frame. Confirmed a green baseline of 305 tests (pre-flight corrected the stale digest figure of 300→305). Recorded the keep/discard methodology (D1) — each borrowed idea is a falsifiable hypothesis with a machine-checkable metric — plus the two shape-constraining decisions: idea #2 is reorder-not-drop (D2, respecting D-009 + the incomplete-propagation anti-pattern in handoff.py) and idea #3 is an invoked, read-only, advisory tool rather than a gate or config flag (D3, respecting D-015/INVARIANT-05). Vetted all three against recorded memory via cz_analyze — no contradictions; the ideas deliberately align with D-013/D-014/D-018 (deterministic, no ML/embeddings). Filed O-01..O-03 for the known unknowns (cache-prefix observability from inside the engine, the miner precision bar, transcript-schema drift). Phases 1–4 are laid out cheapest→most-expensive, each with machine-checkable exit criteria.

### Phase 1 — completed 2026-06-19

Tested the CacheAligner analog by measuring the longest common leading byte-prefix (a deterministic proxy for provider KV-cache hits) of the SessionStart digest across two volatile states. The stable-first reorder works by the proxy (65→786 chars, 7.3%→78.9%) but the whole digest is only ~888 chars (~222 tok), it is rendered once per session (already inside the session's cached growing prefix regardless of order), cross-session benefit is unobservable (O-01) and dominated by the preceding system prompt, and the reorder regresses readability by burying actionable state under boilerplate. DISCARD (D-020, project scope). No engine change made; the harness is kept under _experiments/ as provenance. Handoff ordering deferred to idea #2 (relevance, not caching).

### Phase 2 — completed 2026-06-19

Implemented idea #2a: handoff.assemble now prepends a 'Most Relevant Lessons for This Phase' block — top-k pointers ranked by analyze.rank_relevant (keyword + entity-id overlap, no ML, D-018) keyed on the phase's breakdown block (reusing status_bundle.phase_block) — ABOVE the unchanged cumulative list, and only when active lessons exceed k=5. Pointer-not-authority (D-013); zero drops (D-009 + the incomplete-propagation anti-pattern). 7 new tests (tests/test_handoff_relevance.py) prove relevance ordering, two phases reorder differently, all lessons survive (count-in==count-out), obsolete excluded, pointer absent when <=k/no-query, and the real assembler inserts the block. Suite 312 passed, 4 skipped. KEEP 2a (D-021). DISCARD 2b (D-022) — truncating the tail reintroduces incomplete-propagation for marginal savings; cz_consolidate_lessons is the safe size lever. subsys.rituals version bump + cascade deferred to Phase 4.

### Phase 3 — completed 2026-06-19

Built src/clauderizer/learn.py — a deterministic, stdlib-only failure-miner scanning Claude Code transcript JSONL for (A) tool error→same-tool success, (B) pytest fail→pass, (C) short explicit user corrections — emitting draft cz_add_correction args (propose-only; no flag; no auto-fire). Key finding: is_error is unreliable for shell failures, so errors are detected by content signatures; benign search-tool errors and tool-protocol hiccups are denied to protect precision. Across 11 real project transcripts: 62 proposals (~6/session), ~80% precision on a 20-proposal labeled sample, 2/2 on this session's dogfood (gh-not-found→curl; git-UNC→wsl.exe), and it rediscovers real adopted lessons (H-08 shim, env/test failures). Detector C had 0 recall here (kept for precision). 8 fixture tests; suite 320 passed, 4 skipped. KEEP (D-023). Phase 4 wires the cz_mine_failures MCP tool + version bumps + cascade.

### Phase 4 — completed 2026-06-19

Productionized the survivors and closed out. Idea #2a (handoff relevance pointer) and idea #3 (cz_mine_failures, wired into the shared ops registry as a read-only, propose-only tool) shipped with tests. Recorded all four verdicts: D-020 (discard #1), D-021 (keep #2a), D-022 (discard #2b), D-023 (keep #3). Bumped subsys.rituals 0.6.0→0.7.0 and subsys.mcp-server 0.4.1→0.5.0; cz_cascade walked the one dependent (mcp-server) and cz_resolve_cascade recorded 'no change' (additive). Updated CHANGELOG ([Unreleased]); ran cz_critique (clean on Coherence/Grounding; Coverage gaps were this phase's own criteria); promoted the methodology lesson to L-17; wrote POST-MORTEM.md. Final suite: 322 passed, 4 skipped; registry/tool-name parity holds (31 tools).

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** Test a borrowed idea as a falsifiable hypothesis with a pre-named, machine-checkable keep/discard metric, and MEASURE before shipping. Idea #1's digest reorder "worked" by its prefix-stability proxy (65→786 chars) yet was discarded because the payload was only ~222 tokens and rendered once per session — measurement turned a plausible win into an evidence-based no. A discard is a successful outcome, not a failure; the deliverable is the verdicts plus the survivors. *(evidence: D-020 / D-021 / D-022 / D-023; docs/gameplans/2026-06-19-headroom-borrowed-ideas/_experiments/measure_prefix.py)* (promoted 2026-06-19: L-17)

**2.** A 'degrades gracefully' claim is only as strong as the input diversity it was tested against: exercise non-dict valid JSON, BOM/CRLF, unicode, and empty input before resolving a schema-tolerance item. Adversarial input tests belong in the same phase that makes the robustness claim. (promoted 2026-06-19: L-18)

**3.** Schema-drift tolerance must wrap the WHOLE pipeline, not just json.loads. learn.py crashed through cz_mine_failures on real-transcript shapes the parse try/except never saw: non-UTF-8 bytes (UnicodeDecodeError raised at decode, before json.loads), an unhashable tool_use_id used as a dict key, and a non-str `text` str-joined. Guard at the boundary (open(..., errors="replace"), isinstance checks) AND net per-file in the batch loop. Corollary: precision-over-recall count regexes must exclude zero ([1-9]\d*, not \d+) so a clean "0 failed" run isn't mined as a failure. *(evidence: src/clauderizer/learn.py; post-close diverse verification 2026-06-19; locks in tests/test_diverse_robustness.py (5 crash-vector tests) + tests/test_failure_miner.py::test_zero_failed_count_is_not_an_error; measured 68→65 real-corpus proposals after the regex fix)* (promoted 2026-06-19: L-19)
