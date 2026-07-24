# dreaming-loop Gameplan

> Created: 2026-07-23
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

### D1 — Dreaming ships behind an empirical gate: dogfood metrics decide hardening, and a negative result is a recorded outcome

**Context**: Per-exchange capture risks ritual fatigue and the dreamer risks proposal spam; the repo's discipline (L-17/L-50 falsifiable hypotheses, D-026 empirical gates with the measured -55% handoff precedent) requires new memory machinery to prove marginal utility before hardening.
**Decision**: Phase 5 measures on this repo: capture rate (notes per session), dreamer yield (proposals emitted vs accepted), and accepted-proposal delta versus telemetry-only cz_curate. Thresholds start as plain constants (ripeness ~10 unconsumed notes) and are tuned from dogfood data, not speculation. If the dream signal adds nothing over mechanical telemetry, that result is recorded and scope is reassessed rather than shipped by momentum.
**Consequences**: The feature earns its always-on place with data; the eval mirrors the 0.15.0 focused-vs-full template. Ripeness/size constants stay out of config until evidence says they need tuning knobs.
**Evidence**: docs/ARCHITECTURE.md:77 (measured -55% at equal accuracy); docs/LESSONS.md L-17/L-50; src/clauderizer/telemetry.py:207-216 (resolved>=2 floors precedent)
**Status**: active (2026-07-23)

## Open Items

**O-01.** _(phase 3)_ Dream-proposal persistence shape (Phase 3): dedicated .clauderizer/proposals.dream.jsonl vs generalizing status_bundle's pending_proposals into a multi-producer merge before filter_pending — decide when touching status_bundle.py:600-606; leaning generalized merge so the digest stays one line.

**O-02.** Should cz_curate and cz_mine_failures outputs also join the unified id+ledger proposal queue (they currently have no ids/ledger and can re-surface forever)? Likely a follow-on gameplan once Phase 3 proves the multi-producer merge point — tracked here so it is not silent scope creep.

**O-03.** _(phase 5)_ Ripeness threshold default (~10 unconsumed notes) and note-kind vocabulary (friction/gap/surprise/correction/drift/win): set as constants in Phases 0/2, then validate both against real dogfood usage in Phase 5 — prune unused kinds, tune the threshold from measured cadence.

## Phase Breakdown

### Phase 0: Dream journal substrate & the blessed dream write

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] cz_add_dream appends a schema-valid, sort-keyed JSONL record to gitignored .clauderizer/dreams.jsonl under the H-05 write lock; the op result carries schema_version and a contract-corpus payload is captured
- [ ] Write-time validation rejects oversize notes (> 4 sentences / ~600 chars) and PII patterns (emails, token shapes, absolute home paths) with a clear error and appends nothing on reject (INVARIANT-03: no retroactive redaction possible)
- [ ] Re-submitting an identical note (same content hash) is a no-op — no duplicate journal line
- [ ] Full suite green at >= 953 baseline; new tests cover round-trip, schema reject, PII reject, dedupe, and lock discipline

### Phase 1: Capture ritual & read-only nudges

**Goal**: Define the per-exchange dream-note ritual in the scaffolded CLAUDE/AGENTS templates and GAMEPLAN-PROCEDURE.md, and surface unconsumed-note pressure through the existing read-only digest/hook advisories — quiet when empty, never blocking (INVARIANT-06, D-027).
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Scaffolded CLAUDE/AGENTS templates and GAMEPLAN-PROCEDURE.md (MINOR bump) document the per-exchange dream-note ritual: kinds vocabulary (friction/gap/surprise/correction/drift/win), 2-4 sentences, no-PII guidance
- [ ] Session-start digest shows a one-line dream gauge only when unconsumed notes > 0 (quiet-when-empty); golden digest test updated deliberately; single [Clauderizer] header preserved (INVARIANT-08)
- [ ] All hook handlers remain read-only and exit 0 — INVARIANT-06 test extended to cover the new advisory path
- [ ] Full suite green at >= baseline

### Phase 2: cz_dream — ripeness-gated dream assembly

**Goal**: Ship the read-only cz_dream op: gate on unconsumed-note ripeness, cluster notes with the canonical tokenizer (INVARIANT-09), join corpus/lesson health and one-hop graph adjacency, and return a deterministic dream bundle for agent judgment (INVARIANT-05, D-018-style no-ML assembly).
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] cz_dream is registered writes=False and performs no writes (INVARIANT-05 parity test); below the ripeness threshold it returns not_ripe with counts, at/above it a clustered dream bundle joining corpus_health, lesson_health, and one-hop graph adjacency for referenced entities
- [ ] Clustering uses analyze._tokens exclusively — the INVARIANT-09 single-tokenizer test is extended and passes
- [ ] Same journal + caller-fixed today => byte-identical bundle across two calls (determinism test); contract-corpus payload captured
- [ ] Full suite green at >= baseline

### Phase 3: Durable dream proposals & unified triage

**Goal**: Persist agent-judged dream proposals with stable content-hash ids in a gitignored store via a blessed write, advance the note-consumption watermark only after durable write, and merge dream proposals with modernize's through the one producer-agnostic filter_pending path into the single session-start pending count (extends D-052).
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] A dream proposal persisted via the new blessed write survives process restart and surfaces in the session-start pending-proposals count merged with modernize's — one digest line, one filter_pending path
- [ ] cz_dismiss_proposal / cz_defer_proposal suppress dream proposals through the existing producer-agnostic ledger; identical proposal content yields the same stable content-hash id (spam/dedupe test)
- [ ] The note-consumption watermark advances only after the proposal batch is durably written: a kill-and-resume test re-mines nothing already proposed and loses nothing unproposed
- [ ] Full suite green at >= baseline; golden digest updated deliberately

### Phase 4: The dreaming ritual: skill, loop integration & headless recipe

**Goal**: Ship the clauderizer-dream skill (triage → ripeness check → cz_dream → judged blessed writes), surface dream ripeness in cz_loop_step for the standing-curator loop, and document the ritual, the local-only privacy boundary, and the headless clauderize-ops dreamer recipe in GAMEPLAN-PROCEDURE/TRUST/CROSS-HOST.
**Depends on**: 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] clauderizer-dream skill ships in the scaffold and is registered in SKILLS.md; it drives triage -> ripeness check -> cz_dream -> judged writes exclusively via blessed cz_* ops
- [ ] cz_loop_step surfaces dream ripeness alongside curator proposals for loop gameplans; the standing-curator loop's iteration body references it
- [ ] GAMEPLAN-PROCEDURE.md, TRUST.md, and CROSS-HOST.md document the ritual, the local-only privacy boundary (journal and proposals stay local; only accepted, reviewed writes become tracked memory), and the headless clauderize-ops dreamer recipe
- [ ] Full suite green at >= baseline

### Phase 5: Dogfood, eval & ship 1.13.0

**Goal**: Run the dreaming loop on Clauderizer itself for at least five sessions, measure capture rate / dreamer yield / accepted-proposal delta versus telemetry-only curation as falsifiable outputs (L-17/L-50 discipline), then release 1.13.0 with post-mortem close-out.
**Depends on**: 4.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] >= 5 real dogfood sessions on this repo with dream notes captured; capture rate, dreamer yield (proposals emitted vs accepted), and accepted-proposal delta vs telemetry-only cz_curate recorded as phase outputs — a negative result is recorded, not hidden (L-17/L-50)
- [ ] At least one dream-sourced proposal accepted into tracked memory via blessed writes, or the negative result plus scope reassessment is recorded as an output
- [ ] release-check exit 0; version bumped to 1.13.0; post-mortem written with procedure improvements
- [ ] Full suite green at >= baseline
