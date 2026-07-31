---
id: subsys.kimidesktop
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.bespoke-hosts
  - subsys.winhost
  - subsys.mcp-probe
last_verified: 2026-07-25
---

# Kimi Desktop

The kimi-desktop (daimon runtime) host — the one deliberate D-031 exception (D-053), and the first implementation of `subsys.bespoke_hosts`.

## Why it is the exception

The Kimi Work desktop app embeds kimi-code via a "daimon" runtime and loads MCP servers **only** from its per-user runtime-home `mcp.json` — never the project `.mcp.json`, never `.kimi-code/mcp.json` — and exposes no hook surface. So on that host the MCP server is the *only* orientation lane, and guide-only would mean no Clauderizer at all.

Clauderizer therefore auto-writes that per-user config, under the three mitigations `subsys.bespoke_hosts` supplies: detected-only, non-destructive/atomic/idempotent, and self-healing on external entry points.

## Finding the config

- **`exists()`** — is the daimon runtime home present at all? The detected-only gate.
- **`app_data_roots()`**, **`wsl_windows_roots()`** — the per-user locations, on Windows directly and as seen from WSL.
- **`candidate_configs()`**, **`detect_config()`** — the discovery.

The WSL variants exist because this is routinely a cross-OS setup: a Windows desktop app, a repo living in WSL. `subsys.winhost` supplies the `C:\` ↔ `/mnt/<drive>` translation that makes both vantages work.

## Composing the server entry

- **`server_entry(...)`** — the `{command, args}` written into the daimon's config.
- **`merge_entry(...)`**, **`remove_entry(...)`** — the non-destructive write and its reversal.
- **`wire(...)`** — the whole registration.
- **`KimiDesktopHost`** — the `BespokeHost` subclass, registered into the framework.

The command is a Windows-native `clauderizer-mcp.exe` rather than a bare `uvx`: the app may bundle `uv.exe` but not `uvx.exe`, so `uvx` can never spawn there.

## The serve pin, and why it lives in a sidecar

- **`serve_pin_path()`**, **`read_serve_pin(cfg)`**, **`write_serve_pin(...)`**, **`clear_serve_pin(...)`** — the durable override.
- **`self_heal(...)`** — re-compose from the sidecar and re-probe.

The daimon **regenerates** its `mcp.json`, sometimes to `{}`. Any override read back from the live config is therefore gone after a regeneration, and self-heal that trusted the live config would silently revert to the default. The pin lives in a sidecar the app does not touch, and self-heal re-composes from it.

## The UNC problem

- **`setup_guide()`** — the recovery playbook.

Windows cannot spawn a process with a `\\wsl.localhost\…` working directory, so a repo in WSL opened from the desktop app yields a dead shell. `--serve-wsl-here` pins the MCP server past that (the shell stays broken); the permanent fixes are moving the repo to the Windows filesystem or using Kimi Code CLI inside WSL. A `wsl.exe` MCP wrapper does **not** help. The guide says all of this, and names `docs/` so the agent reads memory directly with file tools, which do work.

The per-server `cwd` this relies on was confirmed by reading the app bundle's config normalizer **and** completing a live `initialize` handshake against a real WSL repo over UNC — and the tempting alternative, an in-WSL `executor` value, was ruled out by reading the bundle's validated executor set rather than assuming it existed (L-66).

## Two products, not one

Moonshot's **Kimi CLI** (`~/.kimi/`, pip) and **Kimi Code CLI** (`.kimi-code/`, npm) are different tools, and the successor does not read `.claude/skills`. Verifying that split from upstream docs — rather than treating it as one product that moved — is why the wiring targets the right paths.

## DAG position

Depends on `subsys.bespoke_hosts` (the framework), `subsys.winhost` (path translation) and `subsys.mcp_probe` (the handshake proof). Registered into the bespoke-host registry by import.
