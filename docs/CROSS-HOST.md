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
| **kimi (Kimi Code CLI)** | T,R | no | 13 events (4 inject) | **yes** (manual) | likely *(unverified)* | `.kimi-code/mcp.json` (project) | **1** if hooks wired, else P7 bootstrap | auto (MCP); guide (hooks TOML) |
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

\* Codex MCP registration is TOML → see §6 (zero-dep) → guide-only or append-only stanza.
Kimi Code CLI's MCP is a project **JSON** config (`.kimi-code/mcp.json`) → auto-write; only
its session-start hooks are TOML (`~/.kimi-code/config.toml`) → guide-only.

## 4. The revised injection-parity ladder (corrects D-029/D-030)

Two empirical corrections from §3, recorded as `C-` corrections:

- **Hooks are widespread, not Claude-only.** ~7–9 hosts expose `SessionStart`/`UserPromptSubmit`-class hooks. Tier 1 is broadly reachable. (Premise in D-029/D-030 was wrong.)
- **No host auto-loads MCP resources.** The "Tier 2 = auto-loaded resource" rung **does not exist on any host** and is **retired**. P3 drops the auto-resource work; resources remain only as an on-demand, model-requested convenience.

Revised ladder (highest reachable wins; deliver **once per session** — INVARIANT-08):

| Tier | Mechanism | Automatic? | Reachable on |
|------|-----------|-----------|--------------|
| **1** | Lifecycle hook injects status (host-native hook config) | **yes** | Claude Code, Copilot, Codex, Gemini, Windsurf, Cline (POSIX), Amp, kimi *(manual wiring — hook is guide-only, D-050)*, (Cursor?) |
| ~~2~~ | ~~Auto-loaded MCP resource~~ | — | **RETIRED — no host supports it** |
| **3** | MCP prompt as `/cz-status` slash command | no (user-invoked) | Cursor, Copilot, Continue, Gemini, Zed |
| **4** | Instructions-file "call `cz_status` first" floor | no (suggestion) | every host that reads an instructions file |
| **(P7)** | Server-side bootstrap: status on first read-like tool result | **yes** | any MCP host — the automatic fallback where hooks are absent/governance-only/not-auto-wired (Cursor, Continue, Zed, **kimi**) |

**Consequence:** P7 (server-side bootstrap) is now *more* valuable, not less — it is the **only automatic** path for the hook-less Tier-3/4 hosts (Continue, Zed, Cursor if its hooks prove governance-only) **and for kimi**, whose hook injects but is guide-only (not auto-wired), so a default `init` repo relies on the bootstrap until the user pastes the hook (D-050).

## 5. The AGENTS.md floor is the majority — not universal — substrate (refines D-029)

AGENTS.md-native hosts (floor for free): Claude Code (via import), Copilot, Codex, Windsurf, Amp, Zed, Cursor. (**kimi / Kimi Code CLI**: AGENTS.md read-status is *unverified* — the legacy Kimi CLI read it via `KIMI_AGENTS_MD`, but Kimi Code CLI's docs don't confirm it; orientation there does not depend on it — the P7 bootstrap covers it, D-050.) **Exceptions needing their native file written instead:**

- **Continue.dev** → `.continue/rules/` (no AGENTS.md)
- **Gemini CLI** → `GEMINI.md` (AGENTS.md only if configured)
- **Aider** → `CONVENTIONS.md` via `read:` config (deferred anyway)

So the floor emitter writes AGENTS.md **plus** a per-host native-instructions shim for those three.

## 6. Zero-dependency format audit (O-04) — stdlib-only invariant holds

| Format | Hosts | Stdlib-writable? | Policy |
|--------|-------|------------------|--------|
| **JSON** | Copilot, Cursor, Cline, Zed, Gemini, Amp, Continue* | yes (`json`) | **auto-write** (comments/key-order not preserved — documented, acceptable) |
| **YAML** | Continue (`.yaml` option) | no (needs PyYAML) | **avoid** — Continue also accepts **JSON** in `.continue/mcpServers/` → write JSON |
| **TOML** | Codex, kimi (hooks only) | read-only (`tomllib`); no stdlib writer | **guide-only OR append-only marker stanza** — never a structured rewrite |
| **Markdown** | all instructions files | yes (marker-block upsert) | **auto-write** (existing `writer.upsert_marker_block`) |

**Result:** the zero-runtime-dep invariant is preserved with no new dependency. The only friction is TOML (Codex, and Kimi Code CLI's *hooks*) → those stay guide-only. Kimi Code CLI's **MCP** is project JSON (`.kimi-code/mcp.json`) → auto-write (D-049).

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
- **Net in-scope first-class hosts:** Claude Code, kimi (done) + Copilot, Codex, Gemini, Windsurf, Cline, Amp (Tier-1 candidates) + Cursor, Continue, Zed (Tier-3/floor + bootstrap) + **Grok Build TUI** (Tier-4/floor + P7 bootstrap; governance hooks) + **Kimi Work desktop / daimon** (auto-write host, added 2026-07-17). **13 hosts** (was 11 after dropping Roo/deferring Aider; Grok added 2026-07-09; Kimi desktop added 2026-07-17).

> **Kimi Work desktop (daimon runtime)** — a distinct host from the Kimi Code CLI (D-053). Loads MCP servers only from its per-user runtime-home `mcp.json` (`…/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/mcp.json`); reads no project config and exposes no hooks, so the MCP server is its only orientation lane. `clauderize init` **auto-writes** that per-user config — the single deliberate exception to D-031's global-config→guide-only rule, justified by UX — detected-only, non-destructive/atomic, with a **repo-agnostic** command (the server serves the repo the app opens). The command is **host-topology-specific** (D-055): a Windows daimon host gets the **absolute path to a Windows-native `clauderizer-mcp.exe`** (the app bundles `uv.exe` but not `uvx.exe`, so a bare `uvx` can never spawn there); macOS/Linux get absolute `uvx`. Registration is **self-healing** — the app regenerates its `mcp.json` on project switch and merges from no persistent source, so every `init`/`doctor`/`status` re-applies the entry (idempotent) — and `doctor` **smoke-tests** it end-to-end with an MCP `initialize` handshake (asserts `serverInfo.name == clauderizer`). A repo living only in WSL with the app on Windows can't be served by the repo-agnostic entry (UNC-cwd spawn limit, D-054); by default the `.exe` entry serves Windows-hosted repos and `init`/`doctor` print the UNC guidance. **Opt-in override (D-057):** `clauderize init --serve-wsl-here` (run in the WSL repo) pins the desktop to serve THAT repo via `{args: ["--repo", "\\wsl.localhost\…"], cwd: "C:\Users\…"}` — the daimon runtime honors a per-server `cwd`, so the server spawns from a Windows-safe cwd and reads the repo over UNC. It's recorded in a `clauderizer-serve.json` sidecar so self-heal survives the app's `mcp.json` wipe, and `doctor` reports which repo it serves (the one tradeoff: a single per-user file, so it serves that repo for every project opened). Unpin via `clauderize uninstall`. Opt out of the host entirely with `CLAUDERIZER_NO_KIMI_DESKTOP=1`.
> **Adding a bespoke auto-write host (D-056)** — kimi-desktop is the first of a *class*: an app whose MCP servers load only from a per-user config it owns (and often regenerates), with no hook surface. Such hosts share a framework in `bespoke_hosts.py` so a new one is an **implementation, not a re-implementation**. Recipe:
> 1. **Subclass `BespokeHost`** (in its own module, e.g. `foo_desktop.py`). Set `id` (also the `.clauderizer/<id>-mcp-setup.md` guide filename), `opt_out_env` (`CLAUDERIZER_NO_<HOST>`), and `servers_key` (the JSON key holding MCP servers). Override only the **variable parts**: `candidate_configs()` (ordered per-user config paths), `compose_entry()` (the `{command, args}` server entry, host-topology-aware — reuse `winhost` for a Windows-native `clauderizer-mcp.exe` and `C:\`↔`/mnt` translation), `setup_guide()`, and optionally `unservable_reason()` (guidance when the app is detected but can't serve *this* repo, e.g. a UNC-cwd spawn limit).
> 2. **Register it**: `_HOST = bespoke_hosts.register(FooDesktopHost())` at module top, and add `from . import foo_desktop` to `bespoke_hosts.all_hosts()` so the registry self-bootstraps (a real `clauderize doctor` won't import your module otherwise).
> 3. **Inherit the rest**: the detect → non-destructive/atomic/idempotent merge → `self_heal` → `remove_registration` lifecycle, the `mcp_probe` `initialize`-handshake verification (`doctor` and `doctor --deep`), and the init/doctor/status/uninstall wiring all run generically over the registry — you write no entry-point code.
> 4. **Test** with a temp config (never a real per-user path — L-29; guard init side-effects behind your `opt_out_env` + an autouse fixture that sets it), and add a fresh-subprocess check that `all_hosts()` still lists your host.

- **Multi-host default (D-046, 2026-07-09):** bare `clauderize init` wires all project-level hosts; `--host` scopes one run. Session routing is runtime-detected (D-047); missing access is configure-on-demand advisory (D-048).
