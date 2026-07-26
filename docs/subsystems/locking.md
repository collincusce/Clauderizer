---
id: subsys.locking
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.paths
last_verified: 2026-07-25
---

# Locking

Advisory inter-process write lock for tracked mutations (H-05).

## Why it is needed

Every tracked doc mutation is read-modify-write markdown, and ID allocation (`next_numbered_id`) reads the current maximum before appending. One MCP server per session means a second window, a subagent, or a `clauderize ops` batch running concurrently will interleave those reads and writes — losing an append, or handing out the same `D-0NN` twice. That is H-05.

The fix is to serialize writers through `.clauderizer/write.lock`.

## How the lock works

- **Acquire** is an `O_CREAT | O_EXCL` create with holder metadata written inside — pid, host, timestamps, and a one-shot nonce. Portable by construction: no daemon, no platform-specific `fcntl`, and it behaves the same on Windows as on POSIX.
- **Stale takeover** — a holder older than `stale_timeout` (default 30s, against mutations that run in milliseconds) is presumed crashed. Takeover *renames* the stale file to a unique trash name rather than unlinking it. Rename is atomic, so exactly one contender wins, and nobody can unlink a rival's freshly created lock by mistake.
- **Nonce re-read** — after every create, the writer re-reads the file and checks its own nonce is still there. A racing takeover that clobbered it is detected rather than silently tolerated.
- **Contention** surfaces as **`LockHeld`**, a clear retryable error naming the current holder — not a hang, and not a silent overwrite.
- **Reentrant per thread** — mutations compose other mutations (`consolidate_lessons` calls `add_lesson`), so the lock counts depth per lock path and creates or removes the file only at the outermost level. Threads within one process serialize on a per-path `RLock`.

`_RELEASE_UNLINK_ATTEMPTS` exists for a Windows-specific race: release-time unlink can lose to a concurrent reader, so it retries for about two seconds before falling back to takeover semantics. The timeouts (`DEFAULT_ACQUIRE_TIMEOUT`, `DEFAULT_STALE_TIMEOUT`, `_POLL_INTERVAL`) are read at call time from module attributes rather than bound at import, so tests and embedders can retune them.

## The surface

- **`write_lock(lock_path, ...)`** — the context manager. Hold it for exactly one mutation.
- **`read_holder(lock_path)`** — the holder metadata currently in the lock file, or `None`. What `doctor` and the `LockHeld` message report.
- **`LockHeld`** — raised when a live writer holds the lock. Retry shortly.

## Read paths never take it

This is the rule that keeps the lock from becoming a liability (L-03): a context fetch must not block, or be blocked by, a writer. Every read op — `cz_status`, `cz_get`, every `listing` call — is lock-free. The cost is that a read can observe a doc mid-sequence-of-writes; the benefit is that a crashed or slow writer can never wedge the surface an agent depends on to orient itself. For append-only markdown that trade is clearly right: a read that misses the newest entry is recoverable, a hung session is not.

## DAG position

Depends on `subsys.paths` for `write_lock_file`. Taken by `mutations` (every tracked write), by `ops` (the write paths that do not route through `mutations` — cascade reports, handoff regeneration, the active-gameplan flip), and by `rituals/preflight`. Never taken by anything on a read path.
