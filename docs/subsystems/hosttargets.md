---
id: subsys.hosttargets
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.hosts
  - subsys.mcp-probe
last_verified: 2026-07-25
---

# Host Targets

Per-host wiring emitters: write Clauderizer's MCP registration into each host's own project config, non-destructively, with a **portable** command.

## The last mile

The cross-host substrate (D-029) already gives every host the `cz_*` tools over MCP and the AGENTS.md floor. This module tells each host *where* its MCP-server registration lives and writes it there — without clobbering the user's other servers, which is the top config-safety risk (D-031).

## Portable, or it must not ship

The emitted command is machine-**independent**: `uvx` resolves `clauderizer` from PyPI. A committable config must never carry an absolute venv path or a `wsl.exe` username shim — which is exactly what this repo's local dogfood `.mcp.json` carries, and exactly what must not ship.

- **`is_path_safe(argv)`** — the predicate.
- **`path_safety_audit(repo_root)`** — every non-gitignored host config carrying a machine-specific command. Gitignored configs are skipped deliberately: a dogfood repo keeps a local, gitignored `.mcp.json` pointing at its editable build, and auditing that would be a false alarm.

## Auto-write versus guide-only

- **JSON project configs are auto-written** — `.cursor/mcp.json`, `.codex/…`, and the rest, via `HostEmitter` table entries.
- **Global-config and TOML hosts are guide-only** (D-031, O-04). The engine writes a setup guide; the user merges it. Editing a per-user config that every repo shares is not the engine's call.

`subsys.bespoke_hosts` is the one sanctioned exception to that rule, kept narrow by its own mitigations.

- **`HostEmitter`** — the table entry: host id, config path, servers key, auto-write flag. **`EmitResult`** — one file written or left unchanged, with `changed`.
- **`emit_mcp(host, root)`**, **`emit_host_wiring(...)`**, **`remove_mcp(...)`** — write and reverse.
- **`emit_instructions(...)`** — the AGENTS.md floor.
- **`read_foreign_json(path)`** — read a host's config **preserving what we do not own**. The whole non-destructive guarantee rests here: merge only the `clauderizer` server, leave every other key byte-identical.

## Guides and hooks

- **`mcp_setup_guide(...)`**, **`hook_setup_guide(...)`**, **`kimi_setup_guide(...)`**, **`grok_setup_guide(...)`** — the guide-only artifacts.
- **`grok_hooks_payload(...)`**, **`emit_grok_hooks(...)`**, **`remove_grok_hooks(...)`** — Grok's hook surface, which is auto-writable where its MCP config is not.

## Scope, not exclusivity

- **`valid_host_targets()`**, **`parse_host_target(v)`**, **`detect_host_target(...)`**, **`all_host_ids()`**, **`HostTargetError`** — the vocabulary.
- **`expand_enabled_hosts(...)`**, **`hosts_to_wire(...)`**, **`configure_hints(...)`** — which hosts this run touches.

Exclusive `--host` is the wrong default for a multi-AI repo (L-48): all project-level hosts are wired by default (`enabled = ["*"]`), and `--host` is a **scope filter**, not an identity. A bare re-init expands rather than narrowing.

## Verification

- **`verify_emitted_wiring(...)`** — capability, via `subsys.mcp_probe`'s handshake, not mere file presence (L-25).
- **`wiring_contract_sweep(...)`** — every host's emitted wiring checked against the contract at once, so a host added later cannot quietly skip the rules.

## DAG position

Depends on `subsys.hosts` and `subsys.mcp_probe`. Consumed by `cli` (`init`, `doctor`, `uninstall`) and extended by `subsys.bespoke_hosts`.
