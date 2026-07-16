---
id: subsys.rituals
type: subsystem
version: 0.10.0
status: active
depends_on:
  - subsys.graph@^0.1.0
  - subsys.markdown-core@^0.1.0
last_verified: 2026-07-16
---

# Rituals

The recurring operations a session used to perform *from memory* — the pre-flight checklist, the cumulative handoff, the cold-start reading order, the self-review — are real engine functions here. They run for real and report; they are not conventions the agent is trusted to honor. Anti-pattern #3 of the original procedure was literally "session claims vs reality" — this subsystem closes that gap by *doing* the work and returning structured evidence.

## Pre-flight (`preflight.py`)

**`run()` executes a list of checks, each an actual operation** — tests and build run the host profile's real commands (`profile.command("test")` / `"build"`), git checks shell out (`git status --porcelain`, `rev-parse`), and the graph-state checks read the gameplan dir. The command set comes from the **profile (data)**, so the engine never hardcodes a language; the runner is injectable so tests stub it without a toolchain.

**The enabled checks come from `config.preflight_checks`, set by size.** Per `config.py` `SIZE_MANIFESTS`, `standard` and `saas` run **eight** checks — `branch_base`, `clean_tree`, `tests`, `build`, `deps_spotcheck`, `branch_creation`, `cascade_hygiene`, `handoff_presence` — while `pet` runs **two** (`clean_tree`, `tests`).

- **`tests` writes the baseline back.** On a green run with a count matched by `profile.baseline_test_regex`, preflight refreshes the gameplan's tracked baseline (closing anti-pattern #7, stale references). It is the one tracked write in an otherwise read-only ritual, serialized under `write_lock` (H-05); a contended lock skips the refresh rather than failing pre-flight — the value self-heals on the next green run.
- **`cascade_hygiene`** fails if `status_bundle.pending_cascades()` finds unresolved reports under `_cascade-reports`. **`handoff_presence`** fails when a handoff the phase table implies should exist is missing (only the first phase and phases whose predecessor is `complete` are required, so a healthy mid-flight gameplan stays clean).
- **Advisory downgrade**: a check listed in `config.preflight_advisory` has a failure demoted to `warn` and never fails pre-flight — so a docs/audit workflow keeps `clean_tree` visible without crying wolf.

Git state is read through a helper that distinguishes `branch` / `detached` / `unborn` / `none` — the `unborn` case (fresh `git init`, zero commits) is a *skip*, not a false "not a git repo", since that is the very first thing a new adopter runs.

## Handoff (`handoff.py`)

**`assemble()` builds a cumulative, self-contained handoff** — the fix for incomplete lesson propagation, made an operation rather than a discipline. Every handoff carries **all still-relevant lessons forward** (so phase N+3 never repeats phase N's mistake), rolled up from the *single canonical list*. Only lessons marked obsolete/promoted/struck-through are pruned (`lesson_state.is_active`).

- **The engine owns only the marker block** `<!-- clauderizer:handoff -->` (D-008). Regeneration replaces just that region and preserves agent prose outside it byte-for-byte (modes `created` / `merged` / `migrated` / `preserved`).
- **A relevance-ranked "Most Relevant Lessons for This Phase" block** rides *above* the full list (D-021): it ranks active lessons against the phase's text via `analyze.rank_relevant` (keyword + entity-id overlap, **no ML** — D-018), capped at `RELEVANCE_K = 5`. Pure surfacing — pointers into canonical memory (D-013), never reordering or dropping — and silent when the list is already short.
- **Project lessons ride across gameplans.** When `docs/LESSONS.md` exists, its active `L-NN` entries roll into a distilled block present in *every* handoff — that is what promotion buys (D-009).

## Status digest (`status_bundle.py`)

**`compute()` produces the cold-start payload** the SessionStart hook injects and `cz_status` returns on demand — it replaces the old hand-written "read these N files in order". For the active gameplan it reports: **phase state** (current/next/blocked from the parsed phase table), the **baseline test count**, **pending cascades** (the shared `pending_cascades()` predicate, identical to the pre-flight check's), unresolved **open items**, and **drift hints** (entities still `planned` while phases are `complete`).

**The memory gauge** counts active/obsolete/promoted lessons plus project lessons and estimates the assembled handoff size (a real `assemble(write=False)`). Past `config.active_lessons_warn` (12) or `project_lessons_warn` (20) it emits consolidation nudges toward `cz_consolidate_lessons` / `cz_promote_lesson` / `cz_obsolete_lesson`. This is **pressure + visibility, not caps** (D-009) — nothing is auto-pruned. `render_digest()` flattens the bundle into the compact `[Clauderizer]` block and surfaces an engine-stale warning when a long-lived server's source changed after start.

## Self-critique (`critique.py`, D-019)

**`critique()` assembles a reference-free rubric** over a target — a phase, the whole gameplan, or the in-progress handoff — across three dimensions, each backed by signals the engine already computes:

- **Coverage** — unresolved open items + unchecked exit criteria, plus incomplete phases for a gameplan target.
- **Coherence** — drift warnings + pending cascade reports.
- **Grounding** — active lessons carrying no `*(evidence: …)*` provenance marker (D-017).

It is read-only and **advisory, exactly like the analyze gate** (D-016): the engine surfaces the deterministically-detectable gaps and prompts; **the agent grades each dimension and decides** — it never scores or blocks (INVARIANT-05). Reference-free and stdlib-only (no embeddings), modeled on STORM's LLM-judge rubric adapted to surface-don't-decide.

## Where it sits in the DAG

`subsys.rituals` depends on **markdown-core** (it reads/writes sections, marker blocks, and lesson state) and the **graph** (drift and analyze ranking). The **mcp-server** depends on it — `cz_preflight`, `cz_write_handoff`, `cz_status`, and `cz_critique` are thin wrappers over `run()`, `assemble()`, `compute()`, and `critique()`.
