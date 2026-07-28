# Enforcement Ladder

> What actually enforces each discipline this system asks of an agent — and the
> honest answer when the enforcement is only text. Shipped by the 2.0 alpha
> (Phase 4, D-076). `tests/test_enforcement_ladder.py` parses the ladder table's
> row name + tier column only, so format churn cannot weaken the pin.

A discipline with no executable check is a hope, not a practice (D-069). This
ladder names, for every discipline, which of FOUR tiers carries it. Each tier is
defined against recorded law — restated verbatim so this document can never
drift into being the vector for the enforcement-creep it exists to prevent:

- **hard-NORMALIZE** — the engine normalizes at the writer/mutations chokepoint.
  D-066, verbatim: "Blessed write ops NORMALIZE caller-supplied strings at the
  render boundary so the rendered document is valid for external readers (L-52
  clause 2) and so no allocated id is ever unreachable … PREFER NEUTRALIZE OVER
  REJECT, so no write is ever lost (INVARIANT-03) and no mutation gains a hard
  block (INVARIANT-05)." Hard never means reject or block; it means the write
  lands well-formed.
- **preflight-blocking** — D-024's deliberate carve-out: pre-flight is the one
  gate that is "meant to block", blocking by default, and "listing it in
  `preflight_advisory` downgrades the fail to a warning" per check, per repo.
  Pre-flight is NOT one of INVARIANT-05's discipline gates; flattening it into
  "advisory" would misstate its real semantics.
- **advisory** — INVARIANT-05, verbatim: "Discipline gates (clarify/open-items,
  exit-criteria, analyze-against-invariants) are advisory and judgment-based:
  they surface findings in tool results for the agent to act on, and MUST NOT
  hard-block a mutation or phase transition, nor introduce an enable/disable
  config flag. The engine surfaces candidates; the agent decides."
- **instructions-floor** — carried by the stanza/AGENTS.md text and the skills,
  with no executable check. This tier is real, not a euphemism for "nothing":
  jcode's guardrail discipline binds its agents the same way (AGENTS.md orders
  "run the guardrails before pushing") and its commit history shows agents
  restructuring code "rather than rebaselining" — documentary binding with
  measured obedience. Where a floor discipline has a D-069 detector, the row
  names it; where it has none, the row says so.

## Capabilities are derived host facts — never config flags

Which tiers can even reach a session is a fact about the HOST, derived at
runtime from `session._HOOK_HOSTS` (hosts whose session hook injects the
digest), `session._PROMPT_HOSTS` (hosts surfacing MCP prompts as slash
commands), and the per-host capability matrix in `docs/CROSS-HOST.md` §3.
There is no enable/disable flag for any of it (INVARIANT-05), and no
capability line in the digest — the negative-capability disclosure lives on
the instructions floor itself (the stanza, README, TRUST.md), because a
standing digest line about missing hooks would violate INVARIANT-08/D-027
minimalism; D-076 records that defense so a later session does not "complete"
the idea by adding one. On a hook-less host, every instructions-floor row
below is carried by the stanza text plus the MCP server-side bootstrap
(the first tool result's one-time status note) alone.

## The ladder

| Discipline | Tier | Mechanism (citations) |
|---|---|---|
| Write-boundary well-formedness (headings, pipes, newlines, markup, empty titles) | hard-NORMALIZE | shared normalizer at the five mutations render sites; tool-call-markup guard; D-066, L-52, H-02 |
| Honest terminal vocabulary (complete / failed / deferred; aliases map, no fourth token) | hard-NORMALIZE | cz_transition_phase status normalization; D-070 P0; tests/test_honest_closeout.py |
| Deferred-reason sanitization (table-safe, engine token leads) | hard-NORMALIZE | _sanitize_reason at the tracker writer; D-070 P0 |
| Epistemics: unknown never reads as zero (probe failures lower the verdict and say so) | hard-NORMALIZE | conditions.py arm coverage + summary wording; D-070 P0; tests/test_epistemics_unknown_never_zero.py |
| Survivor ancestry on consolidate/promote (engine-written, survives text override) | hard-NORMALIZE | _inline_trailer at the lesson writers; D-074 |
| Dream-note PII constraint | hard-NORMALIZE | write-time PII lint at the journal boundary (rejects secret/PII shapes with guidance — the D-058 boundary; the append-only journal cannot be redacted after the fact) |
| Clean tree / branch base / tests green before phase work | preflight-blocking | cz_preflight checks 1–3; D-024; config.preflight_advisory downgrades per check |
| Cascade hygiene (no pending cascade reports) | preflight-blocking | cascade_hygiene check; D-024 |
| Handoff presence (every implied phase handoff exists) | preflight-blocking | handoff_presence check; D-024 |
| Clarify / open-items gate | advisory | cz_add_open_item / cz_transition_phase surfacing; INVARIANT-05 |
| Exit-criteria gate | advisory | cz_check_exit_criterion + transition surfacing; INVARIANT-05 |
| Analyze-against-invariants gate | advisory | cz_analyze; D-016; INVARIANT-05 |
| Laundering advisory (completing with unchecked criteria) | advisory | cz_transition_phase result advisory; D-070 P0 |
| Memory-lag reconciliation (tracker vs repo evidence) | advisory | memory_lag detector in digest + preflight warn; H-22/D-069 |
| Stranded-state heal-on-proof | advisory | rituals/stranded.py, POSIX-gated liveness; D-070 P1 |
| Interrupted-session backstop (work landed, closing writes never ran) | advisory | rituals/interrupted.py with the liveness gate (C-01); D-070 P1 |
| Refusal-journal consumption | advisory | cz_mine_failures refusal source + corpus_health count; D-069/O-03 |
| Per-call live-state stamp (cz_state) | advisory | state_stamp.py, env-armed dormant; INVARIANT-10; D-064 gates any default |
| Budget wind-down | advisory | rituals/budgets.py, declared-dormant; D-072; D-064 gates any default |
| Seen-vs-open receipts split (never-engaged foregrounded) | advisory | receipts.py + digest split, labeling only, drop nothing; D-073/D-068 |
| Merge-base suppression honesty (suppressed_count named; all_proposals kept) | advisory | curate/loop_step/mine ledger filtering; D-074; D-013 display-never-authority |
| Correction write-back (a correction reaches the lesson it contradicts) | advisory | possibly_contradicted detector on cz_add_correction + procedure/skill text; D-074/D-069 |
| Merge-integrity of canonical docs (lost updates, committed conflict markers) | advisory | rituals/merge_audit.py via cz_audit/cz_preflight/cz_status; git evidence only; squash-blind stated |
| Blessed writes only — never hand-edit tracked logs or frontmatter | instructions-floor | stanza + CLAUDE.md rules; drift detectors: cz_critique, reindex reconciliation (D-065) — no write-time detector exists |
| Session-start memory load (cz_status when no digest appeared) | instructions-floor | stanza first paragraph; hook hosts get it mechanically; hook-less hosts rely on this text + the P7 bootstrap |
| Ending protocol (outputs, summary, status transitions, handoff at close) | instructions-floor | do-phase skill + procedure; detectors: memory-lag + interrupted backstop (advisory rows above) |
| Dream capture per substantive exchange | instructions-floor | stanza + procedure v1.8; nudged by the quiet-when-empty gauge; deliberately unenforced (D-015/INVARIANT-05) |
| Correction-discipline text (obsolete superseded lessons rather than appending beside them) | instructions-floor | GAMEPLAN-PROCEDURE v1.11 + close-gameplan/record skills; paired detector is the advisory row above |
| Fleet hub-and-spoke law (all tracked writes through the hub) | instructions-floor | clauderizer-fleet skill briefing contract; D-071; no engine detector — collisions surface via LockHeld counts |
| Fleet assignment ownership (respect cz_assign partitions) | advisory | cz_assignments surfacing; D-071; hub judgment resolves conflicts |
| Memory-gap recording (record the decision/lesson when memory had nothing on a probe) | advisory | cz_analyze result gap advisory + text-free telemetry gap events + corpus_health read-only count; never a digest line (INVARIANT-08); D-075 |
| Reinforce-instead-of-duplicate (strengthen the surviving lesson rather than appending a twin) | advisory | cz_add_lesson near-duplicate advisory offers the third verb; cz_reinforce_lesson is the blessed write; strength is curator EVIDENCE, never authority (D-013/D-063); INVARIANT-09 canonical detector; D-075 |
| Negative-space close-outs (declare "What I did not check") | instructions-floor | GAMEPLAN-PROCEDURE v1.12 Ending Protocol + phase-summary guidance; fleet briefing contract (hub sends back reports lacking it — Phase 7); engine detector explicitly deferred-unenforced (L-68 clause 5) — none exists; D-075 |
| jcode-host wiring claims (verify by live capability probe before claiming wired) | instructions-floor | D-075 vetting conditions (research-jcode-vetting.json) + the phase-5 matrix row; L-25/L-66 capability-not-presence; no engine detector — the matrix row records verified or honestly unverifiable |

The four rows above landed with Phase 8 (D-075/A-002 — gap detection, reinforce
verb, negative-space close-outs, jcode-host wiring), per the lands-second rule
this table inherits from A-001: Phase 4 shipped the ladder first, so the
later-landing phase carried its own rows.

## Engine guarantees (by construction — not agent disciplines)

These bind the ENGINE, not the agent, so they carry no tier: the advisory
inter-process write lock around every mutation (H-05); hook handlers read-only
and exit-0 (INVARIANT-06); status injection at most once per session across all
tiers (INVARIANT-08); append-only memory — the engine never deletes
(INVARIANT-03); one canonical tokenizer and one near-duplicate threshold
(INVARIANT-09); the five cz_state bounds (INVARIANT-10); and cz_dream's
refusal to assemble while staged proposals await triage — a read-assembly
precondition, not a mutation block (D-059/A-001).
