# Chat Handoff Index — Empirical memory gains

> Last updated: 2026-06-20
> Status: All 8 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 446

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
| 0 | Eval harness and baseline capture | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Context-rot trims (evidence-gated removal) | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-1-HANDOFF.md |
| 2 | DAG integrity validation | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Edge-suggester (missing-edge surfacing) | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Decision supersession back-refs and lifecycle | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Bitemporal valid-time (must-earn) | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-5-HANDOFF.md |
| 6 | Persistent steering doc (must-earn) | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-6-HANDOFF.md |
| 7 | Close-out: consolidate, measure, post-mortem | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-7-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-20

Built tests/benchmarks/ - a deterministic, stdlib-only memory-eval harness (LongMemEval 5-ability taxonomy + 3-stage ablation): metrics (recall@k, precision, nDCG, MRR, contradiction, abstention, token-estimate len//4, dangling/cycle DAG primitives), an in-memory ranker corpus + repo-seeding fixtures, and a focused-vs-full agent-eval scaffolder. 11 new tests; suite 400->410 green. The load-bearing self-test proves the harness detects a degraded ranker (MRR 0.46 vs 1.0). Captured the real baseline: digest 263 tok, handoff 3137 tok of which 2737 (87%) are the 21 project lessons (Phase 1 trim target); ranker recall@3/MRR/nDCG=1.0; supersession contradiction=1.0 (Phase 4 target 0). Fixed the stale 0-tests baseline -> 410. Methodology: tests/benchmarks/README.md; baseline: _experiments/measure_baseline.py.

### Phase 1 — completed 2026-06-20

Trimmed the biggest context cost: the cumulative handoff carried all 21 project lessons in full (2737 tok = 87% of a 3137-tok handoff). 3-stage ablation proved the fix safe: retrieval recall@5=100% (the answer lesson is always rank-1 in the focused set), and a focused-vs-full agent-eval tied at 5/6 each. Shipped focused_project_lessons in handoff.py: when project lessons exceed k, the handoff carries the top-k ranked-to-phase (most-relevant first) + a pointer to canonical LESSONS.md; <= k rides full. Result: handoff 3137->1420 tok (-55%) at equal accuracy. Reconciles D-022 (relevance-focus + pointer-to-canonical, not truncation). 4 new tests; suite 415 green. Honest scope: a tie not a win - the gain is token-cost; active length-harm is a larger-scale effect.

### Phase 2 — completed 2026-06-20

Added src/clauderizer/graph/validate.py: deterministic dangling-edge + cycle (iterative Tarjan SCC) detection over the project DAG, surfaced advisorily through the existing status drift channel (never blocks; INVARIANT-05/06). Filled a real gap - query.pin_violations skips edges with unknown targets, so dangling depends_on edges were silently undetected. 12 new tests (100% detection on seeded dangling+cycle fixtures, zero false positives on valid DAGs); suite 415->427 green. Independently re-verified by the orchestrator (tests + code review).

### Phase 3 — completed 2026-06-20

Edge-suggester KEPT (precision 0.75 >= 0.70 bar, recall 1.0). analyze.suggest_edges proposes MISSING depends_on edges from distinctive-token overlap - the complement of D-018's existing-edge walk - surfaced advisorily via cz_analyze.suggested_edges (no new tool, parity green), never auto-writing. Rejected pairs persist as not_related_to frontmatter (symmetric, round-trips). The precision gate did its job: a naive id+type signal scored 0.103 (every entity shares subsys/subsystem), so the impl strips structural boilerplate; the fixture was then hardened with a generic-collision false positive to land an honest 0.75. +11 tests; suite 438 green. Orchestrator hardened the fixture and re-verified the number.

### Phase 4 — completed 2026-06-20

Decision supersession lifecycle: add_decision(supersedes=X) writes a bidirectional 'Superseded by' back-ref on X and flips X's Status to superseded (idempotent, append-only - X is annotated, never deleted), and stamps the new decision Status: active + date. analyze.rank_relevant demotes superseded/deprecated decisions below active peers of equal lexical score via a stable secondary sort key (the relevance score itself is untouched; the stale entry still surfaces, annotated, preserving the audit trail). GATE MET: the Phase 0 harness supersession contradiction_rate fell 1.0 -> 0.0, measured by the UNCHANGED corpora/harness (orchestrator confirmed via git diff that only the baseline-witness test flipped; the measurement core was not touched). +6 tests; suite 438->444 green.

### Phase 5 — completed 2026-06-20

PARKED (evidence-based, no code). Bitemporal valid-time was a must-earn candidate; its gate was to beat Phase 4 on contradiction-rate or as-of correctness. Phase 4 already drove contradiction to 0.0 (the floor - unbeatable), valid-time != transaction-time does not arise in project-scoped decision memory (decisions are effective when made), and as-of/time-travel queries have no demonstrated agent need while their always-present fields would add injected context against D-027 (trim-first). Building a speculative schema to measure zero marginal gain was correctly declined. Per D2, a disciplined park is a successful must-earn outcome. Two keep-path exit criteria (schema/as-of implemented) are intentionally left unchecked - this phase resolved via the park branch.

### Phase 6 — completed 2026-06-20

DROP the always-injected steering/constitution doc (redundant with auto-loaded CLAUDE.md + INVARIANTS.md + the analyze gate; anti-trim D-027; the research evidence was weakest - Kiro's gated steering was refuted, only the always-loaded anti-pattern survived). KEPT the trim-consistent adaptation that fills the real gap underneath: handoff.relevant_invariant_pointer surfaces the top-k phase-relevant INVARIANTS (focused, never an always-all dump, injects nothing when none are relevant). Invariants were never surfaced during phase work before this. Honest scope: the kept feature passes a deterministic CAPABILITY gate (surfaces relevant / skips irrelevant - tested) and its reading-stage benefit is inherited from Phase 1's focused-surfacing result; a dedicated invariant-adherence agent-eval was not run and is recorded as an open item. Two keep-path criteria (build the doc / run the adherence ablation) left intentionally unchecked - resolved via the drop-the-doc branch.

### Phase 7 — completed 2026-06-20

Close-out. Wrote POST-MORTEM.md with the measured per-feature gains table (4 KEEP, 1 PARK, 1 split), what worked (the gain-gate caught the edge-suggester's 0.103 over-retrieval noise; the harness self-test caught recall@k>=N; dogfooding surfaced D-020/021/022 + L-17 that pre-shaped Phase 1), honest caveats (Phase 1 was a Pareto/token win not an accuracy win; Phase 6 adherence inherited not freshly measured; edge precision fixture-measured), and procedure improvements (tests/benchmarks/ is a reusable asset; evaluate must-earn candidates by analysis when their metric is saturated). Suite 400->446 green throughout. Lessons-under-threshold criterion intentionally left unchecked: active 7<12 ok, but the pre-existing 21 project lessons (>20) are curated memory deferred to a dedicated pass rather than auto-merged. No tracked graph entities changed (code-only), so the gameplan-wide cascade is trivially clean.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

**6.** A must-earn feature whose TARGET metric is already saturated by a simpler earlier phase cannot earn its place - park it WITHOUT building it. Bitemporal's gate was 'beat Phase 4 on contradiction-rate', but Phase 4 already hit 0.0 (the floor), so no implementation could win; the only other axis (valid-time / as-of) had no demonstrated need and conflicts with trim-first. Park-by-analysis (cite the saturated metric + absent need + the cost) is a legitimate evidence-based verdict; building it first only to measure zero gain burns effort to reach the same conclusion. *(evidence: Phase 5 park decision; Phase 4 contradiction_rate 0.0; D-027)* (promoted 2026-06-21: L-27)

**9.** The author's environment never exercises the real thing - a monkeypatched-platform test is not the platform, and an editable venv is not uvx --from PyPI. Execute the real surface: preview a foreign CI cell in a native venv on the target OS (one local cycle caught every win32 defect nine months of mocked-platform tests missed), and walk the published install/distribution path from a fresh environment (the README first command was broken in four places while every test passed). Then pin each as a CI job that runs the doc-exact text, with assertions that self-arm when the fix they guard is unreleased. (Consolidates L-12, L-13.) (promoted 2026-06-21: L-23)

**10.** A 'degrades gracefully' claim is only as strong as the input diversity it was tested against (non-dict valid JSON, BOM/CRLF, unicode, empty), AND tolerance must wrap the WHOLE pipeline, not just json.loads: guard the file decode before it (non-UTF-8 -> UnicodeDecodeError) and the shape after it (unhashable key, non-str field), and net per-item in any batch loop so one bad input never aborts the run. Corollary: a regex encoding a domain rule must encode it precisely ([1-9]\d* failed, not \d+ failed). Adversarial-input tests belong in the same phase that makes the robustness claim. (Consolidates L-18, L-19.) (promoted 2026-06-21: L-24)

**12.** Re-distill curated, append-only memory behind a COVERAGE GATE, never by taste: auto-derive a query from each lesson's OWN distinctive tokens (no hand-picked probes) and require that after consolidation the lesson's synthesis still surfaces in the ranker top-k; merge only the tightest clusters, mark sources obsolete with a 'consolidated into L-NN' pointer (never delete - INVARIANT-03), and prove coverage both before apply (simulated) and after apply (on the live file, with the marker stripped so it cannot cheat). Result here: 21 -> 16 active at 9/9 coverage, rollup -20%. *(evidence: _experiments/redistill_lessons.py (pre 21/21) + verify_redistill.py (post 9/9); docs/LESSONS.md L-22..L-25)* (promoted 2026-06-21: L-26)

**13.** A 'strict/blocking' flag on a discipline gate is a double INVARIANT-05 violation (block + toggle). When asked to make a gate enforce, strengthen surfacing/relevance instead — the pending cascade report + cascade_hygiene preflight already supplies the non-blocking pressure.

### Category: Testing

**1.** A retrieval-quality gate must score on a POSITION-SENSITIVE metric (MRR/nDCG), not recall@k with k >= corpus size: recall@k is trivially 1.0 when k spans the whole corpus, so a relevance-blind ranker passes it. The harness self-test caught exactly this - a degraded ranker scored recall@5=1.0 (identical to the real ranker) yet MRR 0.46 vs 1.0. Prove a measurement instrument can detect the failure it guards before trusting its verdicts. *(evidence: tests/benchmarks/test_benchmarks.py::test_harness_detects_ranker_regression; 2026-06-20-empirical-memory-gains Phase 0)*

**14.** A behavior/adherence eval must ISOLATE the variable and NOT PRIME the behavior it measures, or its null result is uninterpretable. The O-01 invariant-pointer eval read 4/4 both arms because (a) the 'control' agents still had repo + CLAUDE.md access (so it compared in-handoff vs available-in-repo, not present vs absent) and (b) the prompt asked 'would you refuse if this conflicts with a rule?', triggering the very rule-check the feature exists to prompt - with a 4/4 ceiling on top. Use self-contained arms (no repo access), neutral framing ('here is a task, proceed'), and subtler violations. Corollary: if the control can reach the signal by another path, you are not measuring your feature - you are measuring the path. *(evidence: _experiments/o01_invariant_adherence_result.md; workflow phase6-invariant-adherence-eval (surfaced 4/4 == control 4/4))* (promoted 2026-06-21: L-28)

### Category: Design

**2.** Focusing injected memory to the top-k relevant entries + a pointer to canonical (NOT truncation) cut the handoff 55% (3137->1420 tok) at EQUAL agent-eval accuracy. But the focused-vs-full eval was a TIE, not focused>full: at small scale (21 lessons / ~5k tok) the length-harm the literature predicts has not yet bitten. Measure the actual scale before claiming 'less context is more' - the honest win at this scale is token-cost at held accuracy, and it grows with lesson count. Ranker recall@k=100% is the precondition that makes focusing safe (the answer is always in the focused set). *(evidence: D4; src/clauderizer/rituals/handoff.py focused_project_lessons; _experiments/eval_focus.py + phase1-focus-eval workflow (focused 5/6 == full 5/6))*

**3.** Semver-pin validation and structural-integrity validation are SEPARATE concerns: query.pin_violations deliberately skips a depends_on edge whose target is unknown (it cannot verify a semver it cannot find), so dangling edges fell through it silently for the life of the project. A graph needs a companion structural check (dangling targets + cycles) distinct from version-pin checks. Detect cycles with iterative Tarjan SCC, never recursive DFS, so a deep/long dependency chain cannot blow the stack. *(evidence: src/clauderizer/graph/query.py pin_violations (skips target is None); src/clauderizer/graph/validate.py; tests/test_dag_validity.py)*

**4.** When measuring lexical similarity BETWEEN tracked entities (not query-to-entity), strip structural boilerplate FIRST: the id prefix (subsys./feat.), the type word (subsystem/feature), and scaffold placeholders are shared by every entity by construction, so naive overlap proposes every pair - measured: edge-suggester precision 0.103 with boilerplate vs 0.75-1.0 after stripping. Tokenize the id on ./- so the specific segment (invoice-ledger -> invoice, ledger) contributes but the prefix does not. This is the cross-entity analog of analyze._STOP dropping ADR template boilerplate, and a concrete instance of the over-retrieval finding (low-precision surfacing is net-negative noise). *(evidence: src/clauderizer/analyze.py suggest_edges / _ENTITY_STOP; tests/test_edge_suggester.py precision arc (0.103 naive -> 0.75 hardened fixture))*

**5.** Demote a stale record by a stable SECONDARY sort key (tie-break), never by penalizing its relevance score. analyze.rank_relevant keeps lexical score as the untouched primary key and sorts superseded/deprecated decisions below an ACTIVE peer only at EQUAL score - driving the knowledge-updates contradiction rate 1.0->0 without distorting retrieval or hiding the audit trail (the superseded entry still surfaces, annotated). Status defaults to active for entries lacking the field, so the change is backward-compatible with every pre-existing decision/invariant. *(evidence: src/clauderizer/analyze.py rank_relevant (-score, stale_flag, id); tests/test_supersession.py; harness contradiction_rate 1.0->0.0)*

**7.** When a borrowed 'always-inject X' pattern (e.g. a steering/constitution doc) duplicates a surface the system already has (auto-loaded CLAUDE.md + INVARIANTS + the analyze gate), the gain is in NOT adding the redundant always-injected context (it would only add context-rot cost), and the real opportunity is usually a FOCUSED surfacing of existing structured data that wasn't being surfaced - here, the phase-relevant invariants the handoff never carried. Reject the bloat form; keep the focused adaptation. *(evidence: Phase 6 decision; handoff.relevant_invariant_pointer; D-027)*

**8.** Round-trip idempotency (apply-twice == apply-once) through the engine's own parser is the load-bearing test for every mutation - but it is necessary, NOT sufficient: an engine can read its own corruption indefinitely, so also assert render-validity for EXTERNAL readers (contiguous tables, valid markdown). (Consolidates L-01, L-06.) (promoted 2026-06-21: L-22)

### Category: Observability

**11.** A health check / guard must verify CAPABILITY, not presence - a green check on a non-launchable setup is worse than none. Prove every probe at the granularity it reports, in BOTH directions (it must fire on the failure it exists for and stay green on health, per matrix cell / per argument), and prefer in-band identity (the output must claim who and what version ran) over exit codes: locally-sound guards compose into false green (a wrapper that always exits 0 defeats a spawn probe that reads exit 0 as launchable). The probe must traverse the consumer's exact execution leg, shell quirks included. (Consolidates L-02, L-09, L-10.) (promoted 2026-06-21: L-25)
