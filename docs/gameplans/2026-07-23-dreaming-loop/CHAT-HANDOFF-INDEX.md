# Chat Handoff Index — dreaming-loop

> Last updated: 2026-07-24
> Status: All 6 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 948

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
| 0 | Dream journal substrate & the blessed dream write | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Capture ritual & read-only nudges | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-1-HANDOFF.md |
| 2 | cz_dream — ripeness-gated dream assembly | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Durable dream proposals & unified triage | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-3-HANDOFF.md |
| 4 | The dreaming ritual: skill, loop integration & headless recipe | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Dogfood, eval & ship 1.13.0 | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-5-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-24

Landed the dream-journal substrate exactly on the telemetry pattern: new src/clauderizer/dreams.py reuses telemetry's sorted-key JSONL appender and torn-line-tolerant reader against a new paths.dreams_file (.clauderizer/dreams.jsonl, gitignored here and ensured by init in target repos — which also closed the pre-existing gap where init never gitignored telemetry.jsonl). The blessed write is mutations.add_dream (@_locked, so the dedupe read and append are one read-modify-write under H-05) surfaced as cz_add_dream (writes=True, centrally stamped, TOOL_NAMES parity kept); gameplan/phase default to the active gameplan's in-progress phase so capture is a two-argument call. Validation is reject-before-append per INVARIANT-03: closed kind vocabulary (friction/gap/surprise/correction/drift/win), 600-char/4-sentence/8-ref caps, and a conservative PII deny-list (emails, known secret-token shapes, absolute home paths — repo-relative paths pass). Duplicate content (whitespace-collapsed, keyed by gameplan+phase+kind+note) is a safe no-op; the same note in a later phase is deliberately new signal.

Evidence: 20 new tests in tests/test_dreams.py (round-trip byte-determinism, all reject classes, dedupe both ways, revision non-bump, registry/lock discipline, init gitignoring, contract key-set pin — the criterion's "corpus payload" is pinned engine-side in test_op_result_carries_schema_version_and_contract_keys; the external PhaseKeep corpus regenerates at the 1.13.0 release per its own capture script). Full suite exit 0 at 973 collected vs 953 pre-phase. Dogfooding started immediately: the first two real notes were captured through the headless clauderize-ops path with defaults resolving correctly (ids in Outputs Registry). Doctor's exit-3 is pre-existing environment noise (kimi-desktop pin serves another repo at 1.11.0), unrelated to this phase.

### Phase 1 — completed 2026-07-24

The capture ritual is now documented at every surface an agent reads: the single-source claude_stanza.md template (and both of this repo's rendered marker blocks) carries a terse cz_add_dream bullet with the kind vocabulary and no-PII guidance; GAMEPLAN-PROCEDURE.md gained a "Dream Notes (experiential capture)" section and a MINOR bump to 1.8.0 (changelog entry, template copy synced byte-identical, this corpus mechanically stamped via clauderize upgrade). Nudges stayed inside INVARIANT-06/D-027 bounds: the session digest gains one quiet-when-empty line ("Dreams: N note(s) awaiting the dreamer."), and the pre-compact reminder now names cz_add_dream alongside the other record-now ops. No per-turn UserPromptSubmit nudge — that would be noise against D-027.

The exit criterion anticipated a deliberate golden-digest update; the quiet-when-empty design made that unnecessary (every fixture repo has no journal, so the golden stays byte-identical — the L-41 identity-default pattern) and positive/negative digest tests pin both sides instead, plus a single-header INVARIANT-08 assertion. The INVARIANT-06 sweep was extended to run all four handlers over a repo WITH a dream journal. Two seam tests close silent-drift channels found en route: stanza source + both renders must mention the ritual together (L-55), and both GAMEPLAN-PROCEDURE copies must carry PROCEDURE_VERSION and the new section. Suite exit 0; live dogfood digest shows Dreams: 4.

### Phase 2 — completed 2026-07-24

cz_dream ships as pure assembly with a two-condition gate, exactly per D-059+A-001: it returns blocked_on_triage (with pending ids) while any staged dream proposal sits untriaged in the producer-agnostic ledger filter — dreaming never piles onto unactioned output; not_ripe with unconsumed/ripeness counts below the 10-note floor; and otherwise a BOUNDED ripe bundle — greedy order-stable clustering over kind+note text using the canonical tokenizer at a dream-specific 0.25 Jaccard (deliberately looser than the 0.40 lesson near-dup threshold, single-sourced in dreams.py), top-8 clusters with at most 3 full-text exemplars each (ids beyond — D-013), a named clusters_dropped tail (no silent caps), corpus-health metrics, lesson_health entries carrying an advisory signal, one-hop graph adjacency for entity-shaped refs, a judgment prompt, and self-reported est_tokens (A-001). Deterministic given caller-fixed today; a snapshot test proves assembly writes nothing.

Phase 3's read-side contracts got defined here by necessity: proposals.dream.jsonl (append-only records with content-hash ids; a terminal {"id","handled"} marker record retires one) and dreams.watermark.json ({"consumed":[ids]}), both tolerant of absence/corruption — O-01 stays open only for Phase 3 to confirm the writer + digest merge. The house io-discipline test caught a bare open() in a new test (encoding= must be pinned — recorded as a dream note of kind correction). The corpus-payload clause is satisfied the Phase 0 way: result key-set and schema_version pinned in-test; the external PhaseKeep corpus regenerates at release. Suite exit 0, 988 collected; live smoke on this repo: 6 notes → not_ripe 6/10.

### Phase 3 — completed 2026-07-24

The dreamer's output is now durable and triaged through the one existing pipeline. cz_dream_propose stages a judged batch into .clauderizer/proposals.dream.jsonl (append-only, content-hash dreamprop ids so restaging identical content is a no-op; details PII-linted with the shared deny-list since accepted writes become tracked memory) and THEN advances dreams.watermark.json over every reviewed note id — evidence ids always, plus the clusters judged not durable, so nothing re-ripens; the ordering is the resumability contract and the kill-and-resume test proves a crash between the two appends double-mines nothing and loses nothing. An empty batch with reviewed ids is a first-class "dreamed, found nothing durable" pass. cz_handle_dream_proposal retires a done proposal with a terminal marker; dismiss/defer needed ZERO changes — D-052's producer-agnostic ledger absorbed the second producer exactly as designed, only docstrings were generalized.

status_bundle now folds dream pending into the single pending-proposals count with a producer tag, and the digest line says "(N dream)" plus what unblocks cz_dream — only when dream proposals exist; the modernize-only wording is byte-unchanged so every golden and existing digest test stayed green untouched. cz_dream's ripe prompt now names the real writer and the reviewed_note_ids contract (closing the Phase 2 friction note). O-01 resolved with this shape. Suite exit 0 at 995 collected; journal at 8 notes after this phase's two dogfood captures.

### Phase 4 — completed 2026-07-24

The dreaming ritual is now a first-class, host-portable workflow. The clauderizer-dream skill (S-09) ships in the engine's skill set (and this repo's installed copy) driving triage-first → dream-if-ripe → one cz_dream_propose call carrying reviewed_note_ids, with the headless clauderize-ops variant documented inline — and it appeared in this very session's skill roster the moment the file landed. cz_loop_step surfaces the dream state (blocked_on_triage / ripe / not_ripe, quiet on an empty journal) beside curator proposals with a summary suffix pointing at the skill, so the standing-curator loop's iterations inherit dreaming with no further wiring. Docs: CROSS-HOST gained §5b (dream capture is deliberately hook-independent — tool calls + the ops fallback reach every host, headless included), TRUST's .clauderizer row now names the three local dream artifacts and the PII boundary, and GAMEPLAN-PROCEDURE already carried the ritual from Phase 1.

The L-21 sweep earned its keep: README's MCP surface had silently drifted FOURTEEN tools behind (the whole 1.12.0 listing-reads contract never landed there). Fixed with a new Listing group + the Dreaming group, count corrected 48→66, and the seam made executable — a test now diffs README's backticked tool names against TOOL_NAMES and pins the count line, so this drift class is dead. Suite exit 0 at 998 collected. The live repo closed the phase with its journal at exactly the ripeness floor: loop_step reports dream ripe, 10 unconsumed — Phase 5's dogfood dream has a real corpus waiting.

### Phase 5 — completed 2026-07-24

The eval phase turned into the strongest possible dogfood: the loop ran end-to-end on its own build's real notes and caught two of its own defects in the process. Twelve organic notes (avg 51 tok) ripened into a 2053-token bundle of 8 clusters; judgment staged 4 proposals; triage accepted 3 into tracked memory (gameplan lesson #1 on executable doc seams, correction C-01 on the missed-transition drift, a CROSS-HOST live-skill-reload note) and dismissed the transcript-arm duplicate — ~1,051 tokens per accepted proposal, loop back to rest with the watermark consuming all reviewed notes. The A-002 comparator answered the founding question with data: the 4.6M-token raw transcript corpus, mined deterministically, produced 31 failure-shaped candidates and ZERO unique durable memories (its one durable hit duplicated a note; detector-C's zero correction-recall reconfirmed D-023), while telemetry-only cz_curate proposed only never-surfaced-lesson obsoletions — zero class overlap. Notes, transcripts-as-failure-miner, and telemetry are three complementary signals; notes own the semantic layer.

Mid-eval the loop's own artifacts exposed two real defects — the phase-default fallback matched a computed "ready" status tables never store (two notes landed phase-less after a skipped transition, itself recorded as C-01), and the digest gauge counted consumed notes ("11 awaiting" right after a dream consumed 11) — both fixed and test-pinned, plus the stale-editable-install version guard fired exactly as designed during release prep. A-003 records the honest measured basis (one build session across five phase contexts; ongoing cadence delegated to the standing-curator loop). Shipped: 1.13.0 single-sourced, suite exit 0 at 1000 collected, origin/main pushed, release-check exit 0 — tag/Release/PyPI deliberately left as the user's irreversible step. O-01/O-02/O-03 all resolved; feat.dream-loop active with its cascade clean.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** When a doc enumerates a code-owned surface (tool lists, version headers, shipped-artifact claims), make the seam EXECUTABLE: a test diffing the doc against the source of truth. README's MCP surface had silently drifted 14 tools behind by 1.12.0; the new test (README backticked names vs TOOL_NAMES + pinned count) and the procedure-version parity test kill the whole drift class that prose sweeps (L-21) only catch once. Dream-sourced: dreamprop:cded8bdd9f36. *(evidence: tests/test_dreams.py::test_readme_mcp_surface_pins_the_full_tool_list; README 48->66 fix in P4)* (promoted 2026-07-24: L-62)
