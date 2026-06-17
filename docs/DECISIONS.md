# Decisions

Project-wide architectural decision records (ADRs). Append-only. Numbered `D-NNN`.
Superseded decisions stay in the record with a `Status: superseded` note.

## Decisions

_(Add entries with `cz_add_decision`.)_

### D-001 — Markdown is the source of truth

**Context**: Agents need durable, human-readable, git-diffable memory.
**Decision**: All state lives in markdown; the graph index is a disposable cache rebuilt on demand.
**Consequences**: If index and markdown disagree, markdown wins. No database.

### D-002 — Engine in Python via pipx/uvx

**Context**: Need one broadly-installable engine.
**Decision**: Implement in Python; distribute with pipx/uvx.
**Consequences**: Covers ~99% of dev machines.

### D-003 — Zero-dependency core; mcp optional

**Context**: A drop-in must work with nothing pre-installed.
**Decision**: Core uses stdlib + a vendored frontmatter parser; mcp is an optional extra.
**Consequences**: uvx clauderize init needs nothing; only the server needs the SDK.

### D-004 — Host-language support is profile data

**Context**: Must clauderize Node/Go/Ruby/Python repos.
**Decision**: A profile is a TOML data file of test/build/lint commands; the engine is host-agnostic.
**Consequences**: Adding a language is a new <lang>.toml, not code.

### D-005 — Graph index is JSON, not SQLite

**Context**: Graphs are tens-to-hundreds of nodes.
**Decision**: Cache to a rebuildable index.json.
**Consequences**: Full rescan is milliseconds; no ORM.

### D-006 — Cascade stays judgment-based

**Context**: True affected? calls need human/AI judgment.
**Decision**: The tool finds dependents and marks them needs-review; the agent decides.
**Consequences**: Preserves post-hoc cascade rather than faking automation.

### D-007 — Single mutation path

**Context**: Edits must stay valid and idempotent.
**Decision**: Every structured write routes through markdown/writer.py.
**Consequences**: No tool does a free-form replace.

### D-008 — Engine-regenerated regions in shared docs are marker-delimited

**Context**: cz_write_handoff regenerates PHASE-N-HANDOFF.md by overwriting the whole file, destroying agent enrichment; meanwhile init already merges the CLAUDE.md stanza through marker blocks without clobbering user text.
**Decision**: Any engine-regenerated content inside a document that agents or humans may also edit is delimited by <!-- clauderizer:NAME:start/end --> markers and rewritten via writer.upsert_marker_block. Regeneration replaces only the block; everything outside is preserved byte-for-byte.
**Consequences**: Handoffs become safely enrichable; the CLAUDE.md stanza and handoffs now follow one pattern; future generated regions (e.g. status digests embedded in docs) inherit it.

### D-009 — Cumulative memory gets consolidation pressure, not caps

**Context**: Finding 5: append-only memory + cumulative handoffs grow monotonically; the only pruning was the (obsolete) marker, with nothing driving it and no cross-gameplan continuity for lessons.
**Decision**: Memory stays append-only — no caps, no auto-deletion, no LRU. Counter-pressure is three blessed writes plus visibility: cz_consolidate_lessons (N->1 within a gameplan), cz_promote_lesson (gameplan lesson -> compact project docs/LESSONS.md carried by all future handoffs), and a memory gauge in the status digest that warns past a documented threshold and names the remedies.
**Consequences**: Handoffs can shrink without losing the audit trail; lessons survive gameplan close through deliberate curation rather than bulk carryover; bloat is a visible, nudged state instead of a silent failure mode.

### D-010 — Probes must traverse the consumer's executor or downgrade their claim

**Context**: H-08: doctor certified the SessionStart hook "verified end-to-end via wsl.exe round-trip" while every harness session got no digest — the harness on Windows interposes Git Bash, whose MSYS2 path conversion mangles the shim's argv before wsl.exe spawns. The probe spawned wsl.exe directly and so traversed a leg the consumer never uses (L-09; third instance of the false-green family after H-06 and the D4/spawn-probe composition).
**Decision**: Every launchability/identity check must name the executor it actually traversed, and may claim "end-to-end" only when it traversed the consumer's real leg — for SessionStart hooks on a windows-wsl session host, that means spawning through the harness's executor (Git Bash via WSL interop when present). Where the real leg is untraversable from the checking host, the check reports honest unverifiability (the exit-3 pattern), never a green.
**Consequences**: Doctor's hook-leg check gains an executor-traversing probe and reworded verdicts; the wiring validation matrix (Git Bash, cmd.exe, PowerShell) becomes part of init's spawn-test contract; any future probe design starts from "which leg does the consumer use and can I traverse it".

### D-011 — Push-then-release is enforced by a check, not remembered by a person

**Context**: v0.7.0 and v0.8.0 were both double-claimed in one day by the same mechanism: a GitHub-UI Release tags the REMOTE branch head, and the staged work — including the publish gate that would have caught it — was local-only at that moment (H-07, lesson L-08). The four version registries (source, remote tags, Releases, PyPI) never sync themselves, and uvx-by-name answers from cache.
**Decision**: Ship a release preflight check (O3) that fails red unless: origin/main == the staged release commit; the version is unclaimed across all four registries queried fresh (git tag -l, git ls-remote --tags, Releases API, PyPI index directly); and publish.yml at the staged commit contains the tag==source gate. No tag or Release is cut while the check is red.
**Consequences**: The release ritual becomes mechanical (run the check, then tag/Release); lesson #8's release-flow steps and L-08's sweep stop being prose-only; O4's 1.0 readiness gates get a natural home next to this check; the check itself needs a way to simulate skew in tests (prove the guard fires).

### D-012 — Beta is an evidence claim, not a feature claim — six gates (B1–B6) gate the classifier flip

**Context**: Clauderizer is feature-complete for its core promise and all findings (H-01..H-09) are resolved, but every proof lives on one machine (the windows-wsl:ubuntu reference host), one repo (itself), and one profile (python). CI runs ubuntu-only; the native-win32 hook.cmd wrapper has never been EXECUTED by a test, only rendered; no non-python profile has ever run the live loop; the quickstart has never been walked by a stranger. An external competitive analysis (2026-06-10) independently flagged "Alpha status" as the adoption blocker. Flipping "Development Status :: 3 - Alpha" → "4 - Beta" on vibes would repeat the false-green family (L-02, L-09, D-010) at the product level.
**Decision**: Beta gates, recorded in docs/RELEASING.md beside the 1.0 gates, each naming its evidence artifact: B1 — the current backlog is SHIPPED (0.9.0 live on PyPI, resolving fresh via uvx --refresh, ritual followed with release-check exit 0 before tagging). B2 — the suite is green in CI on ubuntu, macos, AND windows runners × py3.11–3.13, with the win32 cmd wrapper executed for real on a windows runner (not platform-monkeypatched). B3 — G6 closed or honestly amended: native-leg cold-start evidence with the traversed leg named (D-010 wording discipline). B4 — the full loop (init → gameplan → preflight → tracked writes → transition → handoff → digest) proven live on a non-python repo with zero hand-edits, driven through CLI parity (clauderize ops). B5 — the stranger path: quickstart verified end-to-end in a clean environment; upgrade, uninstall, and the trust model (what init writes into .claude/settings.json and why) documented. B6 — the flip itself ships via the release ritual with zero open findings and doctor exit 0 at flip time; the flip version is chosen by a fresh four-registry sweep (L-08), never assumed.
**Consequences**: The classifier line in pyproject.toml may only change in a release whose staged commit satisfies B1–B5, and that release IS B6. The alpha→beta path becomes a series of gameplans (evidence → stranger-readiness → flip) executing these gates; any gate that cannot be met honestly is amended on the record with a named residual rather than waved through — the same exit-3 honesty doctor uses, applied to the product lifecycle.

### D-013 — Semantic recall is an optional extra over a disposable index, never core; a hit is a pointer to canonical markdown, never an authority

**Context**: Clauderizer is excellent at STRUCTURED recall (state, dependency graph, next-phase handoff) and has nothing for FUZZY recall ("where did we decide X and why" across gameplan dirs + HARDENING + LESSONS + chat transcripts). That gap was felt live: reconstructing H-08 evidence meant hand-grepping .jsonl transcripts; the ChatGPT-share extraction was manual. LEANN (arXiv 2506.08276; PyPI `leann`/`leann-core`; MIT; v0.3.7; 12k★) fills it — a low-storage vector index that RECOMPUTES embeddings from a pruned graph instead of persisting them (97% storage savings) and ships its own Claude Code MCP server (`leann_mcp`). But its footprint is the inverse of Clauderizer's load-bearing promise: a native build chain (libomp/boost/protobuf/zeromq) plus an embedding model (sentence-transformers→torch, or an external API, or Ollama). pyproject says ZERO runtime dependencies; the README sells "no database, no lock-in"; TRUST.md certifies the supply chain on exactly that. Putting LEANN in core would detonate the drop-in promise.
**Decision**: Semantic recall ships ONLY as an optional extra (`clauderizer[semantic]`), gated exactly like `[mcp]` is today — the core stays stdlib-only and `uvx --from clauderizer clauderize init` keeps needing nothing else. Three hard invariants: (1) the vector index is a DISPOSABLE, gitignored, rebuilt-from-markdown cache — the same status as `.clauderizer/index.json`; lose it and you re-index, markdown still wins (L-01). (2) A semantic hit is a POINTER back to the canonical markdown (e.g. "see DECISIONS.md D-012"), never a new source of truth; the agent answers FROM the cited file, not from the retrieved chunk — otherwise we reintroduce L-06 (an engine reading its own stale cache as truth). (3) The curated markdown corpus (docs/) and raw chat transcripts are DISTINCT corpora with distinct trust levels: docs/ is memory and is the primary target; transcript "scrollback search" is a labeled convenience that is explicitly NOT memory and does not substitute for recording a lesson (it must not erode D-009's consolidation pressure). Local embeddings are preferred over an external API for the local-first/your-repo posture.
**Consequences**: A new `clauderizer[semantic]` extra and a `cz_recall`-style tool; init optionally builds the index, doctor reports present/stale, the index is gitignored and rebuildable; degrades gracefully (clear "install the semantic extra" message) when absent, like the MCP extra. TRUST.md gains a semantic-layer section (which embedding backend, what data leaves the machine). The feature can be declined at the spike (D1) without cost. Supersedes nothing; extends the D-012 maturity posture (a Beta feature shipped behind an opt-in extra is house-legal).

### D-014 — NO-GO on LEANN for semantic recall — dependency weight disqualifies it as a shippable extra

**Context**: Phase 0 of the semantic-recall gameplan (D1) spiked LEANN's real install on the windows-wsl reference host. Measured friction: `uv tool install leann-core --with leann` auto-resolved a 5.1 GB CUDA torch build (torch 2.12.0+cu130 + ~4 GB NVIDIA runtime) because uv detected the host GPU (RTX 5080); the concurrent WSL filesystem incident left it corrupted (0-byte libtorch_global_deps.so, uv flagged the tool "malformed"). Repairing with `--torch-backend cpu` still produced a 1.6 GB install (torch 2.12.1+cpu 714 MB + sentence-transformers 5.6.0 + transformers + scikit-learn/scipy), plus a ~440 MB facebook/contriever model downloaded from HuggingFace on first `leann build` (default embedding-mode sentence-transformers) — i.e. ~2 GB of mandatory ML stack to semantic-search a 1.2 MB / 134-file corpus (~1700x dependency-to-data ratio). leann/__init__ → api → chat eagerly imports torch at package load, so torch is unavoidable even for search-only use and the embedding-backend choice (D2) cannot slim it. LEANN also carries a native build chain (libomp, boost, protobuf, zeromq).
**Decision**: NO-GO: do not adopt LEANN. The dependency weight is a barrier to entry — especially on laptops — and clashes with Clauderizer's "your memory is just readable files, no database, no lock-in" identity, even as the optional, opt-in extra D-013 scoped. Retrieval quality was deliberately NOT measured: per D1 a no-go on the install-friction axis alone is a cheap, legitimate outcome, and friction was decisive. The spike was torn down to zero footprint (leann-core uv tool uninstalled; ~/leann-spike, ~/.leann, and the contriever model removed; the repo working tree was never touched because the index was built outside the repo and nothing was registered in the tracked .mcp.json).
**Consequences**: The semantic-recall gameplan closes at Phase 0; Phases 1–3 (gated on a GO) are dropped. Clauderizer keeps its structured-recall lane. If semantic recall is revisited, it must use a torch-free, low-footprint engine (e.g. fastembed/ONNX ~tens of MB, or static embeddings like model2vec ~30 MB) or lexical/BM25 over the curated markdown — the corpus has highly distinctive vocabulary (decision/lesson/hardening IDs) that lexical search handles well — evaluated against the same fixed Phase 0 question set. The install-weight-vs-corpus ratio is now an explicit go/no-go axis for any future memory-search dependency.

### D-015 — Discipline gates are always-on, advisory, and judgment-based — no enable/disable config

**Context**: Three spec-kit-borrowed gates (clarify/open-items, exit-criteria, analyze-against-invariants) could each be built as hard blocks with config escape hatches (the existing [rituals] toggle pattern: preflight/cascade/amendments). But a hard-blocking gate REQUIRES an off-switch so it can't trap a session — multiplying knobs — and config-gated discipline is discipline you can silently disable. The user's directive when scoping this work: avoid new config flags; be intelligent instead.
**Decision**: All three gates are ALWAYS active, ADVISORY (they surface findings in the tool result and prompt the agent; they never hard-fail or block a mutation/phase transition), and JUDGMENT-BASED (the engine surfaces the relevant candidates — conflicting invariants, unresolved open items, unchecked exit criteria — and the agent renders the verdict). No new [rituals] flags. The "intelligence" — which invariants are relevant, which open items touch this phase, which criteria map to a measured signal — replaces the config knob. This mirrors cz_cascade's existing contract: "the engine finds and reports; it does not decide."
**Consequences**: No gate can be disabled, and none needs to be (advisory gates aren't disruptive). The agent is the control surface (matches the agent-as-primary-consumer working style). Implementation invests in relevance/surfacing heuristics rather than toggles, so surfacing precision/recall becomes the thing to test — not enable/disable behavior. A gate that would otherwise hard-block instead returns its finding for the agent to resolve, supersede, justify, or revise.

### D-016 — Consistency analysis surfaces candidate invariants/decisions for agent judgment — no contradiction-detection engine

**Context**: spec-kit's /analyze checks a plan against the constitution for drift, leaning on the LLM to judge. Clauderizer records invariants (INVARIANTS.md) and decisions (DECISIONS.md) but has no check that new work contradicts them — verified ABSENT 2026-06-17: cz_cascade walks the DAG for structural dependents only and explicitly "does not pretend to decide whether each dependent is truly affected." The temptation is to build deterministic contradiction-detection in Python, which is brittle and a category error for natural-language invariants.
**Decision**: The analyze gate (a read-op cz_analyze, plus result-enrichment on cz_add_decision) ASSEMBLES the relevant existing invariants/decisions — selected by entity/keyword/scope relevance — and surfaces them for the AGENT to rule on contradiction. The engine never decides; it presents candidates and the agent records the verdict via existing blessed writes (cz_add_correction, supersedes on cz_add_decision, or a revision). Same contract as cz_cascade.
**Consequences**: No NLP/semantic-contradiction code to maintain or mistrust. The hard part is candidate RELEVANCE — surfacing the right few entries, not the whole file — which is where the intelligence lives and what the tests target. Reuses the supersedes field already on cz_add_decision. cz_analyze is a read-op parallel to cz_graph_query/cz_cascade (no mutation).
