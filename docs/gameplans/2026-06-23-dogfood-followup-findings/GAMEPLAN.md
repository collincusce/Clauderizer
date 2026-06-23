# dogfood-followup-findings Gameplan

> Created: 2026-06-23
> Status: Complete
> Kind: driven
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

A cleanup gameplan for the non-blocking follow-ups the 2026-06-23 stranger-readiness
dogfood surfaced (F1, F4–F13 in that gameplan's friction log), after the critical/high
H-14/H-15 fixes shipped in 1.0.3. The headline is the `clauderize ops` discoverability
cluster — the no-MCP CLI fallback that is load-bearing for cross-host and cross-model use,
yet the least-documented surface. Later phases close the generic-profile preflight gap,
the double-cascade, a few small correctness/lifecycle gaps, and the `uvx` front-door, then
**document** the rough edges that are intentional-by-design rather than churn them.

Every change is additive and must not regress the Claude Code experience (INVARIANT-07).

## Subsystems Touched

- `subsys.mutations` + `subsys.mcp-server` — the shared ops/tool REGISTRY (ops schemas F4, arg-vocab F11, entity-retire F10, serverInfo version F7).
- `feat.init-cli` — the `clauderize ops` CLI surface (F4/F8/F9/F11) and `doctor`/preflight warns (F5).
- `subsys.rituals` + `subsys.profiles` — preflight profile-awareness (F5); cascade dedupe (F6).
- `subsys.scaffold` — the `clauderizer` console-script alias (F1) and rendering/scaffold polish (F12/F13).
- `subsys.graph` — entity retire as a status transition (F10).

## Source-of-Truth Captures

_Captured 2026-06-23 from real systems; authority over the gameplan body._
- **Engine**: `clauderizer 1.0.3` (current latest on PyPI; the H-14/H-15 fixes just shipped).
- **Repo HEAD**: `6bf8be6` (branch `main`, clean tree).
- **Test suite**: green at 1.0.3 (~573-of-record baseline + the 1.0.3 additions; exact count pinned by Phase 0 `cz_preflight`).
- **Findings source**: `docs/gameplans/2026-06-23-stranger-readiness-dogfood/_harness/friction-log.md` (F1, F4–F13). H-14/H-15 in `docs/HARDENING.md` are already FIXED — out of scope here.
- **Governing constraint**: INVARIANT-07 — every fix additive; no regression to the Claude Code experience.
- **Leverage**: the `ops` registry IS the MCP tool registry, so the F4/F11 introspection reuses one schema source (no duplication).

## Amendments

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

### D1 — Scope: fix the ops cluster + F5/F6/F7/F10/F1 + real F12 bugs; document the intentional findings

**Context**: The dogfood logged 12 follow-ups (F1, F4–F13). Some are genuine defects; the F13 set is intentional-by-design and only needs documentation. Every fix must be additive and must not regress the Claude Code experience (INVARIANT-07).
**Decision**: FIX: F4 (ops schemas), F8/F9/F11 (ops ergonomics), F6 (cascade dedupe), F5 (profile-aware preflight warn), F7 (serverInfo version), F10 (entity retire), F1 (uvx alias), and the genuine F12 rendering bugs. DOCUMENT-not-change (F13): AGENTS.md==CLAUDE.md (single-source L-16/D2), hook on every prompt (D-025), .mcp.json gitignored (D-031), saas empty stubs, thin empty-project digest.
**Consequences**: Bounded, value-ordered scope; the ops-discoverability cluster (load-bearing for cross-host/no-MCP, L-05/L-35) leads. Intentional behaviors get explained, not churned.
**Evidence**: docs/gameplans/2026-06-23-stranger-readiness-dogfood/_harness/friction-log.md (F1, F4–F13)
**Status**: active (2026-06-23)

### D2 — ops signals ok:false via an opt-in --strict, never a silent default exit-code change

**Context**: F8: `clauderize ops` exits 0 even when a result is ok:false. Changing the default exit code would break any caller/script relying on exit 0 — including the engine's own cross-host CLI fallback — and risks INVARIANT-07.
**Decision**: Add an opt-in `--strict` (exit non-zero when any result is ok:false). The DEFAULT stays exit 0 for backward-compat. Any default change is gated on auditing every caller (O-01) and would ship as a documented behavior change, never silently.
**Consequences**: Scripts get a reliable failure signal when they ask for it; existing callers are unaffected; INVARIANT-07 honored.
**Status**: active (2026-06-23)

### D3 — Entity retirement is a status transition, never a hard delete (INVARIANT-03)

**Context**: F10: there is no entity retire/delete verb, so cleanup means rm+reindex — contradicting the "never hand-edit tracked files" rule. Memory is append-only (INVARIANT-03).
**Decision**: Add an entity retire/obsolete verb that transitions the entity to a retired/obsolete STATUS (kept, demoted in surfacing), never deletes the doc — mirroring the lesson/skill obsolete lifecycle.
**Consequences**: First-class cleanup without breaking append-only memory or the no-hand-edit floor; dependents and graph history are preserved.
**Status**: active (2026-06-23)

### D4 — Add a `clauderizer` console-script alias so `uvx clauderizer` works; `clauderize` stays canonical

**Context**: F1: the package is `clauderizer` but the executable is `clauderize`, so the intuitive `uvx clauderizer init` fails (uvx's error guides to --from, but it is still a first-run wall).
**Decision**: Add a `clauderizer` console-script entry pointing at the CLI main, so `uvx clauderizer <cmd>` resolves. Keep `clauderize` as the canonical/documented command; the alias is a discoverability safety net.
**Consequences**: The intuitive first-run command works. Minor: two command names exist; docs lead with `clauderize`.
**Status**: active (2026-06-23)

## Open Items

**O-01.** _(phase ops ergonomics and consistency)_ Audit every `clauderize ops` caller (engine code, CI workflows, docs, the cross-host/no-MCP fallback path) before any change to the ops DEFAULT exit code (F8) — confirm none rely on exit 0. Gates whether `--strict` stays opt-in or the default ever flips. _(resolved 2026-06-23: Moot. F8 — the exit-code change O-01 was gating — is a false finding (C-02): `clauderize ops` already exits non-zero on any ok:false (and 0 on success). No exit-code change was made, `--strict` was not built, so no caller audit is needed.)_

**O-02.** _(phase Correctness and lifecycle)_ Verify the installed FastMCP API accepts an explicit server `version` (or equivalent) before implementing F7; if it does not, find the supported way to set serverInfo.version, or de-scope F7 to a documented known-quirk. _(resolved 2026-06-23: Verified: FastMCP exposes no public version parameter, but the lowlevel server it wraps (`mcp._mcp_server`) has a settable `.version`. build_server now sets it to __version__, guarded by try/except so an SDK change can never break startup. serverInfo.version now reports clauderizer's version (test_serverinfo_version.py confirms). F7 implemented, not de-scoped.)_

## Phase Breakdown

### Phase 0: Bootstrap and triage

**Goal**: Triage the 12 follow-ups against shipped 1.0.3 — re-confirm each still reproduces (or is already addressed), classify each fix-now | document-as-intended | wontfix (record the F13 de-scope set per D1), pin the green test baseline via `cz_preflight`, and confirm the finding→phase mapping before any code changes.
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] each follow-up finding (F1, F4-F13) re-confirmed against 1.0.3 or marked already-addressed, with a one-line repro/status
- [x] each finding classified: fix-now | document-as-intended | wontfix (the F13 de-scope set recorded per D1)
- [x] test baseline pinned via cz_preflight (record the green count)
- [x] finding-to-phase mapping confirmed

### Phase 1: ops schema discoverability

**Goal**: Expose op + argument schemas for `clauderize ops` (the no-MCP CLI fallback that is load-bearing cross-host/cross-model) by introspecting the shared ops/tool REGISTRY: `clauderize ops --list` (op names + one-line summaries) and `--schema <op>` (required + optional args from the signature). Fix the dead "see tools_list" hint in the unknown-op error to point at the real introspection. Closes F4; reuses the same registry the MCP surface uses, so no schema duplication.
**Depends on**: Bootstrap and triage.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] `clauderize ops --list` prints op names + one-line summaries from the shared registry
- [x] `clauderize ops --schema <op>` prints required + optional args for that op
- [x] the unknown-op error hint points at the real introspection (no dead 'tools_list' reference)
- [x] tests cover --list/--schema and the corrected hint; suite green

### Phase 2: ops ergonomics and consistency

**Goal**: Tighten `clauderize ops` ergonomics on the schema foundation from P1: (F8) add an opt-in `--strict` that exits non-zero when any result is ok:false — the DEFAULT stays exit 0 for backward-compat (never change the default without auditing every caller, per O-01 and INVARIANT-07); (F9) make the cascade-closure contract explicit so resolving needs no guesswork (document/validate that cz_resolve_cascade wants verdicts AND updates_applied, or accept verdicts-only as complete); (F11) reconcile arg-vocab inconsistencies (cz_create_gameplan name-only vs phases/title; cz_upsert_entity rejecting title) — at minimum surface optional kwargs in P1's --schema output. Closes F8/F9/F11.
**Depends on**: ops schema discoverability.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] `clauderize ops --strict` exits non-zero on any ok:false; default exit code unchanged (exit 0) — both tested
- [x] cascade-closure contract made explicit (cz_resolve_cascade: verdicts (+updates_applied) documented/validated; no guessing)
- [x] arg-vocab inconsistencies reconciled or surfaced via --schema (cz_create_gameplan phases/title; cz_upsert_entity title)
- [x] O-01 (ops caller audit) resolved; suite green

### Phase 3: Cascade dedupe

**Goal**: Stop the double-cascade (F6): cz_transition_status already emits a cascade report, so following CLAUDE.md to then run cz_cascade for the same entity+transition creates a duplicate. Make cz_cascade detect an existing unresolved report for the same (entity, transition) and reuse/refuse rather than create a second — or clearly scope cz_cascade to non-transition manual edits in both the docs and the tool description. Closes F6.
**Depends on**: Bootstrap and triage.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] a transition_status followed by cz_cascade for the same (entity, transition) no longer produces a duplicate report (deduped or refused) OR cz_cascade is clearly scoped to non-transition edits in docs + tool description
- [x] regression test for the no-duplicate behavior; suite green

### Phase 4: Profile-aware preflight

**Goal**: Close the generic-profile preflight gap (F5): init detects the profile on the (empty) dir, writes profile=generic with empty test/build, then preserves profile.lock on re-init — so the tests/build preflight checks are permanent no-ops in a real (e.g. Python) repo. Add an advisory (INVARIANT-05) preflight/doctor WARN when profile=generic leaves test/build empty in a now-detectable-language repo, pointing at re-detection, WITHOUT overriding a user-edited profile.lock. Closes F5.
**Depends on**: Bootstrap and triage.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] preflight/doctor emits an advisory WARN (not a hard block, INVARIANT-05) when profile=generic leaves test/build empty in a now-detectable-language repo
- [x] a user-edited profile.lock is never overridden by the warn/re-detect path
- [x] test covers the warn firing and not-firing cases; suite green

### Phase 5: Correctness and lifecycle

**Goal**: Two small correctness/lifecycle fixes: (F7) pass the engine version to FastMCP so MCP serverInfo.version reports clauderizer's version, not the mcp-SDK version — VERIFY the FastMCP API accepts an explicit version first (O-02); (F10) add an entity retire/obsolete verb — a STATUS transition to retired, never a hard delete (INVARIANT-03 append-only; mirrors the lesson/skill obsolete lifecycle) — so cleanup does not require rm+reindex against the "never hand-edit" rule. Closes F7, F10.
**Depends on**: Bootstrap and triage.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] O-02 resolved: FastMCP version-setting verified; MCP serverInfo.version reports clauderizer's version (or F7 de-scoped with a documented reason)
- [x] an entity retire/obsolete verb transitions status (never deletes); dependents/graph preserved; mirrors the lesson/skill obsolete lifecycle
- [x] tests for retire + serverInfo version; suite green

### Phase 6: Front-door and polish

**Goal**: Front-door + polish: (F1) add a `clauderizer` console-script alias so the intuitive `uvx clauderizer <cmd>` works, keeping `clauderize` canonical; (F12) fix genuine rendering bugs — stub placeholder lines persisting after the first real write, amendment array args rendering as Python list literals, the stale "cascade pending" pointer after a resolved cascade; (F13) DOCUMENT the intentional-by-design items rather than change them (AGENTS.md==CLAUDE.md per L-16/D2; hook on every prompt per D-025; .mcp.json gitignored per D-031; saas empty-stub modules; thin empty-project digest). Closes F1/F12; documents F13.
**Depends on**: Bootstrap and triage.

| Task | Description | Effort |
|------|-------------|--------|
| 6.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] `uvx clauderizer <cmd>` resolves (console-script alias added); `clauderize` still canonical; tested
- [x] F12 rendering bugs fixed: no stale stub placeholder after first write; amendment array args render as a markdown list (not a python literal); no stale 'cascade pending' pointer after resolve
- [ ] F13 intentional items documented (AGENTS==CLAUDE per D-035, hook-on-prompt per D-025, .mcp.json gitignore per D-031, saas stubs, thin digest)
- [ ] suite green; CHANGELOG updated for the user-visible changes

### Phase 7: Documentation diligence and human-usability

**Goal**: The cross-cutting docs pass the dual-audience decision mandates: sweep ALL reference docs as a SET for drift (README MCP/ops surface, the CLAUDE.md/AGENTS.md stanza, TRUST/UPGRADING/SECURITY/TROUBLESHOOTING, the cz_* tool descriptions), confirm every P1–P6 user-visible change is documented, and raise the HUMAN-usable layer — a quickstart, a command + `ops` reference (now feasible via P1's --list/--schema), and troubleshooting. Verify with a fresh-human-reader lens: a subagent reading the docs cold as a human evaluator (mirroring the dogfood's fresh eyes), able to install, run a basic workflow, and recover from a common error using only the docs.
**Depends on**: ops schema discoverability, ops ergonomics and consistency, Cascade dedupe, Profile-aware preflight, Correctness and lifecycle, Front-door and polish.

| Task | Description | Effort |
|------|-------------|--------|
| 7.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] every P1-P6 user-visible change is reflected in the human-facing docs (no behavior left undocumented)
- [x] reference docs swept as a set; zero drift between docs and the actual tool/ops surface (e.g. `ops --list` matches the README/reference)
- [x] a human-usable quickstart + command/`ops` reference + troubleshooting exist and are accurate
- [x] a fresh-human-reader pass (no source access) can install, run a basic workflow, and recover from a common error using only the docs
- [x] CHANGELOG covers all user-visible changes from this gameplan
