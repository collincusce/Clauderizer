# alpha-to-beta-evidence — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-10

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Beta gates on the record; ship 0.9.0 | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | CI proves the OS matrix; win32 leg executed for real | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-1-HANDOFF.md |
| 2 | G6: native-leg cold-start evidence | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Foreign-repo live loop: node profile end-to-end | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Beta-evidence consolidation; scope gameplans B and C | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
b1_release_0_9_0: 0.9.0 SHIPPED 2026-06-10, zero incidents — the first release where the ritual ran unsupervised and nothing went wrong (0.7.0 and 0.8.0 both had same-day incidents). Chain: backlog pushed first (origin/main = 980c451, 4 commits, workflow-free range so WSL-side git sufficed); staged commit bdac36b (version bump pyproject+__version__, CHANGELOG Unreleased→0.9.0, B1–B6 beta gates + evidence table added to docs/RELEASING.md per D-012); editable venv reinstalled (H-03 dist-info); init idempotent (0 files, 20 kept); doctor exit 0 with executor-leg identity clauderizer 0.9.0 BEFORE tagging; release-check exit 0 BEFORE tagging (all 8 checks: clean tree, push ordering, four registries unclaimed fresh, publish gate marker); tag v0.9.0 on the pushed commit; Release https://github.com/collincusce/Clauderizer/releases/tag/v0.9.0; publish run 27311516131 green in 33s (tag==source gate PASSED on a legitimate release — first green passage; Trusted Publishing accepted); fresh-resolve verified `uvx --refresh --from clauderizer clauderize --version` → clauderizer 0.9.0. Ritual step 8 (restart-validate) satisfied by prior evidence: this repo's wiring unchanged by the release (shape C live + restart-validated this morning, transcript e4573a6d). Suite 255 green post-bump. B1 row filled in the RELEASING.md evidence table. Note for Phase 1: publish.yml run annotations warn Node 20 actions deprecated (forced to Node 24 from 2026-06-16) — checkout@v4/upload-artifact@v4/setup-uv@v5 need version bumps when test.yml is reworked.
```

### Phase 2 Outputs

```
b3_g6_native_evidence: G6 closed 2026-06-10 with legs named per D-010 (RELEASING.md G6 note + B3 row). Native half: scratch repo /tmp/cz-g6-njHLN0/repo — plain clauderize init (20 files, exit 0, real spawn tests incl. the hostile-cwd digest probe), doctor 14/14 exit 0, registered command verbatim "/bin/sh <repo>/.clauderizer/hook.sh", then the STRING traversed from hostile cwd /tmp: /bin/sh -c → exit 0 + in-band digest "[Clauderizer] No active gameplan…"; identity via the same leg → clauderizer 0.9.0; /bin/bash -c variant → digest too (L-10 pairing honored). Windows-wsl half: already proven by the harness-truth restart (transcript e4573a6d, shape C verbatim). NAMED RESIDUAL: the native evidence traverses the executor leg faithfully but is not a literal Claude Code cold start on a native-OS machine (this host's harness is Windows) — recorded in the G6 note; close it opportunistically if/when a native-harness machine runs one. Evidence script: /tmp/g6_native.sh (transcript in session log).
```

### Phase 1 Outputs

```
b2_ci_matrix: B2 satisfied: CI run 27312987722 (commit eef7136) — 9/9 cells green, ubuntu/macos/windows-latest × py3.11–3.13, fail-fast off; win32 cmd-twin tests run by construction on windows cells (win32_only mark cannot skip there). TWO CI cycles total. The decisive work happened BEFORE CI via a local native-Windows suite run (py 3.13 venv in %TEMP%, installed from the UNC repo): found and fixed 3 product bugs — (1) _resolve_invocation missed win32 .exe console scripts; (2) text-mode write corrupted the cmd wrapper template \r\n→\r\r\n AND broke init idempotency on win32 (fix: exact_newlines byte writes for wrappers — hook.sh stays \n even when written from win32, the distro sh chokes on \r); (3) doctor freshness read_text normalized CRLF so a healthy win32 wrapper never matched its render (fix: byte read) — plus a doctor gap: windows-wsl registrations carry the distro-side path spelling the host can't stat (fix: repo-local wrapper fallback) — plus cp1252-blind bare read_text() in 5 test files (utf-8 pinned) and the round-2 fix: py3.11 shutil.which does not PATHEXT-resolve explicit paths (test now registers the real .exe). 4 new live cmd-wrapper execution tests (digest passthrough, dead-engine breadcrumb, unreachable-repo breadcrumb, hostile-cwd cd /d anchor). .gitattributes eol=lf (autocrlf runners would corrupt fixture round-trips). Action bumps for Node 24 in both workflows (checkout@v5, setup-uv@v6, upload/download-artifact@v5). Suite 255 → 259 at this phase (261 after Phase 3). Workflow pushes used the Windows git + GCM lane as documented.
```

### Phase 3 Outputs

```
b4_node_loop: B4 satisfied: full loop live on a node scratch repo (/tmp/cz-node2-UwytlN/app, preserved), adopter-realistic (scaffold committed). Transcript: auto-detect → profile=node; init 20 files exit 0 (spawn-test = hostile-cwd digest probe, live); cz_create_gameplan via `clauderize ops` → 2026-06-10-loop-proof; cz_preflight via ops → 7/7 PASS with REAL `npm test` (baseline 2 captured by the mocha regex "(\d+) passing") and REAL `npm run build`; 7-op tracked-writes batch (transition in_progress, decision, lesson, output, phase summary, transition complete, write_handoff) all ok — files rendered valid (handoff + phase table spot-checked); digest direct AND via /bin/sh -c "<registered>" from hostile cwd, both showing "Gameplan 2026-06-10-loop-proof: all 1 phase(s) COMPLETE 🎉 (profile=node), Baseline: 2 tests"; GUARD-FIRES: broken test.js → preflight passed:false (tests ✗ + clean_tree ✗, both honest), git-restore → 7/7 PASS again; doctor exit 0. Zero hand-edits of tracked docs. DEFECT SURFACED AND FIXED: a fresh `git init` repo with zero commits was misdiagnosed by branch_base/branch_creation as "not a git repo" (rev-parse --abbrev-ref HEAD fails on unborn HEAD) — now discriminated via rev-parse --is-inside-work-tree into an honest "no commits yet (unborn branch)" skip; round-1 loop transcript (uncommitted scaffold → clean_tree fail) was the discovery vector; 2 regression tests added (suite 259 → 261); verified live in round 2 step [9].
```

### Phase 4 Outputs

```
b1_b4_simultaneous_hold: All four gates verified simultaneously on commit 89c94e3 (2026-06-10): B1 ✅ 0.9.0 live on PyPI resolving fresh; B2 ✅ CI 9/9 twice consecutively (runs 27312987722 and 27313238924 — the second including the unborn-branch regression tests); B3 ✅ G6 closed with named legs + named residual; B4 ✅ node loop with guard-fires both directions. Fresh doctor exit 0 (16 checks incl. the executor-leg verdict at identity 0.9.0). Fresh release-check exit 2 — the EXPECTED post-release state: all four registries correctly report 0.9.0 claimed (by today's release), push-ordering and publish-gate rows green; the guard refusing version reuse is the designed behavior, recorded here so nobody reads it as drift. Suite 261 green. RELEASING.md evidence table complete for B1–B4 with dated artifacts. DEFERRED (not a straggler to force): the MCP-server staleness nudge belongs engine-side (cz_status comparing engine source mtime vs server start), an ordinary feature for a future gameplan, recorded in the GP-C scope below. SCOPE FOR GAMEPLAN B (stranger-readiness, B5): quickstart walked in a CLEAN environment (fresh container/VM, uvx path); upgrade story (0.8→0.9 re-init semantics + doctor template-predates nudge); uninstall story; trust-model doc (what init writes into .claude/settings.json + hook execution boundary + the always-exit-0 contract); troubleshooting runbook distilled from HARDENING + friction logs; README positioning pass (the "git-native working memory" wedge + beta language). SCOPE FOR GAMEPLAN C (beta-flip, B6): burn down anything GP-B surfaces; classifier line 15 flip 3→4; version by fresh sweep (0.10.0 expected); ship via the ritual; the MCP-staleness nudge if it fits.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
