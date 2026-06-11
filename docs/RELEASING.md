# Releasing Clauderizer

> The ritual is mechanical on purpose: two releases (v0.7.0, v0.8.0) were
> double-claimed in one day by cutting a GitHub Release while the staged
> work — including the publish gate itself — was local-only (H-07, L-08,
> lesson #10). Nothing here is advisory; the check is the ritual.

## The release ritual (O3, D-011)

1. **Stage the source**: bump `pyproject.toml` + `__version__`, refresh the
   editable install (`pip install -e .` — dist-info skew is H-03), update
   CHANGELOG, sync the installed procedure copy if the template changed.
2. **Push first**: `git push origin main`. The GitHub UI tags the REMOTE
   branch head; until origin holds the release commit, every guard you wrote
   is unpushed by construction. *(Pushes touching `.github/workflows/` need a
   credential with `workflow` scope — on this host that is Windows git + GCM,
   not the WSL-side credential or `gh`.)*
3. **Run the check**: `clauderize release-check` — exit 0 required.
   - ✗ anything → stop, fix, re-run. Do not tag.
   - `?` (unverifiable) → verify that registry manually before proceeding;
     an unswept registry is exactly how versions get double-claimed.
4. **Tag the pushed commit**: `git tag v<version>` on the commit origin
   already has; `git push origin v<version>`.
5. **Cut the GitHub Release** for that tag (notes from CHANGELOG).
   Publishing fires on `release: published` — the bare tag publishes nothing.
6. **Watch the gate**: the "Publish to PyPI" run must pass the
   tag==source step and upload via Trusted Publishing.
7. **Verify fresh**: `uvx --refresh --from clauderizer clauderize --version`
   → the new version. `uvx` by name answers from cache — `--refresh` or
   nothing.
8. **Restart-validate** when the release touched wiring: a real harness cold
   start must show the `[Clauderizer]` digest (in-band evidence, L-09) —
   doctor green is not a substitute (H-08).

## 1.0 readiness gates (O4)

1.0 means strangers can trust a cold install. Every gate is a check that
exists (or is named here as owed), not a vibe:

- **G1 — Harness leg truthful**: H-08 resolved with restart evidence (digest
  in a real session's context), and the wiring shape validated across the
  executor matrix (`scripts/wiring_matrix.ps1`: Git Bash, cmd.exe,
  PowerShell, hostile cwd).
- **G2 — Probes traverse the consumer's leg** (D-010): doctor/init verify
  hook launchability through the harness's executor (or report honest
  unverifiability), and from a non-repo cwd (H-09 regression).
- **G3 — Release ritual mechanical**: `release-check` exit 0 is a hard
  precondition for tagging; the publish gate (tag==source) present in
  publish.yml; both pinned by tests.
- **G4 — No open high findings** in `docs/HARDENING.md`; every resolved
  finding carries dated evidence.
- **G5 — Suite green with the structural invariants**: markdown round-trip
  idempotency (L-01), external render-validity (L-06), every engine-written
  file round-trips through its own parser (L-04), CLI/MCP write parity
  (L-05).
- **G6 — Cold-start UX proven on both host shapes**: `native` and
  `windows-wsl:<distro>` installs each demonstrate init → digest → doctor 0
  on a scratch repo.
  *Satisfied 2026-06-10 (legs named per D-010):* **windows-wsl** — a real
  harness cold start on the reference host delivered the digest through
  Git Bash → wsl.exe → sh (transcript `e4573a6d` hook_success, shape C
  verbatim, exit 0). **native** — scratch repo `/tmp/cz-g6-*/repo`: init
  (real hostile-cwd digest spawn-test) → doctor 14/14 exit 0 → the
  registered string traversed via `/bin/sh -c` AND `/bin/bash -c` from a
  hostile cwd → in-band digest + identity `clauderizer 0.9.0`.
  *Named residual:* the native evidence traverses the executor leg
  faithfully but is not a literal Claude Code cold start on a native-OS
  machine (this host's harness is Windows); a native-harness restart
  observation remains open until one runs on such a machine.
- **G7 — Docs match behavior**: README quickstarts, GAMEPLAN-PROCEDURE, and
  this file describe what the code actually does (no aspirational steps).

When all seven hold, `release-check` + this list is the 1.0 sign-off.

## Beta gates (D-012)

Beta (`Development Status :: 4 - Beta`) is an **evidence claim, not a feature
claim**: every current proof runs on one machine, one repo, one profile until
the gates below say otherwise. The classifier line in `pyproject.toml` may
only change in a release whose staged commit satisfies B1–B5 — and that
release IS B6. A gate that cannot be met honestly is amended here with a
named residual (the exit-3 pattern applied to the lifecycle), never waved
through.

- **B1 — Backlog shipped**: 0.9.0 live on PyPI and resolving fresh
  (`uvx --refresh`), ritual followed with `release-check` exit 0 *before*
  tagging.
- **B2 — CI proves the OS matrix**: suite green on ubuntu, macos, AND
  windows runners × py3.11–3.13, with the win32 cmd wrapper EXECUTED on a
  real windows runner (not platform-monkeypatched).
- **B3 — G6 closed or honestly amended**: native-leg cold-start evidence
  with the traversed leg named (D-010 wording discipline).
- **B4 — Foreign-repo loop**: the full loop (init → gameplan → preflight →
  tracked writes → transition → handoff → digest) live on a non-python repo,
  zero hand-edits, driven through CLI parity (`clauderize ops`).
- **B5 — Stranger path**: quickstart verified end-to-end in a clean
  environment; upgrade, uninstall, and the trust model (what init writes
  into `.claude/settings.json` and why) documented.
- **B6 — The flip ships via the ritual**: zero open findings and doctor
  exit 0 at flip time; flip version chosen by a fresh four-registry sweep
  (L-08), never assumed.

| Gate | Status | Evidence (dated artifact) |
|------|--------|---------------------------|
| B1 | ✅ 2026-06-10 | 0.9.0 live on PyPI: release-check exit 0 BEFORE tag (commit bdac36b, all four registries swept); publish run 27311516131 green (tag==source gate passed, Trusted Publishing); `uvx --refresh --from clauderizer clauderize --version` → 0.9.0; doctor exit 0 with executor-leg identity 0.9.0 |
| B2 | ✅ 2026-06-10 | CI run 27312987722 (commit eef7136): 9/9 cells green — ubuntu/macos/windows-latest × py3.11–3.13; the win32 cmd-wrapper execution tests cannot skip on windows runners (win32_only mark), so green cells ⇒ they ran; subsequent runs tracked by the README badge. Surfaced and fixed before CI via a local native-Windows run: .exe console-script resolution, byte-exact wrapper newlines (\r\r\n corruption + idempotency break), CRLF-safe doctor freshness, distro-spelling wrapper fallback, cp1252-blind test reads, py3.11 which() PATHEXT quirk |
| B3 | ✅ 2026-06-10 | G6 satisfied with legs named (see G6 note above): windows-wsl via real harness cold start (transcript e4573a6d); native via scratch-repo init → doctor 14/14 exit 0 → sh -c AND bash -c on the registered string from hostile cwd → digest + identity 0.9.0; residual (literal native-harness restart) named |
| B4 | ✅ 2026-06-10 | Node-profile live loop on a scratch repo (/tmp/cz-node2-*): auto-detect → node; init + scaffold commit; preflight 7/7 PASS running REAL `npm test` (baseline 2 via mocha regex) and `npm run build`; 7 tracked writes via `clauderize ops` (create gameplan, transition ×2, decision, lesson, output, summary, handoff) all ok; digest direct AND from hostile cwd; guard-fires: broken test → preflight FAIL (tests ✗), restored → 7/7 again; doctor exit 0. Zero hand-edits. Defect it surfaced fixed with tests: unborn-branch (fresh `git init`, no commits) no longer misdiagnosed as "not a git repo" |
| B5 | ✅ 2026-06-10 | Quickstart fixed (the published `uvx clauderize init` failed against the live registry; now `uvx --from clauderizer clauderize init` everywhere) and guarded by quickstart.yml — the README's exact install path against the PUBLISHED package on a clean runner, green on the final text (run 27317115908; first run 27316260960); init never wires uvx ephemeral-cache paths (fix + 3 tests, live-proven via local wheel, ships next release; self-arming CI assert). UPGRADING.md (upgrade nudges + five-step uninstall) walked live verbatim; TRUST.md 12/12 code-cited; SECURITY.md; TROUBLESHOOTING.md 9/9 strings grep-verified; README: git-native framing, maturity-with-receipts, absolute doc links, release section follows the ritual |
| B6 | ✅ 2026-06-10 | The flip shipped via the ritual: 0.10.0 staged at 77a87ca, release-check exit 0 pre-tag (nine checks incl. the new README-names-the-ritual guard), publish run 27319860345 green (Trusted Publishing + attestations); "Development Status :: 4 - Beta" verified ON the published artifact (importlib.metadata via uvx --from clauderizer==0.10.0); the self-arming cache-clean guard ARMED and PASSED against published 0.10.0 (quickstart run 27320342612: uv cache clean → pure digest — the ephemeral-wiring fix in the wild); fresh-HOME walk confirmed end-to-end (fresh index resolve → durable uvx -q wiring → doctor 0 → cache-clean survival). Zero open findings at flip time |
