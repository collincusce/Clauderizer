# Post-Mortem — 2026-06-10-alpha-to-beta-evidence

> Closed: 2026-06-10, all five phases complete in one session (interleaved
> with CI waits). **Beta gates B1–B4 satisfied with dated artifacts**
> (docs/RELEASING.md evidence table): 0.9.0 shipped zero-incident; CI is a
> 9-cell OS matrix green twice consecutively; G6 closed with named legs;
> the full loop proven on a node repo via CLI parity. Suite 255 → 261.
> Lesson promoted: L-12 (local CI-cell preview). Gameplans B
> (stranger-readiness) and C (beta-flip) scoped in the outputs registry.

## What worked

1. **Beta-as-evidence (D-012) made the classifier flip executable.** Each
   gate named its artifact up front; the evidence table filled itself as
   phases closed; nothing was left to judgment at flip time. The honest-
   amendment escape hatch was used once (G6's named residual) instead of a
   silent pass.
2. **The local CI-cell preview was the gameplan's highest-leverage hour
   (→ L-12).** A native-Windows venv installed from the UNC repo found three
   real product bugs and a test-encoding class in one cycle, before CI ever
   ran. Nine cells went green on the second CI attempt; the only CI-found
   failure (py3.11 `shutil.which` skipping PATHEXT on explicit paths) was
   one no local 3.13 could produce.
3. **Independent phase dependencies (D2, applying L-11 at planning time)
   paid off in wall-clock.** Phases 2 and 3 executed entirely inside Phase
   1's CI wait windows; no idle time, no corrections, no dependency
   violations to record.
4. **The release ritual's second unsupervised run was boring again** (B1,
   zero incidents) — and Phase 4 deliberately re-ran `release-check`
   post-release to record its exit-2 as the *designed* refusal of version
   reuse, so future sessions don't misread the red.
5. **The foreign-repo loop earned its premise.** B4 existed to find what the
   home repo can't show, and it did: the unborn-branch misdiagnosis sits
   precisely on a brand-new adopter's first preflight. The discovery vector
   was itself instructive — round 1's "mistake" (uncommitted scaffold) was
   an adopter-realistic state the engine diagnosed misleadingly.
6. **`clauderize ops` held up as the real write surface** (L-05): a 7-op
   batch of blessed writes on a foreign repo, zero hand-edits, rendered
   markdown spot-checked valid.

## What didn't (root causes)

1. **"win32 support" was a guess until this gameplan.** Three latent product
   bugs (missed `.exe` console scripts, `\r\r\n` wrapper corruption that
   also broke init idempotency, doctor freshness never matching a healthy
   win32 wrapper) survived because every win32 test passed by monkeypatching
   `sys.platform` on Linux — platform claims that were never executed on the
   platform. D3 predicted exactly this; the matrix now makes the regression
   class impossible to reopen silently.
2. **The engine's IO discipline didn't extend to the tests.** Every `src/`
   read pins utf-8 (L-04 family), but 35 bare `read_text()` calls across five
   test files decoded engine-written utf-8 as cp1252 on Windows. The suite
   was lying about portability in both directions — wrongly green on Linux,
   wrongly red on Windows.
3. **Two exit codes, one diagnosis.** `rev-parse --abbrev-ref HEAD` fails
   identically outside a repo and on an unborn branch; preflight collapsed
   both into "not a git repo". Same family as L-10: a probe's failure mode
   must be discriminated before its verdict is worded.

## Friction log (host/tooling, with workarounds)

1. **The PowerShell→wsl.exe quote chain struck again** (a sed one-liner
   mangled into bash syntax errors). The script-file pattern
   (`Write` to `/tmp/x.sh` via UNC, then `wsl.exe /bin/sh /tmp/x.sh`)
   remains the only reliable lane; re-confirmed, already in memory.
4. **`gh run watch` output through `Select-Object -Last N` loses the job
   table** (annotations flood the tail). Reliable pattern: let watch block
   for the verdict, then query `gh run view <id> --json jobs --jq` for the
   per-cell table.
3. **Background-watch exit semantics are useful**: `gh run watch
   --exit-status` exits 1 on a failed run, so a backgrounded watch doubles
   as a CI notifier (the harness surfaces the task completion).
4. **`pip install` from the UNC repo path works** (both venv creation and
   `--force-reinstall --no-deps` refresh) — the native-Windows preview venv
   is cheap to maintain at `%TEMP%\czwin`.

## Procedure improvements (concrete)

1. **L-12 promoted**: foreign-CI-cell work starts with a local native venv
   preview, not a push.
2. **Platform claims require platform execution** — encoded permanently in
   the CI matrix + the `win32_only` live tests (which cannot skip on windows
   runners, so green cells prove execution).
3. **Candidate structural guard for GP-C**: a meta-test asserting no bare
   `read_text()`/`write_text()` (without `encoding=`) exists in `src/` or
   `tests/` — the cp1252 class, pinned the L-04 way.
4. **Post-release `release-check` exit 2 is the designed state** for a
   just-shipped version; recorded in this gameplan's outputs so the red is
   never read as drift. (The ritual doc already says "run BEFORE tagging".)

## Carried forward

- **Gameplan B — stranger-readiness (B5)**, scoped in
  `b1_b4_simultaneous_hold`: clean-environment quickstart walk, upgrade
  (0.8→0.9 re-init semantics) and uninstall stories, the trust-model doc
  (what init writes into `.claude/settings.json`; the always-exit-0 hook
  contract), troubleshooting runbook distilled from HARDENING + friction
  logs, README positioning pass ("git-native working memory" wedge).
- **Gameplan C — beta-flip (B6)**: burn-down of whatever B surfaces;
  classifier line 15 flip 3→4 shipped via the ritual at a fresh-swept
  version (0.10.0 expected); the MCP-server staleness nudge; the bare-IO
  meta-test (#3 above).
- **G6 residual**: a literal Claude Code cold start on a native-OS machine,
  whenever one exists to run it.

## Final state

0.9.0 live on PyPI and resolving fresh; CI badge backed by a 9-cell matrix
green twice; the win32 leg executed, not simulated; the loop proven beyond
the author's repo and language; B1–B4 ✅ with dated artifacts; suite 261;
doctor exit 0; findings tracker still all-resolved. Beta is now two
gameplans away, and both are scoped from evidence rather than ambition.
