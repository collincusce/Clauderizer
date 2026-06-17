# semantic-recall Gameplan

> Created: 2026-06-17
> Status: Planning
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

### D1 — Spike first: a peer-server go/no-go on retrieval quality AND install friction gates all engine work

**Context**: LEANN ships its own MCP server, so the cheapest possible test of the whole idea needs ZERO Clauderizer code: run `leann_mcp` as a peer Claude Code MCP server pointed at docs/, and just use it. Two things can kill the value before any integration is worth building — retrieval quality (does semantic search over this corpus actually return the right markdown?) and install friction (does the native build chain even build cleanly on the windows-wsl reference host we fought all session?). L-12/L-13 say prove the real artifact on the real target before designing around it.
**Decision**: Phase 0 is a peer-server spike with an explicit, recorded go/no-go BEFORE any `clauderizer[semantic]` code exists. Success is judged on a FIXED question set drawn from this project's real retrieval needs (seeded in the Phase 0 handoff), each with the markdown it should surface — pass = the right file in the top hits, in tolerable latency, with an install a stranger could reproduce. No-go is a legitimate, cheap outcome: the gameplan closes at Phase 0 with the evidence, and Clauderizer keeps its structured-recall lane. Dogfooding happens THROUGH this peer server — the next session runs the spike and uses it live while working.
**Consequences**: Phase 0 is independent (no engine deps); Phases 1–3 depend on a GO. The question set becomes the retrieval regression fixture if the feature proceeds. Install-friction findings feed TRUST.md and the eventual extra's docs. A no-go costs only the spike, not an integration.

### D2 — Local embeddings by default; an external API is an explicit, documented opt-in

**Context**: LEANN takes embeddings from sentence-transformers (local, pulls torch — gigabytes, CPU-slow-or-GPU), an OpenAI-compatible API (light client, but every indexed decision/lesson/transcript leaves the machine), or Ollama (local daemon, middle ground). For a tool whose entire pitch is "your memory is just readable files in your repo — no database, no lock-in," silently shipping the corpus to a third-party API is a posture clash, not a perf detail.
**Decision**: Default to LOCAL embeddings (sentence-transformers or Ollama, decided by what installs cleanly in the Phase 0 spike on the reference host). An external embedding API is allowed but only as an explicit, opt-in config with a one-line consequence stated at the point of choice ("this sends your indexed docs/ and transcripts to <provider>"). TRUST.md must state, for whatever default ships, exactly what data leaves the machine and what does not.
**Consequences**: The spike measures local-embedding install weight and latency as a first-class result (it may be the deciding install-friction factor). The eventual extra's default is privacy-preserving; the API path is documented, never silent. TRUST.md's new semantic-layer section is written against the actual default.

## Open Items

_(O1, O2, … — blockers and cross-phase questions.)_

## Phase Breakdown

### Phase 0: Peer-server spike: prove retrieval quality and install friction before any engine code

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable assertion)_

### Phase 1: The optional extra: clauderizer[semantic] + cz_recall over curated docs/

**Goal**: Turn the spike into a first-class, lifecycle-managed capability per D-013 — IF Phase 0 was a GO. Add a `clauderizer[semantic]` optional-dependency group (LEANN + the chosen local embedding backend); a `cz_recall(query, k)` op in the shared registry (so MCP and `clauderize ops` both expose it, L-05) that returns POINTER-back hits — file path + anchor + snippet, the canonical markdown being the answer, never the chunk. The index lives gitignored under .clauderizer/ (disposable cache, rebuilt from docs/ — same status as index.json); `clauderize reindex` (or a new subcommand) builds/refreshes it; init builds it when the extra is present; doctor reports present/stale/absent and degrades with a clear "install clauderizer[semantic]" message when the extra is missing (exactly like the MCP-absent path). Exit criteria: with the extra installed, cz_recall returns the right markdown for the Phase 0 question set; with it absent, the core suite is fully green and every semantic surface degrades gracefully (no import errors, honest "not installed" messaging); the index is gitignored and rebuilds from markdown; tests cover both present and absent.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 2: Scrollback search: transcripts as a distinct, explicitly non-authoritative layer

**Goal**: Add chat/response-history search as a SEPARATE corpus from curated memory, per D-013's invariant (3) — without eroding D-009's consolidation pressure. A distinct surface (e.g. cz_recall with a `corpus="scrollback"` argument, or a separate cz_search_history op) over the session .jsonl transcripts, with results LABELED as scrollback — raw history, not memory — and copy that steers toward recording a lesson when a hit reveals an undistilled decision. Transcript indexing is opt-in within the extra (the firehose is large and noisy); the curated-docs index from Phase 1 stays the default and the primary. Exit criteria: scrollback search returns the right transcript span for a "what exactly did we do when X" query from this session's history; results are visibly distinguished from curated-memory hits and never presented as authoritative; the curated path is unaffected; the consolidation nudge/discipline is documented so easy raw recall does not quietly replace lesson-writing.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 3: Dogfood consolidation, trust/docs, and the 1.0-implications call

**Goal**: Land the feature as something a stranger can trust and a maintainer can reason about. Capture the live dogfooding evidence (the next sessions' real cz_recall usage across the existing gameplan corpus) as outputs; write TRUST.md's semantic-layer section per D-013/D2 (which embedding backend ships default, what data leaves the machine, the index's disposable status); add the README/docs (the extra, cz_recall, the pointer-back contract, the curated-vs-scrollback distinction); and make the explicit call on whether semantic recall is a 1.0 gate or a post-1.0 optional (it is an opt-in extra, so it should NOT block the 1.0 evidence review — record that reasoning). Exit criteria: TRUST.md and README updated and code-accurate (claims cite implementation, per the G7 discipline); dogfooding evidence recorded; the 1.0-relationship decision written; suite green; close-out ready.
**Depends on**: 0, 1, 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_
