# Post-Mortem — 2026-06-09-agent-autonomy

> Closed: 2026-06-10. Shipped as **0.8.0** (renumbered from 0.7.0), published
> to PyPI 2026-06-10 after a tag-retarget repair. Suite 211 → 215 green.
> H-01, H-04, H-05, H-06, H-07 resolved with evidence; L-05 closed; **H-08
> discovered and open** (accepted for pre-1.0 by user decision).

## What worked

1. **In-band identity over exit codes (D5) paid for itself twice.** It caught
   stale-pin wiring in the H-06 demo, and the restart-validation gate — "the
   digest must appear in a real cold start" — caught H-08 when every
   exit-code-based check in the system was green (doctor 16/16, manual run
   119ms/exit 0). That gate was the only thing standing between "all checks
   pass" and shipping wiring that is dead for every harness session on the
   reference host.
2. **The breadcrumb wrapper failed exactly at its documented boundary.**
   Lesson #6 predicted a repo-side wrapper cannot observe failures below
   itself; H-08 lives precisely there (the harness's shell mangles argv
   before `wsl.exe` spawns). The design was right; the boundary was real.
3. **Harness transcripts are a first-class diagnostic surface.** The client
   records per-hook attachments (`hook_non_blocking_error`: command,
   exitCode, stderr, durationMs). They turned "silent missing digest" into a
   byte-identical root cause in minutes and ruled out trust/timeout/stdin
   without speculation. Added to the runbook.
4. **Blessed-writes discipline held under fire.** H-08, both output upserts,
   the lesson consolidations and promotions all went through `cz_*` tools
   mid-incident — zero hand-edits, clean audit trail (`e207b63`, `892251e`).
5. **Close-out consolidation kept memory lean** (D-009): 10 active lessons →
   5 archived + 2 syntheses; 3 promotions (L-07 channel/layer design, L-08
   release registry discipline, L-09 false-green composition).

## What didn't (root causes)

1. **Two premature releases in one day** (v0.7.0 then v0.8.0; H-07, lesson
   #10 → L-08). Root cause: a GitHub-UI Release binds to the *remote* branch
   head while the staged work — including the publish gate itself — was
   local-only. A guard that isn't deployed guards nothing. The repair
   (delete Release, retarget tag to the pushed release commit, recreate
   Release from preserved notes) re-fired `release:published`; the gate then
   passed and PyPI accepted a real 0.8.0 (run 27256861511, 35s).
2. **H-08: no check ever traversed the consumer's actual execution leg.**
   Doctor's "verified end-to-end via wsl.exe round-trip" spawns `wsl.exe`
   directly; the harness interposes **Git Bash**, whose MSYS2 POSIX→Windows
   argument conversion rewrites `/bin/sh` → `C:/Program Files/Git/usr/bin/sh`
   (exit 127 inside Ubuntu's default-shell wrapper, below our wrapper).
   Probe context ≠ consumer context (L-09). Verified MSYS-immune shapes,
   pending cmd.exe/PowerShell cross-validation: `wsl.exe -d ubuntu sh -c
   'exec /home/…/hook.sh'`; `MSYS_NO_PATHCONV=1` prefix; (untested)
   `//bin/sh` double-slash form.
3. **Stale cold-start briefing via UNC.** The next-session handoff read
   through `\\wsl.localhost` was served pre-update content by the 9P cache;
   `git show HEAD:<file>` disagreed and was right. The session initially
   briefed itself on a superseded plan. Mitigation: trust `git show` over a
   UNC `Read` when they can disagree; recorded in session memory.
4. **Credential-plane fragmentation stalled the repair push.** The WSL-side
   git credential and the gh CLI token both lack `workflow` scope (rejected:
   the range included `publish.yml`); the SSH key is passphrase-locked with
   no live agent. Windows git + GCM (full grant, works on the UNC repo with
   `-c safe.directory=*`) was the only viable lane. Not an engine defect,
   but the release flow must know its lane up front.

## Procedure improvements (concrete)

1. **O3 — release preflight ritual** (carried): before any tag or Release
   exists, assert `git ls-remote origin refs/heads/main` equals the staged
   release commit, then sweep all four registries (L-08): local tags, remote
   tags, Releases API, PyPI directly.
2. **H-08 wiring fix** (next gameplan): `hosts.py` emits an
   MSYS-conversion-immune SessionStart command, validated under all three
   executors (Git Bash, cmd.exe, PowerShell); add a shell-matrix wiring test.
3. **Doctor honesty for the harness leg**: probe hook launchability through
   Git Bash when present (the harness's real executor on Windows hosts), or
   weaken the check's claim wording — a probe must not say "end-to-end" for
   a leg it does not traverse (L-09).
4. **Runbook**: transcript hook attachments first; `BatchMode=yes` for any
   non-interactive ssh probe (turns hangs into definitive failures);
   workflow-file pushes go via Windows git + GCM.

## Carried forward (next gameplan candidates)

- O1: `ACTIVE_LESSONS_WARN` as config.
- O2: project-lesson consolidation trigger past ~20 (now 9).
- O3: release preflight ritual (above).
- O4: 1.0 readiness gates.
- H-08 wiring fix + doctor harness-leg probe (above).

## Final state

0.8.0 live on PyPI and resolving fresh (`uvx --refresh --from clauderizer
clauderize --version` → 0.8.0). Tag, Release, and origin/main aligned.
24 MCP tools, 16 doctor checks, 215 tests green, write lock serializing,
CLI parity via `clauderize ops`. The recording machinery now works — and
fails — out loud, with one known silent spot (H-08) named, reproduced,
and scheduled.
