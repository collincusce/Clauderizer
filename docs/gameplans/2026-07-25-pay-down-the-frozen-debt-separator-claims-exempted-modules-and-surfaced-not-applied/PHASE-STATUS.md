# pay down the frozen debt — separator claims, exempted modules, and surfaced-not-applied — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-26

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Triage the 24 separator-shaped assertions and make the class machine-rejectable | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Pay down the 32 exempted modules | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Close out and ship 1.14.3 with both ratchets tighter | ✅ COMPLETE | 2026-07-26 | 2026-07-26 | handoffs/PHASE-2-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
separator_shaped_assertions_total: 40 sites across 33 distinct `<file>::<literal>` keys (AST scan of src/, tests/, scripts/). The gameplan's "24" was a grep undercount — see C-01. Ratcheted both directions in tests/fixtures/separator_claims_baseline.json.
platform_claims_remaining: 0. All 40 are message assertions. The only real instance of the class (`assert "uv/archive-v0" in m["serving_path"]` plus its sibling `... in digest`) was already fixed by commit f9f8343 in 1.14.2's aftermath, so exit criterion 3 is satisfied vacuously and honestly.
guard_artifacts: tests/test_separator_claims.py (21 tests) + tests/fixtures/separator_claims_baseline.json (the written triage, machine-read by the ratchet). Detector = Rule A (RHS trailing identifier is path/dir/file/root/home, or a bare str() coercion; .as_posix() exempt) OR Rule B (literal is a fragment of an absolute-path literal in the same module).
suite_after_phase_0: 1253 passed, 7 skipped (was 1232 passed at preflight; +21 from tests/test_separator_claims.py). Zero failures.
```

### Phase 1 Outputs

```
modules_with_no_subsystem_doc: 32 → 0. The exemption list is empty; every top-level module under src/clauderizer/ now maps to a subsystem doc. test_no_new_module_escapes_the_seam is therefore at maximum tightness — any new module with no doc fails immediately (arm-tested with a scratch module).
new_subsystem_docs: 32 docs under docs/subsystems/, each a tracked entity created via cz_upsert_entity (frontmatter tool-owned, body hand-written): analyze, assets, bespoke-hosts, cli, config, contract, dreams, engine-identity, hook, hosts, hosttargets, kimidesktop, learn, listing, locking, mcp-probe, model, modernize, nesting, onboard, ops, paths, proposals, release-check, revision, session, skill-discovery, skills, telemetry, templates, tools-list, winhost.
undocumented_per_subsystem: All 32 new docs land at 0 undocumented public callables and are locked there by the both-directions ratchet — including ops, whose 73 public callables are all named by op family. The 6 pre-existing docs are unchanged (graph 13, markdown-core 19, mutations 9, profiles 1, rituals 34, scaffold 3); none improved, so no downward re-baseline was available for them. Baseline keys: 7 → 36.
suite_after_phase_1: 1311 passed, 7 skipped (was 1253). The +58 are the parametrized ratchet cases the 30 new baseline keys generate across test_undocumented_surface_never_grows and test_the_ratchet_tightens_when_docs_improve.
```

### Phase 2 Outputs

```
release_1_14_3: Published. Commit 8e2bece0d4627ebe03c41bef897c6771dc5cf1eb; annotated tag v1.14.3 (tag object 0917f3968, dereferences to 8e2bece); GitHub Release https://github.com/collincusce/Clauderizer/releases/tag/v1.14.3; publish run 30188603659 (build + publish both success). PyPI sha256 — wheel a258023571f40748df02b96fb43eefdd1683eb8080582528f4d8d0a3e36ea6e8, sdist 471feadbd833f475d233055788ac0c578d9819f7d35f178d8460ed06aad45fe5, read in-band from the publish log's attestation lines.
ci_at_job_granularity: 10/10 jobs success, 0 skipped, on 8e2bece BEFORE the tag existed. Tests run 30188517673: fresh-clone + test (ubuntu/macos/windows-latest × 3.11/3.12/3.13). Quickstart run 30188517665: stranger (doc-exact published install path). All three Windows cells green — the exact cells that shipped red in 0.14.0 and 1.14.2.
published_handshake_proof: serverInfo {'name': 'clauderizer', 'version': '1.14.3'} via `uvx --from 'clauderizer[mcp]==1.14.3' clauderizer-mcp`, with UV_CACHE_DIR pointed at a freshly deleted directory so a cached answer could not stand in for a real PyPI fetch (L-51), stdin HELD OPEN, non-repo cwd=/tmp, newline-delimited JSON-RPC. A pre-publish handshake against the locally built wheel in a fresh venv gave the same result.
open_findings_at_close: H-28 (MEDIUM) opened and carried with a dated acceptance (2026-07-26): release-check gates four registries and push ordering but never asks whether CI passed, so a workflow-level green hiding a skipped matrix cell would reach a tag. All 27 prior findings remain resolved. Recorded rather than suppressed — a register kept at zero by not writing down what was found is the write-only pathology D-069 exists to catch.
```

## Corrections Log

### C-01 — Phase 0

**Phase**: 0
**What gameplan said**: There are 24 separator-shaped assertions to triage, found by the pattern `assert "…/…" in …`, and the phase's job is to classify those 24 and fix the ones that are platform claims.
**What was actually correct**: The real class is 40 sites (33 distinct file+literal keys). The 24 was a grep artifact: a text pattern over `assert "…/…" in …` cannot see single-quoted literals, a second literal on the same line (test_init.py:269 has two), the non-first arms of an `or` chain (test_init.py:265/266/267 — grep saw only 265), `not in` forms (5 of them), or a literal whose line differs from the `assert` keyword's. An AST scan over src/, tests/ and scripts/ found all 40. Separately, ZERO of the 40 turned out to be platform claims — every one is a message assertion, because commit f9f8343 had already fixed the only real instance of the class in 1.14.2's aftermath. So the "fix every platform claim" criterion was satisfied vacuously, and the deliverable is the triage plus the guard, not a set of repairs.
**Why**: The phase was scoped by counting with the same kind of tool the defect class hides from. Grep counts text; the class is a property of syntax. Recording this matters because the count itself was load-bearing — the ratchet is pinned at the post-triage number, and pinning it at 24 would have left 16 sites permanently outside the guard while reading as complete.
**Lesson**: Never scope a defect class by a grep count when the class is defined syntactically — count it with the same instrument that will enforce it, or the ratchet inherits the blind spot.
