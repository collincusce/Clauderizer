---
id: subsys.modernize
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.scaffold
  - subsys.config
  - subsys.proposals
last_verified: 2026-07-25
---

# Modernize

Corpus modernization (D-042): a versioned, **two-tier** upgrade pass.

## The problem

When the engine moves ahead of a repo's corpus, the improvements should reach the repo "automatically in the general sense" — a user who upgrades Clauderizer should not have to hand-migrate their memory. But "automatically" cannot mean the same thing for a scaffold file and for a decision log.

## Two tiers, and the line between them

- **The MECHANICAL tier** — engine-owned scaffolds and config migrations. All git-diffable, all reversible by `git checkout`. These **auto-apply** on `clauderize upgrade` / `cz_modernize(apply=true)`.
- **The MEMORY tier** — everything the project actually decided. Only ever **surfaced** as advisory proposals for the agent to act on with the normal blessed writes (INVARIANT-05).

Nothing here ever edits `DECISIONS.md`, `INVARIANTS.md`, `LESSONS.md`, `HARDENING.md`, or any gameplan directory. The single docs write is refreshing the engine-owned `GAMEPLAN-PROCEDURE.md` copy — which is engine-owned precisely so that it *can* be refreshed.

The line is ownership, not risk. A file the engine wrote, the engine may rewrite. A file recording a judgment the project made is not the engine's to edit, however safe the edit looks.

## The surface

- **`report(paths, config)`** — the read-only report: what `apply` *would* do in the mechanical tier, plus the memory-tier proposals. Cheap and side-effect-free, so the digest can call it.
- **`apply(paths, config)`** — apply the mechanical tier only. Proposals remain proposals.

## Stateless by design, with state added elsewhere

`report()` re-derives everything on every run and writes nothing (D-042). That is what keeps the memory tier honest — there is no accumulated state to disagree with the corpus — but it means a proposal cannot be dismissed. `subsys.proposals` adds that layer on top, with content-derived ids so a materially changed proposal re-surfaces while an unchanged dismissed one stays quiet.

## One line in the digest

Detection is read-only and cheap, and the status digest carries **at most one** modernization line (D-027, INVARIANT-08), driven by the config's `procedure_version` stamp alone. A digest that listed every available migration would push the actual gameplan state off the top of the agent's context, which is the failure the trim-first rule exists to prevent.

## DAG position

Depends on `subsys.scaffold` (the mechanical scaffolds it refreshes), `subsys.config` (the `procedure_version` stamp and config migrations), and `subsys.proposals` (triage state). Also reads `subsys.onboard` to surface onboarding when scaffolds are still unseeded, and `subsys.assets` for the packaged templates. Consumed by `cli` (`clauderize upgrade`) and `ops` (`cz_modernize`). `feat.corpus-modernization` is the feature record.
