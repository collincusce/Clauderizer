---
id: subsys.analyze
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.paths
  - subsys.graph
last_verified: 2026-07-25
---

# Analyze

The analyze gate (D-016/D-018): surface the existing invariants and decisions most relevant to a piece of text — and the one-hop graph neighbours it touches but has not connected — for the **agent** to judge contradiction, supersession, or a gap.

## Judgment-based, exactly like cascade

The engine assembles candidates and prompts. It never decides. A machine cannot tell "this decision contradicts D-014" from "this decision refines D-014", and a gate that guessed would either block correct work or wave through a real contradiction. So the output is a ranked shortlist plus a question, and it is advisory — it never blocks a mutation (INVARIANT-05).

## Relevance without embeddings

Ranking is **keyword plus entity-id overlap** (O-01), deliberately dependency-light. An embeddings model would be a large dependency relative to the data it serves — a corpus of a few hundred short markdown entries — and that footprint is a first-class go/no-go axis (L-14), not an afterthought. Results are ranked and capped so the agent sees the right few rather than the whole file.

- **`parse_entries(text, section)`** — parse `### ID — title` blocks into `{id, title, body, status}`. The shared parser under every register read.
- **`rank_relevant(entries, query, limit)`** — the ranker.
- **`scope_filter(entries, scope)`** — D-043 read-time scope filtering. Pure filtering, never shadowing: an entry out of scope is omitted from *this* view, not hidden from the corpus.
- **`analyze(paths, text)`** — the gate itself: the most relevant decisions and invariants for `text`, plus the structural neighbours.
- **`get_entry(paths, id)`** — resolve one entry's full record by id. The `cz_get` read path, and the reason the ranker is a pointer rather than an authority (D-013): what it chooses to render in full does not limit what the agent is allowed to fetch.

## The canonical tokenizer

`_tokens` is the **single** token-splitter definition under `src/` — INVARIANT-09, machine-checked by `tests/test_canonical_tokenizer.py` (exactly one `def _tokens`, import identity, threshold parity; a second fork makes the suite fail).

That invariant exists because a fork was found. Relevance ranking, the abstract index's `token_set`, the write-time near-duplicate advisory, and the corpus-health redundancy metric must all share one definition of "near-duplicate", or the surfaces disagree about what is a duplicate — and the fix was single-sourcing, not tuning a threshold. The threshold itself, `_LESSON_DUP_JACCARD`, is single-sourced here for the same reason.

## Near-duplicates length-normalize

- **`near_duplicate_lessons(paths, text)`** / **`near_duplicate_invariants(paths, text)`** — active entries whose distinctive-token **Jaccard** with `text` clears the threshold.
- **`near_duplicate_gameplan_lessons(paths, gameplan_id, text)`** — the same scan over a gameplan's accumulated numbered lessons (which the abstract index cannot see); the correction-advisory's second corpus (D-074), same tokenizer and threshold.

Jaccard (`|A∩B| / |A∪B|`) rather than a raw overlap count, and the distinction is load-bearing: raw overlap is the *relevance* signal, and a long, entirely distinct entry trips it by sheer size. Length-normalizing is what separates "these say the same thing" from "this one is big".

## The structural complement

- **`adjacent_entities(paths, text)`** — one-hop graph neighbours of what `text` touches but has not named (D-018). "Related but unconnected", found by walking the project graph's own edges, which needs no embeddings either.
- **`suggest_edges(paths, ...)`** — missing `depends_on` edges, the write-side counterpart: the graph knows two entities are related because something links them, so the absent edge is inferable structurally.

## DAG position

Depends on `subsys.paths` and `subsys.graph`. Consumed by `listing` (the shared entry parser and ranker), `mutations` (the write-time near-duplicate advisory), `telemetry` (the redundancy metric), `dreams`, `modernize`, and `ops` (`cz_analyze`, `cz_get`).
