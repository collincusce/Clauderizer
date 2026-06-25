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

### D-017 — STORM methods enter as deterministic engine-surfacing plus skill guidance, never as runtime dependencies

**Context**: The user asked whether Clauderizer can adopt methods from Stanford OVAL's STORM/Co-STORM: perspective-guided question asking, simulated multi-perspective interrogation, a "moderator" that surfaces retrieved-but-unused information to expose unknown-unknowns, outline-before-write, and grounded citations. STORM is a heavyweight DSPy + web-retrieval pipeline that synthesizes one big artifact per run. Clauderizer's engine is stdlib-only with ZERO runtime deps (pyproject dependencies=[]), and its design makes the agent the primary consumer: the engine surfaces candidates and the agent judges (D-016, INVARIANT-05). Importing STORM as a library is a non-starter, and STORM is a knowledge-ACQUISITION system whereas Clauderizer is a knowledge-RETENTION/coherence system — so only the reasoning methods transfer, at Clauderizer's authoring moments (gameplan creation, the analyze gate, the write paths).
**Decision**: Adopt STORM's reasoning methods, not its architecture. Each method splits into (a) a deterministic engine-surfacing layer that stays stdlib-only and embedding-free, consistent with D-013/D-014, and (b) a skill-guidance layer where the AGENT performs the perspective-taking and gap-questioning. The engine never calls an LLM; it only makes the agent's reasoning better-aimed. Every addition stays advisory and judgment-based per INVARIANT-05 — it surfaces, it never blocks.
**Consequences**: Zero new runtime dependencies. Perspective-guided planning ships as a rewrite of the clauderizer-new-gameplan skill (plus a multi-LM cost-split note); the gap-finder ships as an additive extension to the analyze gate (D-016); provenance/citation ships as additive optional fields on the write paths. This decision builds on D-013 (semantic recall is an optional extra, never core), D-014 (NO-GO on heavy deps), D-015 (gates are advisory), D-016 (surface candidates, agent decides), and INVARIANT-05. The Co-STORM hierarchical lesson "mind map" is explicitly OUT of scope here because it would change the lesson data model; it is deferred to its own gameplan.

### D-018 — The analyze-gate gap-finder surfaces one-hop graph adjacency, not semantic similarity

**Context**: cz_analyze (D-016) ranks decisions/invariants by keyword + entity-id overlap — first-degree relevance, which is what contradiction/supersession judgment needs. Co-STORM's "moderator" adds a different signal: it surfaces information that is relevant but not yet connected to the current focus, to expose unknown-unknowns (omissions, not conflicts). We want that gap-finding capability, but without embeddings or any new dependency (D-013/D-014) and without adding a second gate or a config flag (D-015).
**Decision**: Extend cz_analyze to also surface an "adjacent" set: take the top-ranked decisions/invariants plus any entity-id mentioned in the query text, walk the project graph ONE hop (dependents + dependencies via the existing graph index/query), and surface the neighbors the agent has NOT already seen — i.e. exclude ids already in the ranked decisions/invariants results and ids already mentioned in the query. This is structural adjacency computed from the graph the engine already maintains; it uses no embeddings and adds no dependency. It is surfaced as an advisory addition, framed as gap-finding ("you are touching X; X is graph-linked to Y and Z, which nothing here has connected to this decision — should it?"), and it never blocks (INVARIANT-05).
**Consequences**: cz_analyze's result gains an `adjacent` list, mirrored through clauderize ops; the analyze prompt is reworded to invite both contradiction-judgment and gap-judgment. No new gate, no enable/disable flag (D-015). Implementation reuses graph/index.py + graph/query.py. Extends D-016 and is consistent with D-013/D-014 (structural, not semantic) and INVARIANT-05 (advisory). The set is honestly empty when the relevant entities have no graph edges — a true negative, not a failure. This is the structural complement to the optional, deferred semantic recall of D-013.

### D-019 — The self-critique gate surfaces a reference-free coverage/coherence rubric assembled from existing signals; the agent grades

**Context**: STORM grades drafts with a reference-free LLM-judge rubric (Interest, Coherence, Relevance, Coverage; Prometheus). The deep-research second-check (task wt5gn6ai2) flagged this as the highest-leverage STORM method not yet imported, and noted it is reference-free, which fits a system with no gold standard. But D-016 and INVARIANT-05 forbid an engine that scores or blocks, and D-013/D-014 forbid embeddings/ML, so a literal LLM-judge engine is out of bounds.
**Decision**: Add a self-critique gate (cz_critique) that, for a target (a phase, the gameplan, or a handoff), deterministically ASSEMBLES a dimensional reference-free rubric from signals the engine already computes - Coverage (unresolved open items, unchecked exit criteria, phases missing outputs/summary), Coherence (drift of planned-while-complete entities, pending cascades, analyze-surfaced contradictions), and Grounding (lessons/decisions lacking provenance/evidence) - and surfaces it with a prompt for the AGENT to grade each dimension. Surface-do-not-decide: it never scores or blocks (INVARIANT-05); stdlib only, no embeddings (it composes status_bundle signals plus the analyze gate). It is a sibling to the analyze gate (D-016), extending the discipline-gate family (D-015).
**Consequences**: New advisory tool cz_critique reachable via MCP and clauderize ops. It reuses existing deterministic signals; the only new computation is detecting entries that lack an evidence marker (ties to D-017 provenance). Reference-free (no gold standard). The agent grades; nothing blocks. Skill guidance points the agent to run it at checkpoints (before completing a phase, before trusting a handoff, at gameplan close). Builds on D-015, D-016, D-017, INVARIANT-05; consistent with D-013/D-014 (no ML).
**Evidence**: deep-research second-check task wt5gn6ai2 (repo HEAD fb951af + NAACL-2024 arXiv 2402.14207 and EMNLP-2024 arXiv 2408.15232): STORM reference-free Prometheus rubric identified as the highest-leverage missed transfer; STORM eval/ code deleted from current main, rubric documented in the paper.

### D-020 — Idea #1 (prefix-stabilize the SessionStart digest, à la Headroom CacheAligner) — DISCARD

**Context**: Headroom's CacheAligner stabilizes message prefixes to win the provider's ~90% cached-prefix read discount. We tested the analog: reorder status_bundle.render_digest so stable scaffold (banner, profile, tools, protocol) leads and volatile state (summary, counts, cascades, open items) trails. Success metric (D1): longest common leading byte-prefix across two sessions' digests, a deterministic proxy since real cache hits are unobservable from the engine (O-01).
**Decision**: DISCARD. The reorder works by the proxy — common prefix rises 65→786 chars (7.3%→78.9%) — but the entire digest is only ~888 chars (~222 tok), so the absolute caching gain is negligible; the digest is rendered once per session (SessionStart hook), so it already sits inside the session's cached growing prefix regardless of internal order; any cross-session benefit is dominated by the large stable system prompt preceding it and depends on unobservable harness placement (O-01); and stable-first ordering harms readability by burying the actionable state (summary + next action) under ~600 chars of boilerplate, including a Tools list the agent already has from the MCP registry. The principle is sound but the surface is too small to be worth the cost.
**Consequences**: No engine change is made; the measurement harness lives under the gameplan's _experiments/ as provenance only. Revisit only if the digest grows large or the harness exposes cache placement. Handoff ordering is deferred to idea #2, where ordering pays off for salience (relevance), not caching.
**Evidence**: docs/gameplans/2026-06-19-headroom-borrowed-ideas/_experiments/measure_prefix.py — digest common-prefix 65→786 chars; full digest ~888 chars (~222 tok); handoff phase1-vs-phase3 prefix 43 chars

### D-021 — Idea #2a (relevance-ranked lesson POINTER in the handoff) — KEEP

**Context**: Headroom's IntelligentContext fits the most important context into a budget by ranked importance. Clauderizer's handoff was cumulative with no ordering; the memory gauge only nags at >12 lessons. We tested surfacing the lessons most relevant to the current phase.
**Decision**: KEEP. handoff.assemble now prepends a 'Most Relevant Lessons for This Phase' block of ranked pointers (top-k via analyze.rank_relevant — keyword + entity-id overlap, no ML, per D-018) ABOVE the unchanged cumulative list, and only when active lessons exceed k (=5). The relevance query is the phase's breakdown block (name+goal+tasks+exit criteria), reusing status_bundle.phase_block. It reorders nothing and drops nothing — pointer-not-authority (D-013); all lessons still propagate (D-009 + the incomplete-propagation anti-pattern).
**Consequences**: Adds focus to large handoffs at zero propagation risk and zero new dependency. subsys.rituals changes (version bump + cascade scheduled for Phase 4). Covered by tests/test_handoff_relevance.py (7 tests; full suite 312 passed, 4 skipped).
**Evidence**: src/clauderizer/rituals/handoff.py (relevant_lesson_pointer, _phase_query, assemble); tests/test_handoff_relevance.py; 312 passed, 4 skipped

### D-022 — Idea #2b (truncate/collapse the cumulative lessons tail in the handoff) — DISCARD

**Context**: The stretch goal was to shrink large handoffs by replacing low-relevance lessons with a count + pointer (a budget cap on the cumulative list).
**Decision**: DISCARD. Truncating the cumulative list reintroduces exactly the incomplete-lesson-propagation anti-pattern the self-contained handoff exists to prevent, and contradicts D-009 (consolidation pressure, NOT caps). The asymmetry is bad: truncation saves only a few hundred tokens per handoff but risks a phase repeating an already-solved mistake. Size control already has a SAFE lever — cz_consolidate_lessons (synthesis, not deletion) — and 2a already delivers the focus benefit without removal. Truncation is redundant and strictly riskier.
**Consequences**: The handoff always carries every active lesson; focus comes from 2a's pointer, size control from consolidation. No code added for 2b.
**Evidence**: handoff.py module docstring (incomplete-propagation anti-pattern); D-009; cz_consolidate_lessons is the existing safe size lever

### D-023 — Idea #3 (failure-miner, à la Headroom `headroom learn`) — KEEP

**Context**: All Clauderizer learning is manual — the agent must remember cz_add_lesson/cz_add_correction, so lessons are lost when it doesn't volunteer them. Headroom's `headroom learn` mines past sessions for failures and writes fixes. We tested a deterministic, stdlib-only analog over real Claude Code transcripts.
**Decision**: KEEP, as an invoked, read-only, propose-only module (src/clauderizer/learn.py). It scans session JSONL for (A) a tool error then a same-tool success within a window, (B) pytest fail→pass, (C) a short explicit user correction, and emits DRAFT cz_add_correction args for the agent to confirm. is_error is unreliable for shell failures, so errors are detected by content signatures; benign search-tool 'errors' and tool-protocol hiccups are denied to protect precision. It writes nothing and adds no enable/disable flag — being invoked is what makes it opt-in.
**Consequences**: Converts capture from 'agent must volunteer' to 'system surfaces candidates' without violating the advisory-gate (D-015/INVARIANT-05) or append-only (INVARIANT-03). Precision ~80% on a labeled sample; 2/2 dogfood; rediscovers real adopted lessons (H-08 shim, env/test failures). Detector C had 0 recall on this corpus (kept for precision). Phase 4 wires the cz_mine_failures tool, bumps subsys.mcp-server/mutations, and cascades.
**Evidence**: src/clauderizer/learn.py; tests/test_failure_miner.py (8 tests); _experiments/run_miner.py over 11 real transcripts → 62 proposals; 320 passed, 4 skipped

### D-024 — Preflight blocks on a missing-but-expected phase handoff (handoff_presence gate)

**Context**: The completed gameplan 2026-06-19-headroom-borrowed-ideas closed cleanly — cz_critique reported 0 gaps and cz_preflight was green — while its PHASE-STATUS / CHAT-HANDOFF-INDEX tables linked 5 handoff files (PHASE-0..4) that were never written. The run was effectively single-session and pulled phase context via the read-only cz_next_phase_context, never calling cz_write_handoff, so handoffs/ stayed empty while the scaffolded links dangled. Nothing in the verify/close flow detected the mismatch.
**Decision**: Add a preflight check `handoff_presence`. For each phase the table implies a handoff should exist — the first phase, or any phase whose predecessor is COMPLETE (mirroring exactly when handoffs are written: phase 0 at scaffold, phase N at phase N-1's close) — verify handoffs/PHASE-N-HANDOFF.md is on disk. A missing one FAILS preflight (blocking: "write it via cz_write_handoff before proceeding"). It lives in cz_preflight (the gate that is meant to block), NOT in cz_critique/cz_analyze, which stay advisory by INVARIANT-05. Listing it in preflight_advisory downgrades the fail to a warning for intentionally single-session gameplans.
**Consequences**: A gameplan can no longer close or continue with undetected dangling handoff links. Future not-started phases are NOT required, so a healthy mid-flight gameplan produces no false positive. Enabled in the standard + saas size presets and this repo's config; 7 new tests. The running MCP server must restart to load the new check (engine_stale until then).
**Evidence**: src/clauderizer/rituals/preflight.py (_missing_expected_handoffs + handoff_presence check); tests/test_rituals.py (7 tests); proven on the real gameplan — 5 missing handoffs flagged, passed=False — in the 2026-06-19 verification session

### D-025 — Hooks are event-dispatched through one entry; every event handler is read-only and exits 0

**Context**: kimi-code and Claude Code both expose a multi-event hook surface (SessionStart, UserPromptSubmit, PreCompact, PostCompact, ...) with the same contract: JSON on stdin (incl. hook_event_name), stdout-on-exit-0 added to context. Clauderizer wired only SessionStart (clauderizer-hook -> hook.sessionstart:main), which reads no stdin. We want to surface durable-memory context at more lifecycle points without endangering the heavily-hardened SessionStart leg (H-01/H-08/H-09) or violating INVARIANT-05.
**Decision**: Generalize the single hook entry point to read stdin JSON and dispatch on hook_event_name, defaulting to the SessionStart digest when stdin is absent/unparseable (backward compatible, preserves the --version/--help probe path). Every event handler is READ-ONLY (no mutations inside a hook) and ALWAYS exits 0. New events reuse the existing wrapper and hosts.py wiring machinery unchanged; the SessionStart leg is not refactored.
**Consequences**: One code path for all hook events; adding an event is a handler + a registration, not new wrapper/probe plumbing. Read-only + exit-0 keeps hooks safe to fire anywhere. Handlers stay quiet-when-empty to avoid context noise. Whether a handler's stdout actually reaches context is the host's contract, not ours (Claude Code drops PreCompact/PostCompact stdout; kimi injects all) — so wiring is per-host.
**Evidence**: Claude Code hooks ref (24 events; SessionStart source=compact; PreCompact/PostCompact stdout NOT to context; UserPromptSubmit/SessionStart stdout->additionalContext). kimi-cli hooks doc (13 events; exit-0 stdout added to context for all). src/clauderizer/hook/sessionstart.py; src/clauderizer/hosts.py render_hook_wrapper.

### D-026 — Empirical gain-gate: features must prove measurable benefit or they do not land

**Context**: This initiative adds and removes memory features and must guarantee each change is a net gain (user directive). Research shows memory features can be net-negative, so benefit cannot be assumed.
**Decision**: Every feature or removal must pass a Hybrid gate: a deterministic benchmark (repeatable, in CI) AND, for behavioral effects, a seeded agent-eval (focused-vs-full ablation). A change that fails its pre-registered hypothesis/metric is parked or reverted and recorded as a finding - never merged on faith.
**Consequences**: Phase 0 builds the eval harness before any feature ships; each feature phase pre-registers a hypothesis + metric; parked features are valid, recorded outcomes.
**Evidence**: LongMemEval ICLR 2025 (arxiv 2410.10813); user directive to guarantee benefit gains from each feature.

### D-027 — Trim-first: injected-context length and noise degrade the agent; prefer focused injection over more memory

**Context**: The naive assumption that more remembered context is better is contradicted by replicated peer-reviewed evidence on long-context degradation.
**Decision**: Treat injected-context size as a cost to minimize. Inject focused, front-loaded, ranked memory; gate and shrink the always-on digest, the cumulative handoff, and the lesson roll-up. The goal is injecting the right focused tokens, not remembering the most.
**Consequences**: The context-rot trim phase is a first-class high-priority removal phase; any always-injected addition (e.g. a steering doc) must justify its token cost against this.
**Evidence**: EMNLP 2025 context-length-alone-hurts (arxiv 2510.05381); TACL 2024 lost-in-the-middle (arxiv 2307.03172); Chroma Context Rot; LongMemEval focused>full (arxiv 2410.10813).

### D-028 — Three orthogonal host axes: session-host x host-profile x host-target — never conflate

**Context**: Clauderizer already has two host-ish concepts: 'session host' (where commands run: native vs windows-wsl:<distro>, in hosts.py) and 'host profile' (repo language -> build/test commands: python/node/go/ruby/generic; D-004 says host-language is profile data). Cross-tool support introduces a third: which agent tool/harness drives the session (Claude Code, Cursor, Copilot, ...). The analyze gate flagged the collision risk.
**Decision**: Treat 'host target' (the agent tool) as a NEW first-class axis, orthogonal to session-host and host-profile. A HostTarget capability descriptor (hooks? mcp-tools? mcp-resource-autoload? mcp-prompts? rules-file format and location? slash-commands?) is distinct data from the language profile and the execution host. No code path may infer one axis from another.
**Consequences**: Config, capability detection, and emitters key on host-target; preflight/profiles stay language-keyed; wiring/shimming stays session-host-keyed. Prevents a class of mis-detection bugs but adds a third dimension to the test matrix.
**Evidence**: cz_analyze surfaced D-004; current hosts.py (session host) and profiles/ (language) are the two existing axes
**Status**: active (2026-06-21)

### D-029 — AGENTS.md + MCP is the universal substrate; Claude Code hooks are a premium enforcement TIER, not a dependency

**Context**: Deep research: the ecosystem is converging on AGENTS.md + MCP under the Linux Foundation Agentic AI Foundation (Anthropic MCP + OpenAI AGENTS.md + Block goose, 2025-12-09); AGENTS.md is read by ~23 tools across 60k+ repos. Claude Code hooks deterministically inject context but have no clean cross-host equivalent; MCP Resources/Prompts are optional, per-connection-negotiated, and Prompts are user-controlled by design.
**Decision**: Standardize the portable contract on AGENTS.md (instructions) + MCP tools (the cz_* surface). Claude Code keeps CLAUDE.md (which imports/symlinks AGENTS.md) and its hooks as the top, ENFORCED injection tier. Hook-driven auto-injection is demoted from a hard requirement to a Claude-Code/kimi-only enhancement; everything below degrades gracefully.
**Consequences**: Most hosts become reachable with little or no bespoke code. Non-Claude hosts get a best-effort (suggested, not enforced) experience. Betting with the consolidating standard. Claude Code experience is unchanged.
**Evidence**: Linux Foundation AAIF announcement 2025-12-09; agents.md; MCP spec rev 2025-11-25
**Status**: active (2026-06-21)

### D-030 — Injection-parity ladder: hook -> auto-resource -> prompt -> AGENTS.md floor, graceful degradation, single delivery

**Context**: No portable equivalent to Claude Code's deterministic hook injection exists. Different hosts support different MCP primitives and capability is a moving target (Cursor added Resources in v1.6, Sept 2025).
**Decision**: Every host gets the BEST injection tier it supports and never less than the Tier-4 AGENTS.md 'call cz_status first' floor: Tier1 lifecycle hook (Claude Code, kimi) -> Tier2 auto-loaded MCP resource -> Tier3 MCP prompt -> Tier4 floor instruction. Capability is re-probed at session start; any mismatch downgrades safely toward the floor. Status is delivered to the model at most once per session across all active tiers (dedup via the P1 in-memory signal), honoring trim-first.
**Consequences**: Uniform mental model and predictable degradation; no double-injection bloat. Requires per-host capability detection plus a session-scoped delivery signal.
**Evidence**: deep research dimensions 2-3; cz_analyze surfaced D-027 (trim-first)
**Superseded by**: D-034 (2026-06-21)
**Status**: superseded (2026-06-21)

### D-031 — Config-safety: global config -> guide-only; project config -> non-destructive merge; never commit machine paths

**Context**: Writing wiring into 13 hosts multiplies blast radius. kimi already gets a guide (Clauderizer never edits global ~/.kimi/config.toml). init currently leaks absolute venv / wsl.exe paths into .mcp.json / .claude/settings.json. Re-running init for a second host can clobber the first's registration (top config-safety risk).
**Decision**: Classify every host on (1) project-level vs global config location and (2) MCP-capable vs absent. Emitter rules: a host whose config is GLOBAL/user-level is GUIDE-ONLY (never auto-edited); project-level config is written via non-destructive marker-block/structured merge that preserves co-resident hosts' keys; any wiring whose command contains an absolute user/venv/wsl.exe path is guide-only or warned, never silently committed. A `clauderize uninstall [--host]` must exist before any host ships.
**Consequences**: No silent data loss across co-resident hosts; no machine-specific paths in shared repos; reversible installs. More per-host classification work in P0/P4.
**Evidence**: config-safety lens; init.py _register_mcp/_resolve_invocation; kimi guide precedent
**Status**: active (2026-06-21)

### D-032 — Release gate = wiring-contract (well-formed + server launches + simulator round-trips), not 'tested on 13 live hosts'

**Context**: 11 of 13 target hosts are proprietary and cannot be installed/run headless in CI. Proving the host actually READS the emitted config and injects context is irreducibly manual for those. Proving model-agnosticism live needs a paid multi-model fleet.
**Decision**: The automated release gate verifies the WIRING CONTRACT only: emitted config is well-formed and path-safe, the MCP server launches, and an in-process host-simulator stub round-trips cz_status. CONSUMPTION PROOF (a real host reads it and injects) is a manual pre-GA spot-check on 2-3 representative hosts, documented as such. The model-agnostic claim is defined narrowly — the shared surface emits no Claude-specific syntax; any model that can call MCP tools or read AGENTS.md can participate — and verified by static analysis (no model-specific tokens), with live cross-model smoke tests reserved for a manual checklist.
**Consequences**: A credible, achievable green gate that does not overclaim. The README/claims must state the wiring-contract-vs-consumption distinction honestly.
**Evidence**: verification lens; L-20; doctor verify_wiring/verify_hook_wiring
**Status**: active (2026-06-21)

### D-033 — Ship cross-host support incrementally per tier (Floor Release first); fix beta-gate impact up front

**Context**: Seven-plus phases imply a big-bang, but subsystems are independently versioned and the floor hosts are claimable after only P0-P2. D-012: Beta is an evidence claim gated by B1-B6 — adding 13 hosts could either hollow the Beta claim or trigger a gate explosion.
**Decision**: Release incrementally per injection tier: cut a 'Floor Release' once P0-P2 land (AGENTS.md+MCP-native hosts at Tier 4), then middle-tier (P3) and bespoke (P5) hosts as they verify. Up front, decide whether cross-host coverage adds a new Beta evidence gate or is covered by the P6 wiring-contract CI, and record the answer in the parity contract so release criteria are fixed before the work starts. Define a subsystem version-coordination policy (or a doctor coherence check) so users never get mismatched scaffold/mcp-server host support.
**Consequences**: Value ships early; long-tail bespoke hosts do not block release; Beta stays an honest evidence claim. Requires a per-tier release checklist.
**Evidence**: release lens; D-012; independently-versioned subsystems (scaffold 0.7.0, mcp-server 0.5.0)
**Status**: active (2026-06-21)

### D-034 — Revised injection-parity ladder: Tier-1 hooks broadly reachable, Tier-2 auto-resource retired, server-side bootstrap is the hook-less automatic fallback

**Context**: Phase 0 primary-source verification (docs/CROSS-HOST.md) corrected the two premises behind the original ladder D-030: hooks are NOT Claude-only (C-01) and no host auto-loads MCP resources (C-02).
**Decision**: The ladder is Tier 1 lifecycle hook injects status (Claude Code, kimi, Copilot, Codex, Gemini, Windsurf, Cline[POSIX], Amp, possibly Cursor) -> Tier 3 MCP prompt as /cz-status slash command (Cursor, Copilot, Continue, Gemini, Zed) -> Tier 4 instructions-file call-cz_status-first floor (AGENTS.md where native, else the host native file: .continue/rules, GEMINI.md). Tier 2 (auto-loaded resource) is RETIRED. The P7 server-side bootstrap (status on first read-like tool result) is the only AUTOMATIC delivery for hook-less hosts (Continue, Zed, Cursor-if-governance) and is promoted from optional polish to primary fallback. Deliver at most once per session (INVARIANT-08).
**Consequences**: P3 drops the auto-resource tier (prompts + routing only). P7 rises in importance. The floor emitter writes per-host native instructions for the 3 non-AGENTS.md hosts. Tier-1 parity is achievable on ~9 hosts, far beyond the original 2.
**Supersedes**: D-030
**Evidence**: docs/CROSS-HOST.md sections 3-5; per-host primary docs verified 2026-06-21
**Status**: active (2026-06-21)

### D-035 — Keep single-source dual-write of the stanza (CLAUDE.md + AGENTS.md); reject symlink and @import

**Context**: P2 exit criteria proposed CLAUDE.md imports/symlinks AGENTS.md so there is one rendered copy. Two facts make that the wrong call: Clauderizer is dogfooded on Windows/WSL where symlinks are fragile/unreliable, and a CLAUDE.md @AGENTS.md import adds a Claude-Code-parity dependency (the import must resolve) for no functional gain over what already exists.
**Decision**: Keep the existing single-source dual-write: one template (src/clauderizer/templates/claude_stanza.md) is rendered by init into BOTH CLAUDE.md and AGENTS.md within marker blocks. This gives the anti-drift property the criterion wanted (one source, L-16 - the renders cannot diverge) without a symlink (Windows-fragile) or an @import (parity-risky). AGENTS.md is the portable carrier every non-Claude host reads; CLAUDE.md is its Claude Code twin.
**Consequences**: Two rendered copies exist but cannot drift (regenerated together from one source). No Windows symlink fragility, no import-resolution dependency. The host-neutral Tier-4 floor lives in the one template and reaches every host.
**Evidence**: docs/CROSS-HOST.md; INVARIANT-07; L-16; Windows/WSL dogfood host
**Status**: active (2026-06-21)

### D-036 — Documentation is a dual-audience (agent + human), drift-free, in-phase deliverable

**Context**: The stranger dogfood evidenced concrete doc gaps — F4 (ops surface undocumented), F9/F11 (undocumented args), F13 (thin empty-project digest) — and L-21 records that reference docs drift together. The project had trended agent-first (the CLAUDE.md stanza, the cz_* tool descriptions). User feedback (2026-06-23, from their own testing): docs are not diligent enough and must be human-usable too.
**Decision**: Docs serve BOTH the agent and a human reader (someone evaluating/adopting Clauderizer). Diligence = (1) every user-visible change ships its doc update IN the same phase that makes it; (2) reference docs are swept as a SET on any tool/ops/taxonomy change (L-21); (3) a human-usable layer is maintained — quickstart, a command + `ops` reference, troubleshooting — and verified by a fresh-human-reader pass with no source access. This binds every phase of the dogfood-followups gameplan and amends (does not contradict) the agent-primary working stance.
**Consequences**: More doc work per change, but a human can adopt without reading source and the drift class of findings shrinks. Strictly additive to INVARIANT-07 (the Claude Code / agent experience never regresses).
**Evidence**: docs/gameplans/2026-06-23-stranger-readiness-dogfood/_harness/friction-log.md (F4/F9/F11/F13); L-21
**Superseded by**: D-037 (2026-06-23)
**Status**: superseded (2026-06-23)

### D-037 — Docs are written for humans in plain prose; there are no agent-only or agent-styled docs

**Context**: User correction (2026-06-23): D-036's "dual-audience (agent + human)" framing misread the feedback. The user was not asking for a separate agent doc tier — they observed that the documentation the agent produces reads like an agent wrote it (shorthand, F-/H-/D- codes, internal jargon) instead of clear human prose.
**Decision**: All documentation is written for a HUMAN reader in plain, readable prose — quickstart, command/ops reference, troubleshooting. There are no agent-only or agent-styled docs. Agents take their machine contract from the MCP tool schemas and cz_* descriptions (the MCP-native design), so the prose docs are simply human docs. Diligence stands: no drift (reference docs swept as a set, L-21) and every user-visible change documented in the phase that ships it.
**Consequences**: P7 is a human-readability sweep, not a "second audience" pass. The author must watch their own style — no F-/H-/D- shorthand or internal jargon in user-facing docs. Strictly additive to the MCP-native agent surface (no regression, INVARIANT-07).
**Supersedes**: D-036
**Evidence**: supersedes D-036; user correction 2026-06-23
**Superseded by**: D-038 (2026-06-23)
**Status**: superseded (2026-06-23)

### D-038 — Docs: human-first prose with slick machine affordances; the agent's source of truth, refreshed at every close-out and handoff

**Context**: Refines D-037 after further user guidance (2026-06-23). Two clarifications: (1) machine-parseable affordances are welcome, not banned — the objection was agent JARGON in the human-visible prose, not structure that helps the agent parse; (2) docs drive the agent as the canonical source of truth (INVARIANT-01), so keeping them current is load-bearing, with gameplan close-outs and handoffs as the key refresh moments.
**Decision**: Documentation is written human-first: plain readable prose for a person, no agent jargon or codes in the visible text. Machine-parseable affordances — HTML comments, frontmatter, stable headings/anchors (the patterns the engine already uses, e.g. the handoff marker block) — are welcome but kept SLICK and unobtrusive, never cluttering the human reading experience. Because docs are the agent's canonical source of truth (INVARIANT-01), they must be kept current and refreshed at every gameplan close-out and handoff; drift is a defect.
**Consequences**: Humans read clean prose while the agent still gets reliable structure to parse. Close-out and handoff gain an explicit doc-freshness step. Consolidates the docs philosophy into one active decision (supersedes D-037, which superseded the dual-audience D-036).
**Supersedes**: D-037
**Evidence**: supersedes D-037; user guidance 2026-06-23
**Status**: active (2026-06-23)

### D-039 — Two documentation layers — agent working-memory vs human product docs; never conflate them

**Context**: User confirmed (2026-06-23) the distinction behind the docs guidance and worries past gameplans conflated "dogfooding" (using Clauderizer to manage work) with "updating the engine" (changing Clauderizer's code + its human-facing product docs). Complements D-038 (which governs HOW the human docs are written).
**Decision**: Two layers, two consumers. (1) WORKING-MEMORY layer — gameplans, phase handoffs, the cz_* memory (decisions/invariants/lessons/hardening/friction). The AGENT is the consumer; structured density + machine affordances (D-NNN / F-NN codes, marker blocks, frontmatter) are CORRECT here. (2) PRODUCT layer — Clauderizer's code plus the docs a HUMAN reads to evaluate/adopt/use it: README, GAMEPLAN-PROCEDURE.md, `clauderize --help`, the tool descriptions, TRUST/UPGRADING/SECURITY/TROUBLESHOOTING. D-038's human-readability applies HERE. Rules: never write product docs in working-memory shorthand; don't fret over the human-readability of working-memory artifacts; a "dogfooding" request's deliverable is human-readable findings; an "update-the-engine" request's deliverable includes fresh, human-readable product docs.
**Consequences**: P7 is scoped to the product layer. The dense gameplan/handoff artifacts are correct-for-their-layer, not a docs defect. A future initiative will audit past gameplans for where the two were conflated, clarify, and rectify (recorded as a backlog note + a next-session prompt).
**Evidence**: complements D-038; user confirmation 2026-06-23
**Status**: active (2026-06-23)

### D-040 — Fast retrieval is a deterministic abstract index plus addressable per-entry fetch; embedding/LLM extraction declined

**Context**: The agent must load a whole corpus file (DECISIONS/LESSONS/INVARIANTS/HARDENING) to read one entry: cz_analyze returns titles-only (analyze.py:118) and there is no per-entry getter in the tool surface (confirmed — no cz_get in ops.REGISTRY). That forces whole-file reads to resolve a single pointer. Two surveyed systems (SimpleMem, Hyper-Extract, reviewed 2026-06-25) solve adjacent recall problems with embeddings + vector stores + per-document LLM extraction. The goal is to make the agent FASTER and CHEAPER on tokens without losing accuracy, as a COMPLEMENT to the thorough markdown tier — i.e. quick indexing, not richer recall.
**Decision**: Add a deterministic, disposable, per-entry "abstract index" over the append-only corpus, plus an addressable fetch cz_get(id) and an `abstract` field on cz_analyze hits. A retrieval returns abstract + file:line anchor; the full body is fetched only on demand. No embeddings, no LLM, zero new runtime dependencies — borrow the idea deterministically (D-017), never the stack. Markdown stays canonical; the index is a derived cache rebuilt from markdown (INVARIANT-01). This EXTENDS D-013 (a hit is a pointer to canonical markdown, never an authority) and REAFFIRMS D-014's NO-GO on heavyweight ML retrieval for SimpleMem/Hyper-Extract-style stacks.
**Consequences**: Gains: lower tokens-injected-per-lookup; the agent answers from abstracts without a round-trip; stays drop-in and zero-dep. Costs: a SECOND derived cache to keep fresh (concurrency, schema-version, freshness); a DUAL parser (corpus em-dash `### D-001 —` entries vs the LESSONS `**N.**` numbered format). Must be empirically gain-gated before any consumer ships (D-026); a DISCARD verdict is a valid, successful outcome (L-32).
**Evidence**: analyze.py:118 (titles-only), analyze.py:324-327 (full_text whole-file loads), ops.py REGISTRY has no per-entry getter; systems surveyed 2026-06-25 (github SimpleMem, Hyper-Extract)
**Status**: active (2026-06-25)
