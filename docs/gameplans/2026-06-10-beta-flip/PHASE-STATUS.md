# beta-flip — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-10

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Burn-down: structural guards before the flip | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | The flip release: 0.10.0, Development Status :: 4 - Beta | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-1-HANDOFF.md |
| 2 | B6 evidence: the armed guard fires green; all six gates hold | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-2-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
burndown_guards: All three burn-down items shipped (the D2 must-have AND both best-efforts), suite 264 → 270, commit cfe9743. (1) tests/test_io_discipline.py — the bare-IO tripwire (regex walk, balanced-paren arg spans, allowlist: binary modes, os.O_ flag calls, itself; no-space-before-paren rule kills prose false positives) — FIRED ON ITS FIRST SWEEP per L-10: caught 3 real stragglers the B2 sed pass missed (bare write_text in test_engine_hardening ×2, test_mutations ×1; the sed had only fixed read_text()), all pinned. (2) MCP-staleness nudge: status_bundle.PROCESS_STARTED (import-time) + engine_source_newer_than(); ops.cz_status sets bundle["engine_stale"]; render_digest emits "⚠ Engine: source changed since this server started — cz_* tools run the older build; restart the session, or use clauderize ops (fresh process) for writes." Fresh CLI/hook processes never see True; installed packages never (mtimes = install time) — the nudge fires exactly for the dogfooding long-server case. (3) release-check gained "README names the ritual": RITUAL_MARKER="clauderize release-check" must appear in README.md when one exists (the G7-between-sibling-docs tripwire; fail wired to exit 2, proven firing in tests both directions). BONUS (same class, found while in there): subprocess text=True replaced with encoding="utf-8", errors="replace" in preflight._default_runner and release_check._git — win32 locale decode could mojibake or raise on non-ASCII tool output.
```

### Phase 1 Outputs

```
flip_release_0_10_0: 0.10.0 SHIPPED 2026-06-10, zero incidents — the third consecutive boring release. THE FLIP: pyproject classifier line → "Development Status :: 4 - Beta", verified ON THE PUBLISHED ARTIFACT (importlib.metadata via uvx --from clauderizer==0.10.0: "Development Status :: 4 - Beta"). Chain: fresh-eyes tag sweep (local==remote, no v0.10.0); staged commit 77a87ca (version+classifier, README maturity → "beta, with receipts" naming the flip as B6, CHANGELOG [Unreleased]→[0.10.0] incl. the burn-down items); editable reinstall; init 0 files; doctor exit 0 (zero open findings — B6 precondition); push; release-check exit 0 pre-tag with NINE checks (the new README-names-the-ritual check green on its first real staging); tag v0.10.0; Release https://github.com/collincusce/Clauderizer/releases/tag/v0.10.0 ("v0.10.0 — Beta"); publish run 27319860345 green (gate passed, Trusted Publishing + digital attestations); uvx --refresh → clauderizer 0.10.0. Suite 270 on the release commit.
```

### Phase 2 Outputs

```
b6_armed_guard_evidence: ALL SIX BETA GATES ✅ (RELEASING.md evidence table complete). B6's chain: classifier verified ON the published artifact (importlib.metadata via uvx --from clauderizer==0.10.0 → "Development Status :: 4 - Beta"); the self-arming cache-clean guard ARMED and PASSED on published 0.10.0 (quickstart run 27320342612 — post-clean digest pure, no disarm message; contrast run 27319935766 ninety seconds after publish, which honestly self-disarmed because the runner's index view still answered 0.9.0: PyPI propagation lag, exactly the no-false-red/no-false-green behavior the design intends); local fresh-HOME walk: fresh index resolve → 0.10.0, durable uvx -q wiring on both surfaces (.mcp.json + wrapper engine line), doctor exit 0, uv cache clean → digest pure via PyPI re-resolution. PROCESS NOTES for the post-mortem: (1) the propagation-lag disarm is the self-arming pattern working, record as a feature; (2) my PyPI-propagation Monitor never fired — its grep assumed pretty-printed JSON ('"version": "0.10.0"') while PyPI serves minified ('"version":"0.10.0"') — L-10 violated by my own monitoring probe; propagation had completed long before the timeout. CARRIED: G6's literal native-harness cold start (the one residual on the 1.0 runway); no deferred burn-down items (all three landed in Phase 0).
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
