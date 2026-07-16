# Post-Mortem — self-audit-ritual-after-every-gameplan

**Closed:** 2026-07-16 · **Shipped:** Clauderizer 1.8.0 (procedure v1.7.0) ·
**Decision:** D-051 · **Baseline:** 799 → **807 passed, 5 skipped** ·
**cz_audit at close:** 0 findings

## Goal

Add a ritual to every Clauderizer install that audits its own work after each
gameplan — grounded in the failure modes this session's own audit missed.

## Outcome

`cz_audit` — a new advisory (INVARIANT-05) work/release self-audit gate, distinct
from `cz_critique` (which audits memory coherence). Deterministic signals: version
single-sourcing (pyproject vs the package `__version__` vs the top CHANGELOG entry),
an uncommitted tree, unresolved cascades/open items. Judgment checklist for what a
green suite can't prove: verify in a clean environment, re-audit every consumer of a
changed entity, claim only what you verified. Wired into the shipped
`clauderizer-close-gameplan` skill and `GAMEPLAN-PROCEDURE.md` (procedure v1.7.0), so
it runs at every gameplan close on all installs.

## What worked

- **Grounding the gate in a real, recent miss made it concrete, not theoretical.**
  The headline check — pyproject vs `__version__` — is exactly the bug that shipped
  red CI an hour earlier. The regression test reproduces that 1.7.0-vs-1.6.0 drift.
- **The existing ritual pattern carried the whole feature.** `rituals/*.py` +
  `ops.py` wrapper + `REGISTRY` + `tools_list` meant one new file and three
  one-line registrations exposed `cz_audit` to the MCP server, the `clauderize ops`
  CLI, and the status digest with zero bespoke wiring.
- **L-25 (verify a guard in both directions) shaped the tests directly** — the
  version signal is proven to fire on the defect AND stay quiet on a consistent
  repo and on repos missing a side (no false positives).
- **The dogfood closed the loop visibly.** Running `cz_audit` on this gameplan
  flagged its own uncommitted version bumps, then returned 0 findings once
  committed and cascaded — the gate auditing the gameplan that created it.

## What didn't (root causes)

- **Nothing failed in this gameplan** — but it exists *because* the prior release
  work did. Root cause of that miss: `__version__` was hardcoded, not derived from
  package metadata, and a stale editable `.venv` (metadata pinned to the old
  value) made the mismatch invisible locally. `cz_audit` + the install-independent
  guard test now make that class loud. Two defenses, because the venv-staleness
  means either alone can be fooled.

## Procedure improvements (fed back into GAMEPLAN-PROCEDURE v1.7.0)

- The Ending Protocol now says to run exit verification **in a clean environment**
  for release-bearing work — not just the working install.
- The Close procedure gained an explicit **self-audit** step before the post-mortem,
  and the post-mortem is instructed to fold `cz_audit` findings into "what didn't".

## Notes on curation

No gameplan lessons were promoted: this gameplan's lesson is encoded as a **shipped
capability** (`cz_audit`) plus an enforced **guard test**, which is stronger and more
durable than a prose lesson — and the corpus is already over its lesson bound. The
version/clean-env discipline it embodies extends the existing L-20/L-31 family.

## Open threads

- **`cz_audit` in `cz_preflight`/`cz_curate`?** The gate is close-time and advisory.
  A future call could surface a subset (version drift) at preflight too, but that
  risks noise on every phase; deferred deliberately.
- **Version single-sourcing at the source.** The deeper fix is to derive
  `__version__` from `importlib.metadata` so it *cannot* drift from pyproject. Not
  done here (editable-install and import-time trade-offs); `cz_audit` + the guard
  test cover the gap in the meantime.
- **Release stacking.** 1.8.0 stacks on the still-pending 1.7.0 (its CI was blocked
  by a `setup-uv` infra flake, and cutting its GitHub Release needs authenticated
  API this environment lacks). Ship 1.7.0 first, or 1.8.0 supersedes it.
