# stranger-readiness — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-10

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | The stranger's first hour: quickstart truth, live | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Upgrade and uninstall stories, walked live | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Trust model on the record (TRUST.md + SECURITY.md) | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Troubleshooting runbook from the scar tissue | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | README positioning pass + B5 consolidation | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
quickstart_truth: The stranger's first hour, walked and fixed (all evidence 2026-06-10). DEFECTS FOUND: (1) the published quickstart `uvx clauderize init` fails — "clauderize was not found in the package registry" (uvx derives package from command; package=clauderizer, command=clauderize; no squatter, fails loudly) — re-demonstrated verbatim in the fresh-HOME sim post-uv-install; (2) README line 134 ran BARE `clauderize doctor`, absent from a uvx-only PATH; (3) THE WIRING DEFECT: init under uvx wired the ephemeral cache path ($UV_CACHE_DIR/archive-v0/<hash>/bin/clauderizer-mcp) into .mcp.json AND the wrapper — `uv cache clean` then killed MCP wiring (doctor ✗ drift) and every digest (engine-unreachable breadcrumb) until re-init; (4) on a cold cache, uv's "Installed 1 package" stderr rode the wrapper's 2>&1 rerouting INTO session context and in front of the --version identity line the probes parse. FIXES: README ×4 + pyproject comment → `uvx --from clauderizer clauderize init` (+ zero-install note: every bare `clauderize` = the uvx form until installed); _under_uv_cache() in scaffold/init.py — bindir AND which() results under uv's cache (env UV_CACHE_DIR, platform defaults, archive-v0 marker) are never wired, the durable absolutized `uvx -q --from clauderizer` form is (3 new unit tests; suite 261 → 264); DEFAULT_RUN gained -q (kills the cold-cache noise). LIVE FIX-PROOF (pre-release, via local wheel): `uvx --from <wheel> clauderize init` wired `/home/ccusce/.local/bin/uvx -q --from clauderizer clauderizer-mcp`; after `uv cache clean` the digest returned PURE — wiring self-heals by re-resolving. PERMANENT GUARD: .github/workflows/quickstart.yml (push + weekly cron + dispatch) — doc-drift grep ties CI to README text, uv via official one-liner, init/digest/doctor asserted against the PUBLISHED package, cache-clean assertion SELF-ARMING (skips on 0.9.0 with an explanatory message; hard-asserts from the next release). First run: 27316260960 SUCCESS. NOTE: published 0.9.0 still carries the ephemeral-wiring behavior — the fix ships with GP-C's flip release; doctor catches the 0.9.0 failure shape as drift meanwhile.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
