# Chat Handoff Index — abstract-index-fast-retrieval

> Last updated: 2026-06-28
> Status: Phase 7 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 663

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
| 0 | Branch, baseline &amp; cost-harness (fixture-first) | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Abstract index builder (data structure, dual parser, invalidation) | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Addressable fetch (cz_get) and abstract surfacing on cz_analyze | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Cost experiment and gain-gate verdict (KEEP/DISCARD) | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Realize the win in injected surfaces (handoff/status) and re-measure | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Write-time lesson-synthesis advisory (own fixture, own mini gain-gate) | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-5-HANDOFF.md |
| 6 | Upgrade path (init/reindex build, doctor detect) and dogfood on an isolated repo copy | ✅ COMPLETE | 2026-06-28 | 2026-06-28 | handoffs/PHASE-6-HANDOFF.md |
| 7 | Release readiness: CI 9-cell, docs sweep, cross-platform, merge-ready | 🟢 READY | — | — | handoffs/PHASE-7-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-25

Stood up the experiment spine fixture-first, before any feature code. Captured the green baseline (626 -> 632 after adding the cost-harness self-tests). Built tests/benchmarks/cost.py: a deterministic token-cost harness (payload via metrics.token_estimate len//4, plus answer-accuracy and round-trips) modeling baseline (load every surfaced body, no addressable getter) vs candidate (compact abstracts + one cz_get per needed body). Pre-registered the KEEP gate in _experiments/PRE-REGISTRATION.md and froze it as cost.py constants (MIN_SAVING=0.30, accuracy non-regression, MAX_ROUND_TRIPS=2). Proved the harness DISCRIMINATES before the feature exists (L-40): on the synthetic 1-of-5 fixture the real mechanism saves 51.3% (KEEP), a no-op control saves 0.0% (DISCARD), and an accuracy trap that saves 69.5% by dropping the answer is vetoed by the accuracy guard (DISCARD) — gap 51.3pp, locked in CI by test_cost.py (6 tests).

A prerequisite blocker was found and fixed first: the dogfood preflight test command was bare `pytest`, not on the MCP server subprocess PATH (exit 127), so no baseline could be captured even though the suite was green via the venv; repointed to `.venv/bin/python -m pytest` (PATH-independent). Commits: c4386b2 (plan), e200f7b (preflight fix), 530b65d (harness). Next: Phase 1 builds the real abstract-index module (dual parser, mtime+hash+schema-version invalidation) — no consumer yet.

### Phase 1 — completed 2026-06-25

Shipped the abstract-index data structure with no consumer wired (Phase 2 wires consumers). src/clauderizer/graph/abstract_index.py mirrors graph/index.py (build/write_cache/load_or_rebuild) and produces a per-entry record {id, title, abstract, anchor, token_set, content_hash, status, kind} over the four corpus files. The dual parser is the load-bearing detail (O-03): em-dash blocks (### ID — title) for DECISIONS/INVARIANTS/HARDENING via analyze._ENTRY_RE, plus a dedicated **L-NN.** line regex for lessons — lesson_state's own matcher is **N.** (the gameplan-handoff form) and would have silently dropped every project lesson; lesson_state is used only for status. Invalidation per D1: corpus-scoped mtime + a schema_version gate + atomic os.replace write; always re-parse on read, skip the write when fresh; a corrupt/BOM/non-UTF8/truncated cache rebuilds rather than raising (L-24).

Open items resolved: O-01 (abstract = capped(title,200); lessons use the line's first sentence as title), O-02 (schema-version gate scoped to the NEW cache; graph/index.py's mtime-only gate left alone — cosmetic under its always-rebuild model), O-03 (dual lesson parser). No consumer references the index (grep-verified: only paths.py defines the cache path). 16 tests, suite 635 -> 651. Commit 961bf6b.

### Phase 2 — completed 2026-06-25

Phase 2 wired the first consumers of the Phase-1 abstract index, turning it from an unused data structure into a working fast-retrieval layer. Added cz_get(id) — an addressable, read-only fetch that returns one corpus entry's full body resolved from canonical markdown on demand (analyze.get_entry looks the id up in the index for its kind+anchor, then re-parses only that one file for the body the index deliberately omits — the D-013 pointer-store design). It works across all four corpora (D-/INVARIANT-/H-/L-). cz_analyze now enriches each ranked decision/invariant hit with a one-line `abstract` so the agent can often answer without a cz_get round-trip. cz_get was added to tools_list.TOOL_NAMES and ops.REGISTRY at the same index, keeping all tool-surface parity/introspection/MCP-registration tests green (38 -> 39 tools).

The key design constraint resolved was the L-34 shared seam: analyze.analyze is also called by the UserPromptSubmit hook on every prompt, and the existing read-only-handler snapshot test (INVARIANT-06) forbids a cache write there. So the abstract is computed via the index's canonical _cap rule on the title already in hand (zero I/O, no index build/write), with a test cross-checking it equals the built index's abstract, plus a new hook-seam integration test proving the hook still surfaces ids and writes no cache. The **L-NN.** lesson grammar was extracted into abstract_index.parse_lesson_line and reused by both the index builder and get_entry (single-sourced matcher). Human-facing tool-count docs were intentionally left for Phase 7 (O-04/L-21). Suite: 651 -> 661 passed (4 skipped), zero regressions.

### Phase 3 — completed 2026-06-25

THE GATE (D2). Wired the live abstract index + analyze.get_entry into the frozen Phase-0 cost harness and measured against the pre-registered thresholds over 105 real corpus entries (1-of-5 lookups; _experiments/run_live_experiment.py). VERDICT: KEEP — 48.3% mean payload-token saving (>= 30%), candidate accuracy 1.00 == baseline 1.00 (no regression), max round-trips 2 <= 2. The KEEP is credible because the controls still discriminate on the LIVE wiring: noop_full 0.0% saving and starve 70.7% saving but accuracy 0.08 — both DISCARD, so the harness kept its power across the synthetic->real swap (L-39/L-40). The 30% threshold was honored exactly, not moved. 48.3% is conservative (keeps the cz_analyze title/abstract redundancy; short-bodied invariants dilute the mean; the baseline is the lenient K-surfaced-bodies, not the real whole-file status quo).

Recorded as decision D5 + output gate_verdict. Phases 4/6/7 PROCEED; next is Phase 4 (realize the win in injected handoff/status surfaces, then re-measure). Suite unchanged at 661 (the experiment is a provenance script, not a new CI test; the synthetic test_cost.py still guards the harness mechanism). Commit 82a8a49.

### Phase 4 — completed 2026-06-25

Phase 4 set out to "realize the win in injected surfaces" by threading abstract+anchor instead of full bodies through the handoff and status digest, then re-measuring. Investigation + empirical measurement (harness.measure_context_tokens on the live repo) found the win was already banked, so the honest deliverable was a measurement + a regression guard rather than a manufactured code change (amendment A-001, per L-32/L-38 and the Phase-3 session's own explicit Phase-4 handoff flag). The numbers: the SessionStart/UserPromptSubmit digest is 315 tokens of counts+pointers (no bodies, D-027 trim); the handoff is 3704 tokens, 58% of which (2132) is lessons-in-full, mandated full by D-009 and already validated at equal accuracy/-55% by the prior empirical-memory-gains focused-injection work. Zero decision/finding bodies are injected anywhere — they are retrieval-only via the Phase-2 cz_get, whose by-id addressing retroactively turned every injected pointer (id+title) into a fetch handle. Converting lessons to abstract+anchor would regress D-009, so there was no valid swap target.

Concrete output: tests/test_injection_pointer_not_body.py (2 tests) locks the D-013 pointers-not-bodies property at the shared injection seam (the L-34 integration point) — proving the invariant injection surface emits id+title not body, and that neither the assembled handoff nor the hook digest injects a decision/finding body (seeded markers absent). This converts the gameplan's central thesis from an implicit property into an enforced one. The realized retrieval win remains the Phase-3 result (48.3% payload saving). Suite 661 -> 663 passed (4 skipped), zero regressions. Phases 5-7 proceed unaffected.

### Phase 5 — completed 2026-06-25

Added the SimpleMem online-synthesis borrow: a write-time near-duplicate-lesson advisory on cz_add_lesson. analyze.near_duplicate_lessons surfaces active project lessons whose distinctive-token Jaccard with the new lesson >= 0.40; mutations.add_lesson attaches related_lessons + advisory (consolidate instead of append), best-effort and NEVER blocking the append-only write (INVARIANT-03/05), no config flag, no new tool (return-only enrichment — the symmetric write-time enrichment add_decision already had).

The discipline WAS the phase (L-40): built the measuring stick FIRST (_experiments/lesson_dedup_measure.py) — a labeled fixture (true dups + 2 adversarial distinct-but-similar near-misses + novel) and a deliberately naive raw-count strawman. The principled Jaccard detector hit precision 1.00 / recall 1.00 AND beat the naive on 2/2 near-misses (naive 2 false-positives, principled 0) — a real length-normalization mechanism, not a no-check tautology. Recorded as D6 (KEEP) + output dedup_advisory; 4 CI tests (tests/test_lesson_dedup.py); suite 663 -> 667. Scoped to cz_add_lesson per the handoff; extending the same detector to cz_promote_lesson (where the standing 25-project-lesson bloat actually grows) is a clean follow-up. Commit e3de440. (Dogfood caveat: the live MCP server runs published 1.1.1, so the advisory is not live in-session until release — proven by tests, not by a live cz_add_lesson.)

### Phase 6 — completed 2026-06-28

Upgrade path shipped (D3). init + reindex build/refresh the abstract index idempotently and gitignore it; doctor detects a missing or schema-stale cache via the new read-only abstract_index.cache_status and advises reindex without ever building it (INVARIANT-06; runtime self-heals). Reconciled with main first (merged 1.2.0 in — clean auto-merge but for the config focus pointer; union suite green). Proven on an isolated tempfile clone (L-29, isolation asserted before any step): doctor-flags-missing -> reindex-builds (107 entries) -> cz_get resolves a real id -> git status clean (corpus+graph byte-unchanged, caches gitignored) -> no-op re-run; friction log recorded. Suite 707->711 (+4). Phase 7 (release readiness/merge-ready, NOT the release) remains.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

**5.** A downstream "realize/exploit the win" phase can be a no-op whose win an earlier phase or prior gameplan already banked — MEASURE before building, and if so, deliver a measurement + a regression guard that LOCKS the property + an honest amendment, never a manufactured change that regresses validated behavior. Phase 4 ("thread abstract+anchor into injected handoff/status surfaces") measured the surfaces and found: the digest is counts+pointers (D-027 trim), the handoff injects no decision/finding bodies at all, and its only full-text payload is lessons — which D-009 mandates stay full and the prior focused-injection eval already cut -55% at equal accuracy. The architectural reason the win was pre-banked is reusable: an addressable getter keyed by id (Phase-2 cz_get(id)) retroactively upgrades EVERY existing id-bearing pointer into a fetch handle, so "injected pointers" already ARE "abstract+anchor" with zero injection-side change. Extends L-32 (park-by-analysis when the metric is saturated by an earlier phase) to the realize-the-win case, and pairs with L-38 (amend honestly, don't fake the checkbox). *(evidence: Phase 4 of 2026-06-25-abstract-index-fast-retrieval: amendment A-001; harness.measure_context_tokens (digest 315 / handoff 3704 / lessons 2132 tok, 0 decision-finding body tokens injected); tests/test_injection_pointer_not_body.py locks D-013; realized retrieval win = Phase-3 48.3%)*

### Category: Integration

**1.** A dogfood self-check that shells out (preflight's test command) must not depend on the ambient PATH. The MCP server spawns the test command WITHOUT an activated venv, so bare `pytest` exits 127 and preflight cannot capture a baseline even though the suite is green via `.venv/bin/python -m pytest`. Point profile.lock.toml's test command at the venv interpreter explicitly so preflight is robust across launch contexts. Note the shipped python profile template (src/clauderizer/profiles/python.toml) ships `test = "pytest -q"`, carrying the same latent fragility for any MCP-only python host — a candidate engine fix (prefer `python -m pytest`, or venv-detect). Sibling of L-23: the author's environment never exercises the real surface. *(evidence: .clauderizer/profile.lock.toml (e200f7b); cz_preflight exit 127 -> green 632 after the fix; src/clauderizer/profiles/python.toml:8)*

**2.** A shared "is this an entry" matcher may not cover every entry FORMAT in a corpus — verify each format actually matches, or entries silently drop with no error. docs/LESSONS.md uses **L-NN.** but markdown/lesson_state.LESSON_LINE_RE is **N.** (the gameplan-handoff lesson form); reusing it for project lessons would have indexed ZERO of them silently. The corpus carries three grammars: em-dash blocks (### ID — title) for decisions/invariants/findings, project lessons (**L-NN.**), and gameplan lessons (**N.**). When a consumer spans the corpus, enumerate every format and assert each is matched (sibling of L-33 verify-at-point-of-edit; a silent drop is the L-24 degradation face). *(evidence: src/clauderizer/graph/abstract_index.py _LESSON_LINE_RE vs markdown/lesson_state.py:22; tests/test_abstract_index.py::test_lessons_use_the_L_NN_format_not_the_gameplan_N_form)*

**3.** An enrichment added to a function a hook reaches must be COMPUTED in-memory, never materialized through a cache-writing helper. analyze.analyze is shared by the UserPromptSubmit hook; routing the new cz_analyze abstract through abstract_index.load_or_rebuild would have written the disposable cache from inside the hook and tripped test_every_event_handler_is_read_only (which snapshots every file except index.json/write.lock) — an INVARIANT-06 breach that a writes=False flag does NOT catch (the flag governs the write lock, not cache file creation). Use build() (in-memory) or a pure derivation (here abstract_index._cap on the title in hand) on any hook-reachable read path; reserve load_or_rebuild for non-hook ops like cz_get. Sibling of L-34: the phase that ADDS a field must check every existing caller of the shared function, and the hook caller is the dangerous one because its read-only contract is enforced by a snapshot test, not a type. *(evidence: src/clauderizer/analyze.py analyze() abstract enrichment uses abstract_index._cap not load_or_rebuild; guarded by tests/test_hook_dispatch.py::test_user_prompt_submit_real_analyze_surfaces_and_stays_read_only; the read-only snapshot tests/test_hook_dispatch.py::test_every_event_handler_is_read_only skips only index.json/write.lock)*

### Category: Eval methodology

**4.** When an experiment swaps a SYNTHETIC fixture for LIVE data, re-run the negative controls ON the live data — discriminating power is a property of the fixture AND the wiring together, not the design phase alone. A harness proven to discriminate on a synthetic fixture could saturate (or invert) on the real corpus, making a KEEP an artifact. Carry the controls across the swap. Phase 3 re-ran noop_full (0.0% saving) and starve (70.7% saving but accuracy 0.08) on the 105-entry real corpus and confirmed both still DISCARD, so the 48.3% KEEP is a real measured win, not a saturated-live-fixture artifact. Extends L-39/L-40 (build the adversarial fixture + the strawman it must defeat FIRST) to the synthetic->live transition. *(evidence: docs/gameplans/2026-06-25-abstract-index-fast-retrieval/_experiments/run_live_experiment.py (controls evaluated on the live lookups) + RESULTS-live.txt; verdict KEEP exit 0)*

### Category: Design

**6.** For near-DUPLICATE detection, length-normalize the overlap (Jaccard = |A intersect B| / |A union B|) — do NOT use the raw token-overlap COUNT (the relevance-ranking signal). A long distinct-but-similar entry shares many tokens by sheer size, so it trips a count threshold (false positive) while its Jaccard stays low. This is the concrete principled-vs-naive contrast for a dup detector and the exact L-40 discriminator: raw count is the strawman, length-normalization is the real mechanism. Same _tokens as the relevance ranker, different normalization for a different question (is it RELEVANT vs is it the SAME). Measured Phase 5: Jaccard@0.40 precision 1.0 / recall 1.0 with 0 false-positives on 2 adversarial near-misses the naive count false-positived. *(evidence: src/clauderizer/analyze.py near_duplicate_lessons; docs/gameplans/2026-06-25-abstract-index-fast-retrieval/_experiments/lesson_dedup_measure.py; tests/test_lesson_dedup.py)*
