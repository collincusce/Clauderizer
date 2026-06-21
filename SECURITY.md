# Security Policy

## Reporting a vulnerability

Use GitHub's private vulnerability reporting on this repository
(Security → "Report a vulnerability"), or open an issue if the report is
not sensitive. Reports are read by the maintainer; please include the
engine version (`clauderize --version`) and, for wiring issues, the output
of `clauderize doctor`.

## Scope and model

Clauderizer writes repo-local files that register commands your agent
harness executes: its MCP server (and, on hook-capable hosts,
SessionStart/UserPromptSubmit hooks). It supports a range of hosts, so the
registration lands in a **host-specific config file** (e.g. `.mcp.json`,
`.cursor/mcp.json`, `.vscode/mcp.json`) — always as a non-destructive
key-merge that preserves any other servers. The full statement of what is
written per host, what executes when, under which contracts, and what
happens when you clone a repo that already carries the wiring lives in
**[docs/TRUST.md](docs/TRUST.md)** — behavioral claims there that disagree
with the code are treated as bugs. To remove the registration cleanly from
every host, run `clauderize uninstall` (it strips only the `clauderizer`
key).

## Supported versions

Pre-1.0: only the latest released version is supported. The findings
tracker (`docs/HARDENING.md`) is public and append-only; resolved findings
carry dated evidence.
