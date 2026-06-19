# headroom-borrowed-ideas Gameplan

> Created: 2026-06-19
> Status: Complete
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

### D1 — Keep/discard methodology: each borrowed idea is a falsifiable hypothesis with a machine-checkable metric

**Context**: Porting Headroom-inspired ideas wholesale would add speculative complexity to a deterministic, zero-dependency engine. We need to ship only what demonstrably helps and discard the rest with evidence.
**Decision**: Each of the three ideas is a falsifiable hypothesis with a pre-named, machine-checkable keep/discard metric. Idea #1: a deterministic prefix-stability proxy (longest common byte-prefix across volatile-state variants), since real provider KV-cache hits are not observable from inside the engine. Idea #2: zero-drop (count-in==count-out) plus a relevance-ordering test. Idea #3: measured precision on a labeled real-transcript sample, including the dogfood test of surfacing this session's own corrections. Discard on fail.
**Consequences**: A discarded idea is a successful outcome, not a failure. Spikes for discarded ideas are reverted so no dead engine code remains. 'Inherent volatility' is an acceptable discard reason for idea #1. The gameplan's deliverable is the verdicts plus the survivors, not all three features.

### D2 — Idea #2 (relevance-ranked handoff) is reorder-not-drop

**Context**: A 'budgeted' handoff that drops low-relevance lessons would contradict D-009 (consolidation pressure, not caps) and the incomplete-lesson-propagation anti-pattern the self-contained handoff exists to prevent (handoff.py:3).
**Decision**: The relevance ranking reorders lessons (most-relevant-first to the current phase) while keeping ALL of them in every handoff. Tie-breaking falls back to chronological order so output stays deterministic. Collapsing/budgeting the low-relevance tail is a separate sub-experiment (2b) held to a higher bar and may be discarded independently.
**Consequences**: Idea #2's safe core cannot regress lesson propagation; the riskier collapse is isolated and individually falsifiable. Reuses the existing keyword/graph ranker (D-018), adding no ML.

### D3 — Idea #3 (failure-miner) ships as an invoked, read-only, advisory tool — never an auto-firing gate or a config flag

**Context**: Auto-mining failures is attractive, but an always-on or flag-gated mechanism would violate D-015/INVARIANT-05 (gates are always-on, advisory, judgment-based, with no enable/disable flag) and risk flooding the curated store the memory gauge fights.
**Decision**: The miner is a peer of cz_analyze/cz_critique: invoked on demand, read-only, and propose-only. It surfaces candidate corrections/lessons for the agent to confirm through the existing cz_add_correction / cz_add_lesson mutation path; it never writes memory itself and adds no enable/disable flag. Being invoked is what makes it opt-in — not a config toggle.
**Consequences**: Append-only memory (INVARIANT-03) and the advisory-gate invariant are preserved; precision, not automation, is the property that must be proven to keep it.

## Open Items

**O-01.** _(phase 1)_ Whether the Claude Code harness places the SessionStart digest / MCP tool results inside the provider-cacheable prompt prefix is unknown and not observable from the engine; idea #1's real-world payoff therefore rests on the deterministic prefix-stability proxy, not a measured cache-hit rate. _(resolved 2026-06-19: Confirmed unobservable from inside the engine; the prefix-stability proxy was used instead. Idea #1 discarded on cost-benefit grounds, so the unknown no longer blocks anything.)_

**O-02.** _(phase 3)_ The keep bar for the failure-miner's precision must be set from a labeled sample of real transcripts (not a priori); Phase 0 names the rule, Phase 3 measures against it. _(resolved 2026-06-19: Keep bar set from the labeled sample: ≥70% precision + catches the substantive failures + strictly propose-only. Met at ~80% precision (20-proposal sample), 2/2 dogfood, rediscovers H-08-class lessons. Idea #3 KEEP.)_

**O-03.** _(phase 3)_ Claude Code transcript JSONL schema may vary across versions; the miner must degrade gracefully (skip unrecognized record shapes) rather than crash. _(resolved 2026-06-19: Handled: _iter_records tolerates garbled/partial JSONL lines (per-line try/except), _content/_blocks/_user_text defensively handle variant shapes, and the unreliable is_error flag is compensated by content-signature detection. Ran cleanly across 11 heterogeneous real transcripts.)_

## Phase Breakdown

### Phase 0: Baseline & methodology

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_preflight passes green and the baseline test count (300) is confirmed
- [x] Keep/discard methodology recorded as a gameplan decision, naming each idea's machine-checkable success metric
- [x] Idea designs vetted against D-009/D-014/D-015/INVARIANT-05 and the identity constraints (no new deps, deterministic, append-only, advisory, no ML) recorded
- [x] Open items filed for the known unknowns: cache-prefix applicability, miner precision bar, transcript schema stability

### Phase 1: Idea 1 — Prefix-stability (CacheAligner analog)

**Goal**: Test whether prefix-stabilizing the SessionStart digest (status_bundle.render_digest) and the phase handoff (handoff.assemble) yields a meaningfully larger stable byte-prefix — a deterministic, observable PROXY for provider KV-cache prefix hits (real cache hits are not observable from inside the engine). Build a measurement harness that renders each payload twice under differing volatile state (dates, test counts, lesson counts, pending cascades) and reports the longest common leading prefix. Where it does not defeat the payload's purpose, move stable scaffold ahead of volatile state. KEEP if the stable prefix grows materially with no loss of correctness/readability; DISCARD if the payloads are inherently volatile (the digest is a status report) or the gain is negligible. Either verdict is a valid deliverable.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] A measurement harness renders digest + handoff twice under differing volatile state and reports the longest common leading byte-prefix
- [x] Baseline stable-prefix length recorded as an output
- [x] A reorder attempt is implemented OR shown inapplicable, with before/after prefix numbers
- [x] KEEP/DISCARD decision recorded with the measured evidence
- [x] If KEEP: change covered by a test and tests green; if DISCARD: spike reverted, no engine change left behind

### Phase 2: Idea 2 — Relevance-ranked handoff (IntelligentContext analog)

**Goal**: Wire the existing deterministic analyze.rank_relevant (keyword + entity-id overlap, no ML — consistent with D-014/D-018) into handoff lesson assembly so lessons are ordered most-relevant-first to the current phase. Sub-test 2a (reorder-only): keep ALL lessons in every handoff, just reordered — this must satisfy D-009 (consolidation pressure, NOT caps) and the incomplete-lesson-propagation anti-pattern in handoff.py:3. Sub-test 2b (stretch): collapse the low-relevance tail behind a count + pointer. Tie-breaking must be stable (fall back to chronological) so output stays deterministic. KEEP 2a if a test proves count-in == count-out (zero drops) AND ordering demonstrably tracks phase relevance (a phase-relevant lesson precedes an irrelevant one; different phases reorder differently). Evaluate 2b separately and DISCARD it if it risks dropping propagation.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] analyze.rank_relevant wired into handoff lesson ordering behind a deterministic, stable-sorted path
- [x] Test proves ALL lessons survive: count-in == count-out (zero drops)
- [x] Test proves ordering tracks phase relevance (a relevant lesson precedes an irrelevant one; two different phases produce different orders)
- [x] Sub-test 2b (collapse tail) evaluated; its KEEP/DISCARD recorded separately from 2a
- [x] Per-sub-test KEEP/DISCARD decisions recorded with evidence; survivors covered by tests, green

### Phase 3: Idea 3 — Failure-miner (headroom learn analog)

**Goal**: Build a deterministic, stdlib-only miner that scans Claude Code session transcripts (JSONL under ~/.claude/projects/<project-slug>/) for failure→fix patterns: (a) a tool call that errored then a corrected retry that succeeded; (b) a test run that failed then passed; (c) an explicit user correction ("no, do X instead"). It EMITS proposed corrections/lessons for the agent to confirm through the existing cz_add_correction path — an invoked, read-only, advisory tool (a peer of cz_analyze/cz_critique), NEVER auto-firing and with NO enable/disable flag (D-015/INVARIANT-05), preserving append-only (INVARIANT-03). KEEP if precision on a labeled sample of real transcripts clears the bar set in Phase 0 (proposals are mostly genuine, and it surfaces the known corrections from THIS session's own transcript — the dogfood test) and it stays strictly propose-only; DISCARD if precision is too low to be worth the curation-bloat risk the memory gauge fights.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] A deterministic stdlib-only miner parses real JSONL transcripts with no new runtime dependency
- [x] It surfaces at least one genuine failure-then-fix pattern from this session's own transcript (dogfood)
- [x] Precision measured on a labeled sample of real transcripts and recorded as an output
- [x] Tool is invoked / read-only / propose-only: no auto-fire, no enable/disable flag; proposals route through cz_add_correction wording
- [x] KEEP/DISCARD decision recorded against the Phase-0 precision bar; if KEEP, covered by a fixture-transcript test

### Phase 4: Consolidate survivors & close

**Goal**: Productionize the surviving ideas with tests and docs; record per-idea KEEP/DISCARD decisions with measured evidence; bump affected subsystem versions (subsys.rituals for #1/#2, subsys.mcp-server/subsys.mutations for #3) and run cz_cascade + cz_resolve_cascade for dependents; consolidate any new lessons; update CHANGELOG/docs for survivors and document discarded ideas as decisions (with the evidence that killed them); run cz_critique, then write the post-mortem and close the gameplan.
**Depends on**: 1, 2, 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Surviving ideas merged with green tests; final count reported against the 300 baseline
- [x] Per-idea KEEP/DISCARD decisions all recorded with evidence (including why discarded ones were killed)
- [x] Affected subsystem versions bumped; cz_cascade + cz_resolve_cascade completed for dependents
- [x] CHANGELOG/docs updated for survivors; cz_critique run; post-mortem written and gameplan closed
