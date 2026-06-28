# Post-mortem — abstract-index-fast-retrieval

> Completed: 2026-06-28 · Outcome: KEPT and **SHIPPED as 1.3.0** (PR #16 merged → main; tag v1.3.0; GitHub Release latest; PyPI via Trusted Publishing — verified `uvx --refresh`→1.3.0; 9-cell CI green on the release commit)

## What shipped

A per-entry **abstract index** over the append-only corpus (decisions / invariants /
findings / lessons), an addressable **`cz_get`** single-entry fetch, and abstract
surfacing on `cz_analyze` — so a consumer learns an entry's id + one-line abstract
and resolves the full body on demand instead of loading whole corpus files. The
Phase-3 cost gain-gate **KEPT** it (the realized win is the retrieval path + the
already-banked focused-injection; the Phase-4 amendment honestly recorded that the
injected-surface win was already banked and delivered measurement + a regression
guard rather than a manufactured change).

## How it ended (phases 6–7, the resume)

The gameplan sat at phase 6/8 for three days while a separate initiative
(concurrent-multi-axis-gameplans → **1.2.0**) shipped on `main`. Resuming it:

1. **Reconciled first.** The branch was 8 behind `main`. Rather than fear a
   conflict-heavy merge, a dry-run showed the two feature sets are *orthogonal in
   code* — `git merge main` auto-merged everything except the one-line config focus
   pointer. Union suite went green (711) with **zero manual code fixes**.
2. **Phase 6 — upgrade path (D3).** init + reindex build/refresh the gitignored
   abstract index idempotently; `doctor` detects a missing/schema-stale cache
   read-only and advises `reindex` (the runtime self-heals). Proven on an isolated
   tempfile clone (L-29): doctor-flags-missing → reindex-builds (107 entries) →
   `cz_get` resolves a real id → `git status` clean → no-op re-run.
3. **Phase 7 — merge-ready.** 9-cell CI green on PR #16 (the windows legs verify the
   cache's `os.replace` atomicity, mtime granularity, and schema gate). Docs swept
   (README + `mcp-server.md` tool counts 41/31 → 42; entity refreshed). Per
   INVARIANT-07 the release (version bump / tag / PyPI) is **handed back to the
   user** — this branch is merge-ready, not released.

## Lessons

- **L-43 (promoted):** A parked feature branch that's behind a newer release
  reconciles cleanly when the two feature sets are *orthogonal in code* — dry-run
  the merge (`git merge --no-commit`) to measure the real conflict surface before
  assuming a rewrite; here it was a single config-pointer line. Complete parked work
  by reconciling with the release line **first**, then finishing the remaining phases
  against the real target.
- A "realize the win" phase whose win was already banked is closed honestly by
  measuring + guarding the property, not by manufacturing a change (Phase-4 A-001;
  reinforces L-32/L-38).

## Numbers

Union suite 711 passed / 4 skipped · tool surface 41 → 42 (`cz_get`) · 9-cell CI
green (PR #16) · abstract index 107 entries on this repo · schema_version 1.

## Shipped

**2026-06-28 as 1.3.0** (on the user's go, after an independent cross-session verification of the completed work). PR #16 merged → main (`eec9822`); release commit `4be4916`, tag `v1.3.0`, GitHub Release (latest, non-prerelease); `release-check` exit 0 (four-registry sweep); Publish-to-PyPI workflow green (build + publish, Trusted Publishing); verified PyPI `info.version`=1.3.0 + `uvx --refresh`→1.3.0. O-04 fully done: profile.lock reverted to bare `pytest` (H-17 makes it resolve), the fix branch is deleted, docs at 42 tools. Promoted L-44 (Jaccard-for-dedup vs count-for-relevance) and L-45 (a realize-the-win phase can be a measure+guard+amend no-op).
