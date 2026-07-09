# Cross-Host & Cross-Model Substrate — Design & Capability Matrix

> Phase 0 deliverable of gameplan `2026-06-21-cross-host-cross-model-clauderizer-universal-agents-md-mcp-substrate`.
> Capability data verified 2026-06-21 against primary sources (each host's own docs +
> the MCP `clients.mdx`). Cells marked *(unverified)* need emitter-time confirmation.
> This doc is the enduring reference; the decisions it records live in `docs/DECISIONS.md`.

## 1. Three orthogonal host axes (D-028)

Clauderizer now reasons about three **independent** axes. Conflating any two is a bug:

| Axis | Question | Where it lives today | Example values |
|------|----------|----------------------|----------------|
| **session-host** | *Where do commands run?* | `hosts.py` | `native`, `windows-wsl:ubuntu` |
| **host-profile** | *What language is the repo?* (D-004) | `profiles/` | `python`, `node`, `go` |
| **host-target** | *Which agent tool drives the session?* | **NEW (this initiative)** | `claude-code`, `cursor`, `copilot`, … |

The `host-target` is the new first-class axis. It is **not** inferable from the other two.

## 2. The HostTarget capability descriptor

Each supported host is described by a static capability record (no enable/disable flags —
INVARIANT-05; capability is a *fact about the host*, not a user toggle):

```
HostTarget:
  id:                 str          # "cursor", "copilot", ...
  mcp:                none|tools|full
  mcp_primitives:     {tools, resources, prompts}   # subset actually usable
  resource_autoload:  bool         # does it auto-inject MCP resources? (always False — see §4)
  hooks:              none|governance|context        # 'context' = can inject into model context
  hook_events:        [str]        # e.g. ["SessionStart","UserPromptSubmit"]
  hook_os:            all|posix     # Cline hooks are POSIX-only
  instructions_file:  str          # "AGENTS.md", ".continue/rules/", "GEMINI.md", ...
  agents_md_native:   bool
  mcp_registration:   {scope: project|global|none, path: str}
  best_tier:          1|3|4        # highest injection tier reachable (Tier 2 retired)
  write_policy:       auto|guide|skip   # may auto-write project config vs ship a guide
```

## 3. Per-host capability matrix (verified 2026-06-21)

T=tools, R=resources, P=prompts. "Hook→ctx" = hook can inject into model context.

| Host | MCP prims | Resource autoload | Hooks (events) | Hook→ctx | AGENTS.md native | MCP reg (scope) | Best tier | Write |
|------|-----------|-------------------|----------------|----------|------------------|-----------------|-----------|-------|
| **Claude Code** | T,R | no | SessionStart, UserPromptSubmit | **yes** | no (CLAUDE.md imports it) | `.mcp.json` (project) | **1** | auto |
| **kimi** | T,R | no | all 4 | **yes** | yes (`KIMI_AGENTS_MD`) | `~/.kimi/config.toml` (global) | **1** | guide |
| **GitHub Copilot / VS Code** | T,R,P + sampling/elicit | no (manual @) | SessionStart, UserPromptSubmit, PreToolUse, PreCompact, Stop | **yes** | yes | `.vscode/mcp.json` (project) | **1** | auto |
| **Codex CLI** | T (+server-instructions) | no | SessionStart, UserPromptSubmit, PreToolUse, PreCompact, Stop | **yes** | yes | `.codex/config.toml` (project) | **1** | guide* (TOML) |
| **Gemini CLI** | T,R,P | no (manual @) | SessionStart, SessionEnd, BeforeAgent, AfterAgent | likely *(unverified)* | configurable (GEMINI.md default) | `.gemini/settings.json` (project) | **1** | auto |
| **Windsurf** | T,R,P | *(unverified)* | 12 events incl. pre_user_prompt | likely *(unverified)* | yes | `~/.codeium/windsurf/mcp_config.json` (**global**) | **1** | guide (MCP global) |
| **Cline** | T,R (no P) | tool-mediated | TaskStart, UserPromptSubmit, Pre/PostToolUse | **yes** (POSIX only) | per-project *(autoinject unverified)* | `.cline/mcp.json` (CLI) / global UI (ext) | **1**/4 | mixed |
| **Amp** | T (R/P unconfirmed) | no | session.start, agent.start, tool.call (plugins) | **yes** (TS plugin) | yes (originated AGENT.md) | `.amp/settings.json` (project, needs `amp mcp approve`) | **1**/4 | auto+approve |
| **Cursor** | T,R,P + roots/elicit | no (model-init) | beforeSubmitPrompt, beforeMCPExecution, stop | governance *(ctx-inject unverified)* | yes | `.cursor/mcp.json` (project) | **3**/1? | auto |
| **Continue.dev** | T,R,P | no (manual @) | none | n/a | **no** (uses `.continue/rules/`) | `.continue/mcpServers/` (project) | **3** | auto (native rules) |
| **Zed** | T,P (**no R**) | n/a | none | n/a | yes (priority #7) | `.zed/settings.json` `context_servers` (project) | **3** | auto |
| **Grok Build TUI** | T (R/P server-side; not slash-surfaced) | no | SessionStart, UserPromptSubmit, Pre/PostCompact, Pre/PostToolUse, … | **no** (passive stdout ignored) | yes (AGENTS.md + CLAUDE.md) | `.mcp.json` (project) + optional `.grok/config.toml` (TOML) | **4** (+P7 bootstrap) | auto JSON (`.mcp.json`, `.grok/hooks`); guide TOML |
| **Roo Code** | T,R | *(n/a)* | none | n/a | no | `.roo/mcp.json` (project) | — | **DROP — archived 2026-05-15** |
| **Aider** | **none** (unimpl.) | n/a | none | n/a | no (must `read:` it) | n/a | — | **DEFER — no native MCP** |

> **Grok notes** (gameplan `2026-07-09-grok-build-tui-host-support`, verified 2026-07-09 against Grok 0.2.93
> user-guide): `10-hooks.md` Passive Hooks ignore SessionStart stdout (Hook→ctx=**no**);
> `07-mcp-servers.md` loads project `.mcp.json` + `.grok/config.toml` (tools via `search_tool`/`use_tool`);
> `12-project-rules.md` AGENTS.md native; `04-slash-commands.md` slash sources = builtins + SKILL.md only
> (**no** MCP prompts as `/cz-status` → best_tier **4**, not 3). Project hooks/MCP require folder-trust
> (`/hooks-trust` or `--trust`). **Never** put `grok` in `session._HOOK_HOSTS` — that suppresses P7
> bootstrap and leaves cold sessions dark. Wired by bare `clauderize init` (multi-host
> default, D-046) or scoped `init --host grok`.

\* Codex/kimi MCP registration is TOML → see §6 (zero-dep) → guide-only or append-only stanza.

## 4. The revised injection-parity ladder (corrects D-029/D-030)

Two empirical corrections from §3, recorded as `C-` corrections:

- **Hooks are widespread, not Claude-only.** ~7–9 hosts expose `SessionStart`/`UserPromptSubmit`-class hooks. Tier 1 is broadly reachable. (Premise in D-029/D-030 was wrong.)
- **No host auto-loads MCP resources.** The "Tier 2 = auto-loaded resource" rung **does not exist on any host** and is **retired**. P3 drops the auto-resource work; resources remain only as an on-demand, model-requested convenience.

Revised ladder (highest reachable wins; deliver **once per session** — INVARIANT-08):

| Tier | Mechanism | Automatic? | Reachable on |
|------|-----------|-----------|--------------|
| **1** | Lifecycle hook injects status (host-native hook config) | **yes** | Claude Code, kimi, Copilot, Codex, Gemini, Windsurf, Cline (POSIX), Amp, (Cursor?) |
| ~~2~~ | ~~Auto-loaded MCP resource~~ | — | **RETIRED — no host supports it** |
| **3** | MCP prompt as `/cz-status` slash command | no (user-invoked) | Cursor, Copilot, Continue, Gemini, Zed |
| **4** | Instructions-file "call `cz_status` first" floor | no (suggestion) | every host that reads an instructions file |
| **(P7)** | Server-side bootstrap: status on first read-like tool result | **yes** | any MCP host — the automatic fallback where hooks are absent/governance-only (Cursor, Continue, Zed) |

**Consequence:** P7 (server-side bootstrap) is now *more* valuable, not less — it is the **only automatic** path for the hook-less Tier-3/4 hosts (Continue, Zed, and Cursor if its hooks prove governance-only).

## 5. The AGENTS.md floor is the majority — not universal — substrate (refines D-029)

AGENTS.md-native hosts (floor for free): Claude Code (via import), kimi, Copilot, Codex, Windsurf, Amp, Zed, Cursor. **Exceptions needing their native file written instead:**

- **Continue.dev** → `.continue/rules/` (no AGENTS.md)
- **Gemini CLI** → `GEMINI.md` (AGENTS.md only if configured)
- **Aider** → `CONVENTIONS.md` via `read:` config (deferred anyway)

So the floor emitter writes AGENTS.md **plus** a per-host native-instructions shim for those three.

## 6. Zero-dependency format audit (O-04) — stdlib-only invariant holds

| Format | Hosts | Stdlib-writable? | Policy |
|--------|-------|------------------|--------|
| **JSON** | Copilot, Cursor, Cline, Zed, Gemini, Amp, Continue* | yes (`json`) | **auto-write** (comments/key-order not preserved — documented, acceptable) |
| **YAML** | Continue (`.yaml` option) | no (needs PyYAML) | **avoid** — Continue also accepts **JSON** in `.continue/mcpServers/` → write JSON |
| **TOML** | Codex, kimi | read-only (`tomllib`); no stdlib writer | **guide-only OR append-only marker stanza** — never a structured rewrite |
| **Markdown** | all instructions files | yes (marker-block upsert) | **auto-write** (existing `writer.upsert_marker_block`) |

**Result:** the zero-runtime-dep invariant is preserved with no new dependency. The only friction is TOML (Codex/kimi) → those stay guide-only, consistent with kimi today.

## 7. Verification strategy (D-032)

- **Wiring contract (CI-gated, automatable):** emitted config is well-formed + path-safe; the MCP server launches; an in-process **host-simulator** (MCP client stub) reads the emitted config, connects, and round-trips `cz_status`.
- **Consumption proof (manual, pre-GA):** a real host actually reads the config and injects — irreducibly manual for the ~9 proprietary hosts; spot-check 2–3 representatives.
- **Model-agnostic claim (static):** the shared surface emits no Claude-specific syntax (grep-gated); live multi-model smoke tests are a manual checklist, not CI.

## 8. Release & versioning decisions

- **Cadence:** incremental per tier. **Floor/Tier-1 release** once the AGENTS.md+MCP+hook hosts verify; Tier-3 and bespoke hosts follow.
- **Beta gate:** cross-host coverage is evidenced by the §7 wiring-contract CI; it does **not** add a new D-012 B-gate (the gate measures memory quality, not host breadth) — but the README must state the wiring-vs-consumption distinction honestly.
- **Subsystem version coherence (O-05):** `clauderize doctor` gains a check that the installed `scaffold`/`mcp-server` versions declare support for every `host_target` recorded in config; a mismatch surfaces as drift (advisory).

## 9. Scope changes from verification

- **Drop Roo Code** — repo archived read-only 2026-05-15; not a live target.
- **Defer Aider** — no native MCP client (open feature request); revisit if/when it ships. The floor would also need explicit `read:` config, so there is no zero-touch path today.
- **Net in-scope first-class hosts:** Claude Code, kimi (done) + Copilot, Codex, Gemini, Windsurf, Cline, Amp (Tier-1 candidates) + Cursor, Continue, Zed (Tier-3/floor + bootstrap) + **Grok Build TUI** (Tier-4/floor + P7 bootstrap; governance hooks). **12 hosts** (was 11 after dropping Roo/deferring Aider; Grok added 2026-07-09).
- **Multi-host default (D-046, 2026-07-09):** bare `clauderize init` wires all project-level hosts; `--host` scopes one run. Session routing is runtime-detected (D-047); missing access is configure-on-demand advisory (D-048).
