---
id: subsys.assets
type: subsystem
version: 1.0.0
status: active
depends_on:
last_verified: 2026-07-25
---

# Assets

Access to the packaged template, profile and skill payloads that ship inside the wheel.

## Where the assets live

`pyproject.toml` force-includes `templates/`, `profiles/`, `skills/` and `kinds/` into the wheel. At runtime this module reads them straight off disk relative to its own `__file__` — `_PKG / "templates"`, `_PKG / "skills"`. That is deliberately simpler than `importlib.resources`: it is import-light, it works identically from an editable checkout and an installed wheel, and it keeps the engine's zero-runtime-dependency posture.

The consequence worth knowing is that a file which is not force-included in `pyproject.toml` simply will not exist in the wheel, and the failure appears at first use rather than at import. That is what the packaged-asset tests exist to catch, and it is a specific case of the general rule that a claim about a shipped artifact needs a test asserting the artifact actually ships.

## The surface

- **`template_text(rel)`** — read a template by path relative to the templates dir.
- **`render(rel, **vars)`** — read a `$placeholder` template and substitute. Uses `Template.safe_substitute`, so a stray `$` in a template never crashes a write — an important property when the substituted text is user memory that may legitimately contain dollar signs.
- **`doc_template(name)`** — the template text for a named living doc (`doc_template("DECISIONS")`), or `None` when there is none. The `None` matters: `subsys.onboard` compares a doc on disk against its template to decide whether it is still an unseeded scaffold, and a missing template must mean "cannot tell", not "unseeded".
- **`project_template(name)`** — template text for a PROJECT-owned doc seed (D-080), or `None`. Separate from `doc_template` because a name can exist on both sides with different text: the engine's `GLOSSARY` is Clauderizer vocabulary, the project's is their domain. Only ever written on explicit request (`init --seed-project-docs`).
- **`procedure_text()`** — `GAMEPLAN-PROCEDURE.md`, the engine-owned copy that `subsys.modernize` refreshes.
- **`skill_dirs()`** — the packaged Agent Skill directories, sorted, or an empty list when none ship. `init` copies these into the repo's `.claude/skills/`.

## Source, not render

The rule this module enforces on its callers: generated content has a **source template**, and editing only the render leaves the source stale — a future `init` will overwrite the edit. The CLAUDE.md/AGENTS.md stanza and the `.claude/skills` payload both render from here, so a change to either belongs in `src/clauderizer/templates/` or `src/clauderizer/skills/` first, and in the repo's rendered copy second.

## DAG position

Depends on nothing. Consumed by `scaffold/init` (writing docs, skills and stanzas), `mutations` (entity and doc templates), `modernize` (the procedure refresh and mechanical scaffolds), `onboard` (the unseeded-scaffold comparison), `skill_discovery`, and `mcp_server`. `subsys.templates` and `subsys.skills` document the payloads themselves.
