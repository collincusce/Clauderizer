# abstract-index-fast-retrieval — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-28

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Branch, baseline &amp; cost-harness (fixture-first) | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Abstract index builder (data structure, dual parser, invalidation) | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Addressable fetch (cz_get) and abstract surfacing on cz_analyze | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Cost experiment and gain-gate verdict (KEEP/DISCARD) | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Realize the win in injected surfaces (handoff/status) and re-measure | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Write-time lesson-synthesis advisory (own fixture, own mini gain-gate) | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-5-HANDOFF.md |
| 6 | Upgrade path (init/reindex build, doctor detect) and dogfood on an isolated repo copy | ✅ COMPLETE | 2026-06-28 | 2026-06-28 | handoffs/PHASE-6-HANDOFF.md |
| 7 | Release readiness: CI 9-cell, docs sweep, cross-platform, merge-ready | 🟢 READY | — | — | handoffs/PHASE-7-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
baseline_tests: 632 passed, 4 skipped (green via .venv/bin/python -m pytest). Was 626 before this phase added 6 cost-harness tests. 632 is the new green baseline for all later phases.
cost_harness: tests/benchmarks/cost.py — measure_baseline / measure_candidate / evaluate / verdict; token proxy reuses metrics.token_estimate (len//4), no live LLM. Strategies: abstract_then_fetch (real) + noop_full + starve (controls). Phase 3 wires the real abstract index + cz_get into evaluate().
gain_gate_thresholds: Pre-registered in docs/gameplans/2026-06-25-abstract-index-fast-retrieval/_experiments/PRE-REGISTRATION.md and frozen as cost.py constants: MIN_SAVING=0.30, accuracy non-regression, MAX_ROUND_TRIPS=2. KEEP iff all three hold; else DISCARD (L-32).
discrimination_demo: real mechanism 51.3% saving -> KEEP; noop control 0.0% -> DISCARD; starve trap 69.5% saving but accuracy 0.00 -> DISCARD (accuracy guard vetoes). Gap 51.3pp. CI-locked in tests/benchmarks/test_cost.py (6 tests). Run via _experiments/run_cost_harness.py; provenance in _experiments/RESULTS.txt.
```

### Phase 1 Outputs

```
abstract_index_module: src/clauderizer/graph/abstract_index.py — build(paths) / write_cache(index, cache_file) / load_or_rebuild(paths). Per-entry record: {id, title, abstract, anchor (docs/FILE.md:line), token_set (sorted analyze._tokens), content_hash (sha256 title+\n+body), status, kind}. Returns a plain dict {schema_version, corpus_mtime, entries:{id->record}}. SCHEMA_VERSION=1, ABSTRACT_CAP=200.
cache_path: .clauderizer/abstract_index.json (gitignored sibling of index.json; paths.abstract_index_file). Atomic write (.tmp then os.replace), refuse_if_symlink. load_or_rebuild always re-parses and only skips the WRITE when schema_version AND corpus_mtime both match.
parsers: DUAL. Em-dash blocks (### ID — title) for DECISIONS(## Decisions)/INVARIANTS(## Invariants)/HARDENING(## Risks) via analyze._ENTRY_RE. Lessons (## Lessons) via _LESSON_LINE_RE = ^**(L-\d+).** — NOT lesson_state.LESSON_LINE_RE (that is **N.**, the gameplan form, and would drop every L-NN). Status: decisions/findings via **Status**: / - **Status**: regex; lessons via lesson_state.parse_state (active/obsolete/promoted).
baseline_tests: 651 passed, 4 skipped (was 635 at Phase 0; +16 tests in tests/test_abstract_index.py). New green baseline for Phase 2.
```

### Phase 2 Outputs

```
cz_get_op: src/clauderizer/ops.py cz_get(id, kind="auto") -> {ok, id, title, body, status, anchor, kind}; ok=False + error when the id is unknown. Op(cz_get, writes=False), read-only (no write lock, L-03). Registered at index 3 in BOTH tools_list.TOOL_NAMES and ops.REGISTRY (right after cz_graph_query) — order parity asserted by test_registry_is_exactly_the_tool_surface + skill-discovery parity; MCP auto-registers it (server iterates REGISTRY). Tool surface 38 -> 39.
get_entry_fn: analyze.get_entry(paths, entry_id, kind="auto") -> {id,title,body,status,anchor,kind} | None, plus helper analyze._entry_body. Resolution: abstract_index.load_or_rebuild(paths) gives the record's kind+anchor+title+status (the index's status parser handles every corpus form, e.g. the `- **Status**` hardening form); the body the index omits (D-013 pointer store) is re-read from the ONE corpus file named by abstract_index._DOC_SECTION_BY_KIND[kind] — parse_entries for em-dash kinds, abstract_index.parse_lesson_line for lessons. A non-auto kind that disagrees with the id is treated as a miss (->None). Read-only (may refresh the disposable cache, never markdown/the write lock).
cz_analyze_abstract: analyze.analyze now attaches `abstract` to each ranked decision/invariant hit, computed as abstract_index._cap(hit["title"]) — NOT by building the index. Rationale (load-bearing for Phase 4): analyze.analyze is the shared path the UserPromptSubmit hook calls every prompt (hook/handlers.py:138, k=3); using load_or_rebuild there would write abstract_index.json and fail test_every_event_handler_is_read_only (snapshots all files except index.json/write.lock) — breaching INVARIANT-06. cz_analyze ranks only em-dash entries whose abstract IS the capped title, so _cap on the title-in-hand is exactly the index's abstract (test_analyze_hits_carry_abstract_equal_to_the_index cross-checks vs A.build) with zero I/O. cz_analyze docstring updated to note hits carry `abstract` + point to cz_get for the body.
abstract_index_helpers: Two additions to graph/abstract_index.py for the cz_get read path: (1) parse_lesson_line(line) -> (id, title, body) | None — extracted from _lesson_records (behavior-preserving refactor; _lesson_records now calls it) so the **L-NN.** lesson grammar is single-sourced between the index builder and get_entry (the L-2 single-source-the-matcher rule). (2) _DOC_SECTION_BY_KIND: kind -> (doc, section), derived from _EMDASH_CORPUS + ("lesson"->("LESSONS","Lessons")), so it can never drift from what build() indexes. Both covered by new tests in test_abstract_index.py.
baseline_tests: 661 passed, 4 skipped (665 collected) via .venv/bin/python -m pytest — was 651 at Phase 1; +10 Phase-2 tests (test_analyze.py +6: abstract enrichment ×2, get_entry four-corpora/unknown/kind-hint ×3, cz_get op ×1; test_abstract_index.py +3: parse_lesson_line, record/parse equivalence, _DOC_SECTION_BY_KIND; test_hook_dispatch.py +1: L-34 read-only seam). 661 is the new green baseline for Phase 3. NOTE: this host's pytest reporter prints no summary line when piped — use --junitxml to read counts; exit code is authoritative.
tool_surface_docs_deferred: DEFERRED to Phase 7 per L-21 / O-04 (don't sweep human-doc counts mid-feature): bump the README "N tools" line and docs/subsystems/mcp-server.md "reads" count 38 -> 39 (cz_get), and update the subsys.mcp-server entity. No tracked-entity status change was made this phase (additive new tool only; entity/doc updates are Phase 7's job), so no cascade was required.
```

### Phase 3 Outputs

```
gate_verdict: KEEP. Live experiment on 105 real corpus entries (1-of-5 lookups): mean payload-token saving 48.3% (>=30% threshold); accuracy delta 0.00 (candidate 1.00 == baseline 1.00); round-trip delta 0 (candidate 2.0 == baseline 2.0, max_rt 2 <= 2). Controls on live wiring: noop 0.0% saving (DISCARD), starve 70.7% saving but accuracy 0.08 (DISCARD) — harness retains discriminating power (L-39/L-40). Reproduce: .venv/bin/python docs/gameplans/2026-06-25-abstract-index-fast-retrieval/_experiments/run_live_experiment.py (exit 0=KEEP). Phases 4/6/7 PROCEED.
```

### Phase 4 Outputs

```
injection_measurement: Measured via harness.measure_context_tokens on the live repo: digest_tokens=315 (counts+pointers only, no bodies — D-027 trim), handoff_tokens=3704, of which lessons=2132 (58%, full text mandated by D-009), lesson_lines=9. ZERO decision/finding body tokens injected in either surface (decisions/findings are retrieval-only via cz_get). The handoff's non-lesson ~42% is the phase definition + invariant POINTERS (id+title) + lesson pointers + skill menu + scaffolding — necessary context/pointers, not convertible bodies.
realized_delta: Injection-side realized token delta = ~0 from a Phase-4 change, because the win was ALREADY banked: (a) the empirical-memory-gains focused-injection cut handoff lessons -55%/-73% at validated equal agent-eval accuracy, and (b) Phase-2 cz_get-by-id retroactively made every injected pointer (id+title) an addressable handle — the agent fetches any surfaced entry's body on demand. The body-fetch win is the Phase-3 retrieval measurement (48.3% payload saving). No injected surface was re-shaped, so agent-eval accuracy is unchanged by construction. See amendment A-001.
regression_guard: tests/test_injection_pointer_not_body.py (2 tests, the L-34 shared-injection-seam guard): (1) relevant_invariant_pointer emits id+title (a cz_get-addressable pointer), never the body; (2) end-to-end — the assembled handoff AND the hook digest carry no decision/finding body (unique body markers seeded via add_decision/add_finding are absent). Locks the D-013 pointers-not-bodies property so a future "enrichment" can't silently start injecting full bodies. baseline_tests: 661 -> 663 passed (4 skipped); new green baseline for Phase 5.
```

### Phase 5 Outputs

```
dedup_advisory: analyze.near_duplicate_lessons(paths, text, threshold=0.40, k=3) -> [{id,title,jaccard}] active project lessons (abstract index kind=lesson) whose distinctive-token Jaccard with text >= 0.40. Wired into mutations.add_lesson: result gains related_lessons + advisory when dups found; best-effort try/except, never blocks (INVARIANT-03/05). cz_add_lesson docstring updated. NO tool-surface change (return-only enrichment). Uses abstract_index.build (in-memory, no cache write) so it is safe inside the @_locked add_lesson.
```

### Phase 6 Outputs

```
upgrade_path: init (scaffold/init.py) + reindex (cli.cmd_reindex) now BUILD the abstract index via abstract_index.build/write_cache, and ensure .clauderizer/abstract_index.json in .gitignore; doctor (cli.cmd_doctor) calls the new read-only abstract_index.cache_status(paths) -> flags missing/schema-stale with 'run clauderize reindex' advice, never builds it (INVARIANT-06). 4 tests in tests/test_abstract_index_upgrade.py. Suite 707->711.
isolated_dogfood: Isolated-clone dogfood PASSED (git clone of this repo to a tempdir; isolation asserted BEFORE any step, L-29): a clone naturally lacks the gitignored cache = pre-upgrade state; doctor flagged '✗ abstract index fresh — missing — run clauderize reindex' (read-only, did not build); reindex built 107 entries; git status CLEAN afterward (corpus+graph byte-unchanged, caches gitignored) + HEAD unchanged; cz_get D-001 resolved 'Markdown is the source of truth' (retrieval-uses-abstracts); a second reindex was byte-identical (no-op); live repo untouched.
friction_log: Phase-6 friction log (deliverable): (1) Overall smooth — wiring init/reindex/doctor mirrored the existing graph-index pattern exactly; the abstract_index builder/invalidation from Phase 1 already exposed build/write_cache/load_or_rebuild so the upgrade path was pure wiring. (2) Reconciliation: this branch was 8 behind main (1.2.0 shipped meanwhile); merging main in auto-merged cleanly except .clauderizer/config.toml (the focus pointer) — the two feature sets (cz_get vs cz_focus/cz_gameplans/cz_consumes) are orthogonal in code; union suite 707 green with no manual code fixes. (3) Minor design note: doctor exits 2 (drift) for a missing abstract index on every not-yet-reindexed upgraded repo — a loud signal for a self-healing cache, but intended as the one-time upgrade nudge and softened by explicit 'run clauderize reindex' advice; consistent with the existing index-cache check. No tooling blockers.
```

## Corrections Log

### C-01 — Phase 0

**Phase**: 0
**What gameplan said**: D4 point (2) prescribes merging main->feature at EVERY phase close-out to keep the branch a clean fast-forward.
**What was actually correct**: Sync main->feature only at final close-out (or if/when main actually advances) — NOT per phase. O-04's final merge-back checklist covers it.
**Why**: User feedback: "that's a bit much, just do it on closeout not each phase... I'm only working on one feature right now." With no competing branches landing on main, the fast-forward invariant holds without per-phase merges, so they are pure overhead.

### C-02 — Phase 2

**Phase**: 2
**What gameplan said**: Enrich cz_analyze hits with "the entry's abstract from the index" — Phase Notes specced enriching in analyze.analyze sourced from the abstract index (abstract_index.load_or_rebuild).
**What was actually correct**: Enriched in analyze.analyze as specced, but compute the abstract as abstract_index._cap(hit["title"]) — the index's own cap rule applied to the title already in hand — without building or writing the index.
**Why**: analyze.analyze is the shared path the UserPromptSubmit hook calls every prompt; load_or_rebuild would write abstract_index.json and fail test_every_event_handler_is_read_only (INVARIANT-06: read-only handlers). cz_analyze ranks only em-dash entries whose abstract == _cap(title), so the value is byte-identical (a test cross-checks it vs A.build) with zero I/O — honoring the plan's intent (hits carry the entry's abstract) under its own stated read-only+fast constraint. cz_get (not on a hook path) does use load_or_rebuild as specced.
