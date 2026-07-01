---
id: subsys.graph
type: subsystem
version: 0.3.0
status: active
depends_on:
  - subsys.markdown-core@^0.1.0
last_verified: 2026-07-01
---

# Graph

The long-lived **Project DAG**: the durable graph of `subsys.*`, `feat.*`, `ext.*`, and other frontmatter-tracked entities, with edges declared as `depends_on` semver pins. It answers "what depends on this?" and, after a tracked edit, finds the dependents that *might* be affected. The graph is derived, never authoritative — the markdown under `docs/` is the source of truth (`model.py`).

## What an entity is

Any `docs/**/*.md` whose YAML frontmatter carries both an `id` and a `type` becomes an `Entity` (`model.Entity.from_text`); files without them are skipped. An entity also reads `version`, `status`, and `depends_on`. Each `depends_on` line is parsed into a `Pin` (`model.Pin.parse`) of the form `target` or `target@constraint` — e.g. `subsys.markdown-core@^0.1.0`. Subsystem/feature docs declare their edges this way:

```yaml
depends_on:
  - subsys.markdown-core@^0.1.0
  - subsys.graph@^0.1.0
```

## Key modules

**`index.py` — build + cache.** `build()` walks `docs_dir.rglob("*.md")` (skipping `.git`, `.venv`, `.clauderizer`, etc.) into an in-memory `Graph` keyed by entity id. `load_or_rebuild()` is the freshness guarantee every consumer calls: it compares the latest markdown mtime against the cache's recorded `docs_mtime` and **always rebuilds from markdown** — the mtime check only decides whether the cache *write* can be skipped. So out-of-band edits can never serve a stale graph.

**`query.py` — lookups.** `dependencies()` returns an entity's declared pin targets; `dependents()` scans all entities for those that name `entity_id` in `depends_on`; `transitive_dependents()` is the forward closure. `pin_violations()` reports dependents whose pin is no longer satisfied by the target's current `version`.

**`cascade.py` — post-hoc forward walk + report.** `render_report()` / `run()` take a changed `entity_id` and a `transition` label, gather direct + transitive dependents and any pin violations, and emit a Markdown report marking each dependent **"needs review"**.

## The cache contract

`index.json` lives at `.clauderizer/index.json` (gitignored, `version: 1`) and is **disposable** — purely a write-skip optimization. It is never read as truth: `load_or_rebuild()` rebuilds from markdown regardless. If the two ever disagree, markdown wins. `clauderize reindex` (`cli.cmd_reindex`) forces a fresh rebuild and rewrite.

## Cascade is judgment-based

Cascade does **not** edit anything and does not decide whether each dependent is truly affected — it finds and reports, and the agent fills in the verdict. `run()` writes one report per invocation under the active gameplan's `_cascade-reports/` directory (driven by the `cz_cascade` MCP tool; verdicts recorded via `cz_resolve_cascade`, never by hand-editing the report). The report lists **Direct dependents** (with each entity's `status`), **Transitive dependents** (flagged via upstream), any **Semver pin violations**, and two human-filled sections — *Updates applied* and *Updates deferred*. Filenames are `YYYY-MM-DD-<entity>-NN.md` (`report_filename()`); the zero-padded `-NN` sequence disambiguates same-day cascades of one entity that previously overwrote each other, and is deterministic and chronological within a day.

## Semver / pin handling

`model.constraint_satisfied()` implements the subset cascade needs: `^x.y.z` (caret — same major, `>=`), `~x.y.z` (tilde — same major+minor, `>=`), and exact `x.y.z`. It returns `None` when either side is unparseable, and `pin_violations()` treats unknown as **non-violation** — cascade never flags what it can't verify.

## Where it sits

`subsys.graph` depends on `subsys.markdown-core` (it consumes parsed frontmatter; nothing else). It is depended on by the subsystems that mutate and surface the DAG — `subsys.mutations`, the rituals, and `subsys.mcp-server` all reach the graph through `index.load_or_rebuild`.
