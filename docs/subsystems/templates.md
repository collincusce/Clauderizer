---
id: subsys.templates
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.assets
last_verified: 2026-07-25
---

# Templates

The packaged template payload — `src/clauderizer/templates/`.

## What ships

- **`docs/*.md`** — the living-doc scaffolds (`VISION`, `ARCHITECTURE`, `DECISIONS`, `INVARIANTS`, `LESSONS`, `HARDENING`, `SKILLS`, …) that `init` writes into a fresh repo, and that `subsys.onboard` compares a doc against to decide whether it is still an unseeded placeholder.
- **`GAMEPLAN-PROCEDURE.md`** — the engine-owned procedure spec. Refreshed by `subsys.modernize`, which is *why* it is engine-owned: a file the engine wrote is a file the engine may rewrite.
- **The gameplan scaffolds** — `GAMEPLAN.md`, `PHASE-STATUS.md`, `CHAT-HANDOFF-INDEX.md` and the handoff template.
- **The host stanzas** — the marker-block text `init` injects into `CLAUDE.md` and `AGENTS.md`, single-sourced so both carry the same instructions.

## `$placeholder` substitution

Templates are read through `assets.render(rel, **vars)`, which uses `Template.safe_substitute`. Safe rather than strict is deliberate: the substituted text is often user memory, a stray `$` in it is legitimate, and a template render must never be the reason a write fails.

## Source, not render

Everything here is a **source**. What lands in a repo is a **render**. Editing only the render leaves the source stale and a future `init` overwrites it, so a change belongs here first.

The single-sourced CLAUDE.md/AGENTS.md stanza is safe by construction — both render from one template, so they cannot disagree. Docs that are *not* single-sourced are the ones that drift: README's tool list sat 14 tools behind for a release, and the fix was an executable pin diffing it against `subsys.tools-list`, not a promise to remember.

## Append-only history is never a template concern

`CHANGELOG.md`, handoffs and cascade reports record old counts **on purpose** (INVARIANT-03). A regenerated scaffold must never rewrite them to today's numbers; the marker-block discipline exists so regeneration touches only what the engine owns and leaves agent-authored notes outside the markers intact.

## Packaging

Force-included into the wheel by `pyproject.toml`. A missing force-include fails at first use, not at import — which is what the packaged-asset tests exist to catch.

## DAG position

Depends on `subsys.assets`, which reads it. Consumed by `scaffold/init` (docs, stanzas, gameplan scaffolds), `mutations` (entity and doc templates), `modernize` (the procedure refresh) and `onboard` (the unseeded comparison). No public API — it is data.
