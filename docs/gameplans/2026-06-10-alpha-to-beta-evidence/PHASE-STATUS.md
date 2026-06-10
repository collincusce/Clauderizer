# alpha-to-beta-evidence — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-10

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Beta gates on the record; ship 0.9.0 | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | CI proves the OS matrix; win32 leg executed for real | 🟡 IN PROGRESS | 2026-06-10 | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | G6: native-leg cold-start evidence | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Foreign-repo live loop: node profile end-to-end | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Beta-evidence consolidation; scope gameplans B and C | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
b1_release_0_9_0: 0.9.0 SHIPPED 2026-06-10, zero incidents — the first release where the ritual ran unsupervised and nothing went wrong (0.7.0 and 0.8.0 both had same-day incidents). Chain: backlog pushed first (origin/main = 980c451, 4 commits, workflow-free range so WSL-side git sufficed); staged commit bdac36b (version bump pyproject+__version__, CHANGELOG Unreleased→0.9.0, B1–B6 beta gates + evidence table added to docs/RELEASING.md per D-012); editable venv reinstalled (H-03 dist-info); init idempotent (0 files, 20 kept); doctor exit 0 with executor-leg identity clauderizer 0.9.0 BEFORE tagging; release-check exit 0 BEFORE tagging (all 8 checks: clean tree, push ordering, four registries unclaimed fresh, publish gate marker); tag v0.9.0 on the pushed commit; Release https://github.com/collincusce/Clauderizer/releases/tag/v0.9.0; publish run 27311516131 green in 33s (tag==source gate PASSED on a legitimate release — first green passage; Trusted Publishing accepted); fresh-resolve verified `uvx --refresh --from clauderizer clauderize --version` → clauderizer 0.9.0. Ritual step 8 (restart-validate) satisfied by prior evidence: this repo's wiring unchanged by the release (shape C live + restart-validated this morning, transcript e4573a6d). Suite 255 green post-bump. B1 row filled in the RELEASING.md evidence table. Note for Phase 1: publish.yml run annotations warn Node 20 actions deprecated (forced to Node 24 from 2026-06-16) — checkout@v4/upload-artifact@v4/setup-uv@v5 need version bumps when test.yml is reworked.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
