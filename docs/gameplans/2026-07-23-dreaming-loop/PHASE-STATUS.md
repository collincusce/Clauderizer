# dreaming-loop — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-24

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Dream journal substrate & the blessed dream write | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Capture ritual & read-only nudges | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-1-HANDOFF.md |
| 2 | cz_dream — ripeness-gated dream assembly | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Durable dream proposals & unified triage | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-3-HANDOFF.md |
| 4 | The dreaming ritual: skill, loop integration & headless recipe | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Dogfood, eval & ship 1.13.0 | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-5-HANDOFF.md |
| 6 | The schedule plea — beg, explain, instruct at session start | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-6-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
dream write op: cz_add_dream (REGISTRY writes=True, contract-stamped, appended to TOOL_NAMES; defaults resolve active gameplan + current phase via status_bundle._phase_rows)
journal substrate: .clauderizer/dreams.jsonl via src/clauderizer/dreams.py — KINDS=friction|gap|surprise|correction|drift|win, caps 600 chars/4 sentences/8 refs, PII deny (email, token shapes, absolute home paths), id=dream:&lt;12hex&gt; (proposals.proposal_id scheme, gameplan+phase+kind+ws-collapsed note)
tests: tests/test_dreams.py: 20 tests; suite 973 collected, exit 0 (pre-phase baseline 948 passing / 953 collected)
first dogfood notes: dream:165246aa0b42 (gap), dream:77237552fb08 (win) — captured headless via `.venv/bin/clauderize ops` with defaults resolving 2026-07-23-dreaming-loop phase 0
adjacent gap closed: scaffold/init.py now _ensure_gitignore's .clauderizer/telemetry.jsonl too (pre-existing: target repos could commit machine-local telemetry) alongside the new dreams.jsonl line
```

### Phase 1 Outputs

```
ritual surfaces: claude_stanza.md (source) + CLAUDE.md/AGENTS.md renders carry the cz_add_dream ritual bullet; GAMEPLAN-PROCEDURE.md v1.8.0 (+template synced, corpus stamped via clauderize upgrade) gains "## Dream Notes (experiential capture)"
nudges: digest "Dreams: N note(s) awaiting the dreamer." (quiet-when-empty — golden digest proven byte-identical, no update needed, L-41); pre_compact reminder now names cz_add_dream; live repo digest shows Dreams: 4
tests: 6 new (gauge both sides + single header, pre_compact mention, INVARIANT-06 read-only sweep with journal present, stanza/render seam pin, procedure version+section parity pin) — suite exit 0
```

### Phase 2 Outputs

```
cz_dream states: blocked_on_triage (pending ids) | not_ripe (unconsumed/ripeness) | ripe (bounded bundle). Constants in dreams.py: RIPENESS_NOTES=10, BUNDLE_MAX_CLUSTERS=8, CLUSTER_MAX_EXEMPLARS=3, CLUSTER_JACCARD=0.25 (canonical tokenizer, looser than lesson near-dup 0.40)
read-side store contracts: .clauderizer/proposals.dream.jsonl (records {id,...}; terminal marker {"id","handled"}; filtered through producer-agnostic proposals.filter_pending) + .clauderizer/dreams.watermark.json {"consumed":[note ids]} — Phase 3 owns the writers
tests: 9 new (not_ripe counts, ripe joins+weight, cap+named tail, guard both sides, handled-marker unblock, watermark shrink, determinism+read-only snapshot, tokenizer identity, registry/stamp) — suite exit 0 at 988 collected; live smoke: 6 notes -> not_ripe 6/10
```

### Phase 3 Outputs

```
triage ops: cz_dream_propose (stage batch + consume reviewed notes, crash-safe ordering, dreamprop:&lt;12hex&gt; content-hash dedupe, PII-linted details, empty-batch pure-consumption pass) + cz_handle_dream_proposal (terminal marker); dismiss/defer unchanged, docstrings generalized to both producers
digest merge: status_bundle merges dream pending into the single pending_proposals count (bundle.pending_dream_proposals tags the share); digest line gains "(N dream)" wording ONLY when dream>0 — modernize-only wording byte-unchanged, golden green; O-01 resolved with this shape
tests: 7 new (stage/consume/gate, kill-and-resume watermark ordering, nothing-durable pass, PII reject, handle+dismiss retire, digest merge single header, registry/stamp) — suite exit 0 at 995 collected
```

### Phase 4 Outputs

```
skill: clauderizer-dream (S-09): src/clauderizer/skills/clauderizer-dream/SKILL.md + installed .claude/skills copy + SKILLS.md registration — triage-first, then dream-if-ripe, one cz_dream_propose call with reviewed_note_ids, headless clauderize-ops variant documented in the skill itself
loop + docs: cz_loop_step gains a quiet-when-empty dream block (blocked_on_triage/ripe/not_ripe + summary suffix); CROSS-HOST §5b (capture is hook-independent by construction), TRUST .clauderizer row lists the three local dream artifacts + PII boundary; README MCP surface gains Dreaming group AND the missing 1.12.0 listing group — count corrected 48→66, now test-pinned
tests: 3 new (skill ships+registered, README surface pin against TOOL_NAMES, loop_step all four dream states) — suite exit 0 at 998 collected; live loop_step on this repo: dream ripe, 10 unconsumed
```

### Phase 5 Outputs

```
eval metrics: Capture: 12 notes / 5 phase contexts (2.0 per context, basis per A-003), avg 51 tok/note, journal ~1101 tok; kinds gap4/win4/correction1/friction1/surprise1/drift1. Dream: ripe at 11, bundle 2053 est_tokens, 8 clusters (+2 dropped, named). Yield: 4 staged -> 3 accepted / 1 dismissed => ~1051 tok per accepted (journal+bundle). Comparator arm B: 4,619k-tok raw transcript corpus; deterministic slices 31 candidates (6 in-window, all failure-shaped); unique durable accepted 0; overlap with notes arm = 1 (io-discipline, notes caught it first); detector-C corrections recall 0 (reconfirms D-023). Telemetry-only cz_curate baseline: 6 proposals, ALL never-surfaced-lesson obsoletions — zero class overlap with dream output (complementary, as D-058 hypothesized).
accepted dream writes: dreamprop:cded8bdd9f36 -> gameplan lesson #1 (executable doc seams); dreamprop:985caf2461f5 -> correction C-01 (missed in_progress transition + dead fallback); dreamprop:6554b79522d5 -> CROSS-HOST live-skill-reload note; dreamprop:6ee4455aa7d4 [transcript-arm] dismissed (rule already machine-enforced by test_io_discipline)
loop-caught defects: (1) cz_add_dream phase-default fallback matched computed "ready" which tables never store -> falls back to not_started now, test-pinned; (2) digest dream gauge counted the whole journal instead of unconsumed -> read "11 awaiting" right after a dream consumed 11; fixed to unconsumed_notes, test-pinned. Both found BY the loop's own artifacts during the eval.
release: 1.13.0: pyproject + __version__ + CHANGELOG single-sourced (stale editable install caught by the release guard, refreshed); suite exit 0 at 1000 collected (baseline 948); origin/main pushed (81a99f4); release-check exit 0 all gates green. Tag + GitHub Release + PyPI deliberately NOT cut — the irreversible step is the user's call (L-51 also wants the CI matrix green first).
```

### Phase 6 Outputs

```
the plea: 🌙 block inside the single digest, gated on (unconsumed > 0) AND (no schedule registered) AND (no pending dream proposals); plain-English what/why + review guarantee + three scheduling paths (Claude Code routine phrasing / cron + claude -p / run-now) + retirement instruction — key phrases test-pinned; live on this repo at close (2 notes waiting)
schedule registry: cz_register_dream_schedule (tool #67) -> gitignored .clauderizer/dreams.schedule.toml (TOML-escaped writer — the round-trip test caught unescaped quotes in the canonical claude -p command before ship); method=manual quiets as a D-052-style verdict; empty method clears and revives the plea; init ensures the gitignore line
tests: 7 new (plea renders with pinned phrases + single header, quiet on empty journal, register/retire/clear/revive, manual verdict keeps loop active, defers to triage line, op validation + stamp, init gitignore) — suite exit 0 at 1007 collected
```

## Corrections Log

### C-01 — Phase 4

**Phase**: 4
**What gameplan said**: clauderizer-do-phase ritual: cz_transition_phase to in_progress when starting a phase, so notes/telemetry attribute correctly
**What was actually correct**: Phase 4 ran start-to-finish without the in_progress transition; two dream notes landed with phase="" and the empty default exposed a dead engine fallback (phase tables store not_started - "ready" is a computed state the old fallback matched in vain)
**Why**: Mid-flight momentum: after committing P3 the session went straight to P4 recon and code; nothing enforced the transition. The engine fallback now matches real table vocabulary (fixed + tested), and the phase-less notes remain in the journal as honest evidence. Dream-sourced: dreamprop:985caf2461f5.
