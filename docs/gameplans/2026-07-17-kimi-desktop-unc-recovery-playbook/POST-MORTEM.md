# Post-Mortem — kimi-desktop-unc-recovery-playbook

**Closed:** 2026-07-17 · **Shipped in:** Clauderizer 1.9.1 · **Decision:** D-054 ·
**Baseline:** 823 → **840 passed, 5 skipped** · **cz_audit at close:** 0 findings

## Goal

A Kimi K3 desktop session on a WSL repo reported a dead shell (`spawn …bash.exe
ENOENT`) and no `cz_*` tools. The user's framing: Clauderizer is cross-agent memory —
a stuck agent should be able to **read its way out**, not wait for a human to relay
the diagnosis.

## What the debugging found (definitive)

The bundled bash is fine (it runs directly; `msys-2.0.dll` present). The real cause,
proven by `cmd.exe` itself in that directory — *"UNC paths are not supported. Defaulting
to Windows directory."* — is that the app spawns child processes with **cwd = the WSL
repo's `\\wsl.localhost` UNC path**, and **Windows cannot start a process with a UNC
cwd.** So both the shell and the `uvx` MCP server fail to spawn. A restart doesn't fix
it; a `wsl.exe`-wrapper MCP command doesn't either (it dies on the same cwd).

## Outcome

Since **file** tools still work over UNC, the fix is to put the instructions where a
spawn-broken agent can read them: `clauderize init` now emits an **agent playbook** into
`.clauderizer/kimi-desktop-mcp-setup.md` for the WSL+desktop combo (why it fails, how to
keep working via `docs/`, and the two real fixes — repo on Windows, or Kimi Code CLI in
WSL), and `doctor` warns loudly. Shipped as 1.9.1.

## What worked

- **`cmd.exe`'s own error message ended the guessing.** Rather than theorize about the
  ENOENT, running a process in that cwd made Windows state the limitation verbatim —
  the fastest way to a definitive root cause.
- **The channel matched the failure.** The agent can't spawn but *can* read files, so
  delivering recovery via a file (not a CLI/hook) is the one lane that survives.
- **Honesty pass caught a stale claim.** The module docstring still described the
  removed `wsl.exe` wrapper; corrected in the same change (cz_audit's claim-honesty
  discipline, applied by hand).

## What didn't (root cause)

- **My 1.9.0 was subtly wrong for this setup, and I'd have shipped a false fix.** I
  first proposed a 1.9.1 `wsl.exe`-wrapper MCP command; the live diagnosis showed it
  dies on the same UNC cwd. Caught only by running the real spawn — reinforcing: verify
  a host workaround against the real host before shipping it.

## Procedure improvements

- None to `GAMEPLAN-PROCEDURE.md`; the reusable rule (per-user config → repo-agnostic
  command; absolute-per-user writes are an L-29 hazard) is already L-58.

## Open threads

- The underlying spawn bug is Moonshot's — the desktop app should execute via `wsl.exe`
  inside the distro for WSL workspaces. Worth filing upstream.
- macOS/Linux daimon paths remain best-effort (D-053 residual).
