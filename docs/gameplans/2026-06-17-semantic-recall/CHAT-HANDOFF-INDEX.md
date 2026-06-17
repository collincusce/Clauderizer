# Chat Handoff Index — semantic-recall

> Last updated: 2026-06-17
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 266

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
| 0 | Peer-server spike: prove retrieval quality and install friction before any engine code | ✅ COMPLETE | 2026-06-17 | 2026-06-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | The optional extra: clauderizer[semantic] + cz_recall over curated docs/ | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Scrollback search: transcripts as a distinct, explicitly non-authoritative layer | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Dogfood consolidation, trust/docs, and the 1.0-implications call | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-17

Phase 0 ran the LEANN peer-server spike (D1) on the windows-wsl reference host and resolved to a NO-GO on the install-friction axis alone (see D-014). The user's prior `uv tool install leann-core --with leann` had resolved to a 5.1 GB CUDA torch build (uv detected the RTX 5080) and was left corrupted by the concurrent WSL filesystem incident (0-byte libtorch_global_deps.so; uv flagged the tool "malformed"). Repairing with `--torch-backend cpu` produced a still-heavy 1.6 GB install (torch 714 MB + sentence-transformers/transformers/sklearn/scipy), with a further ~440 MB facebook/contriever model downloaded on first build — roughly 2 GB of mandatory ML stack to semantic-search a 1.2 MB / 134-file corpus. leann eagerly imports torch at package load, so the embedding-backend choice (D2) cannot avoid it. The user judged this a barrier to entry (especially on laptops) that clashes with Clauderizer's files-not-databases identity, even as an optional extra.

Retrieval quality was deliberately not measured: a no-go on friction was decisive and cheap per D1. The spike was fully torn down to zero footprint (tool uninstalled; ~/leann-spike, ~/.leann, and the contriever model removed; repo working tree never touched — the index was built outside the repo and nothing was registered in the tracked .mcp.json). The gameplan closes at Phase 0; Phases 1–3 (gated on a GO) are dropped. If semantic recall is revisited, the path is a torch-free, low-footprint engine (fastembed/ONNX, static embeddings like model2vec) or lexical/BM25 over the curated markdown, evaluated against the same fixed question set.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** A dependency's weight relative to the data it serves is a first-class go/no-go axis that can disqualify it before functional quality is even measured. The LEANN spike was a no-go on install friction alone — ~2 GB of torch-based ML stack (1.6 GB CPU / 5.1 GB CUDA install + 440 MB model), with torch eagerly imported so no backend choice could slim it, to search 1.2 MB of markdown. For a tool whose identity is "memory is just readable files, no lock-in," that ratio clashes with the product posture even as an optional extra. Spike the real install early (sibling to L-12/L-13's "prove the real artifact on the real target"), measure weight-vs-value explicitly, and when the ratio is absurd, stop — a cheap no-go beats a heavy integration. (promoted 2026-06-17: L-14)
