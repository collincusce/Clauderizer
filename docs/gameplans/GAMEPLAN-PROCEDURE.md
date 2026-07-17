# Gameplan Procedure

**Procedure version**: 1.7.0
**Last updated**: 2026-07-16
**Origin**: Synthesis of `attago/docs/gameplans/GAMEPLAN-PROCEDURE.md` + `lsatprep` patterns + lessons from poe2.design design session
**Purpose**: A canonical procedure for planning and executing multi-phase projects with AI agents across many sessions, designed primarily as **AI working memory** that survives context window limits.

**Changelog**:
- **v1.7.0** (2026-07-16): **Self-audit after every gameplan.** Closing a gameplan now runs a work/release self-audit (`cz_audit`) before the post-mortem — an advisory gate (INVARIANT-05) for the failure modes a green test suite does not catch. Mechanical signals: version single-sourcing (pyproject vs the package `__version__` vs the top CHANGELOG entry — a mismatch a stale editable install hides), an uncommitted working tree, unresolved cascades/open items. Judgment checklist: verify in a **clean environment** (not a stale editable install), re-audit every **consumer** of a changed entity (including untracked ones — uninstall, CLI, docs claims), and claim only what you **verified**. Distinct from `cz_critique` (which audits memory coherence); its findings feed the post-mortem's procedure-improvements. Born from a real miss: a version bumped in one place but not another, green locally on a stale venv, caught only by a clean install.
- **v1.6.0** (2026-07-01): **Onboarding an existing project.** A repo that already has real documentation deserves seeded memory, not placeholder scaffolds sitting beside it. `cz_onboard` (read-only) lists the Clauderizer docs that are still scaffold placeholders and the repo's existing docs that likely hold project knowledge; the `clauderizer-onboard` skill walks the agent through reading those sources and seeding memory — prose docs rewritten directly, subsystems/features recorded as entities, decisions and rules recorded with provenance naming the source file. `clauderize init` says when onboarding applies, and already-initialized repos learn about it from `clauderize upgrade`. The engine detects and prompts; it never seeds anything itself.
- **v1.5.0** (2026-07-01): **Scoped memory, approval criteria, deliverables, standing conditions, corpus modernization.** Invariants may carry a **Scope** (project-wide, or one gameplan's) and an **Audience** label, and lessons an audience tag — reads *filter* (a gameplan's context carries the shared rules plus its own; untagged entries reach everyone), and nothing is ever hidden from the canonical files or the written handoff. An exit criterion may be an **approval** (`APPROVAL: <artifact-path> — <description>`): recording the sign-off binds it to the artifact's content hash, so editing the artifact makes the approval read as stale everywhere until it is re-approved. Campaign-style kinds define a **deliverable lifecycle**; each deliverable is a tracked entity moving through it, with a board in the gameplan's detail view. Loop and campaign gameplans may declare **standing conditions** (`.clauderizer/conditions.<gameplan-id>.toml`) — probes evaluated whenever status is asked for, proposing an iteration when one trips. **`clauderize upgrade`** modernizes an older corpus: mechanical updates apply automatically (the config's procedure stamp and migrations, missing gate-example files, refreshing this document); memory-shaped improvements only ever surface as proposals. All additive; a repo using none of it behaves exactly as before.
- **v1.4.0** (2026-06-27): **Concurrent multi-axis gameplans.** A repo can run several gameplans at once with an ergonomic **focus** (the default target; `cz_focus` / `cz_gameplans` + a portfolio in the status digest). Gameplan **kinds** become data (`kinds/*.toml`: vocabulary + first-phase template + preflight set; `driven` / `loop` / `campaign` + custom overlays in `.clauderizer/kinds/`; the lexicon is display-only — on-disk structure is identical across kinds). **Per-kind preflight** runs the kind's checks via a command-gate primitive wired in `.clauderizer/preflight.<kind>.toml`. **Cross-gameplan dependencies** (`cz_consumes`) let a cascade fan out across axes. Back-compatible: a single-gameplan repo behaves exactly as before.
- **v1.3.0** (2026-06-21): Added the **Loop Gameplan** (`kind: loop`) as a first-class type — a standing, iterative maintenance initiative (trigger / iteration body / per-iteration exit / convergence metric / spawn-driven escape hatch), complementing the finite driven gameplan. Realized by `cz_loop_step` over the curator (`cz_curate`); autonomous in cadence, supervised in mutation (INVARIANT-05).
- **v1.2.1** (2026-06-09): Amendment entries carry a `Cascade report` line only when the `amendments` ritual is enabled, and as a pending pointer (`run cz_cascade for the affected entities`) rather than a per-amendment filename — cascade reports are per-entity files, so `<date>-A-NNN.md` never exists (the A-001 dangling-pointer bug).
- **v1.2.0** (2026-06-09): Named `clauderize ops <file.json|->` the canonical no-MCP fallback for every tracked write (L-05): op names and arg shapes are exactly the `cz_*` tool names and schemas, so recording never depends on a live MCP client. Ad-hoc stdio-probe/shim patterns are retired.
- **v1.1.0** (2026-05-02): Added **Amendment (`A-NNN`)** concept as a first-class entity for tracking gameplan body changes after Phase 0 starts. Added "Procedure: Amend a Gameplan" with cascade-to-affected-phases rules. Added mini-gameplan-vs-amend-existing decision rule of thumb. Projects adopting may declare `INVARIANT-13: Gameplan amendments cascade before session ends` (poe2.design adopts; smaller projects may not).
- **v1.0.0** (2026-05-02): Initial synthesis from existing project procedures + session-derived improvements.

> This document is project-agnostic. Copy it as-is into any new project's `docs/gameplans/GAMEPLAN-PROCEDURE.md`. All project-specific content goes in `CLAUDE.md` (project root) and `docs/` named files.

---

## Concurrent gameplans: focus, kinds, cross-gameplan

A repo can run **several gameplans at once** — e.g. a *code* gameplan and a *campaign* gameplan — each advanced in its own sessions. The model:

- **Focus.** One gameplan is the *focus* — the default target for `cz_status`, do-phase, handoff, and preflight when you don't name a `gameplan_id`. Switch it with `cz_focus <id>` (or `clauderize focus <id>`); never hand-edit the config pointer. The set of **open** gameplans is *derived* from each gameplan's phase table, never stored.
- **Portfolio.** `cz_gameplans` (or `clauderize gameplans`) lists every open gameplan with its kind, phase, blockers, and the focus mark. The status digest expands a portfolio block automatically once more than one gameplan is open; with a single gameplan it reads exactly as before.
- **Kinds.** Every gameplan has a **kind** (`> Kind:` in `GAMEPLAN.md`) that sets its vocabulary, first-phase template, and preflight checks — `driven` (code), `loop` (maintenance), `campaign` (creative), or a custom kind defined in `.clauderizer/kinds/<name>.toml`. The vocabulary is **display-only**: a campaign reads in *stages* and *assets* while the on-disk structure (`## Phase Breakdown`, `### Phase N`) stays identical, so every parser and tool is unchanged.
- **Per-kind preflight.** A kind's preflight runs *its* checks — a campaign's QA gates (virality, brand-lint, duration, …) instead of tests/build. Gates are generic shell commands you wire in `.clauderizer/preflight.<kind>.toml`; an unwired gate skips with a hint. The engine ships the mechanism; you supply the checks.
- **Cross-gameplan dependencies.** When one axis produces an artifact another consumes, declare it with `cz_consumes` — the consuming gameplan becomes a dependent in the graph, so changing the shared artifact cascades **across** gameplans: the other axis gets a pending cross-ref its own `cascade_hygiene` catches. Memory scoping stays explicit — project invariants/ADRs are shared by all gameplans, a gameplan's own decisions/lessons are local, and consumed artifacts are surfaced in the handoff's "Consumes" section (with each entity's current status and version).

## Scoped Memory (project · gameplan · audience)

Shared memory has two levels and one optional tag, and reads **filter — never shadow, never hide**:

- **Scope.** An invariant is project-wide by default. One that belongs to a single gameplan — a campaign's brand rules, say — is recorded with `scope="gameplan:<id>"` on `cz_add_invariant` and rendered with a `**Scope**:` line. Another gameplan's context simply doesn't carry it; the canonical `INVARIANTS.md` always holds everything, append-only.
- **Audience.** An invariant or lesson meant for one working role (a copywriter, an art director, a coder) may carry an audience label. `cz_next_phase_context(audience=...)` returns that role's view: other roles' tagged entries drop out, untagged entries always pass. The **written handoff file is never filtered** — it stays the complete, self-contained record.
- **Duplication pressure.** Recording an invariant that strongly overlaps an existing one surfaces the overlap and suggests a scoped entry instead of a global re-declaration — advisory, the write always stands. Curation never proposes consolidating entries across scopes or audiences.

## Loop Gameplans (kind: loop)

Most gameplans are **driven**: a finite phase DAG with a terminal post-mortem, advanced phase by phase. A **loop gameplan** (`kind: loop`) is the complement — a *standing* initiative whose "phases" are recurring **iterations** of a maintenance/curation cycle, with no terminal state:

- **Trigger** — what wakes an iteration: a schedule, a threshold (e.g. lessons past a bound), or a gameplan close. Threshold triggers can be *declared* as standing conditions (below) so status itself watches them; calendar cadence belongs to the host's scheduler, which simply opens a session that asks for status.
- **Iteration body** — gather signal → SURFACE proposals → the agent confirms via blessed writes (never auto-mutation, INVARIANT-05). In Clauderizer this is `cz_loop_step` (a corpus-health metric + `cz_curate` proposals + a `converged` flag).
- **Per-iteration exit** — the Loop-Engineering `/goal` triad: an explicit end state, a runnable check, and a guardrail (max-iterations / scope pin). An iteration ends when no actionable proposal remains (`converged`).
- **Convergence metric** — a corpus-health measure trended across iterations (monotone-improving, not a one-shot "done").
- **Escape hatch** — when an iteration detects structural work too big for a maintenance pass, it SUGGESTS spawning a *driven* gameplan (`spawn_gameplan`); it never auto-creates one.

Driven and loop gameplans interlock: driven gameplans **feed** the loop (their lessons/outcomes are its telemetry); the loop **spawns** driven gameplans for the structural work it surfaces. A loop gameplan is **autonomous in cadence, supervised in mutation**.

## Standing Conditions

A loop or campaign gameplan may declare its threshold triggers in `.clauderizer/conditions.<gameplan-id>.toml`:

```toml
[conditions]
backlog_low = "test $(ls campaigns/shorts/approved | wc -l) -lt 3"
weekly_due  = "python tools/cadence_due.py"
```

Each condition is a shell probe — exit 0 means **met**. Probes run only when status is explicitly asked for (`cz_status`, `clauderize status`, pre-flight, `cz_loop_step`), never on a timer and never from the session-start hook. A met condition surfaces as one line — *"standing condition met — iteration proposed"* — and that is all: the engine proposes, the agent decides.

## Deliverables (campaign-style gameplans)

A campaign's real execution units are its **deliverables** — a flagship film, a pillar short, a deck — each progressing independently. A kind may define their lifecycle in its TOML (`[lifecycle] statuses = [...]`; the shipped campaign kind uses `concept → spec-approved → produced → assembled → qa → shipped`), and each deliverable is recorded as a normal tracked entity:

```
cz_upsert_entity(id="deliv.flagship-film", type="deliverable",
                 status="concept", fields={"gameplan": "<gameplan-id>"})
```

Its status then moves through the lifecycle via `cz_transition_status` (an unfamiliar status warns, never blocks), and the gameplan's detail view (`cz_gameplans gameplan_id=...`) renders the deliverables board. The status digest carries at most a one-line rollup ("Deliverables: 3/6 shipped").

**A deliverable is never an individual rendered file.** One film may produce thirty exports across aspect ratios and caption variants — those stay in the repo (a manifest, a directory listing); the *deliverable entity* is the film. Keeping that line is what keeps handoffs small.

## Approval Criteria (hash-bound sign-offs)

The highest-leverage human control — "someone signs off on this artifact before money or reputation is spent" — is an exit criterion of the form:

```
- [ ] APPROVAL: briefs/shot-spec.md — human signs off the shot spec
```

Recording the sign-off (`cz_approve_gate`) stamps the criterion with the artifact's content hash and the date. Every later read recomputes the hash: **edit the artifact and the approval reads as stale everywhere** — check-off, phase completion, pre-flight — until it is re-approved. A hand-ticked checkbox never counts as an approval. Like every gate, this surfaces and never blocks.

## Onboarding an Existing Project

A project that predates Clauderizer already knows what it is — the knowledge
just lives in a README, design docs, or specs instead of in memory. Onboarding
moves the *judgment-bearing distillate* over without moving the files:

1. `cz_onboard` (read-only) reports which Clauderizer docs are still scaffold
   placeholders and which existing files look like specs (paths only — the
   agent reads them itself).
2. The agent reads the sources and seeds: prose docs (VISION, ARCHITECTURE,
   and their siblings) are rewritten directly — they are living documents, not
   append-only logs; subsystems and features become tracked entities; decisions
   and standing rules already in force are recorded with provenance naming the
   source file.
3. Re-running `cz_onboard` shows seeded docs dropping out.

The engine never synthesizes prose or seeds a doc itself — detection and
prompting only. `clauderize init` surfaces the advisory when it applies, and
already-initialized repos are pointed at it by `clauderize upgrade`.

## Corpus Modernization (upgrading delivers improvements)

The engine stamps each repo's config with the procedure version it was last brought up to. When a newer engine meets an older corpus, the status digest and `clauderize doctor` say so in one line, and **`clauderize upgrade`** closes the gap in two tiers:

- **Mechanical — applied for you**: the config stamp and config migrations, missing per-kind gate example files, the refresh of this document. All engine-owned, all visible in `git diff`.
- **Memory — proposed, never applied**: declared QA gates with no wired command, near-duplicate invariants that look like scope-tag candidates, campaigns without deliverable entities, loops without standing conditions. Each proposal names the ordinary recording tool that would act on it; decisions, invariants, lessons, and findings are never edited by the engine.

---

## Why This Exists

AI sessions have two memory limits:
1. **Cross-session**: a new chat starts with nothing in context.
2. **Intra-session**: a long-running session can fill its context window mid-task.

Without a system, both produce the same failure modes:
- Lost decisions ("wait, why did we choose X?")
- Contradicted decisions ("but the previous session said Y")
- Duplicated work ("this was already done in phase 3")
- Drift between intent and reality
- Endless re-derivation of context the human already explained ten times

This procedure solves that by writing everything down in a structured format that **the AI itself reads at the start of every session**, plus an explicit ritual for keeping that record honest as work progresses. It is a *self-documenting code* analogue, applied to project state. The notes belong to the AI; the format prevents the AI from losing track of the reasoning and dependencies.

**Design philosophy (single most important sentence)**: This is structured for AI memory, not human team coordination. Heavy structure, explicit IDs, machine-readable frontmatter, and rigorous cascade discipline are *features*, because the consumer is a stateless agent.

---

## Concepts and Vocabulary

### Three-Level Hierarchy

| Level | What it is | Granularity | Document |
|---|---|---|---|
| **Gameplan** | A coherent project, plan, or initiative — soup to nuts | Days to months | `GAMEPLAN.md` per gameplan |
| **Phase** | A session-sized chunk of a gameplan | 1–3 days of focused work | A row in the gameplan + a phase handoff doc |
| **Task** | A bite-sized unit within a phase | 30 min – 2 hours | A bullet in the phase's task table |

A gameplan contains 5–25 phases. A phase contains 3–15 tasks. Sub-phases (`0A`, `0B`, `0C`) are allowed when one phase needs internal grouping but isn't worth splitting.

### Two Dependency DAGs

**Project DAG** — long-lived, lives across all gameplans:
- Nodes: subsystems, features, capabilities, external services, decisions, invariants
- Edges: "depends on," "implements," "documented in"
- Lives in `docs/` named files (frontmatter declares the graph data)

**Gameplan DAG** — scoped to one gameplan, replaced/closed when the gameplan completes:
- Nodes: phases and tasks within phases
- Edges: execution-order dependencies (`depends_on_phases`)
- Lives in `GAMEPLAN.md` and the phase handoffs

The two DAGs reference each other. A phase declares which subsystems/features it touches; a feature declares which gameplans implemented it. This bidirectional traceability is what makes cross-gameplan reasoning ("what's in flight that affects subsystem X?") tractable.

### Three Roles

| Role | When | Purpose | Lives For |
|---|---|---|---|
| **Planning session** | Once at gameplan start | Writes `GAMEPLAN.md`, makes initial D-decisions, drafts phase breakdown | One session |
| **Coordinator session** | Between phases, throughout | Reviews handoffs, propagates lessons, runs cascades, generates next phase prompt, resolves cross-phase conflicts | Long-lived (spans the project) |
| **Phase session** | One per phase | Reads its handoff, executes the phase, writes the next handoff | One session |

The planning session and coordinator session may be the same physical chat if context allows. Phase sessions are always separate to keep context fresh.

### Document Types

Every document type has a defined role and an owner. The list:

**Project-level (across all gameplans)**:
- `CLAUDE.md` (project root) — auto-loaded by Claude Code; critical rules + project overview.
- `README.md` (project root) — for humans / GitHub landing.
- `CHANGELOG.md` (project root) — milestone-level history.
- `docs/` named living docs (specifications below).
- `docs/plans/` — paired feature plan + design docs (sub-gameplan scale).

**Per-gameplan (lives in `docs/gameplans/<gameplan-id>/`)**:
- `GAMEPLAN.md` — master plan, fixed reference (decisions + phase breakdown).
- `CONTEXT.md` — current technical state at gameplan start (optional if `GAMEPLAN.md` covers it).
- `CHAT-HANDOFF-INDEX.md` — phase tracker + protocol + accumulated lessons (living).
- `PHASE-STATUS.md` — phase status + outputs registry + corrections (living).
- `handoffs/PHASE-N-HANDOFF.md` — self-contained, cumulative per-phase context.
- `POST-MORTEM.md` — written after gameplan completion.

**Universal (shared across projects)**:
- `~/.claude/CLAUDE.md` (or wherever the harness expects it) — global preferences (working style, environment, security baseline). Symlinked from a central location, never copied.

### Frontmatter

YAML metadata at the top of a markdown file, between two `---` lines:

```markdown
---
id: feat.example-feature
type: feature
version: 1.0.0
status: planned
depends_on:
  - subsys.auth
  - feat.other-feature
introduced_by: D-007
documented_in: docs/features/example.md
last_verified: 2026-05-02
---

# Example Feature

[normal markdown body]
```

Frontmatter is the graph-data; body is human/AI-readable prose. Both matter; both are sources of truth.

**Frontmatter is required on**: every doc in `docs/features/`, `docs/subsystems/`, `docs/decisions/` (if split), and any other tracked-entity doc. **Frontmatter is optional on**: prose-heavy docs (VISION, CHANGELOG, post-mortems) where the doc itself is its own entity.

### Semver for Entities

Tracked entities (subsystems, features) declare a `version: MAJOR.MINOR.PATCH` in frontmatter. Dependents pin via standard semver constraints:

```yaml
depends_on:
  - subsys.calc-engine@^1.0.0  # any 1.x
  - subsys.auth@~2.3.0          # any 2.3.x
  - feat.build-editor@1.4.2     # exactly this version
```

Cascade only flags MAJOR-bump dependents for review. Minor and patch bumps are non-breaking by definition; cascade ignores them. **Versions live in the entity's own frontmatter; pinning lives in the dependent's frontmatter.**

### Amendment (`A-NNN`)

A change to a gameplan after it has started executing. Distinct from a **correction** (real-time discovery of a divergence between gameplan and reality, captured in `PHASE-STATUS.md` Corrections Log) and a **decision** (a `D-NNN` ADR that may or may not require gameplan body changes).

Captured as a numbered entry in a `## Amendments` section near the top of `GAMEPLAN.md` (or in a dedicated `AMENDMENTS.md` if the gameplan is large enough that this section grows long). Format:

```markdown
### A-NNN — <Title>

- **Date**: YYYY-MM-DD
- **Affected sections in GAMEPLAN.md**: <list>
- **Affected phases**: <list>
- **Triggered by**: <D-NNN, real-time discovery, scope change, etc.>
- **What changed**: <text>
- **Why**: <text>
- **Cascade report**: _pending — run `cz_cascade` for the affected entities; reports land in `_cascade-reports/`_
```

The `Cascade report` line appears only when the project's `amendments` ritual is enabled (INVARIANT-13 adopters), and always as the pending pointer above — cascade reports are per-entity files named by the engine, so an amendment entry never promises a `<date>-A-NNN.md` filename.

Amendments are append-only (just like decisions) — superseded amendments stay in the record with `Status: superseded` and a `Superseded-by: A-MMM` link.

**Mini-gameplan vs amend-existing**:

- **Amend existing gameplan** (`A-NNN`): the change is *within* the gameplan's existing scope. Examples: "Phase 9 needs a task we missed", "Phase 12's dependency should also include Phase 11", "Source-of-Truth Captures need an additional field for the Stripe customer ID format we discovered."
- **New mini-gameplan** (separate `docs/gameplans/<new-id>/` directory): the change is *outside* the existing scope. Examples: a post-launch leaderboard feature has a different goal and is separable work; a major refactor unrelated to the original gameplan's mission.
- **Rule of thumb**: if you'd write the same `## Project Overview` paragraph for the new work as for the original gameplan, amend; if a fresh project overview makes more sense, mini-gameplan.

Cascade discipline applies to amendments per INVARIANT-13 (if adopted; the project's own `INVARIANTS.md` declares whether it adopts amendment cascade as an invariant — `attago` and `poe2.design` do; smaller projects may not).

### Status Values

Universal across all entity types and phases:

| Status | Meaning | Cascade behavior |
|---|---|---|
| `planned` | Defined, not yet started | None |
| `ready` | All deps satisfied; can begin | Notifies dependents that it's coming online |
| `active` | Currently being worked on | Notifies dependents to expect changes |
| `blocked` | External blocker (e.g., GGG approval, ICANN lock) | Notifies dependents of blocker; lists what unblocks |
| `completed` | Done; deliverable verified | Notifies dependents they can use it |
| `superseded` | Replaced by a newer entity | Notifies dependents to migrate to the replacement |
| `deferred` | Removed from current scope | Notifies dependents this won't happen now |

Every status transition runs cascade (see Cascade Discipline below).

---

## Repository Structure (Canonical)

```
<project-root>/
├── CLAUDE.md                       ← auto-loaded; critical rules + project overview
├── README.md                       ← human / GitHub landing
├── CHANGELOG.md                    ← milestone-level history
├── .gitignore                      ← always exclude docs/gameplans/ if it contains AWS IDs
├── docs/
│   ├── VISION.md                   ← what & why
│   ├── REQUIREMENTS.md             ← scope, tier model, hard constraints
│   ├── ARCHITECTURE.md             ← subsystems + capabilities; with frontmatter
│   ├── ENGINEERING-PRINCIPLES.md   ← N guiding principles for design decisions
│   ├── DEPLOYMENT.md               ← infra, environments, accounts, profiles
│   ├── DATASOURCES.md              ← external data + APIs we depend on
│   ├── SCHEMA.md                   ← data-tier schemas
│   ├── SECURITY.md                 ← auth model, threat model, secrets policy
│   ├── TESTING.md                  ← test discipline, baselines, runners
│   ├── HARDENING.md                ← persistent risk tracker (NEVER delete entries)
│   ├── INCIDENTS.md                ← outage / break-glass log
│   ├── DECISIONS.md                ← project-wide ADRs (D-NNN), append-only
│   ├── INVARIANTS.md               ← rules that hold across all work
│   ├── GLOSSARY.md                 ← domain + planning vocabulary
│   ├── BRANDING.md                 ← if applicable: visual identity, palette, type
│   ├── plans/                      ← paired feature-plan + design docs
│   │   ├── YYYY-MM-DD-feature-plan.md
│   │   └── YYYY-MM-DD-feature-design.md
│   ├── features/                   ← one frontmatter doc per feature (lazy)
│   ├── subsystems/                 ← one frontmatter doc per subsystem (lazy)
│   └── gameplans/
│       ├── GAMEPLAN-PROCEDURE.md   ← THIS DOCUMENT
│       └── <gameplan-id>/          ← e.g. 2026-04-30-mvp-launch
│           ├── GAMEPLAN.md
│           ├── CONTEXT.md           (optional)
│           ├── CHAT-HANDOFF-INDEX.md
│           ├── PHASE-STATUS.md
│           ├── handoffs/
│           │   ├── PHASE-0-HANDOFF.md
│           │   ├── PHASE-1-HANDOFF.md
│           │   └── ...
│           └── POST-MORTEM.md       (after completion)
└── bin/                            ← project tooling (added as needed)
    ├── regen-graph                 ← rebuild project DAG from doc frontmatter
    └── cascade                     ← find dependents of any entity ID
```

**Scaling note**: not every project needs every doc. Empirical sizing matrix from real projects:

| Project shape | CLAUDE.md | docs/ depth | Gameplans? |
|---|---|---|---|
| Pet / friend project (e.g., a single-user web app) | ~50–80 lines | `plans/` + design pair only | Optional, single feature plan often suffices |
| Spec / shared-schema repo | ~20 lines | None — purpose + commands + rules in CLAUDE.md | No — this is a sibling repo |
| Per-language SDK in a multi-repo product | ~50 lines | Maybe TESTING; reference parent project's docs | No — uses parent's gameplan |
| Multi-asset generative project (e.g., AI video pipeline) | ~100 lines | Asset registry + manifest schemas | Single gameplan or none |
| Production SaaS product | ~200+ lines | Full named-doc set + HARDENING + INCIDENTS | Multiple gameplans, each multi-phase |

The full structure is for production-grade products. The minimum is just `CLAUDE.md` (more "rules and conventions" than "system architecture"). Use judgment. **Project-specific data structures (asset registries, source-material catalogs, fixture conventions) belong in the project's CLAUDE.md**, not in this procedure.

### Multi-Repo Projects

When a project spans multiple repos (e.g., a backend + a spec repo + N language SDKs):

- Each repo has its own `CLAUDE.md` with the standard sections.
- Each repo's `CLAUDE.md` includes a `## Related` section listing sibling repos with paths and one-line purposes.
- **The master gameplan lives in the canonical "main" repo** (typically the backend or product). Sibling repos' `CLAUDE.md` reference it: `Master plan: <main-repo>/docs/plans/YYYY-MM-DD-feature-plan.md`.
- Per-language code standards live in each repo's `CLAUDE.md` Code Standards section (Go uses gofmt + pointer receivers; Python uses snake_case + httpx; Ruby uses frozen_string_literal; etc.). Do not try to unify these.
- **Cross-repo sync**: when a change in the main repo (e.g., API surface change) requires SDK updates, the gameplan's phase explicitly lists each sibling repo as a deliverable. The phase's exit criteria includes "all SDKs updated and tests passing."
- **Conformance contract**: a spec repo (JSON Schema, OpenAPI, fixtures) is the truth source between main + SDKs. Each SDK's CI fetches the latest spec and validates against it. Drift between main and a SDK is a failure of the conformance contract, surfaced as a CI break.

---

## Document Specifications

### `CLAUDE.md` (project root)

Auto-loaded by Claude Code at session start. The single most important doc.

**Required sections** (omit any that don't apply):

```markdown
# <Project Name> — <One-Sentence Tagline>

## Project Overview
<1-2 paragraphs: what this is, what it does, what makes it interesting>

## Architecture
<Stack, environments, IaC, key technologies. Bullet list.>

## Key Files
<Table of file path → purpose. Update continuously.>

## Commands
<bash commands for testing, deploying, smoke-testing, validating IaC>

## CRITICAL Rules
<Sub-headings per category. These are the rules a session MUST honor.>

## Documentation
<List of docs in /docs/ that must stay updated with every change>

## Code Standards
<Module system, commit style, test runner, dependency policy>

## Branch Workflow
<main/staging/dev branch policy, PR requirements, merge rules>

## Destructive Actions
<Explicit list of operations that require user confirmation each time,
even if previously authorized>

## Environment
<OS, language version, shell, any quirks>
```

**CRITICAL Rules** in `CLAUDE.md` are non-negotiable. Sessions MUST read this section every time. Examples (project-dependent):
- "After ANY change to scoring logic, deploy data-deltas Lambda BEFORE the dashboard Lambda."
- "Never hardcode secrets — Lambda env vars only, injected by `deploy.sh`."
- "Always include `--profile <name>` for AWS commands; verify with `aws sts get-caller-identity`."
- "Run `npm test` before committing — all N tests must pass."

**Destructive Actions** list: explicit operations requiring user confirmation. Common entries: `git reset --hard`, `git push --force`, `aws lambda delete-function`, `./deploy/teardown.sh`, deleting branches, dropping databases, rm -rf.

### Named Living Docs (`docs/`)

Each named doc has a single canonical purpose. They are updated continuously as work progresses. The `CLAUDE.md` lists which docs must be touched per change category.

| Doc | Purpose |
|---|---|
| `VISION.md` | What and why. Differentiation. Scope boundaries. |
| `REQUIREMENTS.md` | Scope, tier model, constraints, success criteria. |
| `ARCHITECTURE.md` | Subsystems, capabilities, components. Frontmatter declares the project DAG. |
| `ENGINEERING-PRINCIPLES.md` | N (typically 5–10) principles all design decisions follow. |
| `DEPLOYMENT.md` | Infra structure, environments, accounts, IAM, deploy commands. |
| `DATASOURCES.md` | External data + APIs the project depends on. Risk profiles. |
| `SCHEMA.md` | Data-tier schemas (DB tables, JSON shapes, file formats). |
| `SECURITY.md` | Auth model, threat model, secrets policy, INVARIANTS related to data. |
| `TESTING.md` | Test discipline, runner, baseline counts, coverage policy. |
| `HARDENING.md` | **Append-only** risk tracker. Never delete entries. Audit findings, SPOFs. |
| `INCIDENTS.md` | Outage log, break-glass procedures, rollback playbooks. |
| `DECISIONS.md` | ADRs at project-wide scope (`D-NNN`). Append-only. |
| `INVARIANTS.md` | Rules that must hold across all work (`INVARIANT-NN`). |
| `GLOSSARY.md` | Domain + planning vocabulary. |
| `CHANGELOG.md` | Milestone-level history. Updated at gameplan close + significant releases. |

`HARDENING.md` is special: append-only, never delete entries, even after the risk is mitigated (mark as resolved with a date instead). This creates a permanent audit trail of every risk the project has surfaced.

### `GAMEPLAN.md` (per gameplan)

The fixed master plan. Created by the planning session, referenced by every phase session, **never substantially rewritten** during execution. Corrections go to `PHASE-STATUS.md`, not here.

**Required sections**:

```markdown
# <Gameplan Name> Gameplan

> Created: YYYY-MM-DD
> Author: <session info>
> Status: <Planning | Executing | Complete>

## Project Overview
<1–2 paragraphs: what this gameplan accomplishes>

## Subsystems Touched
<List of subsystems this gameplan affects, with frontmatter-style refs>

## Decisions

### D1: <Title>
**Context**: <why this decision was needed>
**Decision**: <what was decided>
**Consequences**: <what falls out>
**Alternatives considered**: <briefly>

### D2: ...

(D-numbers within a gameplan are independent of project-wide D-NNN ADRs.
Project-wide decisions go in docs/DECISIONS.md.)

## Open Items

### O1: <Title>
**Blocking**: <which phases this affects>
**Resolution path**: <how this gets answered>

### O2: ...

## Phase Breakdown

### Phase 0: <Name>
**Goal**: <one sentence>
**Estimate**: <1–3 days>
**Depends on**: <prior phases or external prerequisites>
**Subsystems touched**: <refs>

| Task | Description | Effort | Notes |
|------|-------------|--------|-------|
| 0.1 | ... | 2h | ... |
| 0.2 | ... | 4–6h | ... |

**Exit criteria**:
- [ ] <verifiable assertion>
- [ ] <verifiable assertion>

### Phase 1: ...

## Architecture Overview
<Current state + target state. Block diagram if useful.>

## Economics / Cost Model
<If applicable. Per-line-item, never lump-sum.>

## Source-of-Truth Captures
<Real values from real systems captured at gameplan start: account IDs,
ARNs, API endpoints, env vars, baseline test counts. Authority over
anything in the gameplan body.>
```

**Anti-pattern prevention captured here**: from the post-mortem, "Always capture source-of-truth values from real systems at gameplan start." Add a `Source-of-Truth Captures` section listing actual `aws lambda get-function-configuration` output, current test count, etc. The gameplan body should never contradict these.

### `CHAT-HANDOFF-INDEX.md` (per gameplan)

The central coordination point. Every session reads this first.

**Required sections**:

```markdown
# Chat Handoff Index — <Gameplan Name>

> Last updated: YYYY-MM-DD
> Status: <Phase N of M in progress | Complete>

## How This Works

<Brief explanation of the handoff system + ordered reading list for new sessions>

## Pre-Flight Verification (Mandatory before any code)

CHECK 1 — Correct branch base
CHECK 2 — Clean working tree
CHECK 3 — Tests pass on dev branch
CHECK 4 — Build / IaC validate passes
CHECK 5 — Dependency spot-check (verify prior phase files actually on disk)
CHECK 6 — Branch creation from dev branch HEAD
CHECK 7 — Cascade hygiene (no pending cascade reports unaddressed) [NEW]

If any check fails: STOP. Report to user. Do not proceed.

## Ending Protocol

1. Write next phase's handoff (cumulative — see "Self-Contained Handoffs")
2. Update PHASE-STATUS.md (status + outputs + corrections)
3. Run cascade for any tracked-graph edits (decisions, status transitions, entity definitions)
4. Update CLAUDE.md if any critical-rule context changed
5. Run exit verification (full test suite + build/validate) — in a **clean environment** for release-bearing work, not just your working install (a stale editable install can hide a real defect)
6. Report final test count and any new corrections

## Phase Status Table

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | <Name> | ✅ COMPLETE | YYYY-MM-DD | YYYY-MM-DD | handoffs/PHASE-0-HANDOFF.md |
| 1 | <Name> | 🟡 IN PROGRESS | YYYY-MM-DD | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | <Name> | ⬜ NOT STARTED | — | — | — |
| 3 | <Name> | ⚠️ BLOCKED | — | — | <reason> |

## Per-Phase Completion Summaries
<Added by coordinator after each merge. 1–2 paragraphs per phase
covering what landed, key corrections, and follow-ups.>

## User Working Style
See ~/.claude/CLAUDE.md (global) — symlinked, not copied.
Project-specific style overrides go in <project>/CLAUDE.md.

## Accumulated Lessons
<Numbered sequentially across the entire gameplan. Pruned of items
no longer relevant. Categorized.>

### Category: CI/CD
1. <lesson>
2. <lesson>

### Category: Infrastructure
3. <lesson>
4. <lesson>

(See "Self-Contained Handoffs" for why this lives here AND in every
phase handoff.)
```

### `PHASE-STATUS.md` (per gameplan)

The **living tracker** of phase status, outputs, and corrections. Distinct from `CHAT-HANDOFF-INDEX.md` (which is the protocol) and `GAMEPLAN.md` (which is the fixed plan).

**Required sections**:

```markdown
# <Gameplan Name> — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: YYYY-MM-DD

## Phase Status

(Same table as CHAT-HANDOFF-INDEX, kept in sync. The two docs may
merge for small gameplans; for serious projects keep them split so
the protocol doc stays compact.)

## Outputs Registry

Concrete values produced by completed phases that subsequent phases need.
Examples: AWS account IDs, ARNs, IAM role names, branch protection
status, deployed Lambda names, Cognito pool IDs, captured env vars.

### Phase 0 Outputs
```
<KEY>: <value>
<KEY>: <value>
```

### Phase 1 Outputs
```
...
```

## Corrections Log

Every divergence from the gameplan, captured in real-time.

### C1 — <Phase, brief title>
**Phase**: <number>
**What gameplan said**: <text>
**What was actually correct**: <text>
**Why**: <root cause>
**Lesson**: <generalizable takeaway, propagated to accumulated lessons>

### C2 — ...

## Captured AWS / External Values

Real values from real systems. Don't invent these — capture them.

```
ACM cert ARN: arn:aws:acm:...
Route 53 zone IDs:
  example.com:  Z...
  example.org:  Z...
Lambda env vars (prior phase deployment):
  PROVIDERS: ...
  REGION: ...
```
```

The **Outputs Registry** is the single most-reused artifact across phases. Phase 4 needing the IAM role ARN from Phase 0B reads it from here. Without this registry, sessions either hallucinate values or interrupt the user.

### Phase Handoff (`handoffs/PHASE-N-HANDOFF.md`)

Self-contained. Cumulative. The new session reads this and ONLY this (plus what it points at).

**Required sections**:

```markdown
# Phase N Handoff — <Name>

> For: Next Claude Code chat session
> Phase: N of M
> Branch: <prefix>/phase-N-<name> off <dev-branch>
> Depends on: Phase N-1 (must be merged first)

---

## Pre-Flight Verification (MANDATORY)

<Phase-specific concrete commands for the 7 checks. Include expected
test counts, exact file paths, exact branch names.>

## What This Phase Does

<1–2 paragraphs + sub-phase breakdown if applicable.>

## Current State of the Codebase (Post Phase N-1)

### Architecture
<Diagram or description of all layers built so far.>

### What Exists
<Bullet list of everything implemented/deployed up to this point.>

### What Does NOT Exist Yet
<Bullet list — sets scope boundaries so the session doesn't over-build.>

### Key Files You Must Read
<File paths with purpose descriptions. The session's reading list
before it touches code.>

## Tasks
<Task tables, grouped by sub-phase if applicable. Same shape as
gameplan task tables.>

## Exit Criteria
<Checkbox list — phase is NOT done until all are checked.>

## Decisions Already Made (Don't Re-Litigate)
<Relevant subset of D-numbered decisions from gameplan + project D-NNN.>

## Key Constraints
<Hard rules the session must follow. Critical-rule references from CLAUDE.md.>

## Accumulated Lessons (Cumulative — All Prior Phases)

<Numbered list. Pruned of obsolete items. Categorized. ALL relevant
lessons from ALL prior phases — not just the new ones.>

### Category: CI/CD
1. <lesson>
2. <lesson>

### Category: Testing
3. <lesson>

### Category: Infrastructure
4. <lesson>

## What Comes After
<1–2 sentences about phase N+1.>

## Docs to Update
<List of /docs/ files to update before closing this phase.>

## Status Transitions to Apply on Phase Completion
<Which entities (subsystems, features) change status because this
phase completes. e.g.: "subsys.auth: planned → active",
"feat.character-import: planned → ready". Cascade runs after these.>
```

**Self-Contained Handoffs (Critical Rule)**: each handoff doc must be readable in isolation. The accumulated lessons section contains ALL relevant lessons from ALL prior phases — not just new ones. Don't assume the next session will read 7 prior handoffs. Lesson #3 from Phase 1 still appears in the Phase 8 handoff if it's still relevant.

### `POST-MORTEM.md` (per gameplan)

Written by the coordinator after gameplan completion or when remaining phases are explicitly deferred. **This is where the procedure itself improves.**

**Required sections**:

```markdown
# <Gameplan Name> — Post-Mortem

> Author: <session info>
> Date: YYYY-MM-DD
> Scope: Full retrospective on phases <X-Y>, executed YYYY-MM-DD to YYYY-MM-DD.

## Executive Summary
<1–2 paragraphs: what was delivered, what was the friction, overall verdict.>

## What the Gameplan Got Right
### 1. <Pattern that worked>
<Why it worked, evidence>

## What the Gameplan Got Wrong
### 1. <Failure>
**Cost**: <hours debugging / corrections required>
**Root cause**: <honest analysis>
**Lesson**: <generalizable takeaway — feeds the procedure improvement queue>

## Procedure Improvements
<Specific changes to GAMEPLAN-PROCEDURE.md that this gameplan
revealed are needed. Each becomes a candidate edit to the procedure.>

## Open Threads
<Loose ends, deferred phases, follow-up work for future gameplans.>
```

**Anti-pattern prevention captured here**: from real post-mortems, common categories of "wrong" are stale plans (gameplan written N days before execution), version drift (Node 20 → 24 example), unverified third-party features (GitHub Team plan limitations), missing prerequisite chain (`npm ci` needs lockfile), source-of-truth not captured, line-item budgets missing.

### Feature Plan + Design Pair (`docs/plans/`)

Sub-gameplan scale: a single feature, typically 1–2 sessions of work, doesn't justify a full gameplan structure.

**Two paired files**:
- `YYYY-MM-DD-feature-name-design.md` — architectural reasoning
- `YYYY-MM-DD-feature-name-plan.md` — TDD task list (uses `superpowers:executing-plans` skill)

**Design doc structure**:
- Goal, scope, non-goals
- Architecture decision and alternatives considered
- Data shapes, API surface, edge cases
- Open questions

**Plan doc structure**:
- Goal, architecture (1–2 sentences), tech stack
- Conventions (test command, commit style)
- Phases (sometimes called "phases" even at this small scale, distinct from gameplan phases)
- Per-task: write failing test → run to verify failure → minimal implementation → run to verify pass → commit

These are the right artifact for "build this feature" requests where a full gameplan is overkill but flying-by-the-seat-of-pants is risky.

---

## Frontmatter Convention

Every tracked-entity doc in `docs/features/`, `docs/subsystems/`, `docs/decisions/` (if split per-file), and any other tracked-graph doc has frontmatter at the top. Required fields by type:

### `type: subsystem`
```yaml
---
id: subsys.<kebab-name>
type: subsystem
version: <semver>
status: <planned|active|completed|deferred|superseded>
depends_on:
  - <id>@<semver-constraint>
external_deps:
  - <ext.id>
implements_capabilities:
  - <cap.id>
documented_in: docs/subsystems/<file>.md
last_verified: YYYY-MM-DD
---
```

### `type: feature`
```yaml
---
id: feat.<kebab-name>
type: feature
version: <semver>
status: <...>
tier: <free|paid|internal>
depends_on:
  - <id>@<semver-constraint>
introduced_by: <D-NNN or gameplan id>
documented_in: docs/features/<file>.md
last_verified: YYYY-MM-DD
---
```

### `type: external-service`
```yaml
---
id: ext.<kebab-name>
type: external-service
provider: <vendor>
purpose: <one line>
risk: <low|medium|high>
license: <if applicable>
documented_in: docs/DATASOURCES.md#<anchor>
last_verified: YYYY-MM-DD
---
```

### `type: decision` (when DECISIONS.md is split)
```yaml
---
id: D-NNN
type: decision
status: <active|superseded>
date: YYYY-MM-DD
supersedes: <D-NNN or null>
superseded_by: <D-NNN or null>
---
```

### `type: invariant` (when INVARIANTS.md is split)
```yaml
---
id: INVARIANT-NN
type: invariant
status: <active|relaxed|removed>
introduced_by: <D-NNN>
last_verified: YYYY-MM-DD
---
```

**Discipline**: when you edit a doc's frontmatter (especially `version`, `depends_on`, or `status`), run cascade. See below.

---

## Cascade Discipline

Cascade is **post-hoc, not predictive**: after work is done, walk the dep graph and update what's affected. The DAGs are living truth, updated as we fix things. Cascade is not "what will break if I edit this?" — it's "what depends on this and might need an update now that I've finished?"

### When Cascade Runs (Mandatory)

1. **At phase completion** — automatically as part of the ending protocol. The phase's handoff lists which entities had their status changed; cascade walks the graph for each.
2. **At decision change** — when any `D-NNN` is superseded.
3. **At MAJOR-version bump** of any entity — minor/patch bumps are non-breaking by definition; MAJOR bumps may break dependents.
4. **At gameplan completion** — full project-wide cascade as the closing ritual.
5. **Manual trigger** — user asks, or coordinator chooses to run for safety.

### What Cascade Does

For each changed entity:
1. Walk the dep graph forward (find dependents).
2. For each dependent, **check** whether the change affects it. Use judgment.
3. If affected: update the dependent (edit its docs, plan, code). If verification shows nothing's affected, no edit.
4. Document everything in a cascade report.

### Cascade Report Format

```markdown
# Cascade Report: <id> <transition>

> Generated: YYYY-MM-DDTHH:MM:SSZ
> Phase: <if part of phase ending protocol, the phase ID>

## Trigger
<What changed: status transition, version bump, decision supersession>

## Affected entities

### Direct dependents
- **<id>** (status: ...) — checked: <action taken or "no change needed">

### Transitive dependents
- **<id>** — flagged for review by <upstream id>; checked: <result>

## Updates applied
<Concrete edits made to which files. May reference commits.>

## Updates deferred
<Anything flagged but not yet acted on, with reason and follow-up step.>
```

Saved to: `docs/gameplans/<gameplan>/_cascade-reports/YYYY-MM-DD-<trigger>.md`

### Manual Cascade (When Tooling Doesn't Exist Yet)

Until `bin/cascade` exists:
1. `grep -rE 'depends_on:.*<id>' docs/` to find dependents.
2. Open each, decide if affected, fix or document "no change needed."
3. Write the cascade report by hand.
4. Commit alongside the original change.

This is acceptable indefinitely if the team is small and the cascade frequency is low (~1 per phase + decision changes ≈ 10–25 per gameplan). When it becomes burdensome, build the script.

---

## Pre-Flight Verification (Mandatory Before Code)

Every phase session runs these checks before writing code. If any fail, STOP and report.

```
CHECK 1 — Correct branch base:
  Verify the prior phase's merge is on the dev branch.
  Branching from a stale base = merge conflicts.

CHECK 2 — Clean working tree:
  No unstaged changes, no stale untracked files.
  Leftover files from a prior session = merge conflict risk.

CHECK 3 — Tests pass on dev branch:
  Run the full test suite. ALL must pass before branching.
  Baseline test count must match what's in CHAT-HANDOFF-INDEX.

CHECK 4 — Build / IaC validate passes:
  Run linter, type checker, IaC validator.
  Must pass before any changes.

CHECK 5 — Dependency spot-check:
  Verify key files from prior phase actually exist on the branch.
  Don't trust the handoff alone — confirm on disk.
  This catches "session claimed it committed; it didn't."

CHECK 6 — Branch creation:
  Create new branch from dev branch HEAD.
  Never from main/master, never from a stale local branch.
  Prefix per CLAUDE.md branch convention.

CHECK 7 — Cascade hygiene:
  No pending cascade reports unaddressed in
  docs/gameplans/<gameplan>/_cascade-reports/.
  All reports referenced by recent decisions/transitions must
  show their downstream effects committed.
```

CHECK 7 is new vs. attago's procedure. It prevents starting new work on top of an unresolved cascade.

---

## Anti-Patterns and Preventions

Documented from real post-mortems. Each has a specific prevention.

### 1. Branching Before Prior Phase is Merged
**Symptom**: Merge conflicts when the phase tries to merge back.
**Prevention**: Pre-flight CHECK 1 verifies the prior phase's merge is on dev. Never skip.

### 2. Incomplete Lesson Propagation
**Symptom**: Phase N+3 repeats a mistake Phase N already solved because the lesson wasn't carried forward.
**Prevention**: Self-contained handoffs. Every handoff includes ALL relevant lessons, not just new ones.

### 3. Session Claims vs Reality
**Symptom**: Session says "all tests pass" but code was never committed, or test count doesn't match.
**Prevention**: Exit verification requires running the actual test command and reporting output, not claiming.

### 4. Convention Drift
**Symptom**: Each session uses slightly different conventions (branch prefix, commit format, code patterns).
**Prevention**: Conventions in `CLAUDE.md` CRITICAL Rules + decisions table. Include in every handoff's Key Constraints.

### 5. Shared Code Duplication
**Symptom**: Same utility module copied into multiple locations. Changes don't propagate.
**Prevention**: Decide code-sharing strategy at planning (symlinks, shared layer, build step). Don't discover the problem mid-execution.

### 6. Context Overflow Mid-Phase
**Symptom**: Session hits "prompt too long" before finishing or writing the next handoff.
**Prevention**: Keep phases small (1–3 days). Coordinator can rescue by committing code and writing the handoff externally.

### 7. Stale References in Docs
**Symptom**: Handoff says "tests: 200" but baseline is 350 because several phases passed.
**Prevention**: Coordinator reviews every handoff before generating next prompt. Fix stale numbers, paths, status.

### 8. Plan Stale Before Execution Starts
**Symptom**: Gameplan written week 1, execution starts week 2; tech versions, third-party features, prices have moved.
**Prevention**: Source-of-Truth Captures section in `GAMEPLAN.md` taken at execution start, not planning time. For version-specific items (Node, framework versions), use placeholders or flag with `VERIFY BEFORE EXECUTING`.

### 9. Source-of-Truth Not Captured Before Writing IaC
**Symptom**: IaC encoded "from memory" diverges from real production config (PROVIDERS string example).
**Prevention**: Phase 0 of any gameplan that wraps existing systems must capture live configuration first. `aws lambda get-function-configuration`, `gh api`, etc. Captured values go in `PHASE-STATUS.md` Outputs Registry, then referenced from the gameplan.

### 10. Lump-Sum Budgets
**Symptom**: "AWS: ~$20/mo" turns out to be $53 because Route 53 zones, CloudFront security bundle, etc. weren't broken out.
**Prevention**: Per-line-item budgets, each with a source URL. No lump-sum estimates.

### 11. Unverified Third-Party Plan Features
**Symptom**: "Required reviewers on production environment" specified, then discovered GitHub Team plan doesn't support it (3 phases hit the wall before the gap was named).
**Prevention**: For any third-party service feature mentioned in a gameplan, link to the pricing/feature comparison page in the doc. Verify availability at the actual plan level you're on.

### 12. Prerequisite Chains Not Traced
**Symptom**: `npm ci` specified, blocks Phase 4 because lockfile + .gitignore exception not committed.
**Prevention**: When specifying a command in a plan, trace its prerequisites. `npm ci` needs lockfile in repo. `cdk deploy` needs bootstrapped account. Etc.

### 13. Reinventing Procedure Instead of Adopting It (NEW from poe2.design session)
**Symptom**: A new project's planning is structured ad hoc despite the team having a battle-tested procedure (this very document).
**Prevention**: Step 1 of any new project: copy `GAMEPLAN-PROCEDURE.md` into `docs/gameplans/`. Read it. Then plan.

### 14. Cascade Tooling Debt as Drift (NEW from poe2.design session)
**Symptom**: Cascade discipline is universal; tooling to automate it never gets built; manual cascade rots silently; graph diverges from reality.
**Prevention**: Cascade is post-hoc and runs at phase boundaries (low frequency). Manual cascade reports are tractable until ~25/project. If frequency grows, prioritize building `bin/cascade` immediately.

### 15. Frontmatter Inconsistency (NEW)
**Symptom**: AI sessions write inconsistent frontmatter (missing fields, wrong types). Graph queries break.
**Prevention**: Templates per type live in `docs/_templates/frontmatter-<type>.md`. New entity docs copy the template. A future `bin/lint-frontmatter` script enforces the schema.

---

## Procedures

### Procedure: Bootstrap a New Project ("Do This")

The replication recipe. From a fresh repo, run these in order:

1. **Create `CLAUDE.md`** at project root with the required sections (Project Overview, Architecture, Key Files, Commands, CRITICAL Rules, Documentation, Code Standards, Branch Workflow, Destructive Actions, Environment).
2. **Create `docs/`** with the named living docs (start with VISION, REQUIREMENTS, ARCHITECTURE; add others as work demands).
3. **Copy `GAMEPLAN-PROCEDURE.md`** (this file) to `docs/gameplans/GAMEPLAN-PROCEDURE.md`.
4. **Create the first gameplan directory**: `docs/gameplans/<YYYY-MM-DD-name>/`.
5. **Write `GAMEPLAN.md`** following the spec above. Capture Source-of-Truth values from any pre-existing systems.
6. **Write `CHAT-HANDOFF-INDEX.md`** and `PHASE-STATUS.md` skeletons.
7. **Write `handoffs/PHASE-0-HANDOFF.md`** for the first phase.
8. **Add `.gitignore`** entries for `docs/gameplans/` if it contains AWS account IDs or ARNs (move sensitive content out of git, or split sensitive parts to `/mnt/c/.../<project>-private/`).
9. **Commit the bootstrap**: `git add . && git commit -m "feat: bootstrap gameplan system"`.

After bootstrap, the project is ready for "do next phase" sessions.

### Procedure: Start a Gameplan

1. Identify the goal (e.g., "Launch poe2.design with E-MVP scope").
2. Create `docs/gameplans/<YYYY-MM-DD-id>/`.
3. Capture Source-of-Truth values from existing systems (Lambda configs, AWS account IDs, current branch protections, baseline test counts).
4. Write `GAMEPLAN.md` with: overview, decisions D1.., open items O1.., phase breakdown with task tables, exit criteria, dependencies, architecture overview, economics (per-line-item).
5. Write `CHAT-HANDOFF-INDEX.md` with the protocol + initial phase status table.
6. Write `PHASE-STATUS.md` with the same status table + empty Outputs Registry.
7. Write `handoffs/PHASE-0-HANDOFF.md` for the first phase.
8. Run cascade for any newly defined subsystems/features in `docs/`.
9. Commit.

### Procedure: Execute a Phase

The phase session does this:

1. Read in order:
   - `CLAUDE.md` (auto-loaded; verify CRITICAL Rules section)
   - `docs/gameplans/<id>/CHAT-HANDOFF-INDEX.md`
   - All prior phase handoffs (sequentially)
   - `docs/gameplans/<id>/handoffs/PHASE-N-HANDOFF.md` (the current phase)
   - `docs/gameplans/<id>/GAMEPLAN.md`
   - Any docs the handoff explicitly lists in Key Files You Must Read
2. Run Pre-Flight Verification (7 checks). If any fails: STOP, report.
3. Execute the phase tasks.
4. Run exit verification: full test suite, build/validate. Report final counts.

### Procedure: Complete a Phase

The same phase session does this:

1. Update `PHASE-STATUS.md`: mark phase complete, fill in Outputs Registry, document any corrections (`C1`, `C2`, ...).
2. Update accumulated lessons in `CHAT-HANDOFF-INDEX.md` with anything new from this phase.
3. Apply status transitions on touched entities (subsys / feature `planned → active → completed`). Cascade runs.
4. Write `handoffs/PHASE-N+1-HANDOFF.md` with cumulative lessons. Self-contained.
5. Update `CLAUDE.md` if any critical-rule context changed.
6. Update affected named docs in `/docs/` (per the phase's "Docs to Update" section).
7. Commit. Conventional commits.
8. Push (or signal user to push, per project's auth model).

### Procedure: Coordinate Across Phases

Coordinator session does between phases:

1. Read the just-completed phase's updated handoff + PHASE-STATUS update + cascade report.
2. Verify exit criteria are checked.
3. Confirm test count matches actual output.
4. Check for stale references (test counts, file paths, status, version numbers).
5. Fix any cross-phase inconsistencies (e.g., correction in Phase 3 that propagates to Phase 5's expectations).
6. Generate the prompt for the next phase session (template in CHAT-HANDOFF-INDEX).
7. If any decision needs to be revised mid-gameplan: assign a new D-number, propagate to all affected docs, run cascade.

### Procedure: Close a Gameplan

1. All phases complete or explicitly deferred.
2. Update `CHAT-HANDOFF-INDEX.md` with final status.
3. Update `PHASE-STATUS.md` with final outputs and corrections.
4. Run gameplan-wide cascade (full graph traversal).
5. Update project-level docs (CHANGELOG, ARCHITECTURE, REQUIREMENTS) with final state.
6. Run the work/release **self-audit** (`cz_audit`) — resolve its mechanical findings (version single-sourcing, uncommitted tree, unresolved cascades/open items) and affirm its judgment checklist (verify in a clean environment; re-audit every consumer of a changed entity; claim only what you verified). Advisory (INVARIANT-05); its findings feed the post-mortem.
7. Write `POST-MORTEM.md` covering: what worked, what didn't, procedure improvements (which feed back into the next version of this very document).
8. Move the gameplan directory to "completed" status (the dir stays on disk for reference; nothing is deleted).
9. Commit the closure.

### Procedure: Amend a Gameplan

When the gameplan needs a structural change after Phase 0 has started:

1. **Decide: amend or new mini-gameplan?** Apply the rule of thumb in the Amendment concept section. If amend, continue. If mini-gameplan, follow "Procedure: Start a Gameplan" instead.
2. **Choose the next available `A-NNN`** in this gameplan's amendment sequence. (Project-wide `D-NNN` ADRs and gameplan-internal `D1, D2, ...` decisions have their own sequences; amendments are independent.)
3. **Identify affected phases** by walking the gameplan DAG — any phase whose handoff references the section of `GAMEPLAN.md` being amended is affected.
4. **Write the amendment entry** in the `## Amendments` section of `GAMEPLAN.md` (format above).
5. **Update the gameplan body** to reflect the amendment. Both the body change and the amendment entry land in the same commit.
6. **Run cascade**: `bin/cascade A-NNN` walks the gameplan DAG and outputs a cascade report listing affected phases.
7. **For each affected phase**:
   - **Unstarted (status: `ready` or `pending`)**: the cascade report notes the amendment; the next handoff written for that phase incorporates it.
   - **In progress (status: `in_progress`)**: amendment logged in `PHASE-STATUS.md` Corrections Log with cross-reference; the executing session reconciles mid-flight (either absorbs into current execution or defers to a follow-up).
   - **Completed (status: `completed`)**: cascade report evaluates whether the completed work conflicts with the amendment. If yes, add a `PHASE-NN-revisit` phase as a follow-up amendment (`A-MMM` referencing `A-NNN` as parent).
8. **Save the cascade report** to `<gameplan>/_cascade-reports/YYYY-MM-DD-A-NNN.md`.
9. **Commit**: cascade report + GAMEPLAN.md body change + amendment entry + any PHASE-STATUS log + any handoff updates, in a single conventional commit (`docs: amend <gameplan> A-NNN — <title>`).

### Procedure: Cascade Changes

When something changes (status, version, decision), do this:

1. Identify the entity + transition.
2. Walk the project DAG forward to find direct dependents.
3. For each dependent: check whether change affects it. Use judgment. **Don't change things that aren't broken.**
4. If affected: edit + verify + document.
5. Walk transitive dependents only when direct dependents change in a way that could propagate.
6. Write the cascade report to `docs/gameplans/<active-gameplan>/_cascade-reports/`.
7. Commit cascade report alongside the triggering change.

---

## Quick Reference

### File Layout (canonical)
```
<project>/
├── CLAUDE.md
├── README.md
├── CHANGELOG.md
└── docs/
    ├── VISION.md, REQUIREMENTS.md, ARCHITECTURE.md, ENGINEERING-PRINCIPLES.md,
    │   DEPLOYMENT.md, DATASOURCES.md, SCHEMA.md, SECURITY.md, TESTING.md,
    │   HARDENING.md, INCIDENTS.md, DECISIONS.md, INVARIANTS.md, GLOSSARY.md
    ├── plans/
    │   ├── YYYY-MM-DD-feature-design.md
    │   └── YYYY-MM-DD-feature-plan.md
    ├── features/, subsystems/  (one frontmatter doc per entity, lazy)
    └── gameplans/
        ├── GAMEPLAN-PROCEDURE.md  (this file)
        └── <YYYY-MM-DD-id>/
            ├── GAMEPLAN.md
            ├── CONTEXT.md          (optional)
            ├── CHAT-HANDOFF-INDEX.md
            ├── PHASE-STATUS.md
            ├── handoffs/
            └── _cascade-reports/
```

### Numbering Conventions

- Project-wide decisions: `D-001`, `D-002`, `D-003`, ... (in `docs/DECISIONS.md`)
- Gameplan-internal decisions: `D1`, `D2`, `D3`, ... (in that gameplan's `GAMEPLAN.md`)
- Project-wide invariants: `INVARIANT-01`, `INVARIANT-02`, ... (in `docs/INVARIANTS.md`)
- Open items: `O1`, `O2`, `O3`, ... (in gameplan)
- Phases: `0`, `1`, `2`, `3`, ... (or `0A`, `0B`, `0C` for sub-phases)
- Tasks: `0.1`, `0.2`, `1.1`, `1.2`, ...
- Lessons: sequential across the entire gameplan (`1`, `2`, ... `41`, `42`, ...)
- Corrections: `C1`, `C2`, `C3`, ... (in `PHASE-STATUS.md`)
- Hardening risks: `H1`, `H2`, ... (in `HARDENING.md`, never deleted)

### Entity ID Conventions

- Subsystem: `subsys.<kebab-name>`
- Feature: `feat.<kebab-name>`
- Capability: `cap.<kebab-name>`
- External service: `ext.<kebab-name>`
- Decision (project): `D-NNN`
- Invariant (project): `INVARIANT-NN`
- Phase: `Phase N` (bare integers `0`–`N`) or `Phase 0A`, `Phase 0B` (sub-phases). Found in gameplan `GAMEPLAN.md` phase breakdown.
- Task within a phase: `N.M` (e.g., `0.1`, `1.4`). Found in the phase's task table inside `GAMEPLAN.md`.
- Legacy `STEP-NN` IDs: only in pre-D-028 historical documents (e.g., the original 2026-04-30 design brainstorm in `docs/plans/`); no longer the active convention.

### Symlinks vs Copies

- **Global preferences (`~/.claude/CLAUDE.md`)**: symlink from a central location to each project's `CLAUDE.md` only when the project doesn't override. Never copy — keeps universal preferences in one place.
- **Project `CLAUDE.md`**: per-project, in the project root. May reference global with: `See ~/.claude/CLAUDE.md for working style; project-specific overrides below.`
- **`GAMEPLAN-PROCEDURE.md` (this file)**: copy into each project. The procedure evolves with the project; symlink would create false uniformity.

### Coordinator Checklist (per phase)

- [ ] Read updated handoff doc
- [ ] Verify all exit criteria are checked
- [ ] Confirm test count matches actual output
- [ ] Check stale references (test counts, file paths, status, version numbers)
- [ ] Fix branch prefix if wrong
- [ ] Update `CHAT-HANDOFF-INDEX.md` (status + completion summary)
- [ ] Update `PHASE-STATUS.md` (outputs registry + corrections)
- [ ] Review next phase's handoff for accuracy
- [ ] Run cascade for any tracked-graph edits
- [ ] Generate next phase's prompt

### Phase Prompt Template

```
Read these docs in order before doing anything else:

1. CLAUDE.md (root)
2. docs/gameplans/<id>/CHAT-HANDOFF-INDEX.md
3. docs/gameplans/<id>/handoffs/PHASE-0-HANDOFF.md
... (all prior handoffs in sequence)
N. docs/gameplans/<id>/handoffs/PHASE-<current>-HANDOFF.md
N+1. docs/gameplans/<id>/GAMEPLAN.md

Read ALL docs in this exact order before writing any code.
Then run the Pre-Flight Verification checklist (7 checks)
from the Phase <N> handoff doc — all checks must pass and
be reported to me before you touch a single file.

You are implementing Phase <N>: <Name>.
Branch: <branch-name> off <dev-branch>.

Phase scope:
- <N>.1: <description>
- <N>.2: <description>

Key constraints (the session WILL forget constraints not in the prompt):
- <constraint 1>
- <constraint 2>

Baseline: <test-count> tests must pass + new ones added.

Exit verification: <test-command> + <validate-command>.
Report final test count.

When ending, write Phase <N+1> handoff with cumulative lessons,
update PHASE-STATUS.md, run cascade for status transitions.
```

### Recording Without MCP — `clauderize ops`

The `cz_*` tools are the primary write surface, but recording must never be
hostage to a live MCP connection (L-05). When the tools are absent or the
server can't attach, every operation — reads and writes — is reachable from a
shell:

```
clauderize ops <file.json>     # or `-` to read the batch from stdin
```

The file is a JSON array of `{"op": "<tool name>", "args": {...}}` (a single
object is accepted too). Op names and argument shapes are **exactly** the
`cz_*` tool names and schemas — one shared registry backs both surfaces, so
they cannot drift. Results come back as per-op JSON on stdout (`ok`,
`result`/`error` per entry); the exit code is 0 only when every op succeeded.
Putting args in a file (not shell arguments) is deliberate: it bypasses shell
quoting hazards entirely. Writes serialize on the same inter-process write
lock as every other writer. Do not hand-edit tracked docs as a "fallback" —
`clauderize ops` is the fallback.

---

## How This Procedure Itself Improves

Every gameplan ends with a `POST-MORTEM.md`. The post-mortem's **Procedure Improvements** section lists candidate edits to this file. Coordinator session at gameplan close reviews them and proposes a `GAMEPLAN-PROCEDURE.md` version bump.

Procedure version is semver:
- **PATCH** (1.0.0 → 1.0.1): typo fixes, clarifications, no semantic change.
- **MINOR** (1.0.0 → 1.1.0): added rules, new optional sections, new anti-patterns.
- **MAJOR** (1.0.0 → 2.0.0): structural change to the procedure (rare).

Existing projects on a prior procedure version don't auto-migrate. The procedure they were started under continues to apply unless the user explicitly runs a procedure-upgrade gameplan.

---

## Origins and Synthesis Trail

This document synthesizes patterns from every project surveyed in `~/`:

- **`attago/docs/gameplans/GAMEPLAN-PROCEDURE.md`** (Feb 2026): three-document system, self-contained handoffs, pre-flight checks, anti-patterns.
- **`attago/docs/gameplans/gameplan-2026-02-11/DEVOPS-PHASE-STATUS.md`**: Outputs Registry + Corrections Log pattern.
- **`attago/docs/gameplans/gameplan-2026-02-11/DEVOPS-POST-MORTEM.md`**: budget anti-pattern, version drift anti-pattern, source-of-truth anti-pattern, plan-stale anti-pattern.
- **`attago/CLAUDE.md`**: large-project CLAUDE.md template; CRITICAL Rules sub-headings (scoring, providers, shared modules, secrets, sensitive files); `HARDENING.md` as append-only persistent risk tracker; `ENGINEERING-PRINCIPLES.md` as N guiding principles.
- **`attago-spec/CLAUDE.md`**: minimum-size CLAUDE.md (~20 lines); spec-repo-as-conformance-contract pattern.
- **`attago-js-sdk/CLAUDE.md`**, **`attago-go-sdk/CLAUDE.md`**, **`attago-py-sdk/CLAUDE.md`**, **`attago-rb-sdk/CLAUDE.md`**: per-language SDK pattern; `## Related` cross-repo references; per-language code standards; sibling-repo coordination via parent's `docs/plans/`.
- **`lsatprep/CLAUDE.md`**: scale-down CLAUDE.md for solo / friend-project; explicit Destructive Actions list; explicit "skip product-grade polish" framing for non-product projects.
- **`batman-neverland/CLAUDE.md`**: asset-registry pattern for generative projects; read-only `source-material/` directory; project-specific data-structure documentation in CLAUDE.md.
- **`~/.claude/global-CLAUDE.md`** (global): working style, security baseline, communication preferences. Symlinked into projects when uncustomized, never copied.
- **`poe2design/` design session (Apr–May 2026)**: two-DAG separation (project DAG + gameplan DAG), frontmatter for graph extraction, semver for entities, cascade-on-status-transition, AI-memory-first design philosophy as explicit framing, `bin/cascade` and `bin/regen-graph` as future tooling targets, scale-aware CLAUDE.md sizing matrix.

If you find this procedure missing something a real gameplan would have benefited from, write it up in your gameplan's POST-MORTEM under Procedure Improvements. The next version of this document is built from those.
