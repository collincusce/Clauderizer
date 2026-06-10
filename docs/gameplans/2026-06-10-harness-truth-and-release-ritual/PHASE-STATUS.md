# harness-truth-and-release-ritual — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-10

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Executor matrix: prove the wiring shape | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | hosts.py emits the immune shape; restart-validate H-08 | 🟡 IN PROGRESS | 2026-06-10 | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Doctor traverses the consumer leg (D-010) | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Release preflight ritual (O3) and 1.0 readiness gates (O4) | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Memory guardrails as config: O1 ACTIVE_LESSONS_WARN, O2 consolidation trigger | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
executor_matrix_verdict: Final matrix (artifact: scripts/wiring_matrix.ps1; criterion: digest in-band on stdout, hostile cwd C:\, anchored executable target): CUR gitbash=FAIL(127 MSYS-mangled /bin/sh)/cmd=PASS/ps=PASS — the H-08 control fires exactly where predicted; A `sh -c 'exec …'` PASS/PASS/PASS (needs target +x; quote surface noted); B `MSYS_NO_PATHCONV=1` gitbash-only (env-prefix is bash syntax: cmd 'not recognized', PS CommandNotFound); C `//bin/sh //<path>` PASS/PASS/PASS and re-confirmed against the production wrapper path under Git Bash. ELIGIBLE: A and C. CHOSEN: C per D2 (zero quote surface, byte-minimal delta, no +x dependency); A is the documented fallback. Cell timings 112–172ms. Re-run: powershell -ExecutionPolicy Bypass -File scripts\wiring_matrix.ps1 -HookPath <target> (defaults: real wrapper, hostile cwd).
hook_cwd_dependence: H-09 (open, medium): clauderizer-hook resolves its repo from cwd and the generated wrapper does not anchor — empty/exit-0 silence whenever the executor cwd is not the repo. Proven: engine with --cd /tmp → 0 bytes; cmd.exe structurally drops UNC cwd (falls back C:\Windows) → round-1 matrix cmd column 100% empty on both streams (file-redirect verified); anchored control (/tmp/hook-anchored.sh: cd <repo> before delegating) emits the 758-byte digest from C:\ under all three executors. Phase 1 implements the anchor in the wrapper template; Phase 2 makes init/doctor probes spawn from a non-repo cwd so anchoring is what they verify.
```

### Phase 1 Outputs

```
wiring_regenerated: Registered SessionStart command (verbatim, settings.json): wsl.exe -d ubuntu //bin/sh //home/ccusce/Clauderizer/.clauderizer/hook.sh — shape C live. Wrapper anchored (cd '/home/ccusce/Clauderizer' with repo-unreachable breadcrumb). hosts.py: hook_wrapper_invocation emits //-paths for windows-wsl only (native unchanged); render_hook_wrapper(root=...) optional param; REPO_BREADCRUMB_PREFIX constant; doctor freshness = full content compare vs fresh render, with a template-predates nudge (exit 3) distinct from engine-moved. Suite 215 → 220 (5 new: anchor render sh+cmd, foreign-cwd execution, unreachable-repo breadcrumb, doctor old-template nudge). init: 2 files changed then idempotent (0 on re-run). Doctor 16/16 exit 0 through the new wiring. Matrix vs production wiring from hostile cwd: C = PASS/PASS/PASS (gitbash/cmd/ps); A also all-pass (fallback confirmed); CUR fails only gitbash (control). REMAINING EXIT CRITERION: real harness cold start shows the digest → resolve H-08 quoting the transcript hook_success attachment, then transition phase 1 complete. H-09 resolved this session (anchor live with evidence).
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
