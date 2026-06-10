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
| B2 | ⬜ | _(alpha-to-beta-evidence Phase 1)_ |
| B3 | ⬜ | _(alpha-to-beta-evidence Phase 2)_ |
| B4 | ⬜ | _(alpha-to-beta-evidence Phase 3)_ |
| B5 | ⬜ | _(gameplan B: stranger-readiness)_ |
| B6 | ⬜ | _(gameplan C: beta-flip)_ |
