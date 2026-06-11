# beta-flip Gameplan

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

### D1 — The flip is one release with three faces, and the armed guard is its proof

**Context**: B6 (D-012) requires the classifier flip to ship via the ritual with zero open findings and doctor exit 0 at flip time. Three things are waiting on the same release: the ephemeral-wiring fix + -q wiring (in source since stranger-readiness Phase 0, live-proven via local wheel, but published 0.9.0 still wires cache paths); the classifier line (pyproject.toml:15, Alpha → Beta); and quickstart.yml's cache-clean assertion, which deliberately self-disarms on 0.9.0 and hard-asserts on anything later.
**Decision**: Ship all three atomically as the flip release (0.10.0 expected — the actual number comes from a fresh four-registry sweep at staging time, never assumed, L-08). B6's in-band proof is the guard that has been waiting: the first post-release quickstart.yml run resolves the published flip artifact, ARMS the cache-clean assertion, and must pass it — `uv cache clean` followed by a pure digest against PyPI is the wiring fix proven in the wild, on the same run that proves the install path. The README's maturity section flips to beta wording in the same release commit, so the artifact describes itself truthfully at publish time, not before or after.
**Consequences**: No gate is checked by assertion alone: B6's row will cite the release run, the armed quickstart run, and the fresh-resolve output. If the armed assertion fails post-release, that is a finding against the shipped artifact (file it, fix forward) — the guard exists precisely to catch it while the announcement is one commit old.

### D2 — Burn-down before flip: the must-have is the bare-IO meta-test; the rest defer without ceremony

**Context**: Three burn-down candidates rode out of the evidence gameplans: the bare-IO meta-test (the cp1252 class from B2 — 35 bare read_text() calls once decoded engine UTF-8 as Windows locale), the MCP-staleness nudge (the long-running server holds pre-edit modules; known sharp edge for dogfooding sessions), and a doc-sync check (the README's release section contradicted RELEASING.md for months — G7 drift between sibling docs). Only the first guards a class that already bit twice; the other two are quality-of-life with real but smaller blast radius.
**Decision**: Phase 0 MUST land the bare-IO meta-test (a structural test asserting no read_text/write_text/open-in-text-mode without encoding= across src/ and tests/, allowlisting binary modes — the L-04 discipline applied to the codebase's own IO), proven firing on a synthetic violation per L-10. The MCP-staleness nudge and the doc-sync check are best-effort within the same phase: implement if they fit the session, otherwise record as carried-forward in the close-out with one line each — no amendment ceremony, the gameplan's goal is the flip, not the nice-to-haves.
**Consequences**: The flip artifact carries the guard for the encoding class B2 exposed; deferred candidates stay visible in the post-mortem's carried-forward list rather than silently evaporating; Phase 1 is never blocked on quality-of-life work.

## Open Items

_(O1, O2, … — blockers and cross-phase questions.)_

## Phase Breakdown

### Phase 0: Burn-down: structural guards before the flip

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable assertion)_

### Phase 1: The flip release: 0.10.0, Development Status :: 4 - Beta

**Goal**: Stage and ship the flip per the RELEASING.md ritual: fresh four-registry sweep to confirm the version (0.10.0 expected, never assumed — L-08); bump pyproject version + __version__ + the classifier line (pyproject.toml line 15 → "Development Status :: 4 - Beta"); update the README maturity section to beta wording in the same commit (the artifact describes itself truthfully at publish time); retitle CHANGELOG [Unreleased] → [0.10.0]; reinstall the editable venv (H-03 dist-info); init byte-idempotent; doctor exit 0 with zero open findings (the B6 precondition, verified fresh). Then the mechanical sequence: push → release-check exit 0 BEFORE any tag → tag the pushed commit → GitHub Release → publish.yml gate green → PyPI accepts. Exit criteria: 0.10.0 live on PyPI with the Beta classifier visible; release-check was exit 0 pre-tag; suite green; doctor exit 0 on the release commit.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 2: B6 evidence: the armed guard fires green; all six gates hold

**Goal**: Prove the flip in the wild per D1: `uvx --refresh --from clauderizer clauderize --version` → 0.10.0 fresh from PyPI; the first post-release quickstart.yml run must show the cache-clean assertion ARMED and PASSING against the published artifact (uv cache clean → pure digest — the ephemeral-wiring fix proven on the real install path; cite the run id); a fresh-HOME stranger walk against published 0.10.0 confirming digest survival end-to-end. Then consolidate: B6 row ✅ in RELEASING.md's evidence table with dated artifacts, completing B1–B6; update the README maturity section's receipts if any run ids are worth citing; record the 1.0 runway honestly (G6's literal native-harness cold start remains the one named residual; any deferred burn-down items carried). Exit criteria: all six beta-gate rows ✅ with dated artifacts; quickstart green with the armed assertion; suite green; close-out ready.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_
