# kimi-desktop-daimon-host-mcp-autowrite — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-17

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Confirm the daimon runtime contract + design cross-platform detection | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Bespoke kimi-desktop detection + auto-write emitter | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Wire kimi-desktop into init, doctor, uninstall | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
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

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
