# alpha-to-beta-evidence Gameplan

> Created: 2026-06-10
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

### D1 — Series of three gameplans: evidence → stranger-readiness → flip

**Context**: The user asked for "a gameplan, or SERIES of gameplans" to reach beta. One mega-plan covering B1–B6 would run 10+ phases across very different kinds of work (release mechanics, CI engineering, docs for strangers), while the system's rhythm — per-gameplan lessons, consolidation at close, post-mortems — rewards focused gameplans (the last four each closed within days with clean memory curation). active_gameplan is also singular by design.
**Decision**: Three gameplans, one active at a time: (A) THIS one, alpha-to-beta-evidence — B1–B4 (ship 0.9.0, CI OS matrix, G6 native-leg evidence, foreign-repo live loop); (B) stranger-readiness — B5 (quickstart walked in a clean environment, upgrade/uninstall/trust-model docs, troubleshooting runbook distilled from the friction logs); (C) beta-flip — B6 (burn-down of what A and B surfaced, classifier 3→4, release via the ritual). B and C are scoped precisely at A's close-out from the evidence gathered, recorded in A's post-mortem "carried forward" section.
**Consequences**: Each gameplan gets its own post-mortem and lesson curation; GP-B and GP-C stay cheap to re-scope as evidence comes in; the arc survives session boundaries because D-012's gates live in RELEASING.md, not in any one gameplan's directory.

### D2 — Ship 0.9.0 first — as ordering preference, not declared dependency (L-11)

**Context**: The CHANGELOG [Unreleased] backlog (shape-C wiring, D-010 doctor probes, release-check, RELEASING.md, [memory] config) is done, green, and gated; release-check exists precisely to make this mechanical. Phases 1–3 (CI matrix, G6 evidence, foreign-repo loop) have no technical dependency on the release — they exercise git HEAD, not the PyPI artifact. L-11 (promoted this morning) says declare dependencies by technical need, not narrative order, because narrative chains get violated the moment a gate splits a phase.
**Decision**: Phase 0 ships 0.9.0 first as a sequencing PREFERENCE — B2–B4 evidence should cite work that is already public, and an unshipped backlog is compounding risk (L-08's whole family) — but phases 1–3 are declared independent (no depends_on), so any of them can proceed if the release stalls on credentials or registry state. Precedent: 0.8.0 shipped with H-08 open by explicit user decision; shipping with a named, gated residual is house-legal.
**Consequences**: The phase table carries honest dependencies (only Phase 4 depends on 0–3); a stalled release blocks B1 only; D-012's B1 stays the gate that says whether shipping actually happened.

### D3 — CI leg honesty: windows runners prove the NATIVE win32 leg; the windows-wsl executor matrix stays local dated evidence

**Context**: GitHub-hosted windows runners have no WSL, so scripts/wiring_matrix.ps1 (which spawns wsl.exe -d ubuntu) cannot run in CI — but they DO have Git for Windows and cmd.exe, and the native-win32 surface is currently the least-proven code in the engine: hook.cmd is rendered by tests but has never been executed anywhere; every "win32" test passes by monkeypatching sys.platform on Linux. Claiming "tested on Windows" off monkeypatched platform checks would be exactly the probe-context≠consumer-context false green D-010 retired (L-09, L-10).
**Decision**: B2's windows-runner cells must EXECUTE the native win32 leg for real: hook.cmd spawned via cmd /c — digest passthrough, breadcrumb-on-dead-engine, repo anchor from a hostile cwd — as live win32-only tests (the cmd twins of test_hook_wrapper's posix_only tests). The windows-wsl executor matrix (Git Bash → wsl.exe) remains local evidence: scripts/wiring_matrix.ps1 plus the dated outputs in the harness-truth gameplan registry, re-run on the reference host when wiring changes. Every CI claim and skip guard names the leg it traverses or skips, per D-010.
**Consequences**: The 4 live executor-leg tests skip cleanly on all runners by construction (their guard requires WSL interop); new win32-only live tests skip everywhere except real Windows; the suite stops being silently linux-shaped — expect genuine win32 failures to surface in Phase 1 and be fixed, not skipped around.

## Open Items

_(O1, O2, … — blockers and cross-phase questions.)_

## Phase Breakdown

### Phase 0: Beta gates on the record; ship 0.9.0

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable assertion)_

### Phase 1: CI proves the OS matrix; win32 leg executed for real

**Goal**: Expand test.yml from ubuntu-only to ubuntu/macos/windows-latest × py3.11–3.13 (9 cells, fail-fast off) and make the suite truthful per-OS: fix the genuine win32 failures this will surface (e.g. native init registers hook.cmd on win32 where tests assert hook.sh) by per-OS parametrization — never by weakening assertions — and add win32-only LIVE execution tests for the cmd wrapper per D3 (digest passthrough, dead-engine breadcrumb, hostile-cwd anchor, executed via cmd /c on the real runner). Exit criteria: all 9 cells green on the same commit; the win32 wrapper-execution tests ran (not skipped) in the windows cells; the 4 WSL-interop live tests skipped cleanly everywhere; README badge reflects the matrix run. CAUTION: pushes touching .github/workflows need Windows git + GCM (WSL-side credential lacks workflow scope — see runtime-wiring memory).
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 2: G6: native-leg cold-start evidence

**Goal**: Close (or honestly amend) the last open 1.0 gate: cold-start UX proven on a NATIVE scratch repo. Inside the distro: fresh scratch repo, plain `clauderize init` with session_host native, then the full UX walk — doctor exit 0, digest renders — and the native harness leg traversed faithfully: /bin/sh -c "<registered command string>" from a hostile cwd with the in-band digest as the criterion (L-10 pairing: identity AND digest). If a literal Claude Code cold start on a native-host machine is unavailable, amend G6's wording in RELEASING.md to name exactly which leg was traversed and what residual remains (D-010 honesty applied to the gate itself) — never a silent pass. Exit criteria: G6 marked satisfied in RELEASING.md with dated evidence quoted, or amended with a named residual; the evidence recorded in this gameplan's outputs registry.
**Depends on**: Phase 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 3: Foreign-repo live loop: node profile end-to-end

**Goal**: Prove the full loop on a repo that is not Clauderizer and not python — the first live run of any non-python profile. Scratch node repo with a REAL npm test script (a passing one, then a failing one to prove preflight fires): auto-detect must choose the node profile; then live: init → create a mini-gameplan → cz_preflight runs npm test for real (both directions) → a small tracked change with a decision + lesson recorded → phase transition → outputs + summary → handoff → digest reflects all of it. Drive every tracked write through `clauderize ops` (CLI parity, L-05) so the loop is proven without wiring a second MCP server. Fix every defect found at the defect, with regression tests; zero hand-edits of tracked docs permitted during the loop. Exit criteria: the complete loop transcript recorded in the outputs registry; node-profile defects fixed with tests; suite green.
**Depends on**: Phase 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 4: Beta-evidence consolidation; scope gameplans B and C

**Goal**: Verify B1–B4 hold SIMULTANEOUSLY and put the evidence on the record: an evidence table in docs/RELEASING.md mapping each gate to its dated artifact (B1 → PyPI release + release-check output; B2 → the 9-cell CI run URL; B3 → G6's evidence; B4 → the foreign-repo loop output), re-confirmed with a fresh doctor exit 0, fresh release-check, and the suite green on the final commit. Burn down stragglers phases 0–3 left behind (including the carried-forward MCP-staleness nudge if cheap). Then scope gameplan B (stranger-readiness: B5 — quickstart in a clean environment, upgrade/uninstall/trust-model docs, troubleshooting runbook from the friction logs) and gameplan C (beta-flip: B6) concretely from what the evidence revealed, as this gameplan's carried-forward list. Exit criteria: RELEASING.md evidence table complete for B1–B4 with no unverified cells; zero open findings; close-out ready.
**Depends on**: 0, 1, 2, 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_
