---
id: subsys.untangle
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.ownership
  - subsys.assets
  - subsys.markdown-core
last_verified: 2026-07-30
---

# Untangle

The one-time migration that separates engine memory from the project's docs
(D-080/D-081): engine-owned docs move into `docs/clauderizer/`, everything the
human authored stays exactly where it is.

## The rules that make it safe to run automatically

- **No file is ever split, merged, or rewritten** — only moved or newly created.
  A machine has no business deciding which half of a mixed file is whose.
- **A doc that is theirs stays theirs.** A `docs/GLOSSARY.md` holding real
  project content is left byte-identical and a *fresh* engine glossary is written
  alongside. That is the two-glossary shape, and it is the general case rather
  than a special one.
- **Every entry is conserved** — counts taken across the whole docs tree before
  and after, because a move changes paths and only a tree-wide total can testify
  that nothing was dropped in transit (INVARIANT-03).
- **Idempotent**: a second run reports zero actions.

## The surface

- **`plan(paths, config)`** — the verdicts `apply` would act on, each with a
  stated reason. Writes nothing; this is the `--dry-run`.
- **`apply(paths, config)`** — runs it, records `docs_layout = split`, returns
  the report including the conservation check.
- **`forked_stubs(paths)`** — legacy stubs an OLD engine has written into
  (H-33): entries numbered above the stub's sentinel mean some install resolved
  the pre-migration path and recorded there, so the corpus has forked. Reported
  for a hand merge, never repaired automatically — deciding where someone else's
  entry belongs is judgment, not mechanics (INVARIANT-05). `clauderize doctor`
  renders it as drift with the orphan ids.
- **`STUB_PREFIXES`** — the id prefix and width each numbered register allocates
  from, mirroring `mutations`. Drives the high-water sentinel described below.
- **`entry_count(path)`** — append-only entries in a register, using the same
  anchors `model.next_numbered_id` counts, so "does this hold engine memory?" is
  answered by the writer's own grammar rather than a second guess.

## Classification

For each engine-owned name at its legacy path: still the untouched scaffold, or a
register carrying engine-written entries → **move**. Anything else is a human's
prose sitting at a name the engine also uses → **leave and create alongside**.
Absent → **create**. `git mv` stages a rename so history survives the commit; a
non-git repo still migrates and only loses that.

## The stub is load-bearing, not a courtesy

Every vacated path keeps an inert stub (D-081). Measured against the published
2.0.0 engine, it does three distinct jobs: a human or agent opening the old path
learns where the content went; `dangling_doc_pointers` stops firing, so an older
engine never renders its *"run `clauderize upgrade` to scaffold them"* advice —
which would recreate empty legacy files and split the corpus in two; and
`create_if_absent` sees the stub and never recreates anything.

It does **not** stop an old engine WRITING, which was measured live (H-33): a
`cz_add_decision` through a stale MCP server landed in the stub and numbered
itself `D-001` while the real register ended at `D-081` — a duplicate id in an
append-only corpus. Nothing shipped here can change an already-published
engine's behaviour, so the stub carries a **high-water sentinel** entry
(`D-900000` and its siblings) instead: an old engine allocating from the stub
gets `D-900001`, which cannot collide with anything real and is obvious on
sight. `forked_stubs` then reports it. Containment, not prevention — and
`UPGRADING.md` carries the ordering rule that actually avoids it: upgrade every
install that writes to a repo before migrating it.

## DAG position

Depends on `subsys.ownership` (who owns what), `subsys.assets` (the templates it
writes), `subsys.markdown-core` (`refuse_if_symlink`, `create_if_absent`).
Consumed by `subsys.modernize` (the upgrade action) and `subsys.cli`.
