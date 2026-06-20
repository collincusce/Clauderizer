# kimi-lifecycle-integration — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-19

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Bootstrap &amp; design lock | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Event-dispatching hook engine | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Claude Code wiring of new events | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-2-HANDOFF.md |
| 3 | AGENTS.md and kimi host target | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Docs, version bump, release to PyPI | 🟡 IN PROGRESS | 2026-06-19 | — | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 1 Outputs

```
hook-engine-files: src/clauderizer/hook/dispatch.py (router + console entry), handlers.py (4 read-only handlers: session_start source-aware, pre_compact, post_compact, user_prompt_submit), sessionstart.py (back-compat shim re-exporting build_digest/session_start). Entry point clauderizer-hook repointed pyproject -> clauderizer.hook.dispatch:main.
phase1-test-result: 389 passed, 4 skipped (full suite). +37 new in tests/test_hook_dispatch.py; baseline was 352. --version still prints `clauderizer 0.13.0`; empty stdin -> SessionStart digest verified via the real console script.
```

### Phase 2 Outputs

```
userpromptsubmit-wiring: init._register_hook generalized to register HOOK_EVENTS=(SessionStart, UserPromptSubmit) under the same wrapper command; idempotent, preserves foreign hooks per event, migrates the pre-0.14 SessionStart-only shape (adds UPS without duplicating SS). PreCompact/PostCompact deliberately NOT registered on Claude Code (D1). +5 tests in tests/test_init.py (15 total there).
```

### Phase 3 Outputs

```
agents-md-and-kimi-setup: init step 8b injects the same host-agnostic clauderizer marker-block stanza into AGENTS.md (kimi via KIMI_AGENTS_MD; also Codex et al.). Step 11b writes .clauderizer/kimi-setup.md — non-destructive guide with [[hooks]] for all 4 events (kimi injects all stdout) using TOML literal-string commands pointing at the wrapper, + MCP guidance citing O-01. New RepoPaths.agents_md and RepoPaths.kimi_setup. +5 tests; generated TOML validated via tomllib (SessionStart/PreCompact/PostCompact/UserPromptSubmit).
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
