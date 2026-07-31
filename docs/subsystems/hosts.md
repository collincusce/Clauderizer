---
id: subsys.hosts
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.paths
last_verified: 2026-07-25
---

# Hosts

**Session-host-of-record**: compose and verify wiring for the host that actually spawns sessions.

## The failure it closes

H-04's root cause: wiring composed *inside WSL* was launched *from Windows*, and the consuming host was recorded nowhere. So `init` could compose a shimmed command into an invalid subcommand, and `doctor` stayed green for a setup the real session host could not launch. A health check that passes for an unlaunchable install is worse than no check (L-25) — it converts an unknown into a false assurance.

The fix is to record which host spawns sessions, compose for *that* host, and verify by actually executing.

## The vocabulary

- **`SessionHostError`** — an invalid session-host value, carrying guidance rather than a bare rejection.
- **`detect(...)`** — the adoption heuristic for wiring that already exists, so an existing install is recognized rather than clobbered.
- **`running_inside_wsl()`**, **`current_distro()`**, **`is_wsl_shim(argv)`** — the environment questions, isolated and injectable.
- **`read_wiring(...)`** — what is registered right now.

The vocabulary is `native` or `windows-wsl:<distro>`. Two values, because the distinction that matters is whether a `wsl.exe` shim has to wrap the command.

## Compose

- **`compose(argv, ...)`** — wrap an engine-host argv in the `wsl.exe` shim when sessions are launched from Windows against a WSL repo.
- **`harness_executor(...)`**, **`non_repo_cwd(...)`** — how and from where the harness will actually run it.

## The wrapper

A hook whose engine cannot spawn used to die silently — the harness injects only a hook's **stdout** into session context, and a failed spawn wrote to stderr. So the wrapper is the layer below the engine: it prints a breadcrumb on stdout and exits 0 regardless.

- **`render_hook_wrapper(argv, root=None, windows=False)`** — the wrapper script text with the engine command baked in. `"$@"` forwarding keeps it transparent to `--version` probes. With `root`, it anchors to the repo before delegating (H-09), because the engine discovers its repo from cwd and the executor chain does not reliably preserve the harness's project cwd — cmd.exe cannot hold a UNC cwd at all. An unreachable repo becomes a stdout breadcrumb, not silence.
- **`wrapper_filename(host)`** — `hook.sh` or `hook.cmd`. Assert the **file**, not the slash: a path assertion is itself a platform claim (L-51), and `tests/test_separator_claims.py` now machine-rejects that class.
- **`wrapper_engine_argv(text)`** — read the baked-in command back out, which is how freshness is checked without re-rendering.
- **`hook_wrapper_invocation(...)`**, **`is_hook_command(argv)`** — recognize our own wiring so re-`init` is idempotent.

The POSIX branch interpolates `root.as_posix()`; the Windows branch emits `cd /d "<root>"` with CRLF line endings. Both always end `exit 0` — INVARIANT-04.

## Verify by executing

- **`spawn_probe(argv)`** → **`Probe`** — actually run the composed command with `--version`.
- **`served_version(...)`** — what the spawned engine reports.
- **`verify_wiring(...)`**, **`verify_hook_wiring(...)`**, **`hook_digest_probe(...)`** — capability checks, not presence checks.

Verdicts are three-state (D-010): `ok` with evidence, `fail`, or `unverifiable` — never a false green. A local venv is not `uvx --from PyPI` and a monkeypatched platform is not the platform (L-66), which is why these probes execute rather than simulate.

## DAG position

Depends on `subsys.paths`. Consumed by `cli` (`init` composes, `doctor` verifies). `subsys.hosttargets` is the sibling that writes *per-host MCP registrations*; this module owns the *session hook* wiring. `subsys.mcp_probe` does for MCP server commands what `spawn_probe` does here.
