---
id: subsys.revision
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.paths
last_verified: 2026-07-25
---

# Revision

The monotonic memory revision — the near-free change signal (O-03, §6.4).

## Contract surface, not a cache

`.clauderizer/revision.json` is the one engine artifact external clients are **blessed to read directly**. That exemption is the whole point: a client that wants to know "did memory change?" must be able to ask without paying for a process spawn. Everything else in `.clauderizer/` is private (INVARIANT-01 — clients read the engine's JSON outputs, never the engine's files), and `index.json` and `abstract_index.json` are explicitly disposable caches. This one is a published shape:

```json
{"schema_version": "1.0", "epoch": "<hex>", "revision": 7}
```

## Epoch plus revision, not revision alone

`revision` increments on every engine write that changes memory bytes — markdown mutations, cascade reports, handoff regeneration, the focus flip. `epoch` is minted fresh whenever the file is created or recreated.

The pair exists because a counter alone lies after a reset. Delete the file, and a naive counter restarts at 1 — replaying values a poller has already seen, so the poller concludes nothing changed when in fact everything did. Minting a new `epoch` on (re)creation makes that case detectable: clients treat `(epoch, revision)` as an opaque change key and compare it for equality, never ordering. Both fields are opaque by contract, which leaves the engine free to change how either is produced.

## The calls

- **`revision_file(paths)`** — the location, so callers never spell it.
- **`bump(paths)`** — increment the counter, creating the file and a fresh epoch if needed.
- **`bump_for(written_path)`** — increment the revision of whichever clauderized repo *contains* `written_path`. This is the form the mutation layer actually calls: a write knows the file it touched, not necessarily the repo it belongs to, and in a nested-install layout (`subsys.nesting`) those are different questions.

## Atomicity

The file is written temp-then-`os.replace`, so a reader sees the old value or the new one and never a torn intermediate. That matters more here than in most places precisely because the file is *designed* to be polled by processes the engine does not control and cannot coordinate with — there is no lock a third-party poller could be expected to take.

## DAG position

Depends on `subsys.paths` for the location and on `subsys.contract` for the `schema_version` stamp that makes it a versioned surface. Bumped by `mutations` (every tracked write) and by `ops` (the write paths that do not route through `mutations` — cascade reports, handoff regeneration, the active-gameplan flip). Read by `cz_revision`.
