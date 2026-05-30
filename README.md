# Clauderizer

**Drop-in, MCP-native working memory for AI agents.** Give any repo a durable,
structured memory that survives across stateless sessions — gameplans, phases, a
dependency graph, and post-hoc cascade — over plain, git-diffable markdown.

```bash
uvx clauderize init        # drop it into any repo, one command
```

---

## Why

Long-running AI work has two memory limits: a new session starts with nothing,
and a long session fills its context window. The usual fixes are *conventions* —
"write a handoff doc", "keep a decisions log", "run cascade after edits" — that
rely on the agent remembering to follow them. They rot: the cascade script never
gets built, lessons don't propagate, the plan drifts from reality.

Clauderizer keeps the proven conceptual model of that convention but makes it an
**active system**:

| Goal | How |
|---|---|
| **Discoverable** | Self-describing MCP tools + a SessionStart hook that injects current status into context. No reading-order ritual. |
| **Configurable** | A real `pet` / `standard` / `saas` size dial and host-language profiles — data, not prose advice. |
| **Agentic** | Cascade, pre-flight, and handoff assembly are real tool calls, not instructions the agent must remember. |
| **Drop-in** | One command clauderizes any repo, in any language. |

**Markdown is the source of truth.** The graph index is a disposable cache rebuilt
from the markdown on demand — if they ever disagree, markdown wins. No database.

## Install

```bash
pipx install "clauderizer[mcp]"   # regular use (engine + MCP server)
# or zero-install:
uvx clauderize init
```

The core engine has **no runtime dependencies**; the `mcp` extra is only needed
to run the MCP server.

## What `init` drops in

```
your-repo/
├── CLAUDE.md                    # a Clauderizer stanza (between markers)
├── .mcp.json                    # registers the clauderizer MCP server
├── .claude/
│   ├── settings.json            # SessionStart hook
│   └── skills/clauderizer-*/    # six workflow skills
├── .clauderizer/
│   ├── config.toml              # size dial + host profile + active gameplan
│   ├── profile.lock.toml        # resolved host test/build/lint commands
│   └── index.json               # disposable graph cache (gitignored)
└── docs/                        # the canonical markdown memory
    ├── VISION.md, ARCHITECTURE.md, DECISIONS.md, INVARIANTS.md, ...
    └── gameplans/
        ├── GAMEPLAN-PROCEDURE.md
        └── <date>-<name>/       # GAMEPLAN, handoffs, cascade reports, ...
```

`init` is idempotent: re-running fills gaps and refreshes engine-owned files but
never clobbers your content (marker blocks, key-scoped JSON merges, exists-checks).

## The model

- **Gameplan → Phase → Task** — a coherent initiative, broken into session-sized
  phases, broken into tasks.
- **Project DAG** — long-lived entities (`subsys.*`, `feat.*`, `ext.*`, `D-NNN`,
  `INVARIANT-NN`) declared via frontmatter; edges are `depends_on` (with semver pins).
- **Cascade** — after a tracked change, walk the DAG forward and reconcile
  dependents. It's *post-hoc and judgment-based*: the tool finds what might be
  affected and marks it "needs review"; the agent decides.
- **Cumulative handoffs** — every handoff carries all still-relevant lessons
  forward, assembled from the single canonical list.
- **Append-only memory** — decisions, invariants, hardening risks, incidents,
  corrections, and lessons are never deleted.

## CLI

```bash
clauderize init [--size pet|standard|saas] [--profile auto|node|python|go|ruby]
                [--gameplan "Name"] [--run-cmd "uvx --from clauderizer"]
clauderize status [--json]   # the current digest
clauderize doctor            # verify the install, report drift
clauderize reindex           # rebuild the graph cache from markdown
clauderize mcp               # launch the MCP server (stdio)
```

## MCP tools

Read: `cz_status`, `cz_next_phase_context`, `cz_graph_query`.
Rituals: `cz_preflight`, `cz_cascade`, `cz_write_handoff`.
Mutations: `cz_upsert_entity`, `cz_transition_status`, `cz_add_decision`,
`cz_add_invariant`, `cz_add_lesson`, `cz_add_correction`, `cz_create_gameplan`,
`cz_add_phase`, `cz_add_amendment`.
Resources: `clauderizer://status`, `clauderizer://procedure`,
`clauderizer://entity/{id}`.

## Host-language support

The engine reads/writes markdown and is agnostic to your project's language.
Support for a language is a **profile** — a data file describing its test/build/
lint/typecheck commands. Ships with Node, Python, Go, Ruby, and a generic
fallback; adding one is a new `<lang>.toml`, not code.

## Development

```bash
uv venv && . .venv/bin/activate
uv pip install -e ".[mcp,dev]"
pytest
```

## License

MIT.
