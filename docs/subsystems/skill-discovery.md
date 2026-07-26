---
id: subsys.skill-discovery
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.paths
  - subsys.assets
last_verified: 2026-07-25
---

# Skill Discovery

Read-only, propose-confirm discovery of Agent Skills already installed on this machine.

## What it does

Scans the well-known local skill locations for Agent Skills — a `SKILL.md` carrying `name` and `description` frontmatter — diffs them against what is already registered in `docs/SKILLS.md`, and **proposes** the unregistered ones for the agent to confirm via `cz_register_skill`.

- **`default_roots()`** — the skill locations scanned by default, as `(label, dir)` pairs. Labelled because a proposal has to say *where* a skill was found; two skills with the same name in different roots are different findings.
- **`discover(roots=None)`** — the proposals. Read-only.

## Three constraints that shape it

**It never writes.** Registration is a judgment call — whether a skill belongs in this project's memory is not something a scanner can decide — so the engine assembles candidates and the agent decides (INVARIANT-05). This is the same propose-confirm shape as `subsys.onboard` and `cz_analyze`.

**It never fetches.** Discovery is local-filesystem only; there is no network path here by design (D3, no external ingestion). A memory system that pulls skill definitions from the network is a memory system with a supply-chain surface.

**It degrades gracefully.** Malformed frontmatter, non-UTF-8 bytes, an unreadable directory — the whole read is wrapped, and a bad file is skipped or falls back to its directory name. It never crashes the scan. That matters because discovery runs against directories the engine does not own and cannot make assumptions about; one broken third-party skill must not take out the surface.

The graceful-degradation claim is only as strong as the input diversity it was tested against (L-24), which is why the tests feed it non-UTF-8 bytes, BOM and CRLF variants, empty files, and valid-JSON-but-wrong-shape frontmatter rather than just a happy path and one syntax error.

## DAG position

Depends on `subsys.paths` (locating `docs/SKILLS.md`) and `subsys.assets` (the packaged skills that ship with the engine and are registered already). Consumed by `ops` as `cz_discover_skills`. Its output is confirmed through `cz_register_skill`, which is a `mutations` write.
