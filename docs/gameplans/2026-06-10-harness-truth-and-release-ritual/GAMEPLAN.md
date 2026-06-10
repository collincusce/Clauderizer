# harness-truth-and-release-ritual Gameplan

> Created: 2026-06-10
> Status: Planning
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

### D1 — The wiring shape is chosen by executor-matrix evidence, not reasoning

**Context**: Three candidate MSYS-immune SessionStart command shapes exist with partial evidence: wsl.exe -d ubuntu sh -c 'exec /home/…/hook.sh' (verified under Git Bash only), MSYS_NO_PATHCONV=1 prefix (verified under Git Bash; bash-only env syntax, expected to fail under cmd/PowerShell), //bin/sh double-slash (untested anywhere). The harness's executor choice is not ours to pin and has already changed behavior once (PS 5.1 quoting, Git Bash interposition), and quoting survives the PowerShell→wsl.exe→distro-shell chain differently per executor.
**Decision**: Phase 0 runs every candidate shape under all three Windows executors (Git Bash bash -c, cmd.exe /c, PowerShell direct) against the real wrapper, records the full pass/fail matrix as a phase output BEFORE any hosts.py change, and the only shape eligible for wiring is one that emits the digest under all three. The current broken shape runs in the same matrix to prove the test detects the failure (lesson #4: prove the guard fires).
**Consequences**: Phase 1 (hosts.py emission) is blocked on Phase 0's matrix; the matrix script becomes the regression artifact for D-010's init spawn-test contract; if no shape passes all three executors, the wiring decision escalates to the user with the matrix as evidence instead of shipping a partial fix.

## Open Items

_(O1, O2, … — blockers and cross-phase questions.)_

## Phase Breakdown

### Phase 0: Executor matrix: prove the wiring shape

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable assertion)_

### Phase 1: hosts.py emits the immune shape; restart-validate H-08

**Goal**: Wire the matrix-winning command shape into hosts.py composition (hook leg; audit the .mcp.json leg for the same vulnerability while there), regenerate this repo's wiring via plain clauderize init (byte-identical on re-run), and keep init's spawn-test meaningful for the new shape. Exit criteria: suite green with new shell-matrix-aware wiring tests; doctor 16/16 via shim; manual wrapper run emits digest from PowerShell AND through Git Bash bash -c; and the load-bearing one — a real harness cold start shows the [Clauderizer] digest in session context, after which H-08 transitions to resolved with that evidence quoted.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 2: Doctor traverses the consumer leg (D-010)

**Goal**: Make doctor's hook-launchability check honest per D-010: when session_host is windows-wsl and the harness executor is reachable (Git Bash via WSL interop at /mnt/c/Program Files/Git/bin/bash.exe), the probe spawns the registered command THROUGH that executor and requires in-band identity; verdict wording names the traversed leg; untraversable legs report the exit-3 honesty pattern instead of green. Exit criteria: doctor run against the OLD (pre-Phase-1) wiring shape fails this check loudly (guard-fires proof, lesson #4 — use a scratch repo or pinned fixture), passes against the new shape; suite green with tests covering executor-present and executor-absent hosts.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 3: Release preflight ritual (O3) and 1.0 readiness gates (O4)

**Goal**: Implement D-011 as a runnable check (clauderize release-check or a doctor mode): red unless origin/main == staged release commit, the version is unclaimed across all four registries queried fresh (local tags, git ls-remote --tags, Releases API, PyPI index direct — never uvx cache), and the staged publish.yml carries the tag==source gate. Document the 1.0 readiness gates (O4) next to it: what must be true — H-08 resolved, doctor honest per D-010, release ritual mechanical, suite/coverage thresholds — before a 1.x tag is legitimate. Exit criteria: the check fails red on a simulated skew (unpushed staged commit; an already-claimed version) and green on the real current state; gates documented; suite green.
**Depends on**: Phase 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 4: Memory guardrails as config: O1 ACTIVE_LESSONS_WARN, O2 consolidation trigger

**Goal**: Move the memory-bloat guardrails from prose to config: O1 — ACTIVE_LESSONS_WARN becomes a [clauderizer]/[rituals] config value (current hardcoded warn threshold honored as default; cz_status and handoff assembly read it), and O2 — a project-lesson consolidation trigger: when docs/LESSONS.md active L-entries exceed a configurable threshold (~20; currently 9), cz_status surfaces a consolidation nudge naming the overlap candidates. Exit criteria: both values configurable and documented in the scaffold's config template; warnings fire in tests at the thresholds and stay silent under them; suite green.
**Depends on**: Phase 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_
