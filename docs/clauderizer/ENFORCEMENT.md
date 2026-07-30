# Enforcement Ladder

> What actually enforces each discipline this system asks of an agent — and the
> honest answer when the enforcement is only text. Seeded by `clauderize init`
> (engine 2.0); the tiers and rows describe the ENGINE's mechanisms, and the
> D-/L-/H- citations are the engine project's recorded law (upstream
> provenance, not ids in this repo).

A discipline with no executable check is a hope, not a practice. This ladder
names, for every discipline, which of FOUR tiers carries it. Each tier is
defined against the engine's recorded law — restated verbatim so this document
can never drift into being the vector for the enforcement-creep it exists to
prevent:

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
  documentary binding with measured obedience is a working enforcement class.
  Where a floor discipline has a detector, the row names it; where it has
  none, the row says so.

## Capabilities are derived host facts — never config flags

Which tiers can even reach a session is a fact about the HOST, derived at
runtime from the engine's hook-host and prompt-host sets and the per-host
capability matrix in the engine's CROSS-HOST reference. There is no
enable/disable flag for any of it (INVARIANT-05), and no capability line in
the digest — the negative-capability disclosure lives on the instructions
floor itself (the stanza, the engine README/TRUST docs), because a standing
digest line about missing hooks would violate the engine's injection
minimalism (INVARIANT-08/D-027). On a hook-less host, every
instructions-floor row below is carried by the stanza text plus the MCP
server-side bootstrap (the first tool result's one-time status note) alone.

## The ladder

| Discipline | Tier | Mechanism (citations) |
|---|---|---|
| Write-boundary well-formedness (headings, pipes, newlines, markup, empty titles) | hard-NORMALIZE | shared normalizer at the mutations render sites; tool-call-markup guard with write-time removal echo; D-066, L-52, H-02, H-29 |
| Honest terminal vocabulary (complete / failed / deferred; aliases map, no fourth token) | hard-NORMALIZE | cz_transition_phase status normalization |
| Deferred-reason sanitization (table-safe, engine token leads) | hard-NORMALIZE | _sanitize_reason at the tracker writer |
| Epistemics: unknown never reads as zero (probe failures lower the verdict and say so) | hard-NORMALIZE | preflight/conditions arm coverage + summary wording |
| Survivor ancestry on consolidate/promote (engine-written, survives text override) | hard-NORMALIZE | _inline_trailer at the lesson writers; D-074 |
| Dream-note PII constraint | hard-NORMALIZE | write-time PII lint at the journal boundary (rejects secret/PII shapes with guidance; the append-only journal cannot be redacted after the fact) |
| Version stamps never ratchet backward (a stale engine refuses the downward stamp) | hard-NORMALIZE | modernize report+apply monotonicity guard; H-30 |
| Clean tree / branch base / tests green before phase work | preflight-blocking | cz_preflight checks 1–3; D-024; config.preflight_advisory downgrades per check |
| Cascade hygiene (no pending cascade reports) | preflight-blocking | cascade_hygiene check; D-024 |
| Handoff presence (every implied phase handoff exists) | preflight-blocking | handoff_presence check; D-024 |
| Clarify / open-items gate | advisory | cz_add_open_item / cz_transition_phase surfacing; INVARIANT-05 |
| Exit-criteria gate | advisory | cz_check_exit_criterion + transition surfacing; INVARIANT-05 |
| Analyze-against-invariants gate | advisory | cz_analyze; INVARIANT-05 |
| Laundering advisory (completing with unchecked criteria) | advisory | cz_transition_phase result advisory |
| Memory-lag reconciliation (tracker vs repo evidence) | advisory | memory_lag detector in digest + preflight warn |
| Stranded-state heal-on-proof | advisory | stranded detector, POSIX-gated liveness; zero-false-positive matrix bar |
| Interrupted-session backstop (work landed, closing writes never ran) | advisory | interrupted detector with the liveness gate |
| Refusal-journal consumption | advisory | cz_mine_failures refusal source + corpus_health count |
| Per-call live-state stamp (cz_state) | advisory | state_stamp, env-armed dormant (`CLAUDERIZER_STATE_STAMP=1`); INVARIANT-10 |
| Budget wind-down | advisory | budgets, declared-dormant until budgets are declared |
| Seen-vs-open receipts split (never-engaged foregrounded) | advisory | receipts + digest split, labeling only, drop nothing; D-073/D-068 |
| Merge-base suppression honesty (suppressed_count named; all_proposals kept) | advisory | curate/loop_step/mine ledger filtering; D-074; D-013 display-never-authority |
| Correction write-back (a correction reaches the lesson it contradicts) | advisory | possibly_contradicted detector on cz_add_correction + procedure/skill text |
| Merge-integrity of canonical docs (lost updates, committed conflict markers) | advisory | merge_audit via cz_audit/cz_preflight/cz_status; git evidence only; squash-blind stated |
| Memory-gap recording (record the decision/lesson when memory had nothing on a probe) | advisory | cz_analyze result gap advisory + text-free telemetry gap events + corpus_health read-only count; never a digest line (INVARIANT-08); D-075 |
| Reinforce-instead-of-duplicate (strengthen the surviving lesson rather than appending a twin) | advisory | cz_add_lesson near-duplicate advisory offers the third verb; cz_reinforce_lesson is the blessed write; strength is curator EVIDENCE, never authority (D-013/D-063); INVARIANT-09 canonical detector; D-075 |
| Fleet assignment ownership (respect cz_assign partitions) | advisory | cz_assignments surfacing; D-071; hub judgment resolves conflicts |
| Blessed writes only — never hand-edit tracked logs or frontmatter | instructions-floor | stanza + CLAUDE.md rules; drift detectors: cz_critique, reindex reconciliation — no write-time detector exists |
| Session-start memory load (cz_status when no digest appeared) | instructions-floor | stanza first paragraph; hook hosts get it mechanically; hook-less hosts rely on this text + the server bootstrap |
| Ending protocol (outputs, summary, status transitions, handoff at close) | instructions-floor | do-phase skill + procedure; detectors: memory-lag + interrupted backstop (advisory rows above) |
| Dream capture per substantive exchange | instructions-floor | stanza + procedure; deliberately unenforced (INVARIANT-05) |
| Correction-discipline text (obsolete superseded lessons rather than appending beside them) | instructions-floor | procedure + close-gameplan/record skills; paired detector is the advisory row above |
| Fleet hub-and-spoke law (all tracked writes through the hub) | instructions-floor | clauderizer-fleet skill briefing contract; D-071; no engine detector — collisions surface via LockHeld counts |
| Negative-space close-outs (declare "What I did not check") | instructions-floor | procedure Ending Protocol + phase-summary guidance; fleet briefing contract (hub sends back reports lacking it); engine detector explicitly deferred-unenforced — none exists; D-075 |

## Engine guarantees (by construction — not agent disciplines)

These bind the ENGINE, not the agent, so they carry no tier: the advisory
inter-process write lock around every mutation; hook handlers read-only and
exit-0 (INVARIANT-06); status injection at most once per session across all
tiers (INVARIANT-08); append-only memory — the engine never deletes
(INVARIANT-03); one canonical tokenizer and one near-duplicate threshold
(INVARIANT-09); the five cz_state bounds (INVARIANT-10); and cz_dream's
refusal to assemble while staged proposals await triage — a read-assembly
precondition, not a mutation block.
