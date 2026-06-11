# stranger-readiness — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-10

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | The stranger's first hour: quickstart truth, live | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Upgrade and uninstall stories, walked live | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Trust model on the record (TRUST.md + SECURITY.md) | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Troubleshooting runbook from the scar tissue | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-3-HANDOFF.md |
| 4 | README positioning pass + B5 consolidation | 🟡 IN PROGRESS | 2026-06-10 | — | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
quickstart_truth: The stranger's first hour, walked and fixed (all evidence 2026-06-10). DEFECTS FOUND: (1) the published quickstart `uvx clauderize init` fails — "clauderize was not found in the package registry" (uvx derives package from command; package=clauderizer, command=clauderize; no squatter, fails loudly) — re-demonstrated verbatim in the fresh-HOME sim post-uv-install; (2) README line 134 ran BARE `clauderize doctor`, absent from a uvx-only PATH; (3) THE WIRING DEFECT: init under uvx wired the ephemeral cache path ($UV_CACHE_DIR/archive-v0/<hash>/bin/clauderizer-mcp) into .mcp.json AND the wrapper — `uv cache clean` then killed MCP wiring (doctor ✗ drift) and every digest (engine-unreachable breadcrumb) until re-init; (4) on a cold cache, uv's "Installed 1 package" stderr rode the wrapper's 2>&1 rerouting INTO session context and in front of the --version identity line the probes parse. FIXES: README ×4 + pyproject comment → `uvx --from clauderizer clauderize init` (+ zero-install note: every bare `clauderize` = the uvx form until installed); _under_uv_cache() in scaffold/init.py — bindir AND which() results under uv's cache (env UV_CACHE_DIR, platform defaults, archive-v0 marker) are never wired, the durable absolutized `uvx -q --from clauderizer` form is (3 new unit tests; suite 261 → 264); DEFAULT_RUN gained -q (kills the cold-cache noise). LIVE FIX-PROOF (pre-release, via local wheel): `uvx --from <wheel> clauderize init` wired `/home/ccusce/.local/bin/uvx -q --from clauderizer clauderizer-mcp`; after `uv cache clean` the digest returned PURE — wiring self-heals by re-resolving. PERMANENT GUARD: .github/workflows/quickstart.yml (push + weekly cron + dispatch) — doc-drift grep ties CI to README text, uv via official one-liner, init/digest/doctor asserted against the PUBLISHED package, cache-clean assertion SELF-ARMING (skips on 0.9.0 with an explanatory message; hard-asserts from the next release). First run: 27316260960 SUCCESS. NOTE: published 0.9.0 still carries the ephemeral-wiring behavior — the fix ships with GP-C's flip release; doctor catches the 0.9.0 failure shape as drift meanwhile.
```

### Phase 1 Outputs

```
upgrade_uninstall_walks: docs/UPGRADING.md shipped (upgrade two-moves + doctor-nudge decoder + the 0.9.0 ephemeral-wiring upgrade note + five-step uninstall keeping docs/). Live walks 2026-06-10 (scratch repo /tmp/cz-upg-0Oypa5): UPGRADE A — pre-H-09 wrapper template → doctor rc 3 "wrapper template predates this engine" → re-init wrote exactly 1 file → rc 0 → second init 0 files (idempotent); UPGRADE B — baked engine /old/venv/... → rc 3 "wrapper invokes … but a fresh init would compose …" → re-init → rc 0. UNINSTALL — the doc's five steps verbatim (python3 heredocs for the JSON surgery + rm) → doctor rc 1 "Not a clauderized repo"; preservation proven: decoy MCP server kept, hand-written CLAUDE.md text kept with 0 clauderizer mentions remaining, docs/ kept, zero SessionStart hooks left, .clauderizer and skills gone. README link to UPGRADING.md lands in Phase 4's pass.
```

### Phase 2 Outputs

```
trust_docs: docs/TRUST.md shipped: the one-paragraph model (repo-local writes only, no daemon/network/self-execution, zero runtime deps); the complete init write-surface table with per-surface contracts (key-merge .mcp.json via _register_mcp, matcher-scoped hook replacement via _register_hook/is_hook_command, marker-block-only CLAUDE.md via upsert_marker_block, never-clobber docs/ via create_if_absent, preserved profile.lock.toml); the execution boundary (wrapper contract: anchored cd, stdout-only, breadcrumbs-not-silence, always exit 0; engine hook reads-and-prints, writes nothing; MCP stdio repo-local with reads-never-mutate + write.lock serialization); the spawn-test + WiringRefused + _under_uv_cache pre-write guards; the cloned-preseeded-wiring scenario (nothing runs on clone; harness trust flow gates execution; foreign paths fail VISIBLY as breadcrumbs; wiring is short plain text written to be read); supply chain (zero deps, Trusted Publishing OIDC, tag==source gate, release-check four-registry sweep, quickstart-vs-published-package CI). Root SECURITY.md: GitHub private vulnerability reporting, scope pointer to TRUST.md, pre-1.0 support statement, public append-only HARDENING tracker. Every cited symbol grep-verified present (12/12: _register_mcp, _register_hook, is_hook_command, upsert_marker_block, create_if_absent, WiringRefused, _under_uv_cache, render_hook_wrapper, write.lock, dependencies=[], the publish gate marker, quickstart.yml). README links land in Phase 4.
```

### Phase 3 Outputs

```
troubleshooting_runbook: docs/TROUBLESHOOTING.md shipped, distilled from H-01..H-09 + the gameplan friction logs: the "no digest at session start" ladder (doctor → the breadcrumb decoder table mapping each [Clauderizer] prefix to its layer and cure → windows-wsl/H-08 note with wiring_matrix.ps1 → the harness transcript hook attachments as the durable diagnostic surface, the exact method that diagnosed and resolved H-08); the doctor exit-code contract table (0/1/2/3 with the designed-? honesty note); cz_* tools missing mid-session (server enumerated at start, restart is the last mile, clauderize ops as the no-MCP write fallback per L-05); the unborn-branch preflight skip; release-check red-after-shipping as designed behavior; uvx cache staleness (--refresh; post-0.9.0 wiring survives cache clean). Every quoted string grep-verified against source, 9/9 (both breadcrumb prefixes, status-unavailable, the exit-1/2/3 doctor lines, unborn-branch, the stanza's ops fallback, the matrix artifact). Evidence pointers section routes to HARDENING / RELEASING / post-mortems. README link lands in Phase 4.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
