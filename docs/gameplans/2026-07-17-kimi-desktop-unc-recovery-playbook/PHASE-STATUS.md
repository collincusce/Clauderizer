# kimi-desktop-unc-recovery-playbook — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-17

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Agent-recovery guide + doctor warning for the WSL/UNC combo | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Ship 1.9.1, dogfood close, release | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
recovery-playbook-impl: kimidesktop.setup_guide() expanded into an agent playbook: MCP entry + 'if your shell/tools are failing' section — why (UNC cwd; Windows can't spawn with a \\wsl.localhost cwd), work-now (read docs/ + file tools over UNC; don't rely on the clauderize CLI/bash), fix (repo on Windows OR Kimi Code CLI in WSL where K3 is available). wire() now returns windows_side. init emits the guide into .clauderizer/ when desk.windows_side (WSL cross-boundary), not only on failure, + a loud warning. doctor warns for the combo (_is_windows_side) pointing at the guide. Fixed a stale module-docstring claim (still described the removed wsl.exe wrapper). Escaping fix: doubled backslashes in the f-string (C:\\Users, \\\\wsl.localhost). 3 tests (playbook content, init-emits-on-combo, doctor-warns). Live dogfood on this WSL+desktop machine: doctor showed the UNC warning, init emitted the 9-keyword playbook. Suite 837->840, fresh venv.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
