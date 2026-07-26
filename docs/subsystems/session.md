---
id: subsys.session
type: subsystem
version: 1.0.0
status: active
depends_on:
last_verified: 2026-07-25
---

# Session

The in-memory, per-process delivery signal behind INVARIANT-08 — status reaches the model **at most once per session**, across every active injection tier.

## The problem it solves

The cross-host injection-parity ladder (D-034, `docs/CROSS-HOST.md`) gives the status digest several routes to the model. On hook hosts — Claude Code, Copilot, Codex, Gemini CLI, Windsurf, Cline, Amp — the host's own lifecycle hook delivers it. On hook-less hosts the MCP server is the only automatic path, via the write-first self-correction and the Phase-7 bootstrap. With more than one live route, the same digest can arrive twice; INVARIANT-08 forbids that, and D-027 wants the injected text minimal anyway.

The signal is a **process-global flag, in memory only**. Never persisted, never a config or enable flag — INVARIANT-05 rules out the config flag and INVARIANT-08 rules out the persisted one. It is meaningful only inside the long-lived MCP server process. The stateless `clauderize ops` CLI is a fresh process per call, so the flag is always `False` there, and it never injects regardless, because the gate treats a hook host as the default and the CLI is not a model session.

Where the flag cannot help is nested installs — two processes, each correct about its own repo. That is `subsys.nesting`'s ownership test, not this module's.

## The flag

- **`mark_status_delivered()`** — record that the digest has reached the model this session.
- **`status_delivered()`** — read it, without side effects.
- **`reset()`** — test-only, to clear the signal between cases. Never called in production; a production reset would be exactly the persisted-state mistake the design avoids.

## The routing gate

- **`detect_session_agent()`** — best-effort id of the agent tool running this process, from the environment, or `None` when unknown.
- **`effective_host_target()`** — the host id used for injection routing (D-047), falling back to `DEFAULT_HOST_TARGET` (`claude-code`).
- **`delivers_status_via_hook()`** — whether the host's own lifecycle hook already delivers the digest, in which case the server must stay silent.
- **`best_tier()`** — the highest injection tier the host supports on the D-034 ladder: 1 = lifecycle hook, descending to the AGENTS.md floor.
- **`should_inject()`** — the server-side bootstrap gate: the whole decision in one call.
- **`status_note()`** — the compact bootstrap note. Deliberately not the full digest (D-027: focused, one line).

## The two deliberate absences

`_HOOK_HOSTS` is the code form of the `CROSS-HOST.md` capability matrix, and two hosts are **intentionally missing** from it. Both omissions are load-bearing, and both would look like bugs to a reader who did not know why:

- **Grok Build TUI** has lifecycle hooks, but passive SessionStart stdout is ignored (Hook→ctx=no). Listing it would suppress the P7 server bootstrap and leave cold sessions dark.
- **Kimi Code CLI** hooks *do* inject on exit 0, but Clauderizer cannot auto-wire them (D-050): MCP is auto-written to `.kimi-code/mcp.json` while the hooks stay a guide, because editing the user's global `~/.kimi-code/config.toml` is out of bounds. A default-init kimi repo therefore has no status-delivering hook, so the automatic path is the P7 bootstrap. Claiming auto hook-delivery here would risk the same dark-session trap as grok.

## Purity

Everything here is IO-free and unit-testable on its own. The server (`mcp_server.py`) supplies the live status string and applies the result; this module only decides.

## DAG position

Depends on nothing. Consumed by `mcp_server` for the bootstrap gate. Its guarantee is the one `subsys.nesting` extends to the multi-process case.
