# beta-flip — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-10

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Burn-down: structural guards before the flip | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | The flip release: 0.10.0, Development Status :: 4 - Beta | 🟡 IN PROGRESS | 2026-06-10 | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | B6 evidence: the armed guard fires green; all six gates hold | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
burndown_guards: All three burn-down items shipped (the D2 must-have AND both best-efforts), suite 264 → 270, commit cfe9743. (1) tests/test_io_discipline.py — the bare-IO tripwire (regex walk, balanced-paren arg spans, allowlist: binary modes, os.O_ flag calls, itself; no-space-before-paren rule kills prose false positives) — FIRED ON ITS FIRST SWEEP per L-10: caught 3 real stragglers the B2 sed pass missed (bare write_text in test_engine_hardening ×2, test_mutations ×1; the sed had only fixed read_text()), all pinned. (2) MCP-staleness nudge: status_bundle.PROCESS_STARTED (import-time) + engine_source_newer_than(); ops.cz_status sets bundle["engine_stale"]; render_digest emits "⚠ Engine: source changed since this server started — cz_* tools run the older build; restart the session, or use clauderize ops (fresh process) for writes." Fresh CLI/hook processes never see True; installed packages never (mtimes = install time) — the nudge fires exactly for the dogfooding long-server case. (3) release-check gained "README names the ritual": RITUAL_MARKER="clauderize release-check" must appear in README.md when one exists (the G7-between-sibling-docs tripwire; fail wired to exit 2, proven firing in tests both directions). BONUS (same class, found while in there): subprocess text=True replaced with encoding="utf-8", errors="replace" in preflight._default_runner and release_check._git — win32 locale decode could mojibake or raise on non-ASCII tool output.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
