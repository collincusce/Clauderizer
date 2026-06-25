# abstract-index-fast-retrieval Gameplan

> Created: 2026-06-25
> Status: Planning
> Kind: driven
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

_(1–2 paragraphs: what this gameplan accomplishes.)_

## Subsystems Touched

_(list the subsystems/features this gameplan affects.)_

## Source-of-Truth Captures

_(Real values captured from real systems at gameplan start. Authority over the
gameplan body. Account IDs, ARNs, baseline test counts, versions.)_

## Amendments

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

### D1 — Abstract-index invalidation: scoped per-file mtime plus per-entry content-hash plus a schema-version gate, atomic write, unlocked read path

**Context**: The new cache mirrors graph/index.py, whose load_or_rebuild always re-parses markdown and uses mtime only to skip the cache WRITE (index.py:71-90). Lens findings: (1) graph _latest_mtime scans all of docs/ — too broad for a corpus-only cache; (2) index.json carries version:1 but load_or_rebuild never gates on it, so a schema bump would silently serve a stale-schema cache (latent bug, lens-1 risk #3); (3) write_cache is an unlocked write_text — benign race for identical output, but a larger payload risks a torn write; (4) read paths must not touch the write lock (L-03).
**Decision**: Invalidate on the max mtime of ONLY the four corpus files (not all of docs/), AND store a per-entry content_hash = sha256(title + body) in the cached shape, AND gate load_or_rebuild on a schema_version field (a version bump forces rebuild even when mtime is unchanged — the fix the graph index lacks). Always re-parse from markdown on read; skip the write only when nothing changed. Write atomically (write .tmp then os.replace) to avoid torn reads. The read/build path acquires NO write lock (L-03); the benign concurrent-write race is acceptable exactly as it is for index.json. Cache lives at .clauderizer/abstract_index.json (a sibling of index.json), gitignored.
**Consequences**: Correctness is ironclad (markdown canonical; cache always discardable — INVARIANT-01). Per-entry hashes also let tests and cache-aware callers detect single-entry mutations. The schema-version gate is the upgrade-safety keystone (see the upgrade-path decision). Mirrors existing patterns so reviewers recognize it; the float-mtime compare must use the 1e-6 tolerance like index.py:81.
**Evidence**: graph/index.py:50-90 (build/_latest_mtime/load_or_rebuild), index.py:31 (version:1 ungated), locking.py (write.lock, L-03 read-path rule)
**Status**: active (2026-06-25)

### D2 — Cost gain-gate: pre-registered payload-reduction threshold on a deterministic token proxy, fixture-first, DISCARD is a valid outcome

**Context**: A prior ranker spike (2026-06-24) died because its recall fixture was saturated at 1.0 — no lift was possible (L-39). This feature's KPI is COST, not recall, which has real headroom: a 5-entry-body payload (~1500 chars) vs a 1-abstract payload (~100 chars) is ~6x, measurable with zero calibration. The engine already has a deterministic token proxy token_estimate(text)=len(text)//4 (tests/benchmarks/metrics.py:17, validated by test_benchmarks.py:60-61) and a two-arm harness scaffold (harness.py:88-116 measure_context_tokens; agent_eval.py:34-42 focused-vs-full).
**Decision**: Pre-register the keep/discard gate BEFORE building the consumer (fixture-first, harness-before-feature — L-36): KEEP requires (a) mean payload-char reduction per lookup >= 30%, measured via token_estimate, AND (b) answer accuracy candidate >= baseline (no accuracy regression), AND (c) tool round-trips-to-resolve not worse than baseline. Measure deterministically — no live LLM in the gate. Build the cost fixture so the correct answer needs only 1 of N entry bodies (ground-truth wasted tokens = (N-1) * body_size), and include a negative control (a no-op candidate must show ~0% saving) so the harness has discriminating power (L-40). A DISCARD verdict closes the gameplan early as a success (L-32), recorded with its numbers.
**Consequences**: The experiment can return an honest negative and we will not have shipped machinery first. The 30% threshold is a pre-registration choice and is itself recorded so it cannot be moved post hoc to manufacture a KEEP. Escapes the L-39 saturation trap because the metric is cost, which is not pre-saturated.
**Evidence**: tests/benchmarks/metrics.py:17, harness.py:88-116, agent_eval.py:34-42, 2026-06-24-ranker-spike/_experiments/bm25_spike.py:244-299; L-39/L-40/L-36/L-32
**Status**: active (2026-06-25)

### D3 — Upgrade path for existing repos: init/reindex build the index, doctor only detects-and-advises, dogfooded on an isolated copy

**Context**: Existing clauderized repos (e.g. this one at 1.1.1) have no abstract index. doctor already hard-checks index PRESENCE (cli.py:314) and init/reindex build the graph cache (scaffold/init.py:381-384; cli.py:110-118), but nothing detects a stale SCHEMA. INVARIANT-06 forbids a hook or any read path from mutating docs or blocking a session. L-29 requires isolating destructive/irreversible ops from the real repo and PROVING the isolation before running.
**Decision**: init and reindex BUILD/refresh the abstract index (the only two surfaces that build derived state), idempotently via the existing patterns (_rewrite_if_diff, refuse_if_symlink, _ensure_gitignore for the new file, second-run-zero-diff). doctor DETECTS a missing OR schema-stale index (mirroring the _procedure_drift check at cli.py:580) and ADVISES the user to run reindex/init — it is read-only and never builds the index itself, and no hook ever does either (INVARIANT-06). The runtime load_or_rebuild self-heals on first use as a fallback. The upgrade is dogfooded on an ISOLATED copy/clone of a real existing repo (a tempfile clone, never the live repo in place — L-29), proving the corpus + graph are byte-unchanged except the new gitignored cache, and that a re-run is a no-op.
**Consequences**: Upgrade is safe, idempotent, and observable; the user is nudged but never surprised by an auto-mutation. The schema-version gate (invalidation decision) is what makes "stale" detectable. First-run-after-upgrade rebuild cost is borne by reindex/init, not silently inside a request.
**Evidence**: cli.py:314 (presence check), scaffold/init.py:381-384, cli.py:110-118 (reindex), cli.py:580-591 (_procedure_drift pattern); INVARIANT-06, L-29
**Status**: active (2026-06-25)

## Open Items

**O-01.** _(phase 1)_ Decide the exact deterministic ABSTRACT extraction rule: first sentence vs first N chars vs a dedicated summary line, plus a char budget. Pick against the Phase-1/3 cost data so the abstract is small enough to save tokens but informative enough to often avoid a cz_get round-trip.

**O-02.** _(phase 1)_ Latent graph-index bug discovered while planning: graph/index.py writes version:1 but load_or_rebuild gates on mtime ONLY, so a schema bump would silently serve a stale-schema cache. Decide whether this gameplan also retrofits the schema-version gate onto the EXISTING graph index or scopes the fix to the new abstract index only (avoid scope creep, but record the bug either way).

**O-03.** _(phase 1)_ Confirm the LESSONS dual-parser coverage: verify markdown/lesson_state's regex captures every lesson shape (numbered **N.**, consolidated/obsolete "(consolidated into L-NN)" markers, category headers) so the abstract index neither misses nor garbles lesson entries. A missed shape silently drops lessons from the index.

## Phase Breakdown

### Phase 0: Branch, baseline &amp; cost-harness (fixture-first)

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Work branch feat/abstract-index-fast-retrieval exists off main and main is untouched
- [ ] Green baseline test count captured via cz_preflight and recorded as an output
- [ ] Token-accounting harness measures baseline payload chars, token_estimate (len//4), and round-trips deterministically with no live LLM
- [ ] Cost fixture exists where the correct answer needs only 1 of N entry bodies, and the gain-gate thresholds (>=30% payload reduction, accuracy non-regression, round-trips non-worse) are pre-registered in a committed file
- [ ] Harness discriminates: a no-op negative-control candidate shows ~0% saving and a synthetic abstract-only candidate shows the predicted multi-x saving, all BEFORE the real feature exists

### Phase 1: Abstract index builder (data structure, dual parser, invalidation)

**Goal**: Implement the abstract-index module (e.g. src/clauderizer/graph/abstract_index.py) mirroring graph/index.py, with NO consumer wired yet. build() parses the four corpus files into per-entry records {id, title, abstract, anchor (file:line), token_set, content_hash, status, kind}. write_cache()/load_or_rebuild() implement the D1 invalidation design: max mtime over ONLY the four corpus files (DECISIONS/LESSONS/INVARIANTS/HARDENING), a per-entry content_hash = sha256(title+body), a schema_version gate (a version bump forces rebuild even when mtime is unchanged — the fix the graph index lacks), and an atomic write (.tmp then os.replace); always re-parse on read and skip the write only when nothing changed; a corrupt/absent cache rebuilds rather than crashing. Handle the DUAL parser: reuse analyze.parse_entries/_ENTRY_RE for the em-dash entries (### D-001 — title) in DECISIONS/INVARIANTS/HARDENING AND the LESSONS **N.** numbered format via markdown/lesson_state. The abstract is a deterministic head of the body (exact rule decided against the open item). Reuse analyze._tokens so there is no new similarity metric (L-14). Cache at .clauderizer/abstract_index.json, gitignored.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] build() yields a record for every entry across all four corpora INCLUDING lessons, with the count matching an independent parse
- [ ] load_or_rebuild gates on BOTH mtime AND schema_version; a unit test proves a schema bump forces rebuild while mtime is unchanged
- [ ] Cache writes atomically via os.replace; a corrupt/absent/BOM/CRLF/unicode/empty cache rebuilds and never raises (adversarial test, L-24)
- [ ] Delete-then-rebuild yields byte-identical cache content (INVARIANT-01 round-trip)
- [ ] Suite green and no consumer references the index yet (grep shows zero call sites outside the module and its tests)

### Phase 2: Addressable fetch (cz_get) and abstract surfacing on cz_analyze

**Goal**: Add the retrieval primitive that makes whole-file reads unnecessary. (1) analyze.get_entry(id) reads a single entry's body from the abstract index (re-parsing only the named corpus file on a cache miss). (2) ops.cz_get(id, kind="auto") returns {id, title, body, status, anchor} — read-only (Op writes=False), no write lock on the read path (L-03), safe under INVARIANT-06. (3) enrich cz_analyze output at analyze.py:118 to return {id, title, score, abstract} so the agent can answer from the abstract without a round-trip. Update EVERY tool-surface parity surface or the suite fails: tools_list.TOOL_NAMES (add cz_get), ops.REGISTRY (Op(cz_get, writes=False) + docstring + JSON-serializable defaults), and the parity/introspection tests (test_ops.py test_registry_is_exactly_the_tool_surface + test_mcp_registers_the_registry_functions; test_ops_introspection.py both tests; test_skill_discovery.py). Defer human-doc tool-count updates (README 38->39, docs/subsystems/mcp-server.md reads count) to the release phase per L-21.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] cz_get(id) returns a single entry body for an id drawn from each of the four corpora
- [ ] cz_analyze hits include an abstract field
- [ ] Tool-surface parity green: test_registry_is_exactly_the_tool_surface, MCP registration, both ops-introspection tests, and skill-discovery parity
- [ ] cz_get is read-only (Op writes=False asserted) with a docstring and JSON-serializable defaults
- [ ] Full suite green

### Phase 3: Cost experiment and gain-gate verdict (KEEP/DISCARD)

**Goal**: Wire the live feature (Phase 2) into the Phase-0 token-accounting harness and run the pre-registered cost experiment (D2). Baseline arm = current whole-file/full-body load; candidate arm = abstract+anchor surfaced, body fetched via cz_get only when needed. Compute the verdict against the pre-registered thresholds: KEEP requires mean payload-char reduction per lookup >= 30% (via token_estimate len//4) AND answer-accuracy candidate >= baseline AND round-trips not worse; the negative control (no-op candidate) must show ~0% saving (proves the harness discriminates — L-40). Record the measured numbers in the outputs registry (cz_add_output) and record the KEEP/DISCARD as a decision. THIS IS THE GATE: on DISCARD, raise an honest amendment (L-38) and close the gameplan early as a success with the negative result captured (L-32) — phases 4/6/7 do not proceed. On KEEP, proceed.
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Experiment run on the LIVE feature: baseline (full-body) vs candidate (abstract+cz_get) measured on the cost fixture
- [ ] Verdict computed against the pre-registered thresholds and recorded as a decision
- [ ] Measured payload-reduction %, accuracy delta, and round-trip delta recorded in the outputs registry
- [ ] On DISCARD: an amendment is raised and the gameplan closes early with the negative result captured (a valid success)

### Phase 4: Realize the win in injected surfaces (handoff/status) and re-measure

**Goal**: PROCEED ONLY ON A KEEP VERDICT. Thread abstract+anchor (instead of full bodies, where avoidable) through the surfaces that actually get injected into agent context: the handoff assembly (rituals/handoff.py:221-227 relevant_invariant_pointer and the lesson injection) and the status bundle (rituals/status_bundle.py). This is the L-34 cross-cutting concern: the phase that ADDS the field is not the phase that OWNS the shared injection path, so add an explicit integration test at the shared seam. Re-measure the realized handoff/status token delta on the harness (target: a meaningful reduction at equal agent-eval accuracy, comparable to the prior -55% focused-injection result), and record the realized numbers in the outputs registry. Keep markdown canonical — surfaces carry pointers, the body is fetched on demand via cz_get.
**Depends on**: 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Proceeded only on a KEEP verdict
- [ ] Handoff and status surfaces carry abstract+anchor instead of full bodies where avoidable
- [ ] An integration test exists at the shared injection seam (L-34)
- [ ] Realized handoff/status token delta re-measured and recorded at equal agent-eval accuracy
- [ ] Full suite green

### Phase 5: Write-time lesson-synthesis advisory (own fixture, own mini gain-gate)

**Goal**: Fold in the SimpleMem "online synthesis" borrow, riding the Phase-1 index. At cz_add_lesson time, reuse analyze.rank_relevant over the abstract index's per-entry token_sets to surface near-duplicate EXISTING lessons as an advisory ("this overlaps L-NN strongly — consolidate instead of append?"). Advisory only — never blocks the write, no config flag (INVARIANT-05); it mirrors the write-time analyze enrichment that cz_add_decision already has (mutations.py:163) but cz_add_lesson lacks. Discipline: build a near-duplicate-lessons fixture FIRST and a naive strawman the principled detector must beat on adversarial near-misses (a genuinely distinct-but-similar lesson must NOT be flagged) — credible only if it beats the strawman, not merely a no-check baseline (L-40). Pre-register its own precision/recall keep bar. This phase only needs Phase 1; it runs parallel to the cost spine and bundles into the same release.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] cz_add_lesson surfaces a near-duplicate advisory that never blocks the write and adds no config flag (INVARIANT-05)
- [ ] A near-duplicate-lessons fixture and a naive strawman detector both exist
- [ ] The principled detector beats the strawman on adversarial near-misses, and a genuinely distinct-but-similar lesson is NOT flagged (L-40)
- [ ] Its own precision/recall keep bar is pre-registered and met, or the feature is honestly dropped
- [ ] Full suite green

### Phase 6: Upgrade path (init/reindex build, doctor detect) and dogfood on an isolated repo copy

**Goal**: PROCEED ONLY ON KEEP. Ship the upgrade per D3. (1) init step 12 (scaffold/init.py:381-386) and reindex (cli.py:110-118) BUILD/refresh the abstract index, idempotently (_rewrite_if_diff, refuse_if_symlink, _ensure_gitignore for the new file, second-run-zero-diff invariant). (2) doctor (cli.py near :314, mirroring the _procedure_drift check at :580) DETECTS a missing OR schema-stale abstract index and ADVISES reindex/init — read-only, never builds it, with the right exit code; no hook ever builds it (INVARIANT-06). Handle absent docs/.clauderizer gracefully. (3) DOGFOOD the real upgrade an existing 1.1.1 user hits, on an ISOLATED tempfile clone of this repo — never in place (L-29): prove doctor-flags-missing -> reindex-builds -> retrieval-uses-abstracts, with the corpus + graph byte-unchanged except the new gitignored cache, and a re-run is a no-op. Prove the isolation guard BEFORE any step. Capture a friction log as a first-class deliverable.
**Depends on**: 4.

| Task | Description | Effort |
|------|-------------|--------|
| 6.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] init and reindex build the abstract index idempotently (a second-run-zero-diff test passes)
- [ ] doctor flags BOTH a missing and a schema-stale index with the correct exit code and advice, and never mutates (read-only)
- [ ] Cold upgrade on an isolated tempfile clone: doctor-flags-missing then reindex-builds then retrieval-uses-abstracts, with corpus+graph byte-unchanged except the new gitignored cache and a no-op re-run
- [ ] The isolation guard is proven BEFORE any destructive step (L-29) and a friction log is recorded

### Phase 7: Release readiness: CI 9-cell, docs sweep, cross-platform, merge-ready

**Goal**: Make the branch merge-ready WITHOUT performing the release (the D-011 version-bump/tag/PyPI ritual stays a separate user-initiated act; INVARIANT-07 parity preserved). (1) Run the suite on EVERY CI host leg — the D-012 9-cell matrix — before claiming cross-platform safety: a green on one OS is a guess and a path/separator assertion is itself a platform claim (L-20/L-31). Verify the cache specifically on win32: mtime granularity, atomic os.replace semantics, and the H-10 unlink concerns for the sibling file. (2) Sweep human-facing docs that drift on a tool-surface change (L-21): README MCP-surface tool count 38->39, docs/subsystems/mcp-server.md reads count, and any cross-host doc; update the mcp-server subsystem entity. (3) Confirm the whole feature green end-to-end and the branch is clean and rebased on main. Write the post-mortem and promote any enduring lessons. Then hand back to the user for the release decision.
**Depends on**: 4, 5, 6.

| Task | Description | Effort |
|------|-------------|--------|
| 7.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] The D-012 9-cell CI matrix is green
- [ ] win32 cache behavior verified: mtime granularity, atomic os.replace semantics, and H-10 unlink concerns for the sibling file
- [ ] Human-doc drift swept (README tool count 38->39, docs/subsystems/mcp-server.md reads count, cross-host docs) and the mcp-server entity updated
- [ ] Branch is clean, rebased on main, and merge-ready; post-mortem written and enduring lessons promoted; release handed back to the user (no auto-release, INVARIANT-07)
