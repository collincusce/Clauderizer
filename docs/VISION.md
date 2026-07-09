# Vision

## What & Why

Clauderizer is **git-native working memory for coding agents** — durable project
memory that survives the end of a session and the end of the context window. Plans,
decisions, invariants, a dependency graph, and findings live as plain, git-diffable
markdown under `docs/`, and an MCP server turns reading and updating that memory into
real tool calls the agent just *uses*.

It exists because long-running AI work hits two walls: a fresh session starts blank
(every "where were we?" re-derived from scratch), and a long session fills its context
window mid-task and forgets its own earlier decisions. The usual answer — *conventions*
("keep a decisions log", "run cascade after edits") — rots, because conventions rely on
the agent remembering to follow them. Clauderizer keeps the proven model of that
convention and makes it a **system**: discoverable (lifecycle hooks inject status into
context), configurable (a real size dial + host-language profiles), agentic (cascade,
pre-flight, and handoff assembly are tool calls, not reminders), and drop-in (one command
clauderizes any repo).

## Differentiation

- **Markdown is the source of truth.** The graph index is a disposable cache rebuilt from
  the markdown on demand — if they disagree, markdown wins. No database, no lock-in.
- **MCP-native, not prose advice.** An agent dropped into the repo discovers the whole
  workflow from self-describing tool schemas — no "read these N files in this order" ritual.
- **Memory lives in the repo**, where it ships, diffs, and reviews with the code — not
  following a person (personal-assistant memory) and not rotting in a fat `CLAUDE.md`.
- **Rituals execute.** Cascade walks the graph, pre-flight runs your *real* tests/build,
  handoffs assemble cumulatively — operations, not instructions to remember.
- **Append-only memory with consolidation pressure, not caps.** Nothing is ever
  auto-deleted; overlap is synthesized and the enduring promoted.
- **Many gameplans at once, each its own kind.** Run a feature build, a standing
  maintenance loop, and a creative campaign side by side — the engine tracks the
  whole portfolio, focuses one at a time, speaks each kind's own vocabulary (a
  campaign's "stages" and "assets" over the same canonical structure), runs each
  kind's own quality gates, tracks a campaign's deliverables through their
  lifecycle, and propagates a dependency from one axis to another automatically.
- **Memory that knows who it's for.** A rule can belong to one gameplan (a
  campaign's brand law stays out of every other gameplan's context) or to one
  working role (the copywriter's context skips the render-engine gotchas) —
  filtering at read time, never hiding anything from the canonical record. Human
  sign-offs bind to the approved artifact's content, so an edited artifact
  visibly re-opens its approval.
- **Upgrades deliver themselves.** `clauderize upgrade` brings an existing repo
  up to the engine's current capabilities: mechanical changes apply (config
  migrations, example files, the procedure document), and anything touching
  recorded memory is proposed — never auto-edited.
- **Addressable, summary-first recall.** A compact per-entry index lets the agent
  pull exactly the decision, invariant, or lesson it needs — and see a one-line
  summary inline — instead of loading a whole file; like the graph index it is
  disposable and always rebuilt from the markdown.
- **Host- and model-portable, not a Claude-only bet.** A host-neutral MCP server plus an
  `AGENTS.md` floor reach 12 agents (Claude Code, Cursor, Copilot, Codex, Gemini CLI,
  Windsurf, Cline, Amp, Continue, Zed, kimi, Grok Build TUI); an injection-parity ladder delivers status by
  the best tier each host supports (hook → `/cz-status` prompt → instructions floor).
- **Zero runtime dependencies**; works on native Linux/macOS and Windows→WSL alike.

## Scope Boundaries

- **Per-repo project memory, not a global/personal assistant memory.** It records what
  belongs to *this* codebase.
- **Deterministic, not ML.** Relevance ranking is lexical (keyword + entity-id overlap) —
  no embeddings, no new dependency. The engine surfaces; the agent decides.
- **Language-agnostic, not a build/test/CI tool.** It reads and writes markdown and shells
  out to host-*profile* commands; it never hardcodes a language or runs your pipeline.
- **It surfaces and reports; it never blocks.** Cascade and the discipline gates are
  advisory and judgment-based — they flag, the agent rules (INVARIANT-05).
- **Not a replacement for git history or the code** — it captures the rationale, plan, and
  dependency graph that commits and source don't.
