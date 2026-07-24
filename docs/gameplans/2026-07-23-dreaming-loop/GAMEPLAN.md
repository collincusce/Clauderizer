# dreaming-loop Gameplan

> Created: 2026-07-23
> Status: Complete
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

### A-001 — Re-dream guard and bounded dream bundle

- **Date**: 2026-07-24
- **Affected sections in GAMEPLAN.md**: Phase 2 exit criteria; cz_dream gate design (D-059 mechanics)
- **Affected phases**: 2
- **Triggered by**: User review of the proposed design (2026-07-24): "we shouldn't dream if a dream has already happened but no changes have been made" + "consider token utilization bloat"
- **What changed**: cz_dream's gate gains a second condition: ripeness (unconsumed notes >= threshold) AND no previously emitted dream proposals still pending (untriaged) in the producer-agnostic ledger filter — while pending, cz_dream returns blocked_on_triage instead of a bundle, so dreaming never piles new proposals on top of unactioned ones. The dream bundle is explicitly bounded: top-K clusters, capped exemplar notes per cluster, ids+abstracts over full bodies (D-013), and the bundle reports its own est_tokens.
- **Why**: Without the guard, every ripe session re-dreams and accumulates overlapping proposal batches nobody triaged — proposal spam plus wasted LLM judgment. Without bundle bounds, a large journal makes the dreaming session's input grow unbounded, violating the trim-first discipline (D-027). All phases are unstarted, so no mid-flight reconciliation: the Phase 2 session picks this up from the amended criteria.

### A-002 — Phase 5 eval gains the transcript-sampling comparator and token-utilization outputs

- **Date**: 2026-07-24
- **Affected sections in GAMEPLAN.md**: Phase 5 exit criteria; D1 empirical gate scope
- **Affected phases**: 5
- **Triggered by**: User question (2026-07-24): "full transcript mining already exists — maybe we shouldn't do the notes?" — the strongest rival hypothesis to dream notes is transcript-sampling, not telemetry-only curation
- **What changed**: Phase 5 adds a comparator arm: one dogfood dreaming pass fed by deterministically pre-filtered transcript slices (learn.py-style selection) through the same proposal queue, with accepted-proposal overlap/delta and tokens-per-accepted-proposal recorded for both arms. Token-utilization outputs become explicit phase outputs: notes per session, average note size, dream-bundle est_tokens, and per-arm token cost.
- **Why**: The original eval compared notes only against telemetry-only cz_curate, which cannot answer "should we have skipped the notes and mined transcripts instead" — D-023's detector-C zero recall suggests deterministic mining misses semantic signal, but that is a hypothesis to measure, not assume (L-50). Token accounting keeps the whole loop honest against D-027 trim-first. Phase unstarted; the Phase 5 session picks this up from the amended criteria.

### A-003 — Phase 5 measured basis: one build-session across five phase contexts, not five calendar sessions

- **Date**: 2026-07-24
- **Affected sections in GAMEPLAN.md**: Phase 5 exit criterion 1 (dogfood sessions)
- **Affected phases**: 5
- **Triggered by**: L-50 honesty at close: the user directed "do all phases" in a single session (2026-07-24)
- **What changed**: The ">= 5 real dogfood sessions" clause was measured as one continuous build session spanning five phase contexts (P0-P4), each contributing organic notes at phase boundaries: 12 notes total, 2.0 per phase context, all six kinds used organically except drift (probe only). The full cycle (capture -> ripe -> dream -> stage -> triage -> accepted tracked writes -> loop at rest) ran END-TO-END on real data within it. Ongoing multi-session accumulation is delegated to the standing-curator loop gameplan, whose iterations now surface dream state (P4).
- **Why**: Session boundaries cannot be manufactured honestly inside one directed run; the criterion's intent — a real accumulated corpus exercising the whole loop with measured yield — was met and exceeded (two engine defects found by the loop itself mid-eval: the dead ready-fallback and the gauge counting consumed notes). Recording the basis rather than faking the count (L-50).

### A-004 — Post-close amendment: the session-start dream plea — beg, explain, instruct when no scheduled loop is detected

- **Date**: 2026-07-24
- **Affected sections in GAMEPLAN.md**: New Phase 6; status digest; dreams schedule registration; docs (README/skill/procedure/TRUST/CHANGELOG)
- **Affected phases**: 6
- **Triggered by**: User directive (2026-07-24), after 1.13.0 release-check but BEFORE the tag was cut: capture is ambient, but nothing drives adoption of the dreaming half — "beg people to run the dream loops... explain what this is in plain English... tell them exactly HOW to schedule... a ritual on every session start when no scheduled loop is detected."
- **What changed**: A dream plea renders inside the ONE session-start digest (INVARIANT-08) when three conditions hold: unconsumed notes > 0, no dream schedule registered, and no dream proposals pending (the triage line owns that state). The plea explains the loop in plain English (auto-collected notes -> a short offline pass -> PROPOSED memory fixes the user approves/rejects; nothing changes without review), gives exact scheduling paths (Claude Code routine phrasing, a cron + claude -p line, or run /clauderizer-dream now), and names its own retirement: a new blessed write cz_register_dream_schedule records {method, cadence, command} to gitignored .clauderizer/dreams.schedule.toml — method="manual" is a legitimate quieting verdict (a D-052-style per-user verdict, NOT a feature toggle: the loop, gauges, and skill stay fully active). Empty method clears and the plea revives. Ships inside the still-untagged 1.13.0.
- **Why**: Adoption is the loop's weakest link: capture is ambient and the machinery is built, but a user who never schedules or runs the dreamer accumulates a journal that helps no one. The D-027 trim-first tension is accepted deliberately per explicit user directive — mitigated by strict gating (quiet when scheduled, when empty, when triage already nags, and in every journal-less fixture, keeping goldens byte-identical) and by the plea being self-retiring.

## Decisions

### D1 — Dreaming ships behind an empirical gate: dogfood metrics decide hardening, and a negative result is a recorded outcome

**Context**: Per-exchange capture risks ritual fatigue and the dreamer risks proposal spam; the repo's discipline (L-17/L-50 falsifiable hypotheses, D-026 empirical gates with the measured -55% handoff precedent) requires new memory machinery to prove marginal utility before hardening.
**Decision**: Phase 5 measures on this repo: capture rate (notes per session), dreamer yield (proposals emitted vs accepted), and accepted-proposal delta versus telemetry-only cz_curate. Thresholds start as plain constants (ripeness ~10 unconsumed notes) and are tuned from dogfood data, not speculation. If the dream signal adds nothing over mechanical telemetry, that result is recorded and scope is reassessed rather than shipped by momentum.
**Consequences**: The feature earns its always-on place with data; the eval mirrors the 0.15.0 focused-vs-full template. Ripeness/size constants stay out of config until evidence says they need tuning knobs.
**Evidence**: docs/ARCHITECTURE.md:77 (measured -55% at equal accuracy); docs/LESSONS.md L-17/L-50; src/clauderizer/telemetry.py:207-216 (resolved>=2 floors precedent)
**Status**: active (2026-07-23)

## Open Items

**O-01.** _(phase 3)_ Dream-proposal persistence shape (Phase 3): dedicated .clauderizer/proposals.dream.jsonl vs generalizing status_bundle's pending_proposals into a multi-producer merge before filter_pending — decide when touching status_bundle.py:600-606; leaning generalized merge so the digest stays one line. _(resolved 2026-07-24: Decided in Phase 3: a dedicated append-only .clauderizer/proposals.dream.jsonl store (content-hash ids, terminal handled markers) whose pending set merges into status_bundle's ONE pending_proposals count through the producer-agnostic filter_pending — the digest stays one line, with a "(N dream)" tag only when dream proposals exist, and modernize-only wording is byte-unchanged.)_

**O-02.** Should cz_curate and cz_mine_failures outputs also join the unified id+ledger proposal queue (they currently have no ids/ledger and can re-surface forever)? Likely a follow-on gameplan once Phase 3 proves the multi-producer merge point — tracked here so it is not silent scope creep. _(resolved 2026-07-24: Answered: yes — cz_curate and cz_mine_failures should join the unified id+ledger queue, and Phase 3 proved the exact merge pattern (producer-agnostic filter_pending into the single pending count with a producer tag). Scheduled as a candidate follow-on gameplan; deliberately out of this gameplan's scope. The P5 eval reinforced the need: curate's 6 obsoletion proposals currently re-derive with no dismiss memory.)_

**O-03.** _(phase 5)_ Ripeness threshold default (~10 unconsumed notes) and note-kind vocabulary (friction/gap/surprise/correction/drift/win): set as constants in Phases 0/2, then validate both against real dogfood usage in Phase 5 — prune unused kinds, tune the threshold from measured cadence. _(resolved 2026-07-24: Validated in the P5 dogfood: ripeness 10 produced one full clean cycle (11 consumed, bundle ~2k tok — keep the constant); kind usage gap 4 / win 4 / correction 1 / friction 1 / surprise 1 / drift 1(probe) — all six kinds earn their place, none pruned; CLUSTER_JACCARD 0.25 yielded honest singletons on a deliberately-diverse first corpus (precision over forced grouping) — revisit only if future corpora over-fragment recurring themes.)_

## Phase Breakdown

### Phase 0: Dream journal substrate & the blessed dream write

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_add_dream appends a schema-valid, sort-keyed JSONL record to gitignored .clauderizer/dreams.jsonl under the H-05 write lock; the op result carries schema_version and a contract-corpus payload is captured
- [x] Write-time validation rejects oversize notes (> 4 sentences / ~600 chars) and PII patterns (emails, token shapes, absolute home paths) with a clear error and appends nothing on reject (INVARIANT-03: no retroactive redaction possible)
- [x] Re-submitting an identical note (same content hash) is a no-op — no duplicate journal line
- [x] Full suite green at >= 953 baseline; new tests cover round-trip, schema reject, PII reject, dedupe, and lock discipline

### Phase 1: Capture ritual & read-only nudges

**Goal**: Define the per-exchange dream-note ritual in the scaffolded CLAUDE/AGENTS templates and GAMEPLAN-PROCEDURE.md, and surface unconsumed-note pressure through the existing read-only digest/hook advisories — quiet when empty, never blocking (INVARIANT-06, D-027).
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Scaffolded CLAUDE/AGENTS templates and GAMEPLAN-PROCEDURE.md (MINOR bump) document the per-exchange dream-note ritual: kinds vocabulary (friction/gap/surprise/correction/drift/win), 2-4 sentences, no-PII guidance
- [x] Session-start digest shows a one-line dream gauge only when unconsumed notes > 0 (quiet-when-empty); golden digest test updated deliberately; single [Clauderizer] header preserved (INVARIANT-08)
- [x] All hook handlers remain read-only and exit 0 — INVARIANT-06 test extended to cover the new advisory path
- [x] Full suite green at >= baseline

### Phase 2: cz_dream — ripeness-gated dream assembly

**Goal**: Ship the read-only cz_dream op: gate on unconsumed-note ripeness, cluster notes with the canonical tokenizer (INVARIANT-09), join corpus/lesson health and one-hop graph adjacency, and return a deterministic dream bundle for agent judgment (INVARIANT-05, D-018-style no-ML assembly).
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_dream is registered writes=False and performs no writes (INVARIANT-05 parity test); below the ripeness threshold it returns not_ripe with counts, at/above it a clustered dream bundle joining corpus_health, lesson_health, and one-hop graph adjacency for referenced entities
- [x] Re-dream guard (A-001): while previously emitted dream proposals remain pending (untriaged) in the producer-agnostic ledger filter, cz_dream returns blocked_on_triage with the pending ids instead of a bundle; dreaming resumes once they are handled/dismissed/deferred — tests cover both sides
- [x] Bounded bundle (A-001): the bundle is capped (top-K clusters, max exemplar notes per cluster, ids+abstracts over full bodies per D-013) and reports its own est_tokens; a seeded oversized journal still yields a bundle within the cap — test enforced
- [x] Clustering uses analyze._tokens exclusively — the INVARIANT-09 single-tokenizer test is extended and passes
- [x] Same journal + caller-fixed today => byte-identical bundle across two calls (determinism test); contract-corpus payload captured
- [x] Full suite green at >= baseline

### Phase 3: Durable dream proposals & unified triage

**Goal**: Persist agent-judged dream proposals with stable content-hash ids in a gitignored store via a blessed write, advance the note-consumption watermark only after durable write, and merge dream proposals with modernize's through the one producer-agnostic filter_pending path into the single session-start pending count (extends D-052).
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] A dream proposal persisted via the new blessed write survives process restart and surfaces in the session-start pending-proposals count merged with modernize's — one digest line, one filter_pending path
- [x] cz_dismiss_proposal / cz_defer_proposal suppress dream proposals through the existing producer-agnostic ledger; identical proposal content yields the same stable content-hash id (spam/dedupe test)
- [x] The note-consumption watermark advances only after the proposal batch is durably written: a kill-and-resume test re-mines nothing already proposed and loses nothing unproposed
- [x] Full suite green at >= baseline; golden digest updated deliberately

### Phase 4: The dreaming ritual: skill, loop integration & headless recipe

**Goal**: Ship the clauderizer-dream skill (triage → ripeness check → cz_dream → judged blessed writes), surface dream ripeness in cz_loop_step for the standing-curator loop, and document the ritual, the local-only privacy boundary, and the headless clauderize-ops dreamer recipe in GAMEPLAN-PROCEDURE/TRUST/CROSS-HOST.
**Depends on**: 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] clauderizer-dream skill ships in the scaffold and is registered in SKILLS.md; it drives triage -> ripeness check -> cz_dream -> judged writes exclusively via blessed cz_* ops
- [x] cz_loop_step surfaces dream ripeness alongside curator proposals for loop gameplans; the standing-curator loop's iteration body references it
- [x] GAMEPLAN-PROCEDURE.md, TRUST.md, and CROSS-HOST.md document the ritual, the local-only privacy boundary (journal and proposals stay local; only accepted, reviewed writes become tracked memory), and the headless clauderize-ops dreamer recipe
- [x] Full suite green at >= baseline

### Phase 5: Dogfood, eval & ship 1.13.0

**Goal**: Run the dreaming loop on Clauderizer itself for at least five sessions, measure capture rate / dreamer yield / accepted-proposal delta versus telemetry-only curation as falsifiable outputs (L-17/L-50 discipline), then release 1.13.0 with post-mortem close-out.
**Depends on**: 4.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] >= 5 real dogfood sessions on this repo with dream notes captured; capture rate, dreamer yield (proposals emitted vs accepted), and accepted-proposal delta vs telemetry-only cz_curate recorded as phase outputs — a negative result is recorded, not hidden (L-17/L-50)
- [x] Transcript-sampling comparator (A-002): one dogfood dreaming pass fed by deterministically pre-filtered transcript slices (learn.py-style selection) through the same proposal queue; accepted-proposal overlap/delta vs the notes-fed arm recorded — the notes-vs-transcripts question answered with data
- [x] Token-utilization outputs (A-002): notes per session, average note size, dream-bundle est_tokens, and tokens-per-accepted-proposal for both comparator arms recorded in the Outputs Registry
- [x] At least one dream-sourced proposal accepted into tracked memory via blessed writes, or the negative result plus scope reassessment is recorded as an output
- [x] release-check exit 0; version bumped to 1.13.0; post-mortem written with procedure improvements
- [x] Full suite green at >= baseline

### Phase 6: The schedule plea — beg, explain, instruct at session start

**Goal**: When dream notes accumulate with no registered dream schedule and nothing pending triage, the single session-start digest carries a plain-English plea explaining the dreaming loop, exact scheduling instructions, and its own retirement path via the new cz_register_dream_schedule blessed write (A-004).
**Depends on**: 5.

| Task | Description | Effort |
|------|-------------|--------|
| 6.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] The dream plea renders ONLY when unconsumed notes > 0 AND no schedule is registered AND no dream proposals are pending (the triage line owns that state) — inside the single [Clauderizer] digest (INVARIANT-08); every journal-less fixture stays byte-identical (goldens untouched)
- [x] The plea explains the loop in plain English (auto-collected notes -> short offline pass -> PROPOSED memory fixes the user approves/rejects; nothing changes without review) and gives exact scheduling paths: Claude Code routine phrasing, a cron + claude -p line, run-now via /clauderizer-dream — key phrases test-pinned so wording drift cannot silently drop the instructions
- [x] cz_register_dream_schedule (writes=True, stamped, TOOL_NAMES parity) records method/cadence/command to gitignored .clauderizer/dreams.schedule.toml; empty method clears; method="manual" quiets the plea as a D-052-style per-user verdict while the loop/gauges/skill stay fully active; registration retires the plea and clearing revives it — all test-pinned; init gitignores the file in target repos; hooks stay read-only/exit-0
- [x] Docs in lockstep: README Dreaming group + count (pin test forces it), clauderizer-dream skill gains the schedule/register step, GAMEPLAN-PROCEDURE Dream Notes + template byte-identical, TRUST local-file row, CHANGELOG 1.13.0 bullet (still untagged)
- [x] Full suite green at >= baseline
