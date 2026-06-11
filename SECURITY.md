# Security Policy

## Reporting a vulnerability

Use GitHub's private vulnerability reporting on this repository
(Security → "Report a vulnerability"), or open an issue if the report is
not sensitive. Reports are read by the maintainer; please include the
engine version (`clauderize --version`) and, for wiring issues, the output
of `clauderize doctor`.

## Scope and model

Clauderizer writes repo-local files, two of which register commands that
your agent harness executes (an MCP server and a SessionStart hook). The
full statement of what is written, what executes when, under which
contracts, and what happens when you clone a repo that already carries the
wiring lives in **[docs/TRUST.md](docs/TRUST.md)** — behavioral claims
there that disagree with the code are treated as bugs.

## Supported versions

Pre-1.0: only the latest released version is supported. The findings
tracker (`docs/HARDENING.md`) is public and append-only; resolved findings
carry dated evidence.
