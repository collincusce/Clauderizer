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

## Does the code actually pass? (H-28)

The registries answer whether the **version** is free. None of them answers whether the **code** passes on every platform it claims to support — and that is what has bitten hardest: 0.14.0 and 1.14.2 both shipped with Windows cells red. L-51 sweep (2) named the rule for three releases and it stayed discipline.

- **`_ci_check(root, sha)`** — did CI pass on *this* commit?

It is at **job** granularity on purpose. GitHub reports a workflow as `success` when a matrix cell is *skipped*, so reading the workflow conclusion is precisely the false green this module exists to refuse. Every job of every run for the exact HEAD sha is enumerated, and the run's own `conclusion` is never consulted — pinned by a test that gives a `failure` run whose every job succeeded and asserts the verdict is still computed from the job set.

Green means every job concluded `success`. Everything else is not-green, per conclusion:

- a job `failure`, `cancelled`, `timed_out`, `action_required`, `stale`, `startup_failure`, `neutral` — or **`skipped`** — is a **fail**, and each offender is named;
- a run still `queued` or `in_progress` is a **fail** (tagging mid-run is the race);
- **no run at all** for the sha is a **fail**, not unverifiable: the absence of a run is a definite fact about the code you are about to tag;
- `gh` missing, unauthenticated, or the API unreachable is **`unverifiable`**;
- a repo with no `.github/workflows/` is **`skip`** — absence of CI is not a failure.

**The false-positive surface, stated rather than implied**: a repo with a deliberately conditional job (`if:` at job level) will see it reported as a skipped cell and go red. That is the trade — `unverifiable` renders as "*OK* with unverifiable check(s)", which is too soft for a missing Windows cell. The failure detail names every offending job so the choice is actionable, and a conditional job that must not gate a release should be made unconditional or verified another way. This repo has no job-level conditionals.

## DAG position

Depends on nothing. Consumed by `cli` (`clauderize release-check`).
