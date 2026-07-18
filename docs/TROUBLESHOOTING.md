# Troubleshooting

> Distilled from what actually broke and got diagnosed — every entry names
> its evidence (a finding in [HARDENING.md](HARDENING.md) or a live walk in
> a gameplan's outputs registry), and every quoted string is the code's
> exact text. First move for almost everything: `clauderize doctor`
> (zero-install: `uvx --from clauderizer clauderize doctor`).

## No digest at session start

The SessionStart digest is the system's heartbeat. When a session starts
without a `[Clauderizer]` line, walk this ladder:

**1. Run `clauderize doctor` in the repo.** Its hook verdict tells you which
leg is broken; the exit code tells you what it owes you (see table below).

**2. Read what the session DID get.** The wrapper converts failures into
one-line breadcrumbs on stdout — each names a different layer:

| Line starts with | Meaning | Cure |
|---|---|---|
| `[Clauderizer] engine unreachable: exit N from …` | the wrapper ran but the engine command died (moved venv, cleaned uv cache, uninstalled engine) | re-run `clauderize init` (see [UPGRADING.md](UPGRADING.md)) |
| `[Clauderizer] repo unreachable: …` | the wrapper ran but its repo path no longer exists (moved/renamed repo) | re-run `clauderize init` in the repo's new location |
| `[Clauderizer] status unavailable: …` | engine and repo are fine; reading the tracked docs raised an error | run `clauderize doctor`; inspect the named file |
| *(nothing at all)* | the registered command itself never produced output — the wrapper never ran, or pre-0.9.0 wiring lost its working directory | doctor, then re-init; for windows-wsl hosts see below |

**3. Windows-WSL hosts**: the harness may execute hooks through Git Bash,
whose MSYS2 path conversion can mangle commands (fixed by the
`//`-path wiring shape in 0.9.0; doctor's hook verdict traverses the real
Git Bash leg when it is reachable and says so in its message). The
re-runnable evidence matrix is `scripts/wiring_matrix.ps1`.

**4. The durable diagnostic surface**: your harness's session transcript
records a per-hook attachment (command, exitCode, stderr, durationMs) for
every SessionStart hook — it turns "silent missing digest" into an exact
failing command. This is how the Windows-WSL path-mangling failure was diagnosed and its fix proven.

## Doctor exit codes

| Exit | Meaning | Obligation |
|---|---|---|
| 0 | everything verified | none |
| 1 | `Not a clauderized repo (no .clauderizer/config.toml)` | run `clauderize init` if you expected wiring here |
| 2 | drift — at least one `✗`; the message names the broken leg | `Drift detected — re-run \`clauderize init\` to repair.` |
| 3 | nothing failed, but ≥1 check is `?` — honestly unverifiable from this host, or a freshness nudge | read each `?` line; verify from the named host or re-init for nudges |

Doctor never reports green for a leg nothing traversed — `?` is a designed
verdict, not a failure.

## `cz_*` tools missing mid-session

The harness enumerates MCP servers at session start only — if the server
could not launch, fixing the wiring mid-session cannot attach the tools; a
restart is the last mile. Until then, **every tracked write is reachable
without MCP**: `clauderize ops <file.json|->` executes a JSON batch against
the exact `cz_*` names and schemas (the CLAUDE.md stanza documents this
fallback).

## Preflight says "no commits yet (unborn branch)"

A fresh `git init` with zero commits: branch checks skip honestly (they
used to misread this as "not a git repo"). Commit the scaffold and they
activate.

## `release-check` is red on a version you just shipped

Designed behavior, not drift: after a release, all four registries
correctly report that version as claimed — the check exists to stop the
NEXT release from reusing it. It must be exit 0 *before* tagging, red
*after* shipping.

## uvx answers with a stale version

`uvx --from clauderizer …` by name can answer from uv's cache. Add
`--refresh` when verifying a fresh release; `uv cache clean` also clears it
(and post-0.9.0 wiring survives that clean — see
[UPGRADING.md](UPGRADING.md) if yours does not).

## Kimi Work desktop: no `cz_*` tools, or every shell command fails

The desktop app (daimon runtime) loads MCP only from a per-user config it
**regenerates on project switch** — so a registration can vanish. Fix: run
`clauderize doctor` (or `status`/`init`) from any shell on the machine; it
**self-heals** the entry (and `doctor` handshake-verifies it). If the tools
still don't appear and *every* shell command also fails, your repo lives in
WSL while the app runs on Windows: the app spawns with a `\\wsl.localhost`
**UNC** working directory Windows cannot use, so neither the shell nor the MCP
server can launch **for that repo**. The registered entry still serves
*Windows-hosted* repos — clone the repo onto the Windows filesystem, or use
Kimi Code CLI inside WSL. The full agent playbook is written to
`.clauderizer/kimi-desktop-mcp-setup.md` (readable with file tools even when
spawning is blocked — D-054).

## Where the deeper evidence lives

- [HARDENING.md](HARDENING.md) — the append-only findings tracker
  (resolved findings carry dated evidence and a reproduction).
- [RELEASING.md](RELEASING.md) — the release ritual, the 1.0 gates, the
  beta evidence table.
- `docs/gameplans/*/POST-MORTEM.md` — what worked, what didn't, with root
  causes.
