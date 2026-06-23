# Friction Log — stranger-readiness-dogfood

Append-only. Phase 4 aggregates, dedups, and triages these into confirmed
findings. Orchestrator-found entries (during planning / Phase 0) are seeded
here; the three build subagents return more.

**Entry schema** (one block per finding):
- **id** — F-NN
- **run** — orchestrator | pet | standard | saas
- **surface** — install/uvx · init/wiring · cz_* tool · docs/discoverability · ritual/preflight · host-axis · other
- **step** — what the (first-time) user was doing
- **expected** — what they reasonably expected
- **actual** — what happened
- **severity** — blocker | high | medium | low | nit
- **repro** — minimal command/sequence
- **note** — optional analysis / suspected root cause

---

## F0 — phase-identifier contract is inconsistent across authoring tools
- **run**: orchestrator (planning)
- **surface**: cz_* tool (gameplan authoring)
- **step**: setting exit criteria after adding phases
- **expected**: one consistent way to name a phase across the authoring tools
- **actual**: `cz_add_phase(depends_on_phases=[...])` takes phase **names**; `cz_set_exit_criteria(phase=...)` takes phase **numbers**. Passing a name to set_exit_criteria failed: "phase X not found in Phase Breakdown".
- **severity**: medium
- **repro**: `cz_set_exit_criteria(phase="Harness and baseline", ...)` → not found; `cz_set_exit_criteria(phase="0", ...)` → ok
- **note**: discoverability/consistency. Either accept both forms, or surface the expected identifier in the error.

## F1 — `uvx clauderizer <cmd>` fails; package name ≠ executable name
- **run**: orchestrator (Phase 0 install verification)
- **surface**: install/uvx + docs/discoverability
- **step**: first-time user runs the zero-install path
- **expected**: `uvx clauderizer init` works (the package is "clauderizer")
- **actual**: "An executable named `clauderizer` is not provided by package `clauderizer`." The executable is `clauderize` (no trailing r); correct form is `uvx --from clauderizer clauderize ...`.
- **severity**: high
- **repro**: `uvx clauderizer --version` → error (lists execs, suggests `--from`); `uvx --from clauderizer clauderize --version` → `clauderizer 1.0.2`
- **note**: uvx's error is helpful, which softens it. Fix candidates: (a) add a `clauderizer` console-script alias pointing at the CLI; and/or (b) make the README/quickstart lead with the `uvx --from clauderizer clauderize` form. init.py's DEFAULT_RUN already uses `--from clauderizer`, so the engine knows — only the human-facing first-run command lags. **Status: open** (DX follow-up; not in 1.0.3).

---

# Aggregated findings — Phase 4 (three build runs: pet · standard · saas)

All three fresh-eyes subagents completed (apps built; the saas one is a real servable
website; isolation held — nothing touched outside each project dir; all tracked writes
went through `clauderize ops`, never the cross-repo MCP tools). Findings below are
deduped across runs; **(×3)** means independently reproduced in all three.

| id | severity | surface | finding | status |
|----|----------|---------|---------|--------|
| **F2** | critical | install/init/wiring | **(×3)** `init` wires the MCP server as `uvx -q --from clauderizer clauderizer-mcp`, but `mcp` is an optional extra → server refuses to serve → **no `cz_*` tools on any zero-install**. | **recorded H-14 · FIXED in 1.0.3** (uvx MCP cmd → `--from clauderizer[mcp]`) |
| **F3** | high | ritual/doctor | **(×3)** `clauderize doctor` reports "MCP server launchable" green because it probes `--version`, which never imports `mcp` → false confidence masks F2. | **recorded H-15 · FIXED in 1.0.3** (doctor statically flags a `--from clauderizer` MCP wiring missing `[mcp]`) |
| **F4** | medium | docs/discoverability | **(×3)** `clauderize ops` (the no-MCP fallback CLAUDE.md leans on) has no op list / arg schemas; required args found only by empty-arg probing; the "see tools_list" hint points at an op that doesn't exist. | open (follow-up) |
| **F5** | medium | ritual/preflight + profiles | `init` detects the profile on the *empty* dir → `generic` → empty `profile.lock.toml`, and preserves it on re-init, so a Python project's `tests`/`build` preflight gates are permanent no-ops out of the box. | open (follow-up) |
| **F6** | medium | cz_* / docs | `cz_transition_status` already emits a cascade report; following CLAUDE.md to then run `cz_cascade` creates a duplicate report. | open (follow-up) |
| **F7** | low | mcp-server | MCP `serverInfo.version` reports the **mcp SDK** version (e.g. 1.28.0), not clauderizer's — `FastMCP("clauderizer")` has no explicit `version`. Undermines a "version matches" reading. | open (follow-up; deferred from 1.0.3 — FastMCP version kwarg unverified) |
| **F8** | low | cz_* / ops | `clauderize ops` exits 0 even when a result is `ok:false`; scripts must parse the JSON, not the exit code. | open |
| **F9** | low | cz_* / ops | Cascade closure needs `verdicts` AND an undocumented `updates_applied`; recording all verdicts alone leaves it `pending`. | open |
| **F10** | low | cz_* | No entity-delete/retire op; cleanup means `rm`+`reindex`, which contradicts the "never hand-edit tracked files" rule. | open |
| **F11** | low/nit | cz_* | Arg-vocabulary inconsistency: `cz_create_gameplan` ignores `phases`/`title` (name-only); `cz_upsert_entity` rejects `title` (which `cz_add_decision` accepts). | open |
| **F12** | nit | rendering | Stub placeholder lines persist after the first real write (e.g. DECISIONS.md keeps `_(Add entries…)_`; a "Cascade report: pending" pointer stays after resolve); amendment array args render as Python list literals `['…']`. | open |
| **F13** | nit | init/wiring/docs | `AGENTS.md`==`CLAUDE.md` byte-identical; `.mcp.json` gitignored (so broken wiring is also unreviewable in commits); `kimi-setup.md` written for a claude-code host; hook fires on every prompt; empty-project digest is thin; `saas` size scaffolds empty stubs (oversells "many modules"). | open (all defensible-by-design; documentation candidates) |

**Triage summary.** 2 confirmed product defects fixed in 1.0.3 (F2/H-14 critical, F3/H-15 high).
The rest are real rough edges — chiefly the `ops` discoverability cluster (F4/F8/F9/F11) and the
`generic`-profile preflight gap (F5) — recorded as follow-ups, none blocking. The dogfood's
core hypothesis held: a maintainer's editable venv (with `mcp` present) hides F2/F3 entirely;
only a cold zero-install surfaces them.
