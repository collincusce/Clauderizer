# Post-Mortem — 2026-07-01-engine-1-5-0-onboarding

> Written at close, 2026-07-01. Engine 1.4.1 → 1.5.0; procedure 1.5.0 → 1.6.0; suite 755 → 764; tool surface 44 → 45.

## What this gameplan set out to do

Close the gap the 1.4.x Q&A exposed: `clauderize init` on a repo with real documentation scaffolds placeholder docs next to the actual specs and nothing prompts seeding them. Ship the fix as engine 1.5.0.

## What happened

Five phases, one continuous same-day arc, every suite run green on the first try. The feature landed as the established assemble-and-prompt shape (D-044): a deterministic detector (`onboard.py`), a read-only `cz_onboard`, surfacing at init and through `clauderize upgrade`, and the `clauderizer-onboard` skill. Dogfooded three ways before shipping: a scratch spec-rich repo (advisory fired; the bundle was exactly right), plus both live corpora (procedure stamp 1.6.0 applied; zero false fires because their docs are real).

## What went right

- **The 1.4.0 machinery paid for itself immediately.** The modernization framework built one release ago meant "existing repos learn about onboarding" was a twelve-line tier-2 detector, not a design problem. This is the D-042 contract working as intended: build the delivery rail once, and every subsequent feature rides it.
- **Structure-based unseeded detection.** The "meaningful lines ⊆ current template" predicate survives template wording drift where byte-identity would silently rot — the drift test encodes the exact failure mode considered and rejected during planning.
- **Lean plan, clean execution.** Five phases instead of ten; the recon debt from the 1.4.0 arc (anchors still fresh) meant near-zero exploratory reads. Total new tests: 9.

## What bit

- Nothing engine-shaped. The only friction was self-inflicted harness quoting (the ops-output parse in the dogfood script guessed the envelope shape wrong; the raw output was correct) — the standing script-file rule kept even that cheap.

## Numbers

Phases 5/5 complete. Corrections: 0. Open items: none new. Suite 755 → 764 (+9, tests/test_onboard.py). Surface 44 → 45 (`cz_onboard`, read-only). Seventh packaged skill.

## Ship record

PR #20 → 9-cell CI green before tag → squash-merge `6785b9477` → release-check exit 0 → tag `v1.5.0` → GitHub Release (latest) → OIDC publish green → PyPI `info.version = 1.5.0` → `uvx --refresh` resolves 1.5.0.
