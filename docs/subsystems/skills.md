---
id: subsys.skills
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.assets
last_verified: 2026-07-25
---

# Skills

The packaged Agent Skills payload — `src/clauderizer/skills/`.

## What ships

A directory per skill, each with a `SKILL.md` carrying `name` and `description` frontmatter. `init` copies them into the repo's `.claude/skills/`, and `subsys.assets`' `skill_dirs()` enumerates them.

The shipped set walks an agent through the rituals that are too procedural to leave to judgment and too conditional to encode in a tool: `clauderizer-do-phase` (pre-flight → work → close-out), `clauderizer-new-gameplan`, `clauderizer-amend`, `clauderizer-record`, `clauderizer-cascade`, `clauderizer-close-gameplan`, `clauderizer-onboard`, `clauderizer-modernize`, and `clauderizer-dream`.

## Source, not render

This directory is the **source**. `.claude/skills/` in a clauderized repo is a **render**, written at `init`.

Editing only the render leaves the source stale, and a future `init` overwrites the edit — silently, because nothing compares them. So a change to skill text belongs here first and in the repo's rendered copy second. The same rule governs the CLAUDE.md/AGENTS.md stanza, which renders from `subsys.templates`.

## Not every host reads them

Skills are a Claude Code convention. Kimi Code CLI does **not** read `.claude/skills` — which is why `subsys.hosttargets`' kimi setup guide explains exposing them under `.agents/skills` or `.kimi-code/skills` instead. A successor tool may drop a convention its predecessor had, and assuming otherwise is how wiring silently does nothing (L-66).

## Packaging

The directory is force-included into the wheel by `pyproject.toml`. A file not listed there simply will not exist at runtime, and the failure appears at first use rather than at import — which is why the packaged-asset tests assert the payload actually ships, rather than trusting that it does.

## DAG position

Depends on `subsys.assets`, which reads it. Copied into a repo by `scaffold/init`; discovered and registered through `subsys.skill-discovery` and `cz_register_skill`. No public API — it is data, and the engine's own registry of what a project has available lives in `docs/SKILLS.md`.
