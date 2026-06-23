# stranger-readiness-dogfood Gameplan

> Created: 2026-06-23
> Status: Complete
> Kind: driven
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

A stranger-readiness hardening dogfood. We stand up three brand-new projects under
the user's WSL home — one at each `clauderize init` size (`pet`, `standard`, `saas`)
— and have fresh-eyes subagents role-play first-time Clauderizer users who init,
build a small app (the `saas` one is a website), run a gameplan, and dogfood the
`cz_*` memory tools, logging every point of friction as they hit it. Phase 4
aggregates the three friction logs, triages and reproduces the genuine issues
against this repo, and records confirmed bugs/rough-edges for remediation.

The deliverable is the friction findings and the fixes they motivate — **not** the
apps. The apps are disposable vehicles for exercising init, cross-host wiring, the
size manifests, the ritual gates (preflight / cascade / amendments), and the memory
tool surface from a cold start.

## Subsystems Touched

Under test (exercised, not modified — except trivially-safe Phase 4 fixes):
- `feat.init-cli` — the `clauderize init` flow, `--size`, and host-axis resolution.
- `subsys.scaffold` — file scaffolding, `.mcp.json` / hook wrapper / kimi-setup, gitignore path-safety (D-031).
- `subsys.profiles` — per-project language auto-detection.
- `subsys.rituals` — preflight / cascade / amendments + the handoff-presence gate (D-024).
- `subsys.mcp-server` + `subsys.mutations` + `subsys.graph` — the `cz_*` memory tool surface and the DAG it writes.

The three `SIZE_MANIFESTS` (config.py:44-100) are the matrix axis.

## Source-of-Truth Captures

_Captured 2026-06-23 from real systems; authority over the gameplan body._
- **Engine under test**: published PyPI `clauderize 1.0.2` via `uvx clauderizer …` — the stranger path (D5). uvx resolve to be re-confirmed at Phase 0 start; the repo's own editable engine also reports 1.0.2.
- **Repo HEAD**: `5090dd6` (branch `main`).
- **Test baseline**: 573 tests (`cz_status`).
- **Sizes under test** (config.py:44-100): `pet` = modules[VISION], no cascade/amendments, preflight[clean_tree,tests]; `standard` = 6 modules, +cascade, 8 preflight checks; `saas` = 14 modules (incl. SECURITY/SCHEMA/DEPLOYMENT/INCIDENTS), +cascade +amendments, 8 preflight checks.
- **Project dirs** (NEW, non-colliding — the home dir already holds unrelated projects that must NOT be touched): `~/cz-dogfood-pet`, `~/cz-dogfood-standard`, `~/cz-dogfood-saas`.
- **Host axis**: engine in WSL, sessions Windows-driven → `session_host = windows-wsl:ubuntu` (D-028, D2).
- **Pre-seeded friction F0**: the gameplan-authoring tools use inconsistent phase identifiers — `cz_add_phase(depends_on_phases=[...])` takes phase *names*, but `cz_set_exit_criteria(phase=...)` takes phase *numbers*. Observed live during planning; seeds the friction log.

## Amendments

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

### D1 — Test matrix = the three literal --size values; saas is the website

**Context**: The init `--size` flag has exactly three choices — pet | standard | saas (cli.py:555) — backed by distinct SIZE_MANIFESTS (config.py:44-100). The goal's phrase "pet standard and saas" maps onto these literal sizes, and "at least one a website" is a content constraint on top.
**Decision**: Build one project per size (one each at --size pet, standard, saas). The saas project is the required website; the pet and standard apps are kept deliberately tiny. Coverage thus spans the full size dial in one matrix.
**Consequences**: Friction is comparable across the manifest gradient (pet = 1 module / no cascade ↔ saas = 14 modules + amendments). The leanest and richest scaffolding + ritual surfaces are both exercised, not just an arbitrary middle.
**Evidence**: src/clauderizer/cli.py:555; src/clauderizer/config.py:44-100
**Status**: active (2026-06-23)

### D2 — Projects live in WSL ~ as separate repos; wiring verified by spawn-probe

**Context**: The engine is the WSL editable venv, while Claude Code sessions are Windows-driven (session_host=windows-wsl:ubuntu — the D-028 host axes). Subagents spawned in this run share this session's host; they cannot launch fresh top-level Claude Code sessions inside the sub-projects, so "did the digest inject in a real new session" is not directly observable from here.
**Decision**: Create each project as its own git repo under ~ (sibling to the Clauderizer repo). Each init records session_host=windows-wsl:ubuntu. Verify the hook + MCP wiring by spawn-probing the composed commands — the same gate init.py step 0b uses — rather than asserting a live session fired.
**Consequences**: Clean isolation from the Clauderizer repo; honest, reproducible verification. The "real new session" question becomes a tracked open item rather than a false claim. Local .mcp.json will carry wsl.exe machine paths and must stay gitignored (D-031).
**Evidence**: D-028; D-031; src/clauderizer/scaffold/init.py:207-223
**Status**: active (2026-06-23)

### D3 — Exercise the local editable HEAD install, not the published uvx artifact

**Context**: "Hardening" targets the current code; HEAD is approximately the shipped 1.0.2. Using `uvx clauderizer` would instead test the published wheel — a different question (published-artifact stranger-readiness).
**Decision**: Subagents invoke `clauderize` from the repo editable venv via `wsl.exe -d ubuntu bash -lc`. A uvx-based second pass that validates the published path is deferred to an open item.
**Consequences**: Findings map directly to fixable HEAD code. Published-artifact stranger-readiness is not covered this round unless the open item is taken up.
**Superseded by**: D5 (2026-06-23)
**Status**: superseded (2026-06-23)

### D4 — Subagents role-play first-time users with minimal priming

**Context**: Authentic stranger friction requires fresh eyes; this session's deep recorded context about Clauderizer internals would mask exactly the rough edges we want to find.
**Decision**: Spawn general-purpose subagents given only what a real first-timer has (the README / the injected CLAUDE.md stanza + their assigned size), instruct them to dogfood the cz_* memory tools in-project and to log friction the moment they hit it, and to return a structured friction log. Do not pre-load them with internal lessons or the engine's design rationale.
**Consequences**: Friction is authentic and comparable across the three runs. Subagents may stumble or misuse tools — that is signal (a discoverability/wiring finding), not a run failure.
**Status**: active (2026-06-23)

### D5 — Dogfood the published PyPI artifact (uvx clauderizer 1.0.2), not editable HEAD

**Context**: User directive: test the published PyPI version (1.0.2). That is the true stranger path — what a first-timer actually gets — and carries no local-venv machine path. Supersedes D3 (editable HEAD).
**Decision**: Subagents invoke the published engine via `uvx clauderizer ...` (resolves clauderizer 1.0.2 from PyPI). The editable-venv install is not used for the dogfood projects. Findings are reported against 1.0.2; any that also reproduce on HEAD become repo fixes in Phase 4.
**Consequences**: Validates the shipped wheel and its zero-install wiring (the uvx-based .mcp.json is portable / path-safe, so it is NOT gitignored in a dogfood project). HEAD-only regressions since 1.0.2, if any, are out of scope unless a finding reproduces there. No editable-venv path appears in the dogfood projects.
**Supersedes**: D3
**Status**: active (2026-06-23)

### D6 — Committed gameplan docs carry no machine PII; scrub-verify before the last-step commit

**Context**: User directive: record everything that may impact the project, but keep PII out of committed files — absolute home paths (which embed the OS username) and the names of unrelated sibling projects. Generalizes D-031 (never commit machine paths) from wiring config to all committed content.
**Decision**: Use `~` / placeholder forms in all gameplan docs; keep real absolute paths only in runtime shell commands, never in tracked content. Committing is the final step, gated on a grep that confirms zero username / home-path hits across the gameplan directory.
**Consequences**: The durable record (findings, decisions, source-of-truth) is preserved while privacy holds. A pre-commit scrub-verify becomes a hard gate on the commit step.
**Evidence**: extends D-031
**Status**: active (2026-06-23)

## Open Items

**O-01.** _(phase Harness and baseline)_ Should a second pass validate the published `uvx clauderizer` stranger path in addition to the editable HEAD install? (Deferred per the HEAD-install decision; decide before Phase 4 closes.) _(resolved 2026-06-23: The dogfood targets the published PyPI artifact (uvx clauderizer 1.0.2) as the PRIMARY install per user directive — not a second pass over editable HEAD. See the superseding decision (D3 superseded).)_

**O-02.** _(phase Pet-size build)_ How to verify the hook + MCP actually fire in a real new Claude Code session (beyond an in-band spawn-probe) without the user manually opening a session in each sub-project? Options: ask the user to open one session per project, or script a headless session probe. _(resolved 2026-06-23: Dogfood verified wiring by spawn-probe: hooks fired and emitted the digest; the MCP server FAILED to serve (→ H-14). A fresh top-level Claude Code session was not launched from here, so the live-session check remains: after 1.0.3, re-init a project and open one new session to confirm the cz_* tools load. Detection is now also covered by the H-15 doctor check.)_

## Phase Breakdown

### Phase 0: Harness and baseline

**Goal**: Stand up the dogfood harness — confirm clauderize is reachable in WSL (done: 1.0.2), create the three NEW non-colliding git repos under ~, author the friction-log schema and the first-time-user subagent prompt template, decide where in-repo friction entries land (open items + lessons; `cz_add_finding` is security-only), and pin the size→app→is-website matrix.
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] `clauderize --version` answers from WSL and the exact version string is recorded
- [ ] three empty, git-initialized project dirs exist under ~ (one each for pet/standard/saas)
- [ ] friction-log schema authored and saved (fields: step, expected, actual, severity, surface, repro)
- [ ] first-time-user subagent prompt template authored (minimal priming; role-play + friction capture + dogfood cz_* tools)
- [ ] test matrix recorded: size -> app -> is-website (saas = website)
- [ ] O-01 (uvx second-pass) decided or explicitly carried forward

### Phase 1: Pet-size build

**Goal**: A fresh-eyes subagent role-plays a first-time user: runs `clauderize init --size pet` on the pet project under ~, builds a tiny app, runs a minimal gameplan, makes at least one tracked in-project memory write, and returns a structured friction log. Exercises the leanest manifest (1 module, no cascade ritual, 2 preflight checks).
**Depends on**: Harness and baseline.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] pet project initialized at size=pet; .clauderizer/ + .claude/skills/ present; init report captured
- [ ] composed hook and MCP commands pass a spawn-probe (wiring reachable via the wsl.exe executor)
- [ ] subagent created and advanced a small gameplan and made >=1 tracked in-project memory write
- [ ] structured friction log returned with every entry tagged by surface + severity

### Phase 2: Standard-size build

**Goal**: A fresh-eyes subagent runs `clauderize init --size standard` on the standard project under ~, builds a small standard app/library, and runs a gameplan phase that exercises the cascade ritual and the 8-check preflight. Returns a structured friction log tagged by surface and severity.
**Depends on**: Harness and baseline.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] standard project initialized at size=standard; the 6 expected modules scaffolded
- [ ] composed hook and MCP commands pass a spawn-probe
- [ ] subagent ran a gameplan phase that exercised a cascade (cz_cascade/cz_resolve_cascade) and the 8-check preflight
- [ ] structured friction log returned, tagged by surface + severity

### Phase 3: SaaS website build

**Goal**: A fresh-eyes subagent runs `clauderize init --size saas` on the saas project under ~ and builds a minimal SaaS website (the required website). Exercises the richest manifest (14 modules incl. SECURITY/SCHEMA/DEPLOYMENT) plus the amendments ritual and a cascade. Returns a structured friction log tagged by surface and severity.
**Depends on**: Harness and baseline.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] saas project initialized at size=saas; the 14 expected modules scaffolded
- [ ] the project is a real website (serves a page / runnable web app)
- [ ] composed hook and MCP commands pass a spawn-probe
- [ ] subagent exercised an amendment (cz_add_amendment) and a cascade
- [ ] structured friction log returned, tagged by surface + severity

### Phase 4: Analyze, triage, harden

**Goal**: Aggregate the three friction logs into one dedup'd, severity-ranked report; triage every distinct finding (bug | rough-edge | wontfix) with a one-line repro or rationale; reproduce the genuine bugs against the Clauderizer repo; record confirmed findings into Clauderizer's own memory (cz_add_finding + open items/lessons); produce a prioritized remediation list and apply trivially-safe fixes with the 573-test baseline held green.
**Depends on**: Pet-size build, Standard-size build, SaaS website build.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] all three friction logs aggregated into one dedup'd, severity-ranked report
- [ ] every distinct finding triaged: bug | rough-edge | wontfix, each with a one-line repro or rationale
- [ ] each confirmed bug recorded in-repo via cz_add_finding (open item where a fix is deferred)
- [ ] prioritized remediation list produced; trivially-safe fixes applied with the 573-test baseline held green
- [ ] O-02 (real-session verification) resolved or explicitly carried forward
