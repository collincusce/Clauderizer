---
id: subsys.mcp-probe
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.winhost
last_verified: 2026-07-25
---

# MCP Probe

MCP `initialize`-handshake verification — a host-agnostic **capability** probe (D-056).

## Presence is not capability

A wiring check that confirms a config file contains the right JSON has verified nothing about whether the command in it can run. L-25 states the rule: a health check must verify capability, not presence, because a green check on a non-launchable setup is worse than no check at all — it converts an unknown into a false assurance.

So this module does what an MCP client does. It spawns the composed `{command, args}` **from a non-repo cwd** — the way a client actually launches it, not the way a developer tests it from inside the project — completes an MCP `initialize` handshake over stdio, and asserts `serverInfo.name == "clauderizer"`. Anything less is presence.

It mirrors `hosts.spawn_probe` / `verify_wiring`, which do the same job for the SessionStart hook. This one is for an MCP server command.

## Two facts that were verified, not assumed

- **MCP stdio is newline-delimited JSON-RPC**, not `Content-Length`-framed. Getting this wrong produces a probe that hangs rather than one that fails, which is the worse failure.
- **A Windows `clauderizer-mcp.exe` registered for a desktop host is spawnable from WSL**, by translating its `C:\` path to the `/mnt/<drive>` interop path (`subsys.winhost`). That means a cross-OS command is a real green — not `unverifiable`. `unverifiable` is reserved for a target genuinely unreachable from the probing host, and keeping that verdict narrow is what stops it from becoming a synonym for "did not try".

## The surface

- **`init_request()`** — the JSON-RPC `initialize` payload.
- **`spawn_target(...)`** — `(argv, unreachable_reason)`. What *this* host can spawn to reach the registered command, or a stated reason it cannot. Returning the reason rather than a bare `None` is what lets `doctor` distinguish "broken" from "not checkable from here".
- **`server_info(lines)`** — the `result.serverInfo` from the first JSON-RPC line that carries it, tolerating banner noise on stdout before the response.
- **`handshake_probe(...)`** — the whole thing: spawn from a non-repo cwd, handshake, assert the server identity.
- **`default_run(...)`** — the injectable subprocess runner, so tests can drive the probe without spawning.

## Three-state honesty

Verdicts follow the same discipline as `doctor` and `release_check` (D-010): `ok` shows its evidence, `fail` is red, and a target this host genuinely cannot reach is `unverifiable` — never a false green.

## DAG position

Depends on `subsys.winhost` for the cross-OS path translation. Consumed by `hosttargets` (verifying an emitted registration) and by `cli` (`doctor`). `subsys.bespoke_hosts` requires it: an auto-written per-user config that was never proven launchable is precisely the false green D-056's mitigations exist to prevent.
