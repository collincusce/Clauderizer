---
id: subsys.release-check
type: subsystem
version: 1.0.0
status: active
depends_on:
last_verified: 2026-07-25
---

# Release Check

`clauderize release-check` — the release preflight ritual (O3, D-011).

## A version number is a claim across four registries that never sync

- **source** — `pyproject.toml` and `__version__`;
- **remote git tags**;
- **GitHub Releases**;
- **the PyPI index**.

Nothing keeps those four in agreement. A version can be tagged but unpublished, published but untagged, or claimed on PyPI by a failed attempt whose local trace was cleaned up — and `uvx` answering by name from uv's cache will happily hide that last case. v0.7.0 and v0.8.0 were both double-claimed this way in a single day (H-07).

## Plus one ordering invariant

**origin must hold the staged release commit BEFORE any tag or Release exists.**

This is not a preference. A GitHub-UI release tags the *remote* branch head, so any guard authored locally is unpushed by construction at exactly the moment it would need to fire (L-08). The ordering is the only thing that makes the guards real, and checking it is why this ritual runs before the tag rather than after.

## The surface

- **`Check`** — one verdict with its evidence.
- **`remote_claims(version)`** — is `version` claimed on each remote registry? The reusable core (H-19), separate from the CLI wrapper so other rituals can ask the same question without shelling out.

## Three-state honesty

Verdicts follow `doctor`'s discipline (D3/D-010): **`ok` shows its evidence**, **`fail` is red**, and a registry this host cannot query is **`unverifiable`** — never a false green. Exit codes carry the same distinction: `0` clean, `2` on any fail, `3` clean but with unverifiable checks.

That third exit code is the point. A release preflight that could not reach PyPI and reported success would be worse than one that refused to run, because the operator would act on it. Distinguishing "checked and fine" from "could not check" is what makes the green meaningful.

## What it does not check

`clean_tree` counts **untracked** files as a dirty tree — foreign tool artifacts and regenerable caches will block the ritual even though the published artifact builds from `origin/main` plus the tag. The honest fix is `.git/info/exclude` (local-only, non-committed, deletes nothing), after verifying `git status --untracked-files=no` is empty to prove no real source change is uncommitted.

And it cannot check the thing that has bitten hardest: **CI green on every matrix cell**. A suite green on one OS is a guess about the others, and the publish cannot be undone — 0.14.0 shipped with three Windows cells red on a single path-separator assertion. That belongs to the release ritual as a whole (L-51), verified at job granularity before any tag; `tests/test_separator_claims.py` now machine-rejects that specific class.

## DAG position

Depends on nothing. Consumed by `cli` (`clauderize release-check`).
