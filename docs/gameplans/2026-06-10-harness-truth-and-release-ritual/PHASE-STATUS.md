# harness-truth-and-release-ritual — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-10

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Executor matrix: prove the wiring shape | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | hosts.py emits the immune shape; restart-validate H-08 | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Doctor traverses the consumer leg (D-010) | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Release preflight ritual (O3) and 1.0 readiness gates (O4) | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Memory guardrails as config: O1 ACTIVE_LESSONS_WARN, O2 consolidation trigger | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
executor_matrix_verdict: Final matrix (artifact: scripts/wiring_matrix.ps1; criterion: digest in-band on stdout, hostile cwd C:\, anchored executable target): CUR gitbash=FAIL(127 MSYS-mangled /bin/sh)/cmd=PASS/ps=PASS — the H-08 control fires exactly where predicted; A `sh -c 'exec …'` PASS/PASS/PASS (needs target +x; quote surface noted); B `MSYS_NO_PATHCONV=1` gitbash-only (env-prefix is bash syntax: cmd 'not recognized', PS CommandNotFound); C `//bin/sh //<path>` PASS/PASS/PASS and re-confirmed against the production wrapper path under Git Bash. ELIGIBLE: A and C. CHOSEN: C per D2 (zero quote surface, byte-minimal delta, no +x dependency); A is the documented fallback. Cell timings 112–172ms. Re-run: powershell -ExecutionPolicy Bypass -File scripts\wiring_matrix.ps1 -HookPath <target> (defaults: real wrapper, hostile cwd).
hook_cwd_dependence: H-09 (open, medium): clauderizer-hook resolves its repo from cwd and the generated wrapper does not anchor — empty/exit-0 silence whenever the executor cwd is not the repo. Proven: engine with --cd /tmp → 0 bytes; cmd.exe structurally drops UNC cwd (falls back C:\Windows) → round-1 matrix cmd column 100% empty on both streams (file-redirect verified); anchored control (/tmp/hook-anchored.sh: cd <repo> before delegating) emits the 758-byte digest from C:\ under all three executors. Phase 1 implements the anchor in the wrapper template; Phase 2 makes init/doctor probes spawn from a non-repo cwd so anchoring is what they verify.
```

### Phase 1 Outputs

```
wiring_regenerated: Registered SessionStart command (verbatim, settings.json): wsl.exe -d ubuntu //bin/sh //home/ccusce/Clauderizer/.clauderizer/hook.sh — shape C live. Wrapper anchored (cd '/home/ccusce/Clauderizer' with repo-unreachable breadcrumb). hosts.py: hook_wrapper_invocation emits //-paths for windows-wsl only (native unchanged); render_hook_wrapper(root=...) optional param; REPO_BREADCRUMB_PREFIX constant; doctor freshness = full content compare vs fresh render, with a template-predates nudge (exit 3) distinct from engine-moved. Suite 215 → 220 (5 new: anchor render sh+cmd, foreign-cwd execution, unreachable-repo breadcrumb, doctor old-template nudge). init: 2 files changed then idempotent (0 on re-run). Doctor 16/16 exit 0 through the new wiring. Matrix vs production wiring from hostile cwd: C = PASS/PASS/PASS (gitbash/cmd/ps); A also all-pass (fallback confirmed); CUR fails only gitbash (control). H-09 resolved (anchor live with evidence). H-08 resolved 2026-06-10 via restart validation — see h08_restart_validation.
h08_restart_validation: Real harness cold start 2026-06-10: transcript e4573a6d-1f63-4ab9-b563-5477011b4255.jsonl, hook_success attachment for SessionStart:startup, ts=2026-06-10T16:53:26.319Z — command = registered shape C verbatim (wsl.exe -d ubuntu //bin/sh //home/ccusce/Clauderizer/.clauderizer/hook.sh), exitCode=0, durationMs=388, stderr empty, stdout = full [Clauderizer] digest, which appeared in session context and drove this close-out. Contrast: prior shape's exit-127 hook_non_blocking_error attachments in transcripts 228fb4d0 and 6b9a162f (same harness leg). G1 of docs/RELEASING.md ("H-08 resolved with restart evidence") is satisfied; H-08 and H-09 both carry dated resolutions in docs/HARDENING.md.
```

### Phase 3 Outputs

```
release_check_shipped: clauderize release-check live (src/clauderizer/release_check.py + CLI wiring): doctor-style three-state checks — clean tree; push-then-release (origin/<branch> == HEAD via ls-remote, names the UI-tags-REMOTE-head mechanism); four-registry sweep for v{pyproject version} (local tag, remote tag via ls-remote --tags, GitHub Release via gh seam, PyPI index queried DIRECTLY via urllib — never uvx cache); publish gate marker ('Release tag must match pyproject version') required when publish.yml exists. Exit 0 ok / 2 any fail / 3 unverifiable-but-no-fail (honest middle, D-010). 12 new tests against real git repos with a local bare origin, network seams monkeypatched: every skew individually proven to fire (unpushed commit, dirty tree, local-only tag, REMOTE-ONLY tag — the v0.7.0/v0.8.0 shape, claimed Release, claimed PyPI, gateless workflow, unverifiable→exit-3) plus a marker-drift pin against the real publish.yml. LIVE-FIRE on this repo (dirty tree, 0.8.0 released): exit 2 with clean-tree ✗ and all four registries ✗ claimed, push-ordering ✓, gate ✓ — the H-07 incident shape detected on real data. Suite 220 → 232.
one_dot_zero_gates: docs/RELEASING.md (O4): the mechanical release ritual (push first → release-check exit 0 → tag the pushed commit → push tag → cut Release → watch the tag==source gate → uvx --refresh verify → restart-validate wiring releases) plus seven 1.0 readiness gates: G1 harness leg truthful (H-08 restart evidence + executor matrix), G2 probes traverse the consumer leg incl. non-repo cwd (D-010, Phase 2), G3 release ritual mechanical (release-check exit 0 precondition, gate pinned by tests), G4 no open high findings with dated evidence on resolutions, G5 structural invariants green (L-01/L-04/L-05/L-06), G6 cold-start UX proven on native AND windows-wsl scratch repos, G7 docs match behavior. Credential caveat recorded in the ritual: workflow-file pushes need Windows git + GCM on this host.
```

### Phase 4 Outputs

```
memory_guardrails_config: [memory] config table shipped (O1+O2): active_lessons_warn (default 12 — the pre-O1 constant honored) and project_lessons_warn (default 20). Config dataclass + load (int() raises on garbage per L-04 — never a silent default for a malformed value) + to_toml emission + merge_missing pass-through (ints carry values post-load; `or` would clobber a deliberate 0 = warn-always). _memory_gauge reads thresholds from config (module constants remain the config=None fallback); NEW project-lessons nudge past the line: names docs/LESSONS.md as riding in every handoff across gameplans, prescribes cz_obsolete_lesson L-NN + re-promote a synthesis; both warnings coexist joined with ' | ' on the single ⚠ Memory digest line. Tests: config round-trip with custom values, legacy configs (no [memory]) load defaults, configured thresholds honored incl. 0, both-warnings coexistence, silent-when-under. Suite 232 → 234. This repo's config.toml regenerated via init (1 file, idempotent after); live digest verified silent at 9/20 project lessons.
```

### Phase 2 Outputs

```
consumer_leg_probes: hosts.py gained the D-010 surface: harness_executor() (Git Bash at /mnt/c/Program Files/Git/bin/bash.exe from WSL, C:\Program Files\Git\bin\bash.exe on win32 — None when absent); non_repo_cwd() (system temp dir); hook_digest_probe(argv, cwd=) (NO-args spawn judged in-band: digest prefix [Clauderizer] = ok, either breadcrumb = fail, exit-0 silence = fail naming H-09 — because --version answers BEFORE repo discovery and is therefore anchor-blind); verify_hook_wiring(argv, session_host) (native delegates to verify_wiring; windows-wsl runs direct round-trip first, then bash.exe -c "<registered string> --version" + bash.exe -c "<registered string>" both from non_repo_cwd(), requiring identity == __version__ AND in-band digest; executor unreachable → unverifiable naming Git Bash, with any end-to-end claim stripped). spawn_probe grew cwd= param. Doctor's hook verdict now calls verify_hook_wiring (cli.py); green reads "verified end-to-end via harness executor (git-bash → wsl.exe → sh) from a non-repo cwd — identity clauderizer 0.8.0, digest in-band". init step-11 spawn-test switched from --version to hook_digest_probe from non_repo_cwd().
guard_fires_evidence: Suite 234 → 255 (21 new in tests/test_consumer_leg.py: 17 hermetic — executor resolution per platform, digest-probe judgment matrix incl. both breadcrumbs and the H-09 silent shape, verify_hook_wiring composition matrix incl. no-end-to-end-claim-when-untraversed — plus 4 LIVE skip-guarded on Git Bash interop). The live guard-fires pair ran for real: test_live_old_shape_guard_fires_where_direct_probe_stays_green proves the pre-Phase-1 shape (bare /-paths) FAILS through bash.exe while hosts.verify_wiring (the old direct probe) stays GREEN on it — the false green retired by D-010, demonstrated in one test; test_live_unanchored_wrapper_fails_digest_probe proves identity passes but digest fails when the H-09 anchor is stripped. Design smoke before any code (lesson #4): /tmp/p2probe.sh from WSL — new shape via bash.exe → clauderizer 0.8.0 exit 0; old shape → exit 127 with the exact H-08 stderr (C:/Program Files/Git/usr/bin/sh: No such file or directory); digest from /tmp → full digest. Real-repo verification: doctor 16/16 exit 0 with the new leg-naming verdict; clauderize init idempotent (0 files, 20 kept) with the digest spawn-test live. test_doctor_reports_unverifiable_never_green updated (harness_executor patched to None — on dev boxes the real bash.exe would otherwise turn the hermetic no-interop scenario green).
```

## Corrections Log

### C-01 — Phase 1

**Phase**: 1
**What gameplan said**: Phase dependency chain is strictly sequential: Phase 2 depends on 1, Phase 3 on 2, Phase 4 on 3.
**What was actually correct**: Execution order was 0 → 1 (code work) → 3 → 4 → 1 (restart validation, this session, now complete); Phase 2 has not started. Phases 3 and 4 completed 2026-06-10 while Phase 1 sat IN PROGRESS awaiting its cold-start gate.
**Why**: Phase 1's final exit criterion (digest arriving in a REAL harness cold start) is only observable from a future session — the session that ships the wiring cannot witness its own next startup. Rather than idle, prior sessions executed 3 and 4, which despite the declared chain have no technical dependency on Phase 2's doctor work: release-check and the memory-config guardrails touch disjoint code from the probe leg.
**Lesson**: Declare phase dependencies by technical need, not narrative order: a restart-gated exit criterion guarantees the shipping session cannot close its own phase, so genuinely independent later phases will (and should) run while it waits. What made the split safe was the outputs registry carrying an explicit REMAINING EXIT CRITERION line — the next session resumed and closed the phase cold from that line alone.
