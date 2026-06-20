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
| 4 | Docs, version bump, release to PyPI | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-4-HANDOFF.md |

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

### Phase 4 Outputs

```
pypi-release: clauderizer 0.14.0 LIVE on PyPI (clauderizer-0.14.0-py3-none-any.whl + .tar.gz; index latest=0.14.0). GitHub Release https://github.com/collincusce/Clauderizer/releases/tag/v0.14.0 (publish.yml run 27854738885 success, OIDC). Tag v0.14.0 -> f7da75a (pyproject 0.14.0, H-07 ok). Release commit f7da75a; test-fix 7d708da.
ci-status: main Tests CI 9/9 green (ubuntu+macos+windows x py3.11/3.12/3.13) at 7d708da. The release commit f7da75a had 3 Windows cells red on one Linux-centric test assertion (forward-slash hook path); product unaffected (wheel ships no tests; kimi-setup generates correctly on Windows). Fixed test-only in 7d708da, no re-release needed.
```

## Corrections Log

### C-01 — Phase 4

**Phase**: 4
**What gameplan said**: Full suite green (399 passed) on this machine ⇒ safe to tag and cut the Release.
**What was actually correct**: Green on the WSL/Linux leg only. test_init_writes_kimi_setup asserted a forward-slash hook path ('.clauderizer/hook.') that fails on native Windows, where the wrapper command is '...\\.clauderizer\\hook.cmd'. All 3 Windows CI cells went red — but only AFTER the GitHub Release had already fired publish.yml and 0.14.0 was on PyPI.
**Why**: I ran the suite only through the WSL venv, not the Windows leg, despite this machine's documented ability to run a Windows venv from the UNC repo path (L-12). The new test encoded a platform-specific path assumption (separator), which a Linux-only run can never catch.
**Lesson**: Before tagging a release, execute the suite on every host leg the CI matrix covers — a Linux-only green is a guess about Windows, and the Release→PyPI step is irreversible. A path/separator assertion in a test is itself a platform claim: assert the wrapper FILE (hook.sh|hook.cmd), never the slash.
