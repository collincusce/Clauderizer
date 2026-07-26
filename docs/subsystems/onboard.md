---
id: subsys.onboard
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.paths
  - subsys.assets
last_verified: 2026-07-25
---

# Onboard

Onboarding an existing project (D-044): **the engine detects, the agent seeds.**

## The gap

`clauderize init` on a repo that already has real documentation scaffolds placeholder `VISION.md` and `ARCHITECTURE.md` next to it — and before this module, nothing prompted anyone to fill them in. The repo's actual knowledge stayed in the README while Clauderizer's memory sat empty, which is the worst of both: a memory system that knows nothing, next to documentation it never read.

The engine cannot close that gap itself. It is deterministic and never synthesizes prose; distilling a spec into decisions and invariants is judgment work. So onboarding takes the established assemble-and-prompt shape (D-016/D-019): the engine finds the inputs, and the agent does the reading and the recording through the normal blessed writes.

## What it finds

- **`spec_candidates(paths)`** — existing docs likely to hold project knowledge: well-known root files (`README.md`, `DESIGN.md`, …) plus `docs/**/*.md` outside the Clauderizer-owned set. **Paths and sizes only, never contents** — the agent reads the files itself, which keeps the tool result small and keeps the engine out of the business of deciding what a document says. Empty and oversized files are skipped, and the list is capped at `CANDIDATE_CAP`. Paths are emitted via `relative_to(root).as_posix()`, so the separator is a contract rather than a platform accident.
- **`unseeded_docs(paths)`** — the prose docs on disk that are still scaffold placeholders, compared against their packaged templates from `subsys.assets`.
- **`report(paths)`** — the read-only bundle: both lists plus the seeding prompt. The whole of `cz_onboard`'s result.

## Detecting an unseeded scaffold robustly

The comparison is structural rather than textual. An older template's scaffold has the same *shape* — headings plus placeholder markers — with different placeholder wording than today's template ships, and a check that matched the current template's exact phrases would call those docs seeded. So the detector keys on structure (headings with placeholder-shaped bodies), which is the same principle as rejecting a class by a structural property rather than a list of known bad values (L-63).

The inverse matters too: a doc a human actually wrote must never be called unseeded, because the prompt that follows says "rewrite this" — and rewriting real content would be the worst possible false positive.

## Advisory everywhere

Nothing here ever writes a doc. `cz_onboard` returns the bundle; the packaged `clauderizer-onboard` skill walks the agent through reading the sources and recording what they hold via `cz_upsert_entity`, `cz_add_decision`, `cz_add_invariant` and the rest. Append-only logs are never onboarding targets — `DECISIONS.md` and `LESSONS.md` get entries appended through their own ops, never a wholesale rewrite (INVARIANT-03).

## DAG position

Depends on `subsys.paths` and `subsys.assets` (the templates it compares against). Consumed by `ops` (`cz_onboard`) and by `modernize`, which surfaces onboarding as a proposal when the scaffolds are still unseeded. `feat.onboarding` is the feature record.
