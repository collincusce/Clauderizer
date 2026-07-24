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
| 4 | The dreaming ritual: skill, loop integration & headless recipe | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Dogfood, eval & ship 1.13.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

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

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
