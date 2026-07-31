---
id: subsys.listing
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.paths
  - subsys.analyze
  - subsys.contract
last_verified: 2026-07-25
---

# Listing

The read side of every append-only register.

## The asymmetry it fixes

The write side of each register predates its read side by a long way. At 1.11.0 the ops registry held **33 write ops against 15 reads**, and every register was reachable only by knowing an id in advance (`cz_get`) or not at all. An agent could record a decision and then have no way to ask what decisions existed — memory you can only write to is a log, not memory.

This module is that read side: pure parsers over the same markdown the mutation layer writes.

## Single-sourced grammars

Each parser single-sources its grammar **from the writer that emits it**. That is the property that keeps the two halves from drifting: a change to how `add_decision` renders a supersession link is a change the decision reader sees, because they share the definition rather than each carrying a copy. The alternative — a reader that re-implements the writer's format from observation — is a reader that silently stops matching after the next format change, and nothing fails until someone notices the list went empty.

## The reads

- **`open_items`**, **`decisions`**, **`invariants`**, **`findings`**, **`lessons`**, **`corrections`**, **`amendments`** — the registers as structured records. `decisions` carries supersession links **both ways** (what this supersedes, and what supersedes it), `invariants` carries scope and audience, `findings` is the hardening register (H-NN), and `lessons` carries curation state — active, obsolete, or promoted.
- **`phase_detail`** — every gameplan's full phase table with per-phase exit-criteria state, approvals, dates and goals. Not just the focus gameplan: the read behind portfolio drill-in and reconciliation.
- **`cascade_reports`** — cascade reports as data: the trigger and the per-dependent verdicts, including the ones still pending.
- **`docs_index`** / **`doc`** — the canonical-document index and one document's body, frontmatter-stripped. The front door for a Docs view.
- **`assignments`** / **`gameplan_assignee`** — the assignment surface: the manager role plus every gameplan's assignee, and the gameplan-level default parsed from its `> Assignee:` header.

## Lock-free and additive-stable

Every read here is **lock-free** (L-03). A context fetch must not block or be blocked by a writer — the cost is that a read can catch a doc between two writes, which for append-only markdown means missing the newest entry, and that is recoverable in a way a wedged session is not.

External clients render from these outputs and must never parse the markdown themselves (INVARIANT-01). That makes the shapes here a public contract, so they change **additively** under `contract.CONTRACT_SCHEMA_VERSION`'s rules: new fields are a minor bump, and clients ignore what they do not recognize.

## DAG position

Depends on `subsys.paths`, `subsys.analyze` (the shared `parse_entries` grammar and ranker) and `subsys.contract` (the schema stamp). Consumed by `ops`, which exposes each read as a `cz_list_*` tool. The mirror of `subsys.mutations`, which owns the write side and the grammars this module reads back.
