# stranger-readiness Gameplan

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

### D1 — The doc is the test script: stranger walks execute published commands verbatim, locally and as a permanent CI job

**Context**: B5 (D-012) requires the quickstart verified "in a clean environment" — and the premise validated itself during planning: the README's first command, `uvx clauderize init` (repeated at lines 11/92/133/205, with a third spelling in pyproject's comment), fails against the real registry ("clauderize was not found") because uvx resolves the package FROM the command name and the package is `clauderizer`. The author never sees this: the home repo runs an editable venv. No docker/podman exists in the distro for a true clean container.
**Decision**: Two clean-environment vehicles, both executing the README text verbatim (any deviation is a defect in doc or product, fixed at the right layer, never in the transcript): (1) LOCAL — a fresh-HOME simulation (env -i, fresh UV_CACHE_DIR, uv installed per its own official one-liner, no engine preinstalled) for interactive iteration, with the shared-userland residual named; (2) DURABLE — a quickstart.yml CI workflow on ubuntu-latest (a genuinely clean machine every run) that executes the README's install path and asserts the digest renders, making the stranger walk a permanent regression guard rather than a one-time ceremony.
**Consequences**: The quickstart line gets fixed everywhere to the verified-working form before anything else (likely `uvx --from clauderizer clauderize init`); README claims stay executable forever or the badge goes red; the quickstart.yml push needs the Windows git + GCM credential lane (workflow scope).

### D2 — Trust gets two documents: TRUST.md for the model, SECURITY.md for reporting

**Context**: Clauderizer writes into surfaces the harness EXECUTES (the SessionStart hook command in .claude/settings.json; the MCP server registration in .mcp.json) plus repo content (.clauderizer/ engine files, the CLAUDE.md stanza, skills). A stranger evaluating adoption — or reviewing a teammate's PR that adds the wiring, or cloning a repo with pre-seeded wiring — currently has no document stating what runs when, with what contract. The external competitive analysis (2026-06-10) flagged trust posture as an adoption factor; GitHub convention reserves SECURITY.md for vulnerability reporting.
**Decision**: docs/TRUST.md carries the model, accurate against code with file/function citations: the exact write surfaces of init (all four), the hook execution boundary (the harness executes the registered string at session start; wrapper contract = anchored cd, stdout-only reporting, always exit 0), the MCP server surface (stdio, spawned by the client, repo-local), the cloned-repo-with-preseeded-wiring scenario (the harness's own trust dialog is the execution gate; Clauderizer never self-executes), and the supply-chain posture (zero runtime deps, Trusted Publishing, the tag==source gate). A minimal root SECURITY.md handles reporting and points at TRUST.md. README links both.
**Consequences**: Trust claims become grep-verifiable against the code they describe (G7 discipline applied to a new doc class); the preseeded-wiring scenario gets an honest written answer instead of silence; future wiring changes must keep TRUST.md in sync (cascade-by-review at release time).

### D3 — README positioning: git-native working memory, honest beta arc, absolute links

**Context**: The external analysis recommended pitching "the durable project memory layer for coding agents" / "git-native working memory" — close to the existing pyproject description but sharper than the README's current tagline. The README is also the PyPI long_description, where relative links break. The beta gates are now public in docs/RELEASING.md, and the classifier honestly says Alpha until GP-C flips it.
**Decision**: One copy pass, scoped: adopt the git-native working-memory framing and the adoption wedge (CLAUDE.md alone is too weak → ad-hoc handoffs rot → project memory belongs in the repo → tool-callable infrastructure); fix every quickstart occurrence to the phase-0-verified form; link TRUST/TROUBLESHOOTING/UPGRADING with absolute GitHub URLs (PyPI rendering); state the maturity honestly (alpha classifier, public beta gates, what evidence already exists). No renaming, no identity changes — branding stays the user's call; this is copy, and the user reviews the result as the product's public face.
**Consequences**: README, PyPI page, and reality stop disagreeing; the positioning recommendation gets executed where it was already half-true instead of spawning a rebrand; the maturity statement self-updates pressure toward GP-C (the public gates table shows B5/B6 pending until they are not).

## Open Items

_(O1, O2, … — blockers and cross-phase questions.)_

## Phase Breakdown

### Phase 0: The stranger's first hour: quickstart truth, live

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable assertion)_

### Phase 1: Upgrade and uninstall stories, walked live

**Goal**: Make leaving and upgrading as documented as arriving. UPGRADE: on a scratch repo, simulate the 0.8→0.9 shape (write the pre-H-09 wrapper template via render_hook_wrapper without root), show doctor's "template predates" nudge firing (exit 3), then plain re-init healing it (byte-idempotent after); document the general rule — upgrades are "update the engine, re-run clauderize init, doctor exit 0", with the engine-moved vs template-predates distinction and the uvx-cache caveat (L-08). UNINSTALL: document and walk live what to remove (the clauderizer entry in .mcp.json, the SessionStart hook entry in .claude/settings.json, .clauderizer/, the CLAUDE.md marker block, .claude/skills/clauderizer-*) and what to KEEP — docs/ is the project's memory, not the tool's; verify the walked end-state (doctor reports not-a-clauderized-repo exit 1; a Claude Code session starts clean with no digest and no errors). Ship as docs/UPGRADING.md (upgrade + uninstall sections), README-linked. Exit criteria: both walks transcribed in the outputs registry; the doc's commands executed verbatim from the doc; suite green.
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 2: Trust model on the record (TRUST.md + SECURITY.md)

**Goal**: Write docs/TRUST.md per D2 — the four init write surfaces (.mcp.json registration, .claude/settings.json SessionStart entry, .clauderizer/ engine files incl. the wrapper contract, CLAUDE.md marker block + skills), the hook execution boundary (the harness executes the registered string at session start; anchored cd; stdout-only; always exit 0 — cite hosts.py render_hook_wrapper and the H-01/D4 rationale), the MCP surface (stdio, client-spawned, repo-local), the preseeded-wiring scenario (cloning a repo that already carries wiring: the harness's own trust/permission flow gates execution; Clauderizer adds no self-executing path), and the supply-chain posture (zero runtime deps from pyproject, Trusted Publishing OIDC, the tag==source gate, release-check). Root SECURITY.md: minimal reporting policy pointing at TRUST.md. Every behavioral claim cites the file/function that implements it, grep-verified. Exit criteria: both docs exist and are code-accurate; README links them (absolute URLs per D3); no claim without a citation.
**Depends on**: Phase 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 3: Troubleshooting runbook from the scar tissue

**Goal**: Distill docs/TROUBLESHOOTING.md from what actually broke and got diagnosed (HARDENING H-01..H-09, the gameplan friction logs, doctor's exit contract): "no digest at session start" as the headline ladder (clauderize doctor → the executor-leg verdict reading → breadcrumb meanings: engine unreachable / repo unreachable / status unavailable / pure silence → harness transcript hook attachments as the diagnostic surface → scripts/wiring_matrix.ps1 for windows-wsl hosts → shape A fallback per harness-truth D2); doctor exit codes 0/1/2/3 and what each obligates; release-check exit 2 on a just-shipped version is designed refusal, not drift; cz_* tools absent mid-session (server enumerated at start — restart is the last mile; clauderize ops is the write fallback, L-05); stale uvx cache (--refresh, L-08); unborn-branch preflight skips on fresh repos. Every quoted string (breadcrumb prefixes, check labels, digest first-line) grep-verified against src so the runbook never drifts from the code. Exit criteria: the doc exists; each entry names its evidence source (finding id or live transcript); strings verified; README-linked.
**Depends on**: Phase 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 4: README positioning pass + B5 consolidation

**Goal**: Execute D3's copy pass on the README (361 lines today): the git-native working-memory framing and adoption wedge; every quickstart occurrence corrected to the phase-0-verified command (lines 11, 92, 133, 205 today — plus pyproject's comment spelling); absolute GitHub URLs to TRUST.md, TROUBLESHOOTING.md, UPGRADING.md, RELEASING.md's gates; an honest maturity statement (alpha classifier, public beta gates B1–B4 ✅, B5/B6 pending). Then consolidate B5: re-run the clean-environment walk fast against the FINAL README text, confirm the quickstart CI job is green on the same commit, fill the B5 row in RELEASING.md's evidence table with dated artifacts, and refine GP-C's scope from anything this gameplan surfaced. The README ships via normal push and is explicitly flagged for the user's review as the product's public face. Exit criteria: B5 row ✅ with artifacts; quickstart CI green on the final text; suite green; GP-C scope updated in the outputs registry.
**Depends on**: 0, 1, 2, 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_
