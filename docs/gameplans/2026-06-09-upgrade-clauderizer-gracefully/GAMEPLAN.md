# Upgrade Clauderizer Gracefully Gameplan

> Created: 2026-06-09
> Status: Planning
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

Make engine upgrades boring: a Clauderizer repo crosses engine versions with
zero hand-edits and zero silent breakage. Today nothing in an installed repo
knows what engine wrote it — `create_if_absent` assets never update, the
config's `version = "1"` is write-only, and the only "upgrade" story is
re-running init and hoping (H-04 taught us how that ends). The through-line:
**every asset knows its generation, one idempotent verb migrates forward,
skew in either direction fails loudly with a named fix, and the whole path
is proven on real prior-version trees before it ships.**

Five phases: stamps + skew-aware doctor (D1), the `clauderize upgrade` verb
with config migrations (D2), asset/wiring regeneration under it (D2/D4),
backward-refusal guards + an archive of real old trees (D3/D4), and a release
gated on this repo upgrading itself with both guards seen firing (D5).
Executes after the agent-autonomy gameplan closes — its write lock, ops
registry, and host-of-record composition are direct inputs here.

## Subsystems Touched

- `subsys.scaffold` — asset registry + generation stamps in init; the
  `clauderize upgrade` verb; asset/wiring regeneration
- `subsys.profiles` — config schema v2 (`[assets]` table) and the versioned
  migration chain
- `subsys.mutations` — generation guard beside the Phase-0 write lock in the
  single mutation path (backward-refusal, D3)
- `subsys.mcp-server` — `upgrade` joins the shared ops registry (tool surface
  grows by one)
- `subsys.rituals` — doctor gains skew checks (behind / ahead / match)

## Source-of-Truth Captures

Captured 2026-06-09 at planning time (all values observed live):

- **Engine 0.6.0** in source (`pyproject.toml`), editable venv, and PyPI;
  0.7.0 ships when agent-autonomy closes — this gameplan releases the next
  minor after whatever that ends up being
- **Suite 148 green** (139 baseline + 9 write-lock tests; tracked baseline
  digit refreshes to 148 at the next green preflight); 24 MCP tools; 13
  doctor checks; CLI verbs `init/status/reindex/doctor/mcp` (`ops` lands in
  agent-autonomy Phase 1)
- **`CONFIG_VERSION = "1"`** is written by `Config.to_toml` and **never read
  back for any decision**; the TOML emitter covers exactly tables of
  strings, bools, and lists of strings — the `[assets]` table must fit that
  or extend the emitter
- **Procedure version 1.1.0** (2026-05-02), with an explicit no-auto-migrate
  law (GAMEPLAN-PROCEDURE.md:1152): prior-procedure projects keep their
  procedure unless a procedure-upgrade gameplan is run deliberately
- **Three asset update policies today** (scaffold/init.py): `create_if_absent`
  (config.toml, profile.lock.toml, GAMEPLAN-PROCEDURE.md, module doc
  templates — never updated after first init), marker-block upsert
  (CLAUDE.md stanza), refresh-on-every-init (".claude/skills/, engine-owned",
  init step 9). Plus `.mcp.json` registration, settings-hook registration,
  and a `.gitignore` line. **No generation stamp exists anywhere** (grep
  verified: no version/generation/stamp in init.py)
- **Wiring on this repo is hand-maintained** (H-04): `.mcp.json` +
  SessionStart hook as wsl.exe-shimmed console scripts; regeneration
  machinery (host-of-record + spawn-tests) is agent-autonomy Phase 2, in
  flight at planning time
- **Write lock shipped** (agent-autonomy Phase 0, commit 6f8afc1): all 18
  public `mutations.*` serialize on `.clauderizer/write.lock`; `upgrade`'s
  writes must acquire it; the generation guard (D3) lands beside it at the
  same choke point

## Amendments

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

### D1 — Every installed asset carries a generation stamp; skew is a first-class doctor check

**Context**: Engine 0.6.0 manages three asset classes with three different update policies and no version anywhere: create_if_absent files (config.toml, profile.lock.toml, GAMEPLAN-PROCEDURE.md, module doc templates) never update after first init; the CLAUDE.md stanza upserts through its marker block; .claude/skills/ refreshes on every init ("engine-owned"). config.toml carries version="1" (CONFIG_VERSION) that nothing reads back. So an upgraded engine silently leaves stale assets, and doctor cannot see skew it has no record of (L-02: verify capability, not presence).
**Decision**: init and upgrade stamp every managed asset write with the writing engine's generation: config gains an [assets] generation field, marker-block assets carry the stamp inside their markers, and the procedure keeps its own semantic version (1.1.0 today) per its no-auto-migrate law. doctor compares the running engine against recorded generations and reports behind ("upgrade available"), ahead ("engine older than repo" — a failure), or match — never a skew-blind green.
**Consequences**: Skew becomes observable before it corrupts anything; the managed-asset inventory becomes explicit and testable instead of folklore; doctor grows beyond 13 checks; every later phase (migrations, refusal guards, self-upgrade proof) reads these stamps as its ground truth.

### D2 — One idempotent verb, clauderize upgrade, owns all migrations

**Context**: Today the only regeneration path is re-running init, which create_if_absent-skips most existing assets, historically mis-composed shimmed wiring (H-04, being fixed in agent-autonomy Phase 2), and updates nothing it skipped — so template and procedure improvements never reach existing repos. Scattering migration logic across init flags or hand instructions would repeat the pre-ops shim era: every upgrade a bespoke ritual.
**Decision**: clauderize upgrade = read the D1 stamps, run ordered versioned migration steps (config schema first, then asset regeneration through marker blocks with preserve-body semantics, then wiring re-composition reusing agent-autonomy Phase 2's host-of-record composition and spawn-tests), then restamp. --dry-run prints the full diff and writes nothing; apply-twice == apply-once (L-01); prose outside engine markers is never touched (D-008). The verb joins the ops registry, so MCP and CLI reach it identically.
**Consequences**: Upgrades stop being hand-edit rituals (the current .mcp.json is hand-maintained — exactly the state this kills); every future schema or format change must ship with its migration step or fail review; the H-04 spawn-test guard extends to upgrade-written commands for free.

### D3 — Compatibility is asymmetric: forward-migrate, backward-refuse

**Context**: An older engine reading newer-format docs corrupts silently — an engine "can read its own corruption indefinitely" (L-06), and tolerant parsers make the damage invisible until much later. Supporting two-way migration would double every format change forever. The dangerous direction is writes: a stale engine mutating a newer repo bakes its older format back in.
**Decision**: Engine N migrates assets and docs written by N-1 forward via clauderize upgrade. An engine older than the repo's recorded generation refuses tracked writes loudly at the single mutation choke point (beside the Phase-0 write lock — one guard line, every writer covered), naming both versions and the fix; reads stay best-effort so a stale engine can still report its own staleness. Downgrade is documented as git-revert of docs plus engine reinstall — never automated.
**Consequences**: The silent-corruption window closes in the only direction it opens; the failure mode is an actionable breadcrumb in the H-01 wrapper lineage; the supported skew matrix (N writes N-1: migrate; N-1 writes N: refuse) is two cases, both testable.

### D4 — Tracked markdown migrates by heal-on-blessed-touch, proven against archived real trees

**Context**: Doc formats already evolved three times (anchored ID numbering, contiguous table rebuilds, the lesson-state grammar) and the 0.6.0 healing-write pattern carried fractured trackers through without a migration script. But nothing pins that real prior-version trees stay readable: the suite tests only freshly scaffolded fixtures, so a regression against old repos would ship unseen.
**Decision**: No big-bang doc rewrites, ever: parsers stay N-1 tolerant and blessed writes normalize on touch (the proven pattern). A fixture archive of real prior-generation repo trees (a 0.5.0-era and a 0.6.0-era tree, captured from this repo's own history) joins the suite; every release must read them cleanly and upgrade them to doctor-green, asserting render-validity for external readers as well as the engine (L-06). The archive gains one tree per release.
**Consequences**: Upgrade safety becomes a regression suite instead of a hope; old gameplan history stays parseable forever; the procedure's own no-auto-migrate law (GAMEPLAN-PROCEDURE.md:1152 — prior-procedure projects keep their procedure unless a procedure-upgrade gameplan is run explicitly) is honored: upgrade surfaces "procedure 1.1.0 < shipped X" as guidance, never a silent rewrite.

### D5 — The release gate is a live self-upgrade with both skew guards seen firing

**Context**: House law from two gameplans: a guard that has never been seen to fire is an intention, not a guard (agent-autonomy D5), and releases tag only after a restart-validated cold start. An upgrade tool that has never upgraded a real repo — or whose refusal path has never refused anything — is theater.
**Decision**: Before tagging: (a) this repo itself upgrades end-to-end via clauderize upgrade with zero hand-edits and doctor green after a restart-validated cold start; (b) a scratch clone pinned to the previous release's engine demonstrably gets refused writing to the upgraded repo (D3's guard fires on record); (c) a stale-asset repo under the new engine demonstrably reports "upgrade available" (D1's check fires on record). Output captured in HARDENING as regression evidence; the demo trees feed D4's archive.
**Consequences**: Release == demonstrated graceful upgrade, not asserted; the evidence trail starts at version one of the feature; the scratch-repo + pinned-uvx demo pattern from agent-autonomy Phase 4 is reused, not reinvented.

## Open Items

- **O1** — Execution is gated on agent-autonomy closing: Phase 1 here needs
  its ops registry (P1), Phase 2 here hard-depends on its host-of-record
  composition + spawn-test machinery (P2). If those land differently than
  planned, amend this gameplan (A-NNN) before starting Phase 0.
- **O2** — Release version is decided at Phase 4: next minor after whatever
  agent-autonomy ships (0.8.0 if that line holds at 0.7.0).
- **O3** — Phase 0 task 0.1 must settle whether `.mcp.json` / settings-hook
  registrations and the `.gitignore` line are stampable assets or
  spawn-test-verified wiring only (they have no marker block to carry a
  stamp; the registry may record them as "verified, not stamped").

## Phase Breakdown

### Phase 0: Asset inventory + generation stamps

**Goal**: Every asset init manages is enumerated in a tested registry and
stamped with the engine generation that wrote it, and doctor reads the stamps
to report behind / ahead / match instead of being skew-blind — the
observability floor everything else builds on (D1).
**Depends on**: nothing (first phase; agent-autonomy must be closed).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | Managed-asset registry: one tested table of (path, update-class, stamp carrier) covering config.toml, profile.lock.toml, GAMEPLAN-PROCEDURE.md, module templates, CLAUDE.md stanza, skills/, .mcp.json + hook registrations, .gitignore line; settles O3 (stampable vs verified-only) | 1.5h |
| 0.2 | Stamp emission: `[assets] generation` in config (groundwork for schema v2); every init asset write records the writing engine's generation; marker-block assets carry it inside their markers | 1.5h |
| 0.3 | doctor skew check: behind → "upgrade available (assets X < engine Y)", ahead → failure "engine X older than repo assets Y", match → green; never a skew-blind pass (L-02) | 1.5h |
| 0.4 | Tests: stamps round-trip through the engine's own parser (L-04); registry completeness pinned by enumeration against init's actual writes; doctor matrix behind/ahead/match | 1.5h |
| 0.5 | Dogfood: stamp THIS repo via a fresh-process run; doctor reports match; record the stamped inventory as phase outputs | 0.5h |

**Exit criteria**:
- [ ] A deliberately back-stamped fixture makes doctor say "behind", a forward-stamped one fails loudly as "engine older than repo" — demonstrated, not assumed
- [ ] An enumeration test pins every init-written path to a registry entry (a new init write without a registry entry fails the suite)
- [ ] This repo is stamped and doctor-green; full suite passes and grows

### Phase 1: clauderize upgrade skeleton: config migrations + restamp

**Goal**: The verb exists and owns config-schema migration: ordered steps keyed by config version (CONFIG_VERSION "1" -> "2" as the proving change, adding the [assets] table), --dry-run prints the diff and writes nothing, apply-twice == apply-once, successful runs restamp generations (D2). Acquires the agent-autonomy Phase 0 write lock around every mutation it makes.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | Migration framework: ordered (from-version → step) chain over config; CONFIG_VERSION "2" introducing the `[assets]` table is the proving migration; unknown future version → refuse (D3 applies to config too) | 1.5h |
| 1.2 | `clauderize upgrade`: read stamps → plan steps → apply under the write lock → restamp; per-step JSON results on stdout (ops result shape); non-zero exit when any step fails | 2h |
| 1.3 | `--dry-run`: prints the full planned diff, writes nothing (tree-hash-identical, tested) | 1h |
| 1.4 | Idempotency regression: apply-twice == apply-once across the whole tree (L-01) | 1h |
| 1.5 | Register `upgrade` in the shared ops registry → MCP + CLI reach it identically (agent-autonomy P1 surface) | 0.5h |

**Exit criteria**:
- [ ] A version-"1" config (no `[assets]`) upgrades in place to v2; an immediate second run is a byte-identical no-op
- [ ] `--dry-run` leaves the tree byte-identical while printing the diff it would apply
- [ ] Full suite passes; `upgrade` callable via both CLI and the ops surface

### Phase 2: Asset + wiring regeneration under upgrade

**Goal**: upgrade regenerates stale managed assets without touching prose: CLAUDE.md stanza through its marker block, module templates and skills refreshed, wiring re-composed for the session-host-of-record and spawn-tested before writing (reuses agent-autonomy Phase 2 machinery — hard dependency), procedure handled per its no-auto-migrate law (surface guidance, never rewrite). Prose outside engine markers stays byte-identical (D2, D4).
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | Regeneration by update-class: marker-block assets re-rendered through their markers (preserve-body), engine-owned assets refreshed, stale create-if-absent assets refreshed via their registered class — prose outside markers untouched (D-008) | 2h |
| 2.2 | Wiring re-composition through host-of-record + spawn-test before any write (agent-autonomy P2 machinery); a failing probe aborts the upgrade loudly with guidance, leaving no partial wiring | 1.5h |
| 2.3 | Procedure policy: detect procedure 1.1.0 < shipped version; print adopt-guidance naming a procedure-upgrade gameplan; never rewrite (the no-auto-migrate law) | 1h |
| 2.4 | Tests: fixture with 0.6.0-era stanza + hand-maintained wiring upgrades to regenerated equivalents, diff-verified; user/agent prose byte-identical outside engine markers | 1.5h |

**Exit criteria**:
- [ ] The 0.6.0-era fixture upgrades to regenerated stanza + wiring with zero prose changes outside markers — diff shown in the test
- [ ] A composition whose spawn probe fails aborts the whole upgrade with actionable guidance and no partial writes
- [ ] Full suite passes

### Phase 3: Skew guards + prior-version tree archive

**Goal**: Backward-refusal enforced at the single mutation choke point (one generation check beside the write lock covers every writer): an engine older than the repo's recorded generation refuses tracked writes with a breadcrumb naming both versions and the fix, reads stay best-effort (D3). A fixture archive of real 0.5.0-era and 0.6.0-era trees from this repo's history joins the suite: every tree reads cleanly and upgrades to doctor-green, render-valid for external readers (D4, L-06).
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | Generation guard in the single mutation path, beside the write lock: engine older than repo assets → refuse every tracked write with a breadcrumb naming both versions and the fix; reads untouched | 1.5h |
| 3.2 | Fixture archive: capture real 0.5.0-era and 0.6.0-era trees of this repo from git history into tests/fixtures/archive/ | 1.5h |
| 3.3 | Archive suite: every archived tree parses cleanly, upgrades to doctor-green, and renders valid markdown for external readers (L-06) | 1.5h |
| 3.4 | Refusal error shape pinned (versions + fix named, retryable=false) and wording in the H-01 breadcrumb lineage | 1h |

**Exit criteria**:
- [ ] A pinned older engine refuses a tracked write against an upgraded tree — demonstrated live, output captured
- [ ] Both archived real trees read + upgrade green under the current engine
- [ ] Full suite passes; the archive is wired so every future release adds its tree

### Phase 4: Live self-upgrade + release

**Goal**: The release gate is the demonstration (D5): this repo upgrades end-to-end via clauderize upgrade with zero hand-edits and a restart-validated cold start; the D3 refusal guard and D1 staleness check are both seen firing against pinned scratch repos, output captured in HARDENING; CHANGELOG/README written; version bumped to the next minor after agent-autonomy's release; gameplan closed per Ending Protocol.
**Depends on**: 0, 1, 2, 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | Self-upgrade: this repo end-to-end via `clauderize upgrade`, zero hand-edits; restart-validated cold start; doctor green | 1.5h |
| 4.2 | Guard demos on scratch repos: D3 refusal fires under a pinned previous-release engine; D1 staleness check fires on stale assets under the new engine; both captured in HARDENING as regression evidence | 1.5h |
| 4.3 | CHANGELOG + README (upgrade verb, generation stamps, skew policy, downgrade-is-git-revert doc); version bump per O2 | 1h |
| 4.4 | Release + close out per Ending Protocol; D4 archive gains this release's tree | 1h |

**Exit criteria**:
- [ ] This repo was upgraded by the tool itself — zero hand-edits, cold-start validated, doctor green
- [ ] Both skew guards seen firing with output captured in HARDENING
- [ ] Version bumped, CHANGELOG written, gameplan closed per Ending Protocol
