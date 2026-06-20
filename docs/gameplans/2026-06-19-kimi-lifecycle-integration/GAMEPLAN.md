# kimi-lifecycle-integration Gameplan

> Created: 2026-06-19
> Status: Executing
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

_(1–2 paragraphs: what this gameplan accomplishes.)_

## Subsystems Touched

_(list the subsystems/features this gameplan affects.)_

## Source-of-Truth Captures

_(Real values captured from real systems at gameplan start. Authority over the
gameplan body. Account IDs, ARNs, baseline test counts, versions.)_

## Amendments

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

### D1 — Per-host hook wiring matches each host's real stdout contract

**Context**: Confirmed: Claude Code drops PreCompact/PostCompact stdout (not added to context) but re-fires SessionStart with source=compact (stdout IS injected) and injects UserPromptSubmit stdout. kimi injects ALL hook stdout on exit 0, but its SessionStart source is only startup|resume (no compact).
**Decision**: Wire each host to the events where stdout actually reaches context. Claude Code: register UserPromptSubmit (auto-analyze) and make the existing matcher-less SessionStart digest source-aware (it already re-fires on compact) — do NOT register PreCompact/PostCompact there (dead stdout). kimi: wire the full set (SessionStart, PreCompact, PostCompact, UserPromptSubmit) since all inject. The dispatch engine implements every handler regardless; only registration differs.
**Consequences**: Compaction-survival is delivered on Claude Code via SessionStart(compact) and on kimi via PostCompact — same durable digest, different event. No dead registrations that silently do nothing. Honest per-host docs.
**Evidence**: claude-code-guide confirmation (code.claude.com/docs/en/hooks); kimi-cli hooks.md exit-0 stdout->context.

### D2 — kimi host target is non-destructive: AGENTS.md stanza + emitted setup snippet, no global-config mutation

**Context**: kimi loads AGENTS.md (KIMI_AGENTS_MD) and reads .claude/skills/ (so Clauderizer's skills already work there). But kimi config is global ~/.kimi/config.toml, no project-level config is documented, and the MCP-server registration TOML schema is NOT documented (only client timeout + [[hooks]] are).
**Decision**: init's kimi target writes only project-local, non-destructive artifacts: inject the Clauderizer stanza into AGENTS.md (marker block, via writer.py) and emit a kimi setup snippet (.clauderizer/kimi-setup.md) containing the exact [[hooks]] entries (pointing at the existing wrapper) and MCP-registration guidance. It does NOT auto-edit the user's global ~/.kimi/config.toml.
**Consequences**: Zero clobber risk; no guessed schema shipped. The user merges the snippet into their kimi config. AGENTS.md support also benefits other AGENTS.md-aware harnesses (Codex, etc.), not just kimi.
**Evidence**: kimi-cli config-files.md (global config only; MCP-server registration undocumented); skills.md (.claude/skills brand group); AGENTS.md / KIMI_AGENTS_MD.

### D3 — No enable/disable flag for hooks; settings.json registration is the on/off; handlers quiet-when-empty

**Context**: INVARIANT-05 forbids enable/disable config flags for advisory surfaces. UserPromptSubmit fires on every prompt; an auto-analyze that always prints would add context noise and per-prompt cost.
**Decision**: No clauderizer config dial gates the hooks — presence/absence of the registration in the host config is the only switch. init registers the new events by default. Handlers print NOTHING when they have no signal (e.g. analyze finds no relevant decisions/invariants), so they are silent unless they add value.
**Consequences**: Consistent with INVARIANT-05. Upgraders are not retroactively spammed because quiet-when-empty bounds the noise; users who do not want an event simply omit its registration.
**Evidence**: INVARIANT-05; Claude Code UserPromptSubmit 30s timeout (handler must be fast + quiet).

## Open Items

**O-01.** _(phase Phase 3)_ kimi's MCP-server registration TOML schema is undocumented in kimi-cli config-files docs (only client timeout + [[hooks]] are shown). Phase 3 therefore emits a setup snippet instead of auto-wiring the global ~/.kimi/config.toml. Resolve by confirming the schema from a real kimi install or upstream issue before any future auto-wiring.

## Phase Breakdown

### Phase 0: Bootstrap &amp; design lock

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] D-025 + INVARIANT-06 + gameplan D1-D3 recorded; O-01 tracks the kimi MCP-schema unknown
- [x] Design matches confirmed host contracts (Claude Code: UserPromptSubmit + SessionStart source=compact; kimi: full event set)
- [x] Baseline full suite green at HEAD before any source change (captured)

### Phase 1: Event-dispatching hook engine

**Goal**: Generalize the single hook entry point to read stdin JSON and dispatch on hook_event_name — default (absent/unparseable stdin) is the source-aware SessionStart digest (backward compatible), with read-only handlers for PreCompact (reminder + status), PostCompact (digest), and UserPromptSubmit (auto-analyze). Every handler exits 0, is quiet-when-empty, and the --version/--help probe path is preserved.
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] clauderizer-hook dispatches on hook_event_name; empty/garbage/non-JSON stdin falls back to the SessionStart digest (backward compatible)
- [x] --version and --help probe paths return the engine identity unchanged (answered before stdin/repo read)
- [x] PreCompact, PostCompact, UserPromptSubmit handlers are read-only, always exit 0, and emit nothing when there is no signal
- [x] New unit tests cover event routing, each handler's output shape, exit-0-always, and the probe path; full suite green

### Phase 2: Claude Code wiring of new events

**Goal**: Teach `clauderize init` to register UserPromptSubmit on Claude Code (reusing the existing hardened wrapper) and keep the matcher-less SessionStart registration (now source-aware, covering compact). Idempotent re-init; the existing SessionStart leg and --version probe are untouched. Do not register PreCompact/PostCompact on Claude Code (stdout dropped there).
**Depends on**: Phase 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] clauderize init writes a UserPromptSubmit registration into .claude/settings.json pointing at the same wrapper command as SessionStart
- [x] The existing SessionStart registration is preserved and init is idempotent on re-run (no duplicate entries)
- [x] test_init and new wiring tests green; SessionStart leg and --version probe unaffected

### Phase 3: AGENTS.md and kimi host target

**Goal**: Add an AGENTS.md stanza injected as a marker block via writer.py (idempotent), and emit a kimi setup snippet (.clauderizer/kimi-setup.md) containing the exact [[hooks]] entries for all events (pointing at the wrapper) plus MCP-registration guidance. Strictly non-destructive: no mutation of the user's global ~/.kimi/config.toml.
**Depends on**: Phase 1.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] init injects the Clauderizer stanza into AGENTS.md as a marker block via writer.py, idempotently (re-run is a no-op)
- [x] .clauderizer/kimi-setup.md is emitted with correct [[hooks]] entries (wrapper command) for all events + MCP guidance
- [x] No write touches ~/.kimi or any path outside the repo; a test asserts non-destructiveness
- [x] New tests green; full suite green

### Phase 4: Docs, version bump, release to PyPI

**Goal**: README + CHANGELOG 0.14.0 entry, bump the version across every registry, bump the touched subsystem versions and resolve the cascade, run `clauderize release-check` and the full suite green, commit to main, tag v0.14.0 (tag must equal pyproject version per H-07), push, then create a GitHub Release to trigger the OIDC publish and verify clauderizer 0.14.0 on PyPI.
**Depends on**: Phase 2, Phase 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Version is 0.14.0 across pyproject.toml, clauderizer.__init__, and CHANGELOG; touched subsystem versions bumped and the cascade resolved
- [ ] clauderize release-check passes and the full suite is green on this machine
- [ ] Committed to main and tagged v0.14.0 (tag == pyproject version, H-07 guard), pushed to origin
- [ ] GitHub Release published; publish.yml succeeds; clauderizer 0.14.0 is visible on PyPI
