---
name: clauderizer-onboard
description: Seed a freshly clauderized project's memory from its existing documentation. Use right after `clauderize init` on a repo that already has a README or design docs, when init or `clauderize upgrade` suggests onboarding, or when VISION/ARCHITECTURE are still scaffold placeholders.
---

# Onboard an existing project

The engine detects; you read and seed. Nothing is seeded automatically.

1. Run `cz_onboard`. It returns the Clauderizer docs still sitting as scaffold
   placeholders (`unseeded`), the repo's existing documentation that likely
   holds project knowledge (`candidates` — paths only), and how many docs are
   already seeded.
2. Read each candidate file. As you read, keep three sorting bins: *what this
   project is* (vision material), *how it is built* (architecture material),
   and *rules and choices already in force* (memory entries).
3. Seed the prose docs directly — `docs/VISION.md`, `docs/ARCHITECTURE.md`, and
   their siblings are living documents, not append-only logs. Replace the
   placeholder stanzas with real prose distilled from what you read; do not
   paste whole source files in.
4. Record the structure through the blessed writes, with provenance:
   - Each real subsystem/feature/external service → `cz_upsert_entity` (add
     `depends_on` edges where the sources describe them).
   - Each decision the project already made ("we chose Postgres because…") →
     `cz_add_decision`, citing the source file in `evidence`.
   - Each standing rule ("never expose X", "all writes go through Y") →
     `cz_add_invariant` with `introduced_by`/`evidence` naming the source.
5. Re-run `cz_onboard` — seeded docs drop out of `unseeded`. Anything you
   deliberately leave unseeded, say so to the user rather than leaving it
   silent.
6. Finish with `cz_status` so the digest reflects the seeded corpus.

Judgment notes: prefer distillation over transcription (memory is compact by
design); when a source contradicts itself or reality, record the contradiction
as an open item instead of guessing; the original files stay where they are —
Clauderizer memory points at them, it does not replace them.
