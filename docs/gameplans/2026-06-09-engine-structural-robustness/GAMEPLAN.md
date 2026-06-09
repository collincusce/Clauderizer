# Engine Structural Robustness Gameplan

> Created: 2026-06-09
> Status: Executing
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

Close the engine-robustness cluster left open by the discipline-seams and
context-economics post-mortems, plus today's cold-start findings (H-01..H-03):
cascade report filename collisions, placeholder-poisoned ID auto-numbering, the
tracked surfaces that still lack blessed writes (Outputs Registry, Per-Phase
Completion Summaries, tracker header lines), substring-matched lesson state,
doctor identity checks, and the close-out memory-gauge gap.

The through-line is **structure over substrings**: every defect here comes from
the engine writing or reading markdown via line/substring heuristics rather than
structural grammar — tables appended as paragraphs, IDs counted in prose, state
inferred from anywhere-in-line markers. v0.6.0 makes those writes structural,
heals the existing corruption write-through, and certifies engine identity, so a
cold agent can trust the docs *as rendered* and require nothing from the user.
Live dogfood evidence at planning time: this gameplan's own decisions numbered
D3..D9 with a phantom D6 gap — the Phase 0 bug performing inside its own plan.

## Subsystems Touched

- `subsys.markdown-core` — `model.next_numbered_id`, table-aware row writes, new `lesson_state` grammar
- `subsys.mutations` — `add_phase`/`transition_phase` table healing, `add_output`, `add_phase_summary`, header write-backs, lesson-state call sites
- `subsys.rituals` — status_bundle gauge note + pending-report ordering, handoff roll-up via the grammar
- `subsys.scaffold` — CLAUDE.md stanza CLI fallback, doctor identity checks (cli.py)
- `subsys.mcp-server` — `cz_add_output`, `cz_add_phase_summary`; tools_list 22 → 24

## Source-of-Truth Captures

Captured 2026-06-09 from the live repo (authority over the gameplan body):

- **Baseline test count**: 109 passing (`.venv/bin/python -m pytest`, 2.06s)
- **Engine**: source + editable venv both 0.5.0; procedure 1.1.0; **MCP tools: 22**
- **Collision format**: `report_filename()` = `f"{YYYY-MM-DD}-{entity}.md"`
  (src/clauderizer/graph/cascade.py) — no disambiguator
- **Numbering scan**: `\b{prefix}{sep}(\d+)\b` over the full document
  (src/clauderizer/model.py); live evidence: this gameplan's decisions numbered
  D3..D9 *skipping D6* (template prose "D1, D2" + a cross-reference to
  context-economics D6 inside a decision's text were both counted as real IDs)
- **Broken tables on disk**: CHAT-HANDOFF-INDEX.md + PHASE-STATUS.md of both
  closed 2026-06-09 gameplans (blank-line-separated rows; legend mid-section) —
  and this gameplan's own trackers, freshly broken by today's add_phase appends
- **Lesson-state substring sites**: `status_bundle._memory_gauge`,
  `handoff._filter_lessons`, `mutations.obsolete_lesson` / `promote_lesson` /
  `consolidate_lessons` (markers `(obsolete`, `(promoted`, `~~`)
- **Stale headers observed**: `> Status: Phase 0 ready` (both closed indexes),
  `> Status: Planning` (both closed GAMEPLAN.md) — all phases complete in reality
- **Pending-cascade predicate strings**: `_(fill in concrete edits` and
  `_needs review_` (shared predicate `status_bundle.pending_cascades`)
- **Wiring**: hook + MCP = `/home/ccusce/Clauderizer/.venv` console scripts
  (editable install, python 3.12); `clauderize doctor` all-green today

## Amendments

### A-001 — Preflight resolves profile commands against the engine's interpreter environment

- **Date**: 2026-06-09
- **Affected sections in GAMEPLAN.md**: Phase Breakdown (Phase 0 task table, exit criteria)
- **Affected phases**: 0
- **Triggered by**: Phase 0 preflight failure on this repo: tests check ran `pytest` and got 'pytest: not found' while .venv/bin/pytest exists
- **What changed**: Add task 0.6: preflight's default runner prepends the running interpreter's bin directory to PATH for profile commands, so a venv-installed engine finds its own toolchain without shell activation.
- **Why**: The repaired wiring launches the engine by absolute venv path with no activation; profile commands resolve against the inherited PATH and miss the engine's own environment - the same capability-gap class as H-01, one layer down.
- **Cascade report**: _cascade-reports/2026-06-09-A-001.md

## Decisions

### D3 — Table healing is write-through normalization, not a one-off migration

**Context**: Four tracker docs already hold broken phase tables (H-02); a migration script would fix files once and let the writer keep breaking new ones.
**Decision**: Phase-table rows are written through a table-aware writer that rebuilds the section's table block contiguously (header, separator, data rows) on every blessed touch, preserving legend/prose after the table. The four broken docs heal on their next blessed write.
**Consequences**: No separate migration tooling; normalization must be idempotent (apply-twice == apply-once); rendered markdown becomes valid for external readers, not just the engine's parser.

### D4 — Cascade report filenames carry a zero-padded sequence, never timestamps

**Context**: report_filename is date+entity, so two same-day cascades of one entity silently overwrite (discipline-seams lesson #5); timestamps would fix uniqueness but make names non-deterministic and diff-noisy.
**Decision**: New reports are named YYYY-MM-DD-<entity>-NN.md with NN the next free zero-padded sequence for that date+entity; legacy unsuffixed reports stay valid and sort before numbered ones of the same day.
**Consequences**: Lexicographic order equals chronological order within a day; 'latest pending' semantics keep working; no clock dependency beyond the date.

### D5 — Per-phase cascade resumes, reversing context-economics D6

**Context**: D6 deferred all cascades to gameplan close specifically to dodge the filename collision; this gameplan fixes the collision in Phase 1.
**Decision**: Each phase close runs its own entity transitions + cascade. Phase 0 cascades before the fix (fresh entities, no same-day repeats, safe); Phases 2-3 re-cascade the same entities the same day, exercising the sequence suffix live.
**Consequences**: The collision fix is demonstrated on this repo's own reports rather than only in tests; close-out cascade returns to being per-phase routine.

### D7 — Tracker header lines are engine-owned write-backs

**Context**: '> Status:' and '> Last updated:' header lines of CHAT-HANDOFF-INDEX, PHASE-STATUS, and GAMEPLAN.md have no blessed write, so both closed gameplans still read 'Phase 0 ready' / 'Planning' (open thread, twice observed).
**Decision**: transition_phase (and add_phase) write the headers back on every call: Last updated = today; index/status Status = phase summary ('Phase N of M in progress', 'All N phases complete'); GAMEPLAN.md Status moves Planning -> Executing on first in_progress and -> Complete when all phases complete.
**Consequences**: Headers can no longer rot silently; agents and humans never hand-edit them; the baseline write-back pattern (discipline-seams D5) is generalized.

### D8 — Lesson state is a trailing structured marker with one parser

**Context**: Lesson state is currently inferred by substring tests for '(obsolete' / '(promoted' / '~~' scattered across five call sites; a lesson whose TEXT mentions those strings is silently miscounted or mispruned.
**Decision**: A single grammar module (markdown/lesson_state.py) parses state from a line-final marker only: '(obsolete <date>[: reason])' or '(promoted <date>: L-NN)' at end of line, or a fully struck-through line. All consumers (memory gauge, handoff roll-ups, obsolete/promote/consolidate validation) call it.
**Consequences**: Mid-text mentions of the marker words become inert; state semantics live in exactly one place; the markers stay human-readable in the markdown.

### D9 — Doctor verifies the engine it runs is the engine the repo expects

**Context**: Today's session found pip metadata at 0.3.0 while source was 0.5.0, and H-01's wiring could silently run a stale PyPI build when dogfooding; doctor checked launchability but never identity (L-02 capability gap, one level up).
**Decision**: Doctor adds two checks: (a) the running engine's importlib metadata version must match its source __version__ (catches stale editable/cached installs); (b) when the repo's own pyproject names this package, the repo source version must match the running engine version (catches dogfooding skew).
**Consequences**: A green doctor now certifies 'the code that runs is the code you see'; both checks fail loudly rather than warn.

## Open Items

_(O1, O2, … — blockers and cross-phase questions.)_

## Phase Breakdown

### Phase 0: Structural numbering and table writes

**Goal**: Auto-numbered IDs anchor to real entry lines (scaffold prose and
cross-references inert) and phase-table rows are written/healed as one
contiguous table block — closes the C-01 thread and H-02.
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | `model.next_numbered_id`: count IDs only at entry anchors — `^### <ID> —` headings and `^**<ID>.**` bold entries (multiline); prose/cross-reference mentions become inert | 1.5h |
| 0.2 | Table-aware row write: `writer.upsert_table_row(path, heading, row, key_col)` inserts/updates a row in the section's first table block and rebuilds the block contiguous (header, separator, rows); legend/prose preserved after the table | 2h |
| 0.3 | `mutations.add_phase` + `_set_phase_row` route rows through the table writer, so any blessed touch heals a broken tracker | 1h |
| 0.4 | Tests: numbering regressions (template placeholder prose; the cross-reference D6 skip; heading + bold anchors across D/A/C/H/INVARIANT/L series), table healing from a fixture replicating today's broken layout, apply-twice idempotency | 2h |
| 0.5 | Dogfood: blessed touches heal this gameplan's own trackers and the four older broken docs; verify rendered tables are contiguous | 0.5h |
| 0.6 | (A-001) preflight's default runner prepends the running interpreter's bin dir to PATH, so profile commands resolve in the engine's own environment without activation | 1h |

**Exit criteria**:
- [ ] A fresh scaffold's first decision numbers D1 with placeholder prose present; a decision whose text cites another gameplan's D6 does not shift numbering
- [ ] `add_phase` twice on a fresh gameplan yields one contiguous table; all six broken trackers on disk (4 old + 2 this gameplan) healed by blessed writes only
- [ ] Full suite passes; baseline grows from 109

### Phase 1: Collision-proof cascade reports

**Goal**: Two same-day cascades of one entity produce two distinct, ordered reports; resolve/pending semantics unchanged for legacy names.
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | `graph/cascade.report_filename(entity, now, reports_dir)`: zero-padded `-NN` sequence per date+entity; `run()` passes its reports_dir | 1h |
| 1.2 | `status_bundle.pending_cascades` + `resolve_cascade` default report: explicit sort key (date, seq, name) so "latest pending" is the newest report; legacy unsuffixed names rank before `-01` of the same day | 1h |
| 1.3 | Tests: two same-day runs produce two ordered files; resolve defaults to the newest; legacy + numbered coexist; dry_run writes nothing | 1.5h |

**Exit criteria**:
- [ ] Two same-day cascades of one entity on this repo produce two reports, both visible to cascade_hygiene until resolved (demonstrated live by the Phase 2/3 close-outs per D5)
- [ ] Full suite passes

### Phase 2: Bless the remaining tracked surfaces

**Goal**: Outputs Registry, Per-Phase Completion Summaries, and tracker header lines get blessed engine writes; doctor gains self-skew checks; the memory gauge explains itself at gameplan close; the CLAUDE.md stanza names the CLI fallback.
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | `mutations.add_output(gameplan_id, phase, key, value)` → "### Phase N Outputs" fenced block under the PHASE-STATUS Outputs Registry (placeholder replaced; per-key upsert, idempotent) + `cz_add_output` | 1.5h |
| 2.2 | `mutations.add_phase_summary(gameplan_id, phase, text)` → per-phase block under the index's Per-Phase Completion Summaries (placeholder replaced; per-phase upsert) + `cz_add_phase_summary` | 1.5h |
| 2.3 | `writer.set_blockquote_field` + header write-backs in `transition_phase`/`add_phase` per D7 (index/status `> Status:` + `> Last updated:`; GAMEPLAN.md Status Planning → Executing → Complete) | 2h |
| 2.4 | doctor: engine-identity checks per D9 (running metadata vs `__version__`; source-repo pyproject version vs running engine) | 1h |
| 2.5 | status_bundle: gauge close-out note per H-03 — `(handoff n/a: gameplan complete)` instead of silent omission | 0.5h |
| 2.6 | `claude_stanza` template gains the CLI fallback line (`clauderize status` / `doctor`) per H-01; installed stanza refreshed via init | 0.5h |
| 2.7 | Tests: outputs/summary round-trips + idempotency; header write-backs across all three docs; doctor skew pass/fail; gauge note | 2h |

**Exit criteria**:
- [ ] The Ending Protocol runs end-to-end with zero hand-edits (outputs, summary, headers all blessed) — demonstrated by this phase's own close-out
- [ ] The stale headers on both closed gameplans are corrected via blessed writes; doctor stays all-green; CLAUDE.md stanza names the CLI fallback
- [ ] Full suite passes

### Phase 3: Structural lesson state and 0.6.0 release

**Goal**: One trailing-marker grammar for lesson state shared by every consumer; version 0.6.0, CHANGELOG, README, installed assets refreshed; gameplan closed out.
**Depends on**: Phase 1, Phase 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | `markdown/lesson_state.py`: `parse_state(line)` → (state, detail) from line-final markers only, plus mark helpers used by obsolete/promote | 1.5h |
| 3.2 | Convert the five substring call sites (gauge, handoff filter, obsolete/promote/consolidate validation) to the grammar | 1.5h |
| 3.3 | Tests: a lesson whose text contains "(obsolete" mid-line counts active and survives roll-up; trailing markers prune; legacy `~~` honored; apply-twice round-trips | 1.5h |
| 3.4 | Release: version 0.6.0 (pyproject + `__init__`), CHANGELOG, README tool list (24), re-run init to refresh installed assets | 1h |
| 3.5 | Close-out: lesson curation (consolidate/promote), per-phase cascades resolved, post-mortem incl. this session's friction log, final headers/status via blessed writes | 1.5h |

**Exit criteria**:
- [ ] A lesson whose text contains the literal string "(obsolete" rolls up as active in handoffs and counts active in the gauge; trailing markers still prune
- [ ] `clauderize --version` reports 0.6.0; doctor all-green including the identity checks; CHANGELOG documents 0.6.0
- [ ] Gameplan closed: post-mortem written (with the friction list), all cascades resolved, digest reports completion
