# evidence traversal 1.14.0 Gameplan

> Created: 2026-07-24
> Status: Executing
> Kind: driven
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

1.14.0 repairs one phenomenon wearing nine costumes: **the engine asserts
things from evidence it never traversed.** A findings register reports every
entry `active` because its parser matched nothing and the reader defaulted. The
curator proposes deleting a lesson because a machine-local, gitignored file is
absent — on a fresh clone that is 100% of the corpus. `doctor` reports the MCP
server "launchable" from `shutil.which`. The graph reports "no dependents" for a
document it silently dropped. The release gate reports the wiring "verified"
from a substring match. Each of those defenses was built after a real incident,
recorded, declared resolved — and is live again, because nothing diffs a claim
against its source.

So this release ships **no new capability, no tuning, and no ranker change.** It
makes the existing defenses actually fire, and ships the executable seam test
for each one — every new test must be demonstrated **red on the pre-fix tree**,
because a fix without its seam test buys about three months, which is the
measured lifespan of the seventeen defenses in `docs/HARDENING.md` that were
declared resolved and came back. And because a defect only counts if it is wrong
for somebody who is not the author, every repair ships as a D-042 tier-1
`clauderize upgrade` action — otherwise it fixes nothing for anyone who already
ran `init`, which is every install in the world.

## Subsystems Touched

- `subsys.markdown-core` — the atomic write path, the shared normalizer at the
  five render sites, the single-sourced status grammar (Phases 0, 1, 2)
- `subsys.mutations` — well-formedness at the write boundary; the phase-table
  escape that closes H-02 (Phase 2)
- `subsys.rituals` — parse reconciliation in corpus-health, the curator's
  zero-telemetry arm, the digest's open-findings line, the preflight baseline
  move, full lesson propagation in the handoff (Phases 0, 3, 5, 6)
- `subsys.graph` — drop records and duplicate-id collisions instead of a silent
  `None` (Phase 5)
- `subsys.scaffold` — preserve-and-refuse on foreign JSON config, the gitignore
  set, `ensure_gitignore_current` and `refresh_claude_stanza` as tier-1 actions
  (Phases 5, 6)
- `subsys.mcp-server` / `feat.init-cli` — capability-not-presence identity in
  `doctor`, the real handshake in the wiring contract (Phase 4)
- `feat.corpus-modernization` — the tier-1 delivery path that makes any of this
  reach an existing install (Phase 5)

## Source-of-Truth Captures

Measured 2026-07-24/25. **Authority over anything in this gameplan's body.**

```
engine source (pyproject + __version__)  : 1.13.0   PUBLISHED to PyPI 2026-07-24
procedure version (engine + both copies) : 1.9.0    corpus stamp: 1.9.0
suite baseline                           : 1002 passed, 5 skipped
safety tag before the write-path work    : pre-1.14.0-writepath @ d52ef6e
MCP tool surface                         : 67 tools, 50,382 chars on the wire
  descriptions                           : 28,228 chars (56%) — NOT to be trimmed (D-064 rule 2)
hardening register (ground truth in md)  : 20 findings — 17 resolved, 3 open (H-16, H-19, H-20)
  what cz_list_findings reports today    : 20 x active, date null  <-- the Phase 0 defect
status-pattern copies under src/         : 3 disagreeing (analyze.py:29, listing.py:87,
                                           abstract_index.py:74 — the last already widened)
active project lessons                   : 25   never surfaced to any phase: 6
  never-surfaced ids                     : L-11, L-24, L-52, L-56, L-57, L-62
  handoff renders                         : 5 of 25 (RELEVANCE_K=5, if/elif) <-- the Phase 6 defect
cz_curate obsolete proposals, live repo  : 6   on a telemetry-free clone: 25 of 25
telemetry                                : 77 events; outcomes 46/46 complete, 0 failed, pass_rate 1.0
  criteria_checked variance              : 7 of 46 partial, aggregate 188/195, stdev 0.08
cascade corpus                           : 53 reports / 123 verdicts / 97 no-change / 26 already-done / 0 discovered
tracked per-machine files (must untrack) : hook.sh, revision.json, proposals.dream.jsonl,
                                           dreams.watermark.json
init gitignore list                      : 6 paths (none of the four above)
ranker: Spearman(length, surfacing)      : +0.868 over 220 real phase queries
  Jaccard normalization                  : McNemar exact p = 0.1250 (NOT supported)
  supersession ties destroyed by it      : 3,222 -> 116 (~96%)  <-- why D-061 is parked
```

## Amendments

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

**O-01.** _(phase 1)_ Windows os.replace under a held handle. locking.py:192-211 documents the sharing-violation class for os.unlink; nobody has tested it for os.replace while a lock-free reader or the SessionStart hook holds the file open. Resolution: a windows-latest test in Phase 1 that opens a second handle and asserts the write either succeeds via retry or fails cleanly WITHOUT truncation. This is a Phase 1 exit criterion, not a hope — test.yml already runs the cell. _(resolved 2026-07-25: MEASURED on the windows-latest CI cells, and the answer is the second branch of the disjunction this item specified. A handle held for longer than the retry budget denies os.replace outright with WinError 5 — retrying does not help, because the handle stays open for the whole window — so the write RAISES. Verified that the safety property holds: the target is left byte-identical to its original content and no temp file survives. That is strictly safer than what it replaced, where truncate-then-write would have destroyed the file. The retry still earns its place for a TRANSIENT handle (an antivirus scanner, a reader that closes promptly). Behavioral consequence worth knowing: engine reads are lock-free by design and open/close immediately, so the exposed window is a user's editor or another tool holding the document — a condition the caller now sees instead of having it silently swallowed. Recorded in write_atomic's docstring and asserted by test_replace_survives_a_second_open_handle_on_windows, which now pins the disjunction rather than assuming success. This is a defect no local run could have produced.)_

**O-02.** _(phase 4)_ Cold-cache handshake cost is unmeasured. Warm is 0.71-0.94s; cold (after uv cache clean) is the one unverified input to Phase 4's default-on design. Resolution: measure on a scratch HOME in Phase 4 and record it as a phase output. If it exceeds the timeout budget the verdict is unverifiable — which is already the designed behavior — not a slow doctor. _(resolved 2026-07-25: MEASURED. Warm handshake 0.99-1.22s; COLD cache (isolated UV_CACHE_DIR, never touching the real one) 2.72s — both comfortably inside the 8.0s default-path budget, so the default-on design holds and no fallback to opt-in is needed. If a future environment does exceed it, the verdict degrades to `unverifiable` by name, which is the designed behavior rather than a slow doctor or a false green.)_

**O-03.** _(phase 3)_ criteria_checked as a lesson-utility signal — pre-registered experiment, NOT actioned in 1.14.0. Hypothesis: a phase's criteria_checked/criteria_total ratio predicts subsequent phase-level rework better than chance. Metric: over at least 30 further recorded outcomes, the correlation between that ratio and whether a later phase reopens or amends its outputs. Kill criterion: no correlation, or the signal is explained by which agent authored the criteria (the self-declaration confound). Note it is still agent-declared, so it does not clear D-063's externally-sourced bar as originally argued — but pass_rate is saturated and this varies (7 of 46 partial, stdev 0.08), so the question is empirical. Run no earlier than 1.15.0. Honest coupling: Phase 5's preflight fix removes SPURIOUS pre-flight failures while D-063's unparking trigger is a stream of GENUINE ones, so that fix moves D-063 FURTHER from unparking.

**O-04.** _(phase 0)_ The 27 founding decisions carry date null. D-001 through D-027 have no date, so no tool can order them temporally — which matters to supersession-demotion and to any is-this-still-current pass. Phase 0's reconciliation will correctly report them as defaulted rather than as an error. Resolution: backfill from git history in 1.14.1 (frontmatter/metadata, append-only-safe), or record the gap explicitly. Not in 1.14.0 because the ordering only matters to the parked ranker work.

**O-05.** _(phase 5)_ Whether .claude/settings.json should join the gitignore set. HARDENING.md:154 records leaving it to the user as deliberate; it contains an always-absolute hook path, so it is machine-specific by construction. Phase 5 deliberately does not change it. Resolution: needs its own decision in the cross-host gameplan, paired with the wrapper-regeneration guarantee — this is a policy question, not a patch. Until then docs/TRUST.md and the README both disclose it and tell the reader to gitignore it themselves.

**O-06.** _(phase 6)_ D-022's formal status. It reads active with superseded_by null while the engine did the exact thing it discarded (tail truncation of lesson propagation). D-068 resolves the BEHAVIOR; whether D-022 is now honored or superseded by D-027 is a records question. Resolution: under D-068 the honest reading is that D-022 is HONORED — nothing is dropped — and D-027 governs the FORM of the roll-up rather than its completeness. Record that reading in Phase 6; if a reviewer disagrees, mark D-022 superseded by D-068 instead.

**O-07.** _(phase 6)_ H-16 (engine writes follow a symlinked PARENT directory) stays open through 1.14.0. HARDENING.md:211 records the deferral with a real compatibility rationale — the naive fix would break legitimate setups where a user symlinks docs/ — and the correct fix, repo-root containment threaded through every write call, is a dedicated hardening pass. Phase 1 explicitly does NOT attempt it. Resolution: named residual against RELEASING.md gate G4 in Phase 6, per D-012's own rule, since pyproject.toml declares Production/Stable; the real fix belongs to the cross-host gameplan alongside D-032's host-simulator stub.

## Phase Breakdown

### Phase 0: Single-source the status parser and expose defaulted status

**Goal**: The corpus registers are parsed by one shared grammar, and a status the reader *defaulted* is distinguishable from a status it *read*.
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | Move the status pattern to one module and import it in analyze.py, listing.py and abstract_index.py (whose copy is already widened). Do NOT touch the writer at mutations.py:353 | 2h |
| 0.2 | Return `status_source` as parsed/defaulted from analyze._entry_status and listing._entry_record so a defaulted status is distinguishable from a read one | 2h |
| 0.3 | tests/test_render_roundtrip.py — L-52 made executable: for each of the 5 kinds, write via the real mutation op and read via the real listing op; assert id, title, status and date survive | 3h |
| 0.4 | Shape-aware parse reconciliation per register in cz_corpus_health and doctor. A flat heading-count check is vacuous because the readers default | 3h |
| 0.5 | Regenerate tests/fixtures/contract_corpus/.../cz_list_findings.json, which freezes the corruption in a golden. The diff is a free reviewable proof artifact | 1h |
| 0.6 | Surface open hardening findings in cz_critique Coverage and as a conditionally-emitted digest line (zero bytes when none are open, per INVARIANT-08) | 2h |
| 0.7 | Build the shared L-24 adversarial-input fixture in conftest (BOM, CRLF, unicode, empty, valid-non-dict JSON, truncated); Phase 5 consumes it | 2h |

**Exit criteria**:
- [x] STANDING ORACLE (every phase): each new test is demonstrated RED on the pre-fix tree in this phase's output record. "Suite >= 1002" is a precondition, never a criterion
- [x] `grep -rn 'Status\*\*' src/clauderizer/` shows exactly ONE compiled status pattern; tests/test_canonical_parsers.py asserts single definition + import identity and fails if a fourth copy appears (note: graph/abstract_index.py:74 ALREADY has the widened regex — this is three disagreeing copies, not two stale ones)
- [x] `cz_list_findings` returns 20 findings: 17 resolved, 3 open (H-16, H-19, H-20), every entry with a non-null date. Pre-fix: 20 x active, date null
- [x] pytest tests/test_render_roundtrip.py green for all 5 kinds (decision, invariant, finding, correction, lesson) written via the real mutation op and read via the real listing op; demonstrated red with the pre-fix regex
- [x] `cz_corpus_health` emits parse_reconciliation with HARDENING.status_defaulted == 0; planting one unparseable Status line in a scratch copy makes it non-zero AND names the entry id. Expected shapes: DECISIONS 27 defaulted (D-001..D-027, by design), INVARIANTS 9 defaulted (by design), LESSONS uses **L-NN.** not ###
- [x] status_source is returned as parsed|defaulted from analyze._entry_status and listing._entry_record — a defaulted status is distinguishable from a read one
- [ ] tests/fixtures/contract_corpus/driven-rich/ops/cz_list_findings.json regenerated; its git diff shows 20 statuses moving off active and dates populating; pytest tests/test_contract_corpus.py green
- [x] `cz_critique` Coverage output contains H-16, H-19, H-20; `clauderize status` carries an open-findings line whose byte length on a zero-open-findings fixture is UNCHANGED from 1.13.0 (INVARIANT-08)
- [x] The shared L-24 adversarial-input fixture (BOM, CRLF, unicode, empty, valid-non-dict JSON, truncated) exists in conftest and is consumed by Phase 5
- [x] `git status --porcelain` empty; suite >= 1002 passed, 5 skipped

### Phase 1: One atomic symlink-refusing write path for tracked markdown

**Goal**: A failed or interrupted engine write can never truncate canonical memory, and no future writer can skip the symlink guard. Highest regression risk in the release.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | Add writer.write_atomic: refuse_if_symlink, parent.mkdir, SIBLING temp in the same dir (never mkstemp, whose 0600 would re-permission every tracked doc), copy the target's mode, os.replace, unlink in a finally | 3h |
| 1.2 | Route writer.py:45, :128 and :190 through it, preserving _write_if_changed's old==new early exit and its revision-bump ordering | 2h |
| 1.3 | Reroute handoff.py:566, cascade.py:171 and cascade.py:225 to write_atomic — NOT to upsert_marker_block, which would drop _AGENT_SCAFFOLD and kill legacy migration | 2h |
| 1.4 | graph/index.py:68 gets the JSON atomic helper abstract_index.py:258-265 already uses for its cache | 1h |
| 1.5 | Bounded retry around os.replace mirroring locking.py:192-211 — on Windows a lock-free reader or the SessionStart hook holding the file raises PermissionError | 2h |
| 1.6 | tests/test_write_path.py — PATH-SHAPED guard: no write_text on a docs/ or .clauderizer/ path outside writer.py. A literal allowlist is rejected (30 sites; an allowlist that size is a registry the next writer joins) | 3h |
| 1.7 | The three probes: RLIMIT_FSIZE truncation (sha256-compared), planted leaf symlinks on both the handoff and cascade paths, and a windows-latest test holding the target open in a second handle | 4h |

**Exit criteria**:
- [x] MANDATORY MITIGATION: tag pre-1.14.0-writepath exists BEFORE this phase starts (done: d52ef6e), and this phase's own cz_* bookkeeping runs on the PUBLISHED engine `uvx --from 'clauderizer[mcp]==1.13.0'` until these criteria pass — expect and accept the skew warning
- [x] `grep -rn '\.write_text(' src/clauderizer/rituals/ src/clauderizer/graph/ | grep -v abstract_index.py` returns 0 lines; tests/test_write_path.py enforces it PATH-SHAPED (no write_text on a docs/ or .clauderizer/ path outside writer.py) and fails if handoff.py:566 is reverted. A literal allowlist is rejected — 30 write_text sites exist and an allowlist that size is a registry the next writer joins
- [x] Under RLIMIT_FSIZE a failing write on a populated docs/DECISIONS.md raises and leaves the file byte-identical (sha256 compared); the same probe pre-fix destroys it (measured 92,027 -> 38,334 bytes)
- [x] After that failed write AND after the full suite, `git status --porcelain` is empty — no *.tmp residue (.gitignore has no *.tmp rule and clean_tree is git status --porcelain)
- [x] A planted leaf symlink at docs/gameplans/<gid>/handoffs/PHASE-N-HANDOFF.md makes cz_write_handoff return ok:false; same for cz_cascade's report path. Both return ok:true and write OUTSIDE the repo pre-fix
- [x] pytest tests/test_handoff.py asserts all four _merge modes (created/merged/migrated/preserved) still reachable and _AGENT_SCAFFOLD still present on a fresh handoff — writer.upsert_marker_block is NOT a drop-in for handoff.py:566
- [x] cz_revision increments exactly once per real change and zero times on a no-op; write_atomic itself does NOT bump (handoff.py:567, cascade.py:174, cascade.py:226 already call revision.bump_for — verified, correcting all three drafts)
- [x] A 0644 doc's mode is unchanged after an atomic write (stat compared in-test, not via GNU-only shell flags) — sibling temp, never mkstemp whose 0600 would re-permission every tracked doc
- [ ] Full 9-cell test.yml matrix green INCLUDING windows-latest, with a Windows test holding the target open in a second handle (bounded retry around os.replace, mirroring locking.py:192-211)
- [x] H-16 (symlinked PARENT directory) is NOT attempted here; HARDENING.md:211 records the deferral rationale and Phase 6 re-confirms it as a named residual

### Phase 2: Well-formedness at the write boundary

**Goal**: No caller string can forge an entry, absorb another entry's body, burn ids, escape a marker block, or produce an entry no reader can reach. Validation is not a discipline gate.
**Depends on**: 0, 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | Shared normalizer at the five render sites (mutations.py:167-173, :274-276, :352-357, :425, phase-table row): single-line-ify structurally single-line fields via the helper already at learn.py:212 | 3h |
| 2.2 | Backslash-escape LINE-LEADING headings and **N.** markers in multi-line bodies. Scoped to column-zero only — a mid-line bold Status label was probed and does not fool the resolver | 3h |
| 2.3 | Visible placeholder for an empty or whitespace-only title, so no id is ever allocated to an entry cz_get and listing cannot reach | 1h |
| 2.4 | Neutralize the handoff MARKER string in any field rendered inside a block — a body containing it permanently escapes the block, voiding D-008 with no op to undo it | 2h |
| 2.5 | Escape pipes and collapse newlines in phase-table cells. This is H-02, marked resolved and live | 2h |
| 2.6 | Extend _PII_PATTERNS with the measured misses and apply the lint at the render boundary as an ADVISORY payload warning, never a block — D-058's own justification names the append-only surface | 3h |
| 2.7 | tests/test_write_wellformed.py — the eight named cases, including the fenced-heading accident case that needs no adversary | 4h |

**Exit criteria**:
- [x] RECORDED VERBATIM SO A REVIEWER CANNOT KILL THIS WITH THE WRONG INVARIANT: validation is NOT a discipline gate. INVARIANT-05 enumerates three gates (clarify/open-items, exit-criteria, analyze-against-invariants); dreams.validate (dreams.py:81) and D-058 are the shipped precedent that a blessed write may check its own input. Normalization runs BEFORE the diff, is deterministic, and NEVER rejects — no write is lost (INVARIANT-03), no mutation gains a hard block (INVARIANT-05)
- [x] test_forged_heading: cz_add_decision(title='ok\n\n### D-900 — FAKE\n\n**Context**: forged') produces exactly ONE new heading, allocates D-<n+1> never D-901, the prior entry's body is byte-unchanged, and cz_list_decisions contains no D-900
- [x] test_accident_fenced_heading: a context containing a fenced ```\n### D-999 — example\n``` leaves parse_entries count at exactly before+1 (no adversary required — this repo quotes markdown constantly)
- [x] test_empty_title_reachable: cz_add_decision(title='') yields an id that cz_get retrieves and listing reports — no id is ever allocated to an unreachable entry
- [x] test_lesson_number_not_burned: cz_add_lesson(text='the roll-up showed:\n**99.** a quoted line') advances the lesson number by exactly 1
- [x] test_phase_table_contiguous: cz_add_phase(name='A|B') and name='A\nB' each produce a row whose cell count equals the header's, and cz_transition_phase on that phase succeeds. This is H-02, marked resolved and live
- [x] test_marker_escape: a field rendered inside a handoff block containing the literal MARKER string (handoff.py:345) cannot escape the block — D-008's byte-for-byte guarantee holds
- [x] test_invariant_multiline_contract pins mutations.py:274-276's first-line-is-title contract; writing byte-identical input twice returns changed:False with no cz_revision bump
- [x] test_pii_advisory: decision bodies containing AKIA and sk_live_ each return a WARNING and still write. _PII_PATTERNS extended with the measured misses (sk_live_, ASIA[0-9A-Z]{16}, arn:aws:, AIza, npm_, pypi-, xapp-, password=) and applied at the mutations.py render boundary — D-058's own justification is that INVARIANT-03 makes retroactive redaction impossible, yet it ships only on the gitignored journal where deletion is trivial
- [x] Escaping is scoped to LINE-LEADING #{1,6} and **N.** only — a mid-line '- **Status**:' was probed and does NOT fool resolve_finding; do not over-scope to any string. Backslash-escape renders identically in CommonMark so the human view is byte-equivalent
- [x] Phase 0's round-trip harness green for all 5 kinds after normalization; DECISIONS.md:382, :467 and HARDENING.md:245 left byte-identical (append-only, they parse, cosmetic)

### Phase 3: Implement D-063 so the curator stops proposing from absent evidence

**Goal**: No checkout can be talked into obsoleting a corpus it never measured, and the loop that proposes deleting never-surfaced lessons is cut. Smallest phase, highest severity per line.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | Remove the surfaced_count==0 obsolete arm at telemetry.py:366-372, per D-063's own recorded text. Leave corpus_health's never_surfaced COUNT untouched and honest | 1h |
| 3.2 | Compute _has_telemetry once; where a never-surfaced framing survives (_lesson_signal, telemetry.py:207, feeding dreams.py:307), gate the wording to read UNMEASURED and set suggested_op to None | 2h |
| 3.3 | loop_step's summary must distinguish 'converged: no evidence to act on' from 'converged: corpus healthy', or the guard trades a false wipe for a false green | 2h |
| 3.4 | Gate status_bundle.py:118-127's re-distill instruction on >=1 non-flag proposal — silencing the tool while leaving the surface that issues the instruction is a half-fix | 1h |
| 3.5 | Add the fresh-clone leg to test.yml: clone to a temp dir with no telemetry.jsonl, run cz_curate, assert zero obsoletion proposals | 2h |
| 3.6 | tests/test_curator_no_telemetry.py, demonstrated red pre-fix (25 obsolete proposals) | 2h |
| 3.7 | Record the criteria_checked unparking experiment as an open item with its kill criterion — pre-registered, run no earlier than 1.15.0 | 30m |

**Exit criteria**:
- [x] IMPLEMENT, DO NOT RE-DECIDE: D-063 already states the never-surfaced obsoletion pressure is removed. It was never coded — telemetry.py:207 and telemetry.py:366-372 are both live. One change at the same two lines is simultaneously the zero-telemetry corpus-wipe fix, not two workstreams
- [x] test_curator_no_telemetry: on a telemetry-free clone of this repo, cz_curate returns 0 proposals with action=='obsolete'. Pre-fix: 25. Demonstrated red pre-fix
- [x] On the LIVE repo, cz_curate returns 0 obsolete proposals. Pre-fix: 6 (L-11, L-24, L-52, L-56, L-57, L-62) — three of which are outputs of the consolidation ritual and one promoted the day before
- [x] Driving the shipped loop body on a telemetry-free clone leaves corpus_health()['active_project_lessons'] == 25. Pre-fix it converges to 0 and reports converged:True
- [x] loop_step['summary'] on a telemetry-free checkout DIFFERS from the healthy-convergence string (asserted, not eyeballed) — the guard must not trade a false wipe for a false green
- [x] status_bundle.py:118-127's 'Re-distill: cz_obsolete_lesson the superseded L-entries' sentence is gated on there being >=1 non-flag proposal — silencing the tool while leaving the surface that issues the instruction is a half-fix, and 25 active lessons is over threshold today so it fires on the very next fresh clone
- [x] Where a never-surfaced framing survives (_lesson_signal, telemetry.py:207, feeding dreams.py:307), the wording with zero events reads UNMEASURED not unused, and suggested_op is None
- [x] A fresh-clone CI leg is added to test.yml (L-23): clone to a temp dir with no .clauderizer/telemetry.jsonl, run cz_curate, assert zero obsoletion proposals
- [x] tests/test_curator.py::test_consolidate_proposal_for_redundant_pair and tests/test_telemetry.py (never_surfaced == 3 with no telemetry) pass UNMODIFIED; corpus_health's never_surfaced COUNT stays untouched and honest
- [x] `clauderize status` on a telemetry-free clone emits no cz_obsolete_lesson instruction, asserted by a string test
- [x] `git diff` shows NO new key in .clauderizer/config.toml or Config — INVARIANT-05 and D-015 forbid an enable/disable flag
- [x] The criteria_checked unparking EXPERIMENT is recorded as an open item, not actioned: it is still agent-declared so it does not clear D-063's externally-sourced bar as argued, but its variance is real. Pre-registered for 1.15.0 with a kill criterion

### Phase 4: Resolve H-20 with capability-not-presence engine identity

**Goal**: Doctor cannot report green on a .mcp.json that will not launch or that serves a different engine. Parallelizable with phases 1 through 3.
**Depends on**: Phase 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | One handshake_probe on the path-safe .mcp.json near cli.py:319, MEMOIZED on the (command, args) tuple so 9 identical auto-write entries collapse to one spawn | 3h |
| 4.2 | Assert serverInfo.name and compare serverInfo.version to __version__, reusing the warning shape that already exists at cli.py:441-445 and is absent from the emitter branch | 2h |
| 4.3 | Delete the CLAUDE_CODE skip at cli.py:347 — the host INVARIANT-07 makes a release blocker is the one host --deep never deepens | 30m |
| 4.4 | Three-state contract per D-010/D-048/INVARIANT-05: timeout, cold cache, offline, proxy all yield `unverifiable` BY NAME, warn, exit 3. Never a silent green, never a free pass | 3h |
| 4.5 | Upgrade hosttargets.verify_emitted_wiring from JSON-parse-plus-substring to the real handshake, and fix its docstring, which claims it launches clauderizer-mcp | 3h |
| 4.6 | init spawn-tests the PORTABLE_COMMAND it is about to write (not the locally-resolved console script), as a warning — never WiringRefused, so an offline first run still installs | 2h |
| 4.7 | Extend quickstart.yml with the MCP leg and a serverInfo.version == tag-under-test assertion; test.yml runs in-process and structurally cannot see this (L-60) | 3h |
| 4.8 | Measure the cold-cache handshake cost on a scratch HOME and record it as a phase output; cz_resolve_finding H-20 with the shipped evidence | 2h |

**Exit criteria**:
- [x] THIS PHASE RESOLVES AN OPEN FINDING THE REPO ALREADY WROTE. HARDENING.md:250-260 records the defect, the recommended fix, and three regression tests. Criteria 2-4 below ARE H-20's own recorded regression tests — read them rather than re-deriving them (all three planning drafts re-derived this from scratch)
- [x] wiring_contract_sweep FAILS for a host whose emitted config names a nonexistent command. Today it passes for all 11
- [x] The gate completes an initialize handshake and receives serverInfo.name == 'clauderizer' for at least one emitted config
- [x] A doc-pin test asserts docs/CROSS-HOST.md section 7's description matches the behavior that ships
- [x] With a PATH-shadowed uvx stub that exits 1: default `clauderize doctor` prints no green check for MCP and does not print OK. Pre-fix: green MCP launchable + exit 0
- [x] With a stub returning serverInfo {clauderizer, 0.1.0}: default doctor prints a version-skew warning and exits 3. Pre-fix with --deep: green on all 9 hosts, exit 0
- [x] With the stub hanging: doctor reports 'unverifiable' and exits 3; grep for the failure glyph in that output is empty. Three-state contract per D-010/D-048/INVARIANT-05 — never a silent green, never a free pass for an awkward host (L-59)
- [ ] `if hid == hosttargets.CLAUDE_CODE: continue` at cli.py:347 is deleted — the host INVARIANT-07 makes a release blocker is the one host --deep never deepens
- [x] The handshake is MEMOIZED on the (command, args) tuple: a counting stub asserts exactly ONE handshake subprocess on a fully-wired repo (all 9 auto-write emitters share the portable entry), wall time < 2.0s warm. Today 0.09s; --deep today is 9 identical handshakes at 9.09s
- [x] tests/test_hosts.py:319 test_doctor_native_repo_stays_green passes UNMODIFIED
- [ ] init.py spawn-tests the PORTABLE_COMMAND it is about to write (not the locally-resolved console script at :229-244), as report.warnings.append never WiringRefused — an offline or proxied first run must still install
- [x] quickstart.yml gains the MCP leg with a serverInfo.version == <tag under test> assertion (L-23; test.yml runs in-process and cannot see this — L-60)
- [x] cz_resolve_finding H-20 with the shipped evidence; cz_list_findings reports H-20 resolved with a date

### Phase 5: Preserve foreign config and converge existing installs

**Goal**: No engine write destroys a file it did not author or crosses a repo boundary, and every already-initialized repo receives the policy fixes via a tier-1 upgrade action. Largest phase, first in the cut order.
**Depends on**: 0, 1.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | Preserve-and-refuse at all four JSON writers (init.py:533-534, :562-563, hosttargets.py:279-287, bespoke_hosts.py:60-72): decode utf-8-sig, validate shape, and on unparseable input refuse the merge with a warning naming the file — never rewrite | 4h |
| 5.2 | model.from_file returns a drop record instead of a bare None; index.build accumulates drops and duplicate-id collisions; both surface in corpus_health and doctor | 3h |
| 5.3 | Delete the basename-suffix fallback at ops.py:1003-1005 so the caller's existing ok:False hint fires. Keep the explicit-arg and env-var paths | 1h |
| 5.4 | Add the six per-machine paths to init's gitignore list and widen tests/test_dreams.py:206 — this keeps the promise docs/TRUST.md already published | 2h |
| 5.5 | doctor nudge naming every still-tracked per-machine path with the exact git rm --cached command; a gitignore line does not untrack | 2h |
| 5.6 | ensure_gitignore_current as a D-042 tier-1 action in modernize.py, plus the wrapper-regeneration guarantee that answers the hook.sh objection with a mechanism rather than an exemption | 3h |
| 5.7 | Move the preflight baseline off the tracked CHAT-HANDOFF-INDEX.md to a gitignored sidecar or the phase-transition write. Do NOT make preflight advisory — D-024 reserves it as the blocking gate | 3h |

**Exit criteria**:
- [ ] tests/test_config_preservation.py parametrized over the L-24 matrix x 4 writers (init.py:533-534, init.py:562-563, hosttargets.py:279-287, bespoke_hosts.py:60-72): a pre-existing {'mcpServers':{'github':...,'postgres':...}} retains BOTH keys byte-identical after init for every encoding; on unparseable input the file is byte-identical and a warning names it. Pre-fix the BOM case leaves only clauderizer
- [ ] bespoke_hosts is a GLOBAL out-of-repo config with no git to recover from — L-29's 'git checkout restores' is false there, so preserve-and-refuse is mandatory, not preferred
- [ ] A BOM'd entity doc under docs/ yields a non-zero graph.dropped naming the path in cz_corpus_health, and entities_indexed + dropped == entities_on_disk; two docs sharing an id produce a collision warning naming both paths. Without this D-018's 'an empty adjacent set is a true negative' is unsound
- [ ] cz_mine_failures from a repo whose slug does not exist returns ok:False with the hint (the basename-suffix fallback at ops.py:1003-1005 is deleted; zero tests pin it). Pre-fix a probe returned ok:True with 47 proposals from an UNRELATED project. Explicit-arg and CLAUDERIZER_TRANSCRIPTS_DIR paths regression-tested unchanged
- [ ] KEEP THE COMMITTED PROMISE: docs/TRUST.md in HEAD now promises init will gitignore proposals.dream.jsonl, dreams.watermark.json, revision.json AND the hook wrapper. init.py:483-491 gitignores six paths, none of them these. All four are added, plus write.lock and write.lock.stale-*
- [ ] The hook.sh objection (a clone with committed .claude/settings.json pointing at a missing wrapper) is answered with a MECHANISM not a refusal: a test asserts init/upgrade/doctor regenerate a missing wrapper
- [ ] A gitignore line does not untrack: `clauderize doctor` names every still-tracked per-machine path with the exact git rm --cached command, asserted by a string test against `git ls-files .clauderizer/`. Four are tracked right now: hook.sh, revision.json, proposals.dream.jsonl, dreams.watermark.json
- [ ] SHIPPED AS A D-042 TIER-1 MECHANICAL ACTION: ensure_gitignore_current in modernize.py beside the existing five, so `clauderize upgrade` converges repos scaffolded by <=1.13.0. Without this, 1.14.0 fixes nothing for anyone who already ran init — which is every install in the world
- [ ] `clauderize upgrade` on a fixture repo scaffolded by 1.13.0 adds exactly the missing lines, regenerates a deleted hook.sh, and leaves every docs/** byte hash-identical (D-042: no markdown memory file is ever auto-mutated); a second run reports no changes
- [ ] cz_preflight run twice on a repo whose TEST COUNT JUST CHANGED (the only case preflight.py:98 does not early-return) reports clean_tree:pass on the second run. Pre-fix it fails. Baseline moves to a gitignored sidecar or to the phase-transition write — preflight is NOT made advisory, D-024 reserves it as the blocking gate deliberately

### Phase 6: Restore full lesson propagation, close H-19, ship 1.14.0

**Goal**: The handoff stops dropping 20 of 25 project lessons, the release gate stops certifying a version that exists nowhere, and every claim this release repaired has a test that diffs it against its source.
**Depends on**: 1, 2, 3, 4, 5.

| Task | Description | Effort |
|------|-------------|--------|
| 6.1 | Change handoff.py:526-545's elif so it renders BOTH the focused block and a compact id + one-line-title index of every active project lesson; fix the module docstring that already claims this | 3h |
| 6.2 | Close H-19 with its own recommended fix: cz_audit calls release_check's remote legs, reports `unverified` on an unreachable registry, and emits 'source X is ahead of release Y' | 3h |
| 6.3 | Fix docs/TRUST.md's excerpt-cap claim — it says 600 characters; learn.py:211 caps at 160 and 600 is the candidate filter. A doc-vs-code mismatch inside the honesty repair itself | 30m |
| 6.4 | The four claim-pin tests (L-62), each demonstrated red when its counterpart is mutated, including the live ancestor-CLAUDE.md staleness case | 4h |
| 6.5 | refresh_claude_stanza as a second D-042 tier-1 action; modernize.py:112-144 has no stanza action so older installs rot | 2h |
| 6.6 | Apply D-063's own amendment text to L-53; record the D-022-is-honored reading; re-confirm H-16 as a named residual in RELEASING.md against gate G4 | 2h |
| 6.7 | Close-out: cz_add_output per phase, cz_add_phase_summary, cascade, handoff, CHANGELOG, version bump, release-check exit 0, tag, publish, and the post-publish four-registry proof | 4h |

**Exit criteria**:
- [ ] MAKE D-021 TRUE INSTEAD OF AMENDING IT TO BE FALSE: handoff.py:120 RELEVANCE_K=5 and handoff.py:526-545 is an if/elif — the focused block REPLACES the full project-lesson list, so a phase sees 5 of 25 while D-021 says it 'drops nothing'. The elif also renders a compact id + one-line-title index of EVERY active project lesson
- [ ] tests/test_handoff_propagation.py: a generated handoff for any phase contains every active L-NN id (25/25); pre-fix it contains 5. cz_next_phase_context output contains L-24, L-52 and L-62 — the three lessons this entire release rests on, all currently never surfaced
- [ ] cz_audit emits the source-vs-release line ('source X is ahead of the latest release Y'); a fixture-mocked test asserts an unreachable registry yields 'unverified', never a pass (no live network in the suite); cz_list_findings reports H-19 resolved
- [ ] Four claim-pin tests (L-62), each demonstrated RED when its counterpart is mutated in a scratch copy: (a) every path TRUST.md describes as gitignored appears in init.py's _ensure_gitignore calls; (b) the excerpt cap named in TRUST.md equals learn._excerpt's default; (c) no doc asserts release-check is CI-enforced while `grep -rn release-check .github/` is empty; (d) the CLAUDE.md and AGENTS.md marker blocks equal the template render, extended to the ANCESTOR-staleness case which is live today
- [ ] `grep -n '600 char' docs/TRUST.md` returns nothing — TRUST.md says excerpts are 'up to 600 characters' but learn.py:211 caps at 160; 600 is the candidate filter at learn.py:121. A doc-vs-code mismatch shipped inside the honesty repair itself
- [ ] refresh_claude_stanza ships as a second D-042 tier-1 action (modernize.py:112-144 has no stanza action, so older installs rot); a test asserts the rendered block equals the template byte-for-byte
- [ ] cz_list_corrections returns the corrections of the decision-corrections section with resolvable targets; the D-063 amendment text is applied to L-53, which rides in every handoff and was never updated
- [ ] cz_list_findings shows H-16 still open and docs/RELEASING.md carries it as a named residual against gate G4, per D-012's own rule, since pyproject.toml:15 claims Production/Stable
- [ ] INVARIANT-10 is ratified here ONLY if its wording survived the release unchanged; otherwise it stays a decision
- [ ] `clauderize release-check` exits 0 for 1.14.0 BEFORE the tag; after publish, git ls-remote --tags, the GitHub Releases API and the PyPI JSON API all report 1.14.0
- [ ] Full 9-cell matrix green plus the new fresh-clone leg and quickstart.yml's MCP identity assertion
- [ ] POST-MORTEM.md written; the superseded gameplan 2026-07-24-workflow-critique-repairs-... is closed with its own post-mortem explaining supersession
