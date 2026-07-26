---
id: subsys.nesting
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.paths
last_verified: 2026-07-25
---

# Nesting

Two clauderized repos, one nested inside the other, produce **two SessionStart hooks and two contradicting digests**. `/home/ccusce` is itself a clauderized repo containing `/home/ccusce/Clauderizer`, so a session opened in the inner repo fired both hooks and the OUTER one announced "No active gameplan" — about a repo that was mid-release. That was the *first* thing in the executing session's context, and it was read past for an entire release before a second, colder session flagged it (H-23).

## Why the obvious fix is the wrong one

INVARIANT-08 already guarantees at-most-once status injection per session, enforced by an in-memory, per-process signal (`subsys.session`). Nesting defeats that guarantee **structurally**, not by a bug: these are two separate processes, and each is perfectly correct about its own repo. Making them agree would require a shared flag — persisted, cross-process state — which INVARIANT-05 and INVARIANT-08 both rule out.

The right frame is **ownership**, not deduplication. For any session cwd, exactly one clauderized repo owns it: the nearest clauderized ancestor. An install that is not the owner of the session it was fired for stays silent. That verdict is decided fresh from the hook payload on every event — no flag, no file, nothing that can fall out of date.

## The ownership calls

- **`is_clauderized(d)`** — the definition of a clauderized repo, in one place: `d/.clauderizer/config.toml` is a file. An `OSError` reading it is `False`, not a raise.
- **`owner_of(cwd)`** — resolves `cwd`, walks to its repo root via `subsys.paths`, and returns that root when it is clauderized. `None` when no install covers the directory.
- **`outranked_by(anchored_root, session_cwd)`** — the actual gate the hook consults. Returns the install that should speak *instead of* this one, or `None` when this install is the right one to speak.

`outranked_by` fires **only in the H-23 shape**: the session's owner is a *proper descendant* of this install's root. A session outside this repo entirely is deliberately not covered — silencing that case would change behavior for anyone who wired a hook globally on purpose, and INVARIANT-07 makes cross-host parity regressions a release blocker. The change is additive: it can only ever add silence in the nested case, never remove existing output.

## The reporting calls

Ownership silences the *duplicate digest*. It does not tell anyone the nested install exists — and a nested install's hook, CLAUDE.md stanza and MCP wiring rot independently of the outer one, with nothing else in the engine reporting them.

- **`nested_installs(root, max_depth=MAX_SCAN_DEPTH)`** — clauderized repos strictly beneath `root`, nearest first, for `doctor`. Bounded and pruned in four ways, because an unbounded walk of a home directory is not something `doctor` may do: depth is capped at `MAX_SCAN_DEPTH` (4), hidden directories and the `_SKIP_DIRS` vendor set (`node_modules`, `venv`, `site-packages`, `AppData`, …) are skipped, symlinks are not followed, and a found install's own subtree is **not** descended — the finding is the install, not everything under it. Unreadable directories are skipped rather than raised.
- **`clauderized_ancestors(root)`** — the mirror image, walking up: clauderized repos strictly above `root`, nearest first. This is what makes an `init` here a *nested* install rather than a fresh one.
- **`describe_nested(root, nested)`** — doctor's line, naming each install by path and stating the consequence: a session inside a nested repo is owned by that repo, so its wiring is only exercised — and only repairable — from inside it.
- **`describe_ancestors(root, ancestors)`** — init's warning: initializing here creates a SECOND, independent install. Supported, but the two corpora never merge and each must be maintained separately, so it points at the outer repo in case that was what the user meant.

Both `describe_*` functions return prose rather than printing, so the caller owns the channel.

## Constraints

Nothing here writes. The whole module is read-only path arithmetic plus a bounded directory scan, which is what makes it legal for a hook to call at all (INVARIANT-06). Every entry point swallows `OSError`/`ValueError` into an empty or `None` result: a hook must never fail because a directory was unreadable.

## DAG position

Depends on `subsys.paths` for `find_repo_root`. Consumed by the hook handlers (the ownership gate, on every event) and by `cli` — `doctor` reports nested installs, `init` warns about clauderized ancestors.
