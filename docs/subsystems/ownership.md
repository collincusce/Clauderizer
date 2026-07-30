---
id: subsys.ownership
type: subsystem
version: 1.0.0
status: active
depends_on: []
last_verified: 2026-07-30
---

# Ownership

Who owns a doc — the structural boundary between engine state and project prose
(D-080).

## The problem

Until this module existed, the engine had **no notion** that its own memory and
the project's writing were different things. Every doc was a file in `docs/`, so
the engine scaffolded `ARCHITECTURE.md`, `SECURITY.md` and `GLOSSARY.md`
straight into the human's namespace, and could not tell a decision log it wrote
from a runbook they wrote. D-039 recorded the distinction as two documentation
layers on 2026-06-23 and nothing on disk enforced it; measured across five real
repos on 2026-07-30, engine memory was interleaved with project docs in every
one, and a project's own `SECURITY.md` shared a name the `saas` manifest claimed.

The user's framing is the one that settled it: Clauderizer's docs are **more like
configs** than prose. They are addressable engine state that happens to be
markdown.

## The surface

- **`owner_of(name)`** — `engine` | `project` | `product` for a doc name, with or
  without `.md`. The single source of truth; no call site infers ownership from a
  filename.
- **`is_engine_owned(name)`** — the predicate `RepoPaths.doc()` routes on.
- **`ENGINE_DOCS` / `PROJECT_DOCS` / `PRODUCT_DOCS`** — the classification.
  `ENGINE_DIRS` names the tracked-entity directories (`features`, `subsystems`)
  that travel with the engine corpus.
- **`ENGINE_NAMESPACE`** — the subdirectory (`clauderizer`) engine docs occupy
  under the docs root once a repo is on the split layout.
- **`LAYOUT_LEGACY` / `LAYOUT_SPLIT`** — the two layouts, mirrored by
  `Config.docs_layout`.

## An unknown name belongs to the project

`owner_of` returns `project` for anything it does not recognize, and that default
is the whole point rather than a fallback: a doc the engine has never heard of is
the human's, and the engine keeps its hands off it. The engine may no longer
create a file in the project's namespace without being asked, nor treat a file it
finds there as its own.

## The identity default is what makes this shippable

`RepoPaths.engine_docs` defaults to `None`, and `engine_docs_root` then resolves
to the project docs directory — so on the legacy layout `doc('DECISIONS')`
returns `docs/DECISIONS.md`, exactly as it did before ownership existed. The
concept lands with **zero** files moved and a byte-identical digest; only the
untangle migration flips a repo to `split`. This is L-41's pattern (an identity
default lets a large generalization land with no behavior change) applied to a
breaking relocation, and it is why the change can be staged across phases instead
of landing as one unreviewable jump.

## Two glossaries, and one deliberate exception

`GLOSSARY` is the one name that legitimately exists on both sides, and it is the
general shape rather than a special case: a glossary of Clauderizer vocabulary
(gameplan, cascade, handoff, deferred) is genuinely useful to an agent and
belongs to the engine, while the project's domain glossary belongs to the
project. They are never merged, and a migrated repo ends with both.

`GAMEPLAN-PROCEDURE.md` is the exception that does not move. D-039 places it in
the product layer, and — measured — it is the file `_procedure_drift` reads to
detect a MAJOR skew. Relocating it would destroy the one loud signal an older
engine trips on a migrated repo (O-02), so it keeps `docs/gameplans/`.

## DAG position

Depends on nothing — deliberately leaf, so `paths` and `config` can both import
it without a cycle. Consumed by `subsys.paths` (doc routing), `subsys.config`
(the `docs_layout` key), `subsys.scaffold` (what init may create), and
`subsys.modernize` (what the untangle moves).
