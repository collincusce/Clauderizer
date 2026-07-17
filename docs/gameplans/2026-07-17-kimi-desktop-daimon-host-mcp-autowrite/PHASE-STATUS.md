# kimi-desktop-daimon-host-mcp-autowrite — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-17

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Confirm the daimon runtime contract + design cross-platform detection | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Bespoke kimi-desktop detection + auto-write emitter | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Wire kimi-desktop into init, doctor, uninstall | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Docs, ship 1.9.0, dogfood close | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
daimon-design: Runtime-home mcp.json paths (relative suffix: kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/mcp.json): Windows %APPDATA% (Roaming); macOS ~/Library/Application Support; Linux ~/.config. WSL->Windows case (user's real setup): glob /mnt/c/Users/*/AppData/Roaming/kimi-desktop/.../home/mcp.json. Detection: the home/ dir must already exist (app installed) -> write; else guide. Command: uvx --from clauderizer[mcp] clauderizer-mcp; resolve uvx to absolute via shutil.which when found; when init runs inside WSL against a /mnt/c (Windows-side) config, wrap as wsl.exe -d <distro> -e bash -lc 'cd <repo-posix> && <cmd>' so the Windows-spawned server runs where uvx+repo live (reuse session.running_inside_wsl/current_distro). The runtime-home config is machine-local (not committed) so a machine-specific/wsl.exe command is APPROPRIATE there (L-48 caveat applies only to committed portable configs). Tests inject the home base (never touch real per-user dirs, L-29). D-031 exception recorded as D-053 with mitigations (detected-only, non-destructive atomic, robust command).
```

### Phase 1 Outputs

```
kimidesktop-emitter: src/clauderizer/kimidesktop.py: candidate_configs (pure path construction per platform + WSL-windows roots), detect_config (detected-only: home/ dir must exist), server_entry (uvx-absolute via injected which; wsl.exe -d <distro> -e bash -lc 'cd <repo> && uvx ...' when in_wsl+windows_side+distro), merge_entry (non-destructive atomic temp-write+os.replace), remove_entry (surgical), wire (detect->build->merge, returns status wired/not_detected/failed + warnings for missing-uvx/no-distro), setup_guide (fallback md). Everything injectable (home/platform/environ/in_wsl/distro/users_dir/which) so tests never touch real per-user dirs (L-29). tests/test_kimidesktop.py (8): per-platform paths, detected-only both directions, non-destructive merge, WSL->windows wsl.exe wrapper (the user's real setup), missing-uvx warning, surgical remove, no leftover .tmp. Machine-local config => machine-specific/wsl.exe command is correct (L-48 caveat = committed configs only). Suite 823->831, fresh venv.
```

### Phase 2 Outputs

```
wired-into-init-doctor-uninstall: init.py calls kimidesktop.wire() after the multi-host loop: detected->auto-write (repo-agnostic), failed->emit .clauderizer/kimi-desktop-mcp-setup.md + warn, not_detected->silent no-op (no guide clutter for a host you don't have — a UX refinement of the 'emit guide otherwise' criterion). doctor (cli.cmd_doctor) reports kimi-desktop: '· not detected' / '✓ MCP registered (path)' / warn 'detected but not wired', plus a loud uvx-not-on-PATH warning. uninstall (full path) removes only the clauderizer entry from the detected runtime-home. Design correction C-01: repo-agnostic command (not cd-wrapper) + CLAUDERIZER_NO_KIMI_DESKTOP opt-out + autouse conftest guard so the suite never writes real per-user config (verified untouched across 837 tests). Real-machine E2E: init detected the Windows config via /mnt/c, wrote bare uvx idempotently (no pollution), warned about Windows PATH. Suite 831->837, fresh venv.
```

## Corrections Log

### C-01 — Phase 2

**Phase**: 2
**What gameplan said**: Phase 0/D-053 designed the WSL->Windows-desktop command as a wsl.exe -d <distro> -e bash -lc 'cd <repo> && uvx ...' wrapper so the Windows-spawned server runs where uvx + the repo live.
**What was actually correct**: That wrapper is repo-SPECIFIC, but the daimon config is ONE per-user file shared by every repo the desktop app opens — so pinning it to one repo's cd path is wrong, and worse, a live smoke revealed that running `clauderize init` from any repo (incl. the test suite's tmp repos) OVERWROTE the user's real desktop config with a pointer to a since-deleted dir (a pytest tmp path was found in it). Two fixes: (1) the entry is now REPO-AGNOSTIC — always `uvx --from clauderizer[mcp] clauderizer-mcp` (the user's verified working shape); the server discovers the open repo from the desktop app's cwd, so one entry serves all repos and re-init is idempotent. For the WSL->Windows case the command runs on Windows, so write a BARE uvx (not the WSL-absolute path) + a loud warning, never a wsl.exe/cd wrapper. (2) tests must never touch real per-user state: added CLAUDERIZER_NO_KIMI_DESKTOP env opt-out that detect_config honors, and an autouse conftest fixture that sets it, so init() in the suite no longer writes the real config (verified: the real config stayed the clean uvx entry through the whole 837-test run).
**Why**: Caught by dogfooding the real `clauderize doctor`/`init` against the actual installed desktop app (the machine this is developed on has it). A per-user single-config host must be repo-agnostic; and any init step that writes absolute per-user paths is an L-29 hazard in tests.
**Lesson**: A host whose config is a single per-user file (shared across all repos) must get a REPO-AGNOSTIC server command — one that discovers the repo from the host's working directory — never a repo-pinned `cd <repo>` wrapper, or the last init wins and re-init from another repo silently repoints it. And any init/emit step that writes an absolute per-user path (outside the repo) is an L-29 test hazard: guard it behind an env opt-out and an autouse fixture so the suite never mutates real machine state — verify by asserting the real file is untouched after a full run.
