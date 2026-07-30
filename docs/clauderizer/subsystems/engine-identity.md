---
id: subsys.engine-identity
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.paths
last_verified: 2026-07-25
---

# Engine Identity

Is the process answering this call the build the working tree describes? (H-27)

## The failure this exists for

Measured live on 2026-07-25. `.mcp.json` wires `uvx --from clauderizer[mcp] clauderizer-mcp` — correct and deliberate, because committable wiring must be machine-independent (`subsys.hosttargets`). The consequence for a session that *edits the engine* is that every `cz_*` write is served by the **released** build from uv's cache while the fix sits green in the working tree.

A write guard was authored, tested at 26 tests, and committed — and executed for zero tool writes that day. It was found only when a malformed call produced exactly the corruption the guard exists to prevent. The tests were green, the code was correct, and none of it was running.

## Why the existing staleness check cannot see it

`status_bundle.engine_source_newer_than` compares source mtimes against process start. That detects the *editable-install* case, where the tree's files are the served files and one of them was touched after launch. An installed package's mtimes are install-time, so a uvx-served server is never "newer than" anything — the check is silent by construction for the exact case that bit.

Identity is a different question from freshness, and needs a different answer: not *when were these files touched*, but *are the files serving this call the files in this tree*.

## The four calls

- **`tree_package_dir(root)`** — `<root>/src/clauderizer` when this repo actually contains the engine's source, else `None`. A repo that merely *uses* Clauderizer has no tree package, and for it the whole question is meaningless — there is no mismatch to report.
- **`tree_version(root)`** — `__version__` as declared in the working tree's source, read from the file rather than imported, so it reports the tree's claim even when the tree is not what is loaded.
- **`serving_build(root)`** — the mismatch record, or `None` when the process *is* running the tree's source. The record carries `serving_path` and `serving_version` (where this process's `clauderizer` package actually lives, and what version it claims) alongside `tree_path` and `tree_version`.
- **`describe(mismatch)`** — the one-line claim, shared by every surface so they cannot word it differently. `status`, `doctor` and the digest all render the same sentence from the same function.

`serving_build` returning `None` is the ordinary case and is not reported anywhere — a correct setup stays quiet (quiet-when-empty).

## The separator lesson lives here

`serving_path` is `str(Path)`. On Windows it renders with backslashes, so `assert "uv/archive-v0" in m["serving_path"]` can never match — and that assertion shipped three Windows cells red in 1.14.2, with L-51 already recorded and already surfaced to the session that wrote it. The fix asserts the separator-agnostic token (`"archive-v0"`), and the class is now machine-rejected by `tests/test_separator_claims.py`. Any future assertion against `serving_path` is flagged by that check's Rule A, precisely because the name declares itself a path.

## DAG position

Depends on `subsys.paths` for repo resolution. Consumed by `rituals/status_bundle` — the digest carries the identity line — which is how `cz_status` reports `engine_identity` and how `engine_stale` is computed. Deliberately dependency-light and side-effect-free so any surface can ask the question cheaply.
