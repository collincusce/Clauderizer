# Post-Mortem — 2026-07-23-dreaming-loop (1.13.0)

> Closed: 2026-07-24 · 6/6 phases complete · suite 948 → 1000 collected, exit 0
> · release-check exit 0 (tag/Release/PyPI deliberately left for the user after
> the CI matrix greens 81a99f4)

## What shipped

The dreaming loop (D-058/D-059): `cz_add_dream` (per-exchange experiential
notes → local PII-linted append-only journal) → `cz_dream` (triage-debt +
ripeness gate, canonical-tokenizer clustering, bounded deterministic bundle) →
`cz_dream_propose` / `cz_handle_dream_proposal` (durable content-hash
proposals, crash-safe watermark, the D-052 producer-agnostic triage — one
pending count, one digest line) → accepted writes become tracked memory.
Plus: the capture ritual in the stanza + procedure 1.8.0, quiet-when-empty
digest gauge, pre-compact nudge, `cz_loop_step` dream state, the
clauderizer-dream skill (S-09), CROSS-HOST §5b, and the L-21 doc sweep that
found README 14 tools stale and made the seam executable.

## What worked

- **Dogfooding as the eval.** The loop ran end-to-end on its own build's notes
  in the shipping session: 12 organic notes → ripe dream → 4 staged → 3
  accepted into tracked memory (lesson #1 → promoted L-62, correction C-01, a
  CROSS-HOST fact) → loop at rest. The A-002 comparator answered the founding
  question with data: deterministic slices over a 4.6M-token transcript corpus
  yielded 31 failure-shaped candidates and **zero unique durable memories**
  (detector-C's zero correction-recall reconfirmed D-023); telemetry-only
  `cz_curate` proposed only lesson-hygiene obsoletions. Three signals, three
  disjoint classes — notes own the semantic layer at ~1,051 tok per accepted
  proposal.
- **The loop caught its own defects mid-eval** — the strongest possible
  validation: phase-less notes exposed the dead `ready` fallback, and the
  gauge reading "11 awaiting" right after consuming 11 exposed the
  gauge/watermark seam. Both fixed + test-pinned within the phase.
- **Substrate reuse kept every phase session-sized**: telemetry's appender/
  reader, `proposal_id`, the `@_locked` mutation shape, the producer-agnostic
  ledger (absorbed producer #2 with ZERO changes to dismiss/defer), central
  stamping, and quiet-when-empty additions that left every golden byte-stable
  (L-41 applied three times: gauge, digest line, loop_step block).
- **Recorded memory steered the design before a line was written**: the
  planning fan-out surfaced INVARIANT-06 (killing hook capture), D-052 (the
  landing zone), D-023 (the comparator's prior), D-027 (bundle bounds) — the
  final architecture is close to forced by the corpus, which is what the
  corpus is for.

## What didn't, with root causes

- **Phase 4 ran without its `in_progress` transition** (C-01). Momentum after
  the P3 commit went straight to recon+code; nothing enforces the ritual.
  Consequence chain: two phase-less notes → which exposed that the engine's
  fallback matched the computed "ready" status tables never store (dead
  branch since Phase 0). Root causes: unenforced ritual step + a default
  written against assumed rather than actual table vocabulary.
- **The Phase-1 gauge counted the whole journal**; the Phase-3 watermark never
  revisited it — the exact L-55 class ("the phase that adds a concept is not
  the phase that owns the earlier surface"). Caught live, not by tests,
  because no test crossed the two phases' features until the dogfood did.
- **README's MCP surface was 14 tools stale on arrival** — the 1.12.0 listing
  contract never landed there (L-21's known class). Sweeps find instances;
  only the new pin test kills the class (promoted as L-62).
- **The stale-editable-install guard fired at release prep** (installed
  metadata 1.12.0 vs source 1.13.0 → 5 test failures). Expected class, guard
  worked as designed; cost: one `pip install -e .`.
- **Self-inflicted test friction**: the seed helper asserted every note
  appends, then re-seeded identical content (the dedupe correctly refused);
  and a bare `open()` tripped the io-discipline test. Both caught in-suite
  within minutes — the discipline tests earn their keep.

## Procedure improvements

1. **Executable doc seams by default** (L-62, dream-sourced): any doc that
   enumerates a code-owned surface gets a pin test in the same change that
   creates the enumeration.
2. **Consider adding the dream note + the in_progress transition to the
   do-phase skill's explicit step list** — C-01 happened because the
   transition lives in habit, not in the skill's numbered steps; capture
   survived only because nudges exist. (Skill-template change; follow-on.)
3. **Queue unification follow-on** (O-02, resolved as scheduled): `cz_curate`
   and `cz_mine_failures` should join the id+ledger triage — P3 proved the
   merge pattern; curate's 6 obsoletion proposals currently re-derive with no
   dismiss memory.
4. **When a phase adds a concept that an earlier phase's surface summarizes
   (gauge/counter/digest), grep for that surface in the same change** — the
   L-55 corollary this gameplan paid for twice.

## Open threads

- **Tag → GitHub Release → PyPI for 1.13.0**: user's call after the CI matrix
  greens the pushed 81a99f4+ (L-51: never tag on one OS's green).
- **The running MCP server predates the new ops** — the dream tools worked via
  `clauderize ops` all session (validating the headless leg); interactive
  `cz_add_dream`/`cz_dream` over MCP need the next session's fresh server.
- **The standing-curator loop takes the focus from here**: dream state rides
  its `cz_loop_step`; first iteration inherits curate's 6 obsoletion
  proposals and the 24>20 project-lesson redistill pressure (which L-62 just
  nudged to 25).
- **Kind vocabulary**: five of six kinds validated organically; `drift` only
  via probe — watch it in real use (O-03 resolution).
- **Audit affirmations**: clean-environment verification deferred to the CI
  matrix run (editable refresh done locally); consumers re-audited (digest
  golden, hooks, REGISTRY/CLI/op_schema, uninstall's rm -rf covers the new
  local files, doc sweep); claims verified live (CROSS-HOST hot-reload marked
  with its verification date); shipped artifacts test-asserted (skill,
  gitignore lines, README pin).
