# Clauderizer

### Durable, structured memory for AI agents — drop it into any repo in one command.

```bash
uvx clauderize init
```

Clauderizer gives a stateless coding agent something it normally lacks: a **memory that
survives the end of the session and the end of the context window.** Plans, decisions,
invariants, a dependency graph, and findings live as plain, git-diffable markdown — and
an MCP server turns reading and updating that memory into real tool calls the agent can
just *use*.

It's the active, MCP-native successor to a battle-tested markdown "gameplan" convention —
and it was built by dogfooding itself: Clauderizer planned and tracked its own construction.

---

## The problem it kills

Long-running AI work hits two walls:

1. **A fresh session starts blank.** Every "where were we?" is re-derived from scratch — or re-explained by you for the tenth time.
2. **A long session fills its context window** mid-task and forgets its own earlier decisions.

The usual answer is *conventions*: "keep a decisions log," "write a handoff," "run cascade
after edits." But conventions rely on the agent **remembering to follow them**, so they rot —
the cascade script never gets built, lessons stop propagating, the plan quietly drifts from
reality. (If you've watched an agent confidently contradict a decision it made an hour ago,
you know the failure mode.)

Clauderizer keeps the proven *model* of that convention and makes it a **system** instead of a
hope:

| Goal | How |
|---|---|
| 🔎 **Discoverable** | Self-describing MCP tools + a SessionStart hook that injects current status into context. No "read these 7 files in this order" ritual. |
| 🎛️ **Configurable** | A real `pet` / `standard` / `saas` size dial and host-language profiles — *data*, not prose advice. |
| 🤖 **Agentic** | Cascade, pre-flight, and handoff assembly are real tool calls — not instructions the agent has to remember to run. |
| 📦 **Drop-in** | One command clauderizes any repo, in any language. |

> **Markdown is the source of truth.** The graph index is a disposable cache rebuilt from the
> markdown on demand — if they ever disagree, markdown wins. No database, no lock-in: your
> memory is just readable files in `docs/`.

---

## What a session actually feels like

You open a fresh agent session in a clauderized repo. Before you type anything, the
SessionStart hook has already injected:

```
[Clauderizer] Gameplan 2026-06-05-launch: Phase 3/8 IN PROGRESS — "Wallet review".
Baseline: 142 tests passing. Pending cascades: 0.
Next: cz_next_phase_context, then cz_preflight.
Tools: cz_status, cz_next_phase_context, cz_cascade, cz_preflight, cz_write_handoff, …
```

The agent now *knows where things stand* and what to do next — no reading order, no re-briefing.
A typical loop:

```
cz_next_phase_context   → the full bundle for this phase (read-only; assembles, doesn't write)
cz_preflight            → runs the host project's real tests/build/lint, for real, not "claimed"
… do the work …
cz_add_decision / cz_add_invariant / cz_add_finding / cz_upsert_entity   → structured records
cz_cascade              → walk the graph, flag dependents that may need updating
cz_write_handoff        → assemble the next cumulative handoff (all still-relevant lessons)
```

Every write goes through one idempotent path, so IDs auto-number and frontmatter stays valid —
the agent never hand-mangles your docs.

---

## Install

```bash
pipx install "clauderizer[mcp]"   # regular use (engine + MCP server)
# or zero-install:
uvx clauderize init
```

The core engine has **no runtime dependencies**; the `mcp` extra is only needed to run the
MCP server. `init` prefers the installed `clauderizer-mcp`/`clauderizer-hook` scripts (venv /
pipx) and falls back to `uvx` only when nothing's on your PATH — so it wires up correctly on
native Linux, macOS, and Windows→WSL alike.

## What `init` drops in

```
your-repo/
├── CLAUDE.md                    # a Clauderizer stanza (between markers — your text is preserved)
├── .mcp.json                    # registers the clauderizer MCP server
├── .claude/
│   ├── settings.json            # SessionStart hook
│   └── skills/clauderizer-*/    # six workflow skills (/do-phase, /cascade, /record, …)
├── .clauderizer/
│   ├── config.toml              # size dial + host profile + active gameplan
│   ├── profile.lock.toml        # per-project test/build/lint commands (editable override)
│   └── index.json               # disposable graph cache (gitignored)
└── docs/                        # the canonical markdown memory
    ├── VISION.md, ARCHITECTURE.md, DECISIONS.md, INVARIANTS.md, HARDENING.md, …
    └── gameplans/
        ├── GAMEPLAN-PROCEDURE.md
        └── <date>-<name>/       # GAMEPLAN, handoffs, cascade reports, status
```

`init` is **idempotent**: re-running fills gaps and refreshes engine-owned files but never
clobbers your content (marker blocks, key-scoped JSON merges, exists-checks). Run
`clauderize doctor` any time to verify the install is not just *present* but actually
*runnable* (it probes that the MCP/hook commands can launch — a green check on a broken
setup is worse than no check).

## The model

- **Gameplan → Phase → Task** — a coherent initiative, broken into session-sized phases,
  broken into tasks.
- **Project DAG** — long-lived entities (`subsys.*`, `feat.*`, `ext.*`, `D-NNN`, `INVARIANT-NN`)
  declared via frontmatter; edges are `depends_on` (with semver pins). Query it with
  `cz_graph_query`.
- **Cascade** — after a tracked change, walk the DAG forward and reconcile dependents. It's
  *post-hoc and judgment-based*: the tool finds what might be affected and marks it "needs
  review"; the agent decides. (No more "I'll build the cascade script later" — it's built in.)
- **Cumulative handoffs** — every handoff carries all still-relevant lessons forward,
  assembled from one canonical list, so phase N+3 never repeats a mistake phase N already solved.
- **Append-only memory** — decisions, invariants, hardening findings, incidents, corrections,
  and lessons are never deleted, only superseded. A permanent audit trail.

## CLI

```bash
clauderize init [--size pet|standard|saas] [--profile auto|node|python|go|ruby]
                [--gameplan "Name"] [--run-cmd "uvx --from clauderizer"]
clauderize status [--json]   # the current digest
clauderize doctor            # verify the install is present AND runnable; report drift
clauderize reindex           # rebuild the graph cache from markdown
clauderize mcp               # launch the MCP server (stdio)
```

## MCP surface

**Read** · `cz_status` · `cz_next_phase_context` · `cz_graph_query`
**Rituals** · `cz_preflight` · `cz_cascade` · `cz_write_handoff`
**Mutations** · `cz_create_gameplan` · `cz_add_phase` · `cz_add_amendment` · `cz_add_decision`
· `cz_add_invariant` · `cz_add_finding` · `cz_add_lesson` · `cz_add_correction`
· `cz_upsert_entity` · `cz_transition_status`
**Resources** · `clauderizer://status` · `clauderizer://procedure` · `clauderizer://entity/{id}`

The tools are deliberately separate and self-describing rather than one generic `mutate` — that's
the whole point of going MCP-native: an agent dropped into the repo *discovers* the workflow from
the tool schemas, no documentation pass required.

## Configurable two ways

**Size dial** — `pet` (just a gameplan + handoffs), `standard` (named docs + cascade + full
7-check preflight), `saas` (the full doc set + incidents + amendments). It governs which doc
modules and rituals are active. It's a data manifest, not a fork.

**Host-language profiles** — the engine reads/writes markdown and is agnostic to your project's
language. Support for a language is a *profile*: a data file describing its test/build/lint/
typecheck commands. Ships with Node, Python, Go, Ruby, and a generic fallback; need per-project
commands? Edit `.clauderizer/profile.lock.toml` and they take effect. Adding a language is a new
`<lang>.toml`, not code.

## Development

```bash
uv venv && . .venv/bin/activate
uv pip install -e ".[mcp,dev]"
pytest
```

## License

MIT.
