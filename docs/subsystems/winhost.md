---
id: subsys.winhost
type: subsystem
version: 1.0.0
status: active
depends_on:
last_verified: 2026-07-25
---

# Winhost

Windows/WSL command composition — host-agnostic primitives (D-056).

Extracted from the kimi-desktop wiring (D-055) so any bespoke auto-write host that must launch a **Windows-native** Clauderizer server can reuse it, rather than that knowledge living inside one host's emitter.

## The two jobs

**Compose** the absolute path to a Windows-native `clauderizer-mcp.exe` for a daimon or desktop host that runs on Windows. The `.exe` is required rather than preferred: such an app may bundle `uv.exe` but not `uvx.exe`, so a bare `uvx` command can never spawn there. The `.exe` is the verified command, and the module probes the per-user install locations to find it.

**Translate** between the `C:\` spelling Windows launches and the `/mnt/<drive>` path a WSL vantage can `stat` and spawn (WSL interop). Both directions are needed because `init` composes the wiring from inside WSL and `doctor` verifies it from inside WSL, while the host that actually runs the command is Windows.

## The surface

- **`win_path_to_wsl(p)`** — `C:\Users\me\x.exe` → `/mnt/c/Users/me/x.exe`, or `None` when `p` is not a Windows path. The call that makes a cross-OS command *verifiable* from WSL.
- **`windows_profile_from_cfg(cfg_path)`** — from a WSL-mounted Windows config path, derive `(mnt_base, win_base)`: the same user profile in both spellings. Deriving it from the config's own location avoids guessing the Windows username from the WSL one, which is a common and wrong assumption.
- **`wsl_repo_to_unc(root)`** — a WSL repo root (`/home/me/proj`) → its Windows UNC path (`\\wsl.localhost\<distro>\home\me\proj`).
- **`windows_safe_cwd(...)`** — a working directory the daimon can actually spawn from. This exists because **cmd.exe cannot hold a UNC cwd at all**; handing a Windows host a `\\wsl.localhost\…` working directory produces a dead shell, so the composed command must anchor somewhere Windows can stand.
- **`win_exe_candidates(...)`** — `(stat_path, command_str)` pairs for a Windows-native executable: where WSL should look to confirm it exists, and what string Windows should be told to run. The two differ, and conflating them is the bug this shape prevents.

## Pure and injectable

Every function takes its `platform`, `home` and `users_dir` as injectable parameters rather than reading the environment. That is what lets the WSL-side tests exercise the Windows paths and vice versa without monkeypatching `sys.platform` — and it matters here more than most places, because a monkeypatched platform is not the platform, and every real defect in this area was found by running on the target OS rather than by simulating it.

## DAG position

Depends on nothing. Consumed by `mcp_probe` (translating a Windows command into something WSL can spawn for the handshake) and by `kimidesktop` (composing the daimon's server entry). `subsys.bespoke_hosts` is the framework that made this extraction worth doing.
