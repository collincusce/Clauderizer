# evidence traversal 1.14.0 Gameplan

> Created: 2026-07-24
> Status: Planning
> Kind: driven
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

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

_(Auto-numbered O-NN via cz_add_open_item; close with cz_resolve_open_item. Blockers and cross-phase questions — unresolved ones surface in cz_status and when a phase is completed.)_

## Phase Breakdown

### Phase 0: Single-source the status parser and expose defaulted status

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] STANDING ORACLE (every phase): each new test is demonstrated RED on the pre-fix tree in this phase's output record. "Suite >= 1002" is a precondition, never a criterion
- [ ] `grep -rn 'Status\*\*' src/clauderizer/` shows exactly ONE compiled status pattern; tests/test_canonical_parsers.py asserts single definition + import identity and fails if a fourth copy appears (note: graph/abstract_index.py:74 ALREADY has the widened regex — this is three disagreeing copies, not two stale ones)
- [ ] `cz_list_findings` returns 20 findings: 17 resolved, 3 open (H-16, H-19, H-20), every entry with a non-null date. Pre-fix: 20 x active, date null
- [ ] pytest tests/test_render_roundtrip.py green for all 5 kinds (decision, invariant, finding, correction, lesson) written via the real mutation op and read via the real listing op; demonstrated red with the pre-fix regex
- [ ] `cz_corpus_health` emits parse_reconciliation with HARDENING.status_defaulted == 0; planting one unparseable Status line in a scratch copy makes it non-zero AND names the entry id. Expected shapes: DECISIONS 27 defaulted (D-001..D-027, by design), INVARIANTS 9 defaulted (by design), LESSONS uses **L-NN.** not ###
- [ ] status_source is returned as parsed|defaulted from analyze._entry_status and listing._entry_record — a defaulted status is distinguishable from a read one
- [ ] tests/fixtures/contract_corpus/driven-rich/ops/cz_list_findings.json regenerated; its git diff shows 20 statuses moving off active and dates populating; pytest tests/test_contract_corpus.py green
- [ ] `cz_critique` Coverage output contains H-16, H-19, H-20; `clauderize status` carries an open-findings line whose byte length on a zero-open-findings fixture is UNCHANGED from 1.13.0 (INVARIANT-08)
- [ ] The shared L-24 adversarial-input fixture (BOM, CRLF, unicode, empty, valid-non-dict JSON, truncated) exists in conftest and is consumed by Phase 5
- [ ] `git status --porcelain` empty; suite >= 1002 passed, 5 skipped

### Phase 1: One atomic symlink-refusing write path for tracked markdown

**Goal**: A failed or interrupted engine write can never truncate canonical memory, and no future writer can skip the symlink guard. Highest regression risk in the release.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] MANDATORY MITIGATION: tag pre-1.14.0-writepath exists BEFORE this phase starts (done: d52ef6e), and this phase's own cz_* bookkeeping runs on the PUBLISHED engine `uvx --from 'clauderizer[mcp]==1.13.0'` until these criteria pass — expect and accept the skew warning
- [ ] `grep -rn '\.write_text(' src/clauderizer/rituals/ src/clauderizer/graph/ | grep -v abstract_index.py` returns 0 lines; tests/test_write_path.py enforces it PATH-SHAPED (no write_text on a docs/ or .clauderizer/ path outside writer.py) and fails if handoff.py:566 is reverted. A literal allowlist is rejected — 30 write_text sites exist and an allowlist that size is a registry the next writer joins
- [ ] Under RLIMIT_FSIZE a failing write on a populated docs/DECISIONS.md raises and leaves the file byte-identical (sha256 compared); the same probe pre-fix destroys it (measured 92,027 -> 38,334 bytes)
- [ ] After that failed write AND after the full suite, `git status --porcelain` is empty — no *.tmp residue (.gitignore has no *.tmp rule and clean_tree is git status --porcelain)
- [ ] A planted leaf symlink at docs/gameplans/<gid>/handoffs/PHASE-N-HANDOFF.md makes cz_write_handoff return ok:false; same for cz_cascade's report path. Both return ok:true and write OUTSIDE the repo pre-fix
- [ ] pytest tests/test_handoff.py asserts all four _merge modes (created/merged/migrated/preserved) still reachable and _AGENT_SCAFFOLD still present on a fresh handoff — writer.upsert_marker_block is NOT a drop-in for handoff.py:566
- [ ] cz_revision increments exactly once per real change and zero times on a no-op; write_atomic itself does NOT bump (handoff.py:567, cascade.py:174, cascade.py:226 already call revision.bump_for — verified, correcting all three drafts)
- [ ] A 0644 doc's mode is unchanged after an atomic write (stat compared in-test, not via GNU-only shell flags) — sibling temp, never mkstemp whose 0600 would re-permission every tracked doc
- [ ] Full 9-cell test.yml matrix green INCLUDING windows-latest, with a Windows test holding the target open in a second handle (bounded retry around os.replace, mirroring locking.py:192-211)
- [ ] H-16 (symlinked PARENT directory) is NOT attempted here; HARDENING.md:211 records the deferral rationale and Phase 6 re-confirms it as a named residual

### Phase 2: Well-formedness at the write boundary

**Goal**: No caller string can forge an entry, absorb another entry's body, burn ids, escape a marker block, or produce an entry no reader can reach. Validation is not a discipline gate.
**Depends on**: 0, 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] RECORDED VERBATIM SO A REVIEWER CANNOT KILL THIS WITH THE WRONG INVARIANT: validation is NOT a discipline gate. INVARIANT-05 enumerates three gates (clarify/open-items, exit-criteria, analyze-against-invariants); dreams.validate (dreams.py:81) and D-058 are the shipped precedent that a blessed write may check its own input. Normalization runs BEFORE the diff, is deterministic, and NEVER rejects — no write is lost (INVARIANT-03), no mutation gains a hard block (INVARIANT-05)
- [ ] test_forged_heading: cz_add_decision(title='ok\n\n### D-900 — FAKE\n\n**Context**: forged') produces exactly ONE new heading, allocates D-<n+1> never D-901, the prior entry's body is byte-unchanged, and cz_list_decisions contains no D-900
- [ ] test_accident_fenced_heading: a context containing a fenced ```\n### D-999 — example\n``` leaves parse_entries count at exactly before+1 (no adversary required — this repo quotes markdown constantly)
- [ ] test_empty_title_reachable: cz_add_decision(title='') yields an id that cz_get retrieves and listing reports — no id is ever allocated to an unreachable entry
- [ ] test_lesson_number_not_burned: cz_add_lesson(text='the roll-up showed:\n**99.** a quoted line') advances the lesson number by exactly 1
- [ ] test_phase_table_contiguous: cz_add_phase(name='A|B') and name='A\nB' each produce a row whose cell count equals the header's, and cz_transition_phase on that phase succeeds. This is H-02, marked resolved and live
- [ ] test_marker_escape: a field rendered inside a handoff block containing the literal MARKER string (handoff.py:345) cannot escape the block — D-008's byte-for-byte guarantee holds
- [ ] test_invariant_multiline_contract pins mutations.py:274-276's first-line-is-title contract; writing byte-identical input twice returns changed:False with no cz_revision bump
- [ ] test_pii_advisory: decision bodies containing AKIA and sk_live_ each return a WARNING and still write. _PII_PATTERNS extended with the measured misses (sk_live_, ASIA[0-9A-Z]{16}, arn:aws:, AIza, npm_, pypi-, xapp-, password=) and applied at the mutations.py render boundary — D-058's own justification is that INVARIANT-03 makes retroactive redaction impossible, yet it ships only on the gitignored journal where deletion is trivial
- [ ] Escaping is scoped to LINE-LEADING #{1,6} and **N.** only — a mid-line '- **Status**:' was probed and does NOT fool resolve_finding; do not over-scope to any string. Backslash-escape renders identically in CommonMark so the human view is byte-equivalent
- [ ] Phase 0's round-trip harness green for all 5 kinds after normalization; DECISIONS.md:382, :467 and HARDENING.md:245 left byte-identical (append-only, they parse, cosmetic)

### Phase 3: Implement D-063 so the curator stops proposing from absent evidence

**Goal**: No checkout can be talked into obsoleting a corpus it never measured, and the loop that proposes deleting never-surfaced lessons is cut. Smallest phase, highest severity per line.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] IMPLEMENT, DO NOT RE-DECIDE: D-063 already states the never-surfaced obsoletion pressure is removed. It was never coded — telemetry.py:207 and telemetry.py:366-372 are both live. One change at the same two lines is simultaneously the zero-telemetry corpus-wipe fix, not two workstreams
- [ ] test_curator_no_telemetry: on a telemetry-free clone of this repo, cz_curate returns 0 proposals with action=='obsolete'. Pre-fix: 25. Demonstrated red pre-fix
- [ ] On the LIVE repo, cz_curate returns 0 obsolete proposals. Pre-fix: 6 (L-11, L-24, L-52, L-56, L-57, L-62) — three of which are outputs of the consolidation ritual and one promoted the day before
- [ ] Driving the shipped loop body on a telemetry-free clone leaves corpus_health()['active_project_lessons'] == 25. Pre-fix it converges to 0 and reports converged:True
- [ ] loop_step['summary'] on a telemetry-free checkout DIFFERS from the healthy-convergence string (asserted, not eyeballed) — the guard must not trade a false wipe for a false green
- [ ] status_bundle.py:118-127's 'Re-distill: cz_obsolete_lesson the superseded L-entries' sentence is gated on there being >=1 non-flag proposal — silencing the tool while leaving the surface that issues the instruction is a half-fix, and 25 active lessons is over threshold today so it fires on the very next fresh clone
- [ ] Where a never-surfaced framing survives (_lesson_signal, telemetry.py:207, feeding dreams.py:307), the wording with zero events reads UNMEASURED not unused, and suggested_op is None
- [ ] A fresh-clone CI leg is added to test.yml (L-23): clone to a temp dir with no .clauderizer/telemetry.jsonl, run cz_curate, assert zero obsoletion proposals
- [ ] tests/test_curator.py::test_consolidate_proposal_for_redundant_pair and tests/test_telemetry.py (never_surfaced == 3 with no telemetry) pass UNMODIFIED; corpus_health's never_surfaced COUNT stays untouched and honest
- [ ] `clauderize status` on a telemetry-free clone emits no cz_obsolete_lesson instruction, asserted by a string test
- [ ] `git diff` shows NO new key in .clauderizer/config.toml or Config — INVARIANT-05 and D-015 forbid an enable/disable flag
- [ ] The criteria_checked unparking EXPERIMENT is recorded as an open item, not actioned: it is still agent-declared so it does not clear D-063's externally-sourced bar as argued, but its variance is real. Pre-registered for 1.15.0 with a kill criterion

### Phase 4: Resolve H-20 with capability-not-presence engine identity

**Goal**: Doctor cannot report green on a .mcp.json that will not launch or that serves a different engine. Parallelizable with phases 1 through 3.
**Depends on**: Phase 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] THIS PHASE RESOLVES AN OPEN FINDING THE REPO ALREADY WROTE. HARDENING.md:250-260 records the defect, the recommended fix, and three regression tests. Criteria 2-4 below ARE H-20's own recorded regression tests — read them rather than re-deriving them (all three planning drafts re-derived this from scratch)
- [ ] wiring_contract_sweep FAILS for a host whose emitted config names a nonexistent command. Today it passes for all 11
- [ ] The gate completes an initialize handshake and receives serverInfo.name == 'clauderizer' for at least one emitted config
- [ ] A doc-pin test asserts docs/CROSS-HOST.md section 7's description matches the behavior that ships
- [ ] With a PATH-shadowed uvx stub that exits 1: default `clauderize doctor` prints no green check for MCP and does not print OK. Pre-fix: green MCP launchable + exit 0
- [ ] With a stub returning serverInfo {clauderizer, 0.1.0}: default doctor prints a version-skew warning and exits 3. Pre-fix with --deep: green on all 9 hosts, exit 0
- [ ] With the stub hanging: doctor reports 'unverifiable' and exits 3; grep for the failure glyph in that output is empty. Three-state contract per D-010/D-048/INVARIANT-05 — never a silent green, never a free pass for an awkward host (L-59)
- [ ] `if hid == hosttargets.CLAUDE_CODE: continue` at cli.py:347 is deleted — the host INVARIANT-07 makes a release blocker is the one host --deep never deepens
- [ ] The handshake is MEMOIZED on the (command, args) tuple: a counting stub asserts exactly ONE handshake subprocess on a fully-wired repo (all 9 auto-write emitters share the portable entry), wall time < 2.0s warm. Today 0.09s; --deep today is 9 identical handshakes at 9.09s
- [ ] tests/test_hosts.py:319 test_doctor_native_repo_stays_green passes UNMODIFIED
- [ ] init.py spawn-tests the PORTABLE_COMMAND it is about to write (not the locally-resolved console script at :229-244), as report.warnings.append never WiringRefused — an offline or proxied first run must still install
- [ ] quickstart.yml gains the MCP leg with a serverInfo.version == <tag under test> assertion (L-23; test.yml runs in-process and cannot see this — L-60)
- [ ] cz_resolve_finding H-20 with the shipped evidence; cz_list_findings reports H-20 resolved with a date

### Phase 5: Preserve foreign config and converge existing installs

**Goal**: No engine write destroys a file it did not author or crosses a repo boundary, and every already-initialized repo receives the policy fixes via a tier-1 upgrade action. Largest phase, first in the cut order.
**Depends on**: 0, 1.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

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
| 6.1 | _(describe)_ | _(est)_ |

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
