---
id: subsys.bespoke-hosts
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.hosttargets
  - subsys.mcp-probe
last_verified: 2026-07-25
---

# Bespoke Hosts

The framework for **bespoke auto-write MCP hosts** (D-056).

## What qualifies

A *bespoke auto-write host* is one whose MCP servers load **only** from a per-user config the app owns — often regenerating it — never from this repo's project config, and with no hook surface. For such a host, the MCP server is the only orientation lane, and a guide-only approach means the host simply never gets Clauderizer.

So the engine auto-writes that per-user config. This is the **single sanctioned exception** to "global config → guide-only" (D-031), justified purely by UX (D-053).

## Three mitigations that keep the exception narrow

They live *here*, in the base class, so every such host inherits them rather than re-deriving them:

- **Detected-only** — write only when the app's config directory already exists. Clauderizer never creates a config for an app that is not installed.
- **Non-destructive, atomic, idempotent** — merge only the `clauderizer` server, via temp-write plus `os.replace`, and skip the write entirely when the entry is already current. A reader sees old-or-new, never torn.
- **Self-healing** — re-applied on every write-permitted entry point.

## Why self-healing has to ride external entry points

The host owns the config file, and a host that **regenerates** it on context-switch cannot bootstrap its own re-heal: once the entry is wiped, that host's MCP server is not loaded, so nothing running on it can re-register.

Durable registration therefore rides *other* CLI runs on the same machine — `init`, `doctor`, `status` — which are write-permitted and idempotent, so re-applying is a safe no-op. It can never be a hook (INVARIANT-06) nor an MCP read op (L-03), because both are read-only by construction.

Per-host **override** state (a `--repo` pin, a custom cwd) must live in a durable **sidecar** the host leaves alone. Self-heal re-composes the override from the sidecar and re-probes the volatile bits. Reading the override back from the live config is a same-session fallback, never durability: when the host's regeneration wipes its `mcp.json` to `{}`, the override is simply gone, and self-heal that reads it back from the current config finds nothing and silently reverts to the default.

## The surface

- **`BespokeHost`** — the base. Subclasses set `id` and `opt_out_env` and implement the host-specific config discovery and server-entry composition.
- **`merge_entry(...)`**, **`read_entry(...)`**, **`remove_entry(...)`** — the non-destructive primitives.
- **`register(host)`**, **`all_hosts()`** — the registry.

## The registry is populated by import

`register(Impl())` runs at module top, which means the registry is **empty until something imports the implementation module** (L-60). A consumer that iterates `all_hosts()` without having imported the concrete hosts gets an empty list and no error — the worst shape of failure, because it looks like "no bespoke hosts configured". The import is therefore explicit at the entry points, and tested.

## Opt-out and proof

Every bespoke host honours an `opt_out_env` variable, which is also what keeps the test suite from mutating real machine state: any step writing an absolute per-user path outside the repo would otherwise touch the developer's actual config (L-29). The suite sets the opt-out and asserts the real file is byte-unchanged after a full run.

Registration is verified by **capability** — `subsys.mcp_probe` spawns the command the way the consumer will and completes a real MCP `initialize` handshake asserting `serverInfo.name` (L-25).

## DAG position

Depends on `subsys.hosttargets` (the emitter vocabulary it extends) and `subsys.mcp_probe` (the capability proof). `subsys.kimidesktop` is the first and currently only implementation. Imported by `cli` at the entry points that must self-heal.
