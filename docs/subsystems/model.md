---
id: subsys.model
type: subsystem
version: 1.0.0
status: active
depends_on:
last_verified: 2026-07-25
---

# Model

The core data shapes parsed out of the markdown source of truth.

## Nothing here is authoritative

This is the module's whole contract, and it is worth stating before the types: **the markdown is authoritative; these dataclasses are a view.** Everything here is derived from files on disk, held in memory, and thrown away. Rebuilding them from the markdown must always be possible — that is INVARIANT-01, and it is why `index.json` and `abstract_index.json` are disposable caches rather than a database.

The practical consequence is a direction of travel: a change to memory is a change to markdown, and the model follows. A change made to a model object and not written through the mutation layer is a change that did not happen.

## The types

- **`Entity`** — a frontmatter-tracked node in the long-lived Project DAG. Its `id`, `type`, `version`, `status`, and `depends_on` are the frontmatter fields, parsed; `path` is where it was found. Subsystems, features and deliverables are all `Entity`.
- **`Pin`** — one parsed dependency edge: a target id plus an optional semver constraint. `subsys.graph@^0.1.0` is a target and a constraint; `subsys.graph` is a target with `None`, which is a legal, unpinned edge.
- **`Drop`** — a `docs/` file that *was trying to be a tracked entity and could not be*, with the reason. This type is the reason the graph does not silently swallow mistakes: a file with a malformed id, a partial frontmatter block, or a fenced pseudo-entity becomes a reported `Drop` rather than vanishing from the index. Classification is conservative — only files that clearly *intended* to be an entity count, or the report acquires standing false positives and stops being read.
- **`SemVer`** — the parsed version triple, with comparison.

## The two functions

- **`constraint_satisfied(version, constraint)`** — does `version` satisfy `constraint`? Backs the graph's pin-violation report, which is how a dependent learns its dependency moved out from under it.
- **`next_numbered_id(text, prefix)`** — compute the next id for an append-only numbered series found in `text` (`D-014` → `D-015`, `L-67` → `L-68`). Every append-only register allocates ids through this one function, which is why the allocation is consistent across `DECISIONS`, `INVARIANTS`, `LESSONS`, `HARDENING`, corrections and amendments — and why it must be called under the write lock (`subsys.locking`): reading the current maximum and appending are two steps, and H-05 is exactly what happens when they interleave.

## DAG position

Depends on nothing. Consumed by `mutations` (id allocation and entity writes) and by `graph/index` and `graph/query`, which build the DAG from these shapes. Deliberately import-light — it is a leaf so that everything else can depend on it without a cycle.
