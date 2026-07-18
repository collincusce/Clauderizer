# Post-Mortem — kimi-desktop wiring end-to-end repair (D-055)

**Gameplan:** `2026-07-17-kimi-desktop-wiring-end-to-end-repair`
**Shipped:** clauderizer **1.10.0** (staged; not yet published to PyPI — see Open Threads)
**Span:** 6 phases (0–5), all complete. Suite **840 → 873 passed**, 5 skipped (+33 tests).
**Governing decision:** D-055 (supersedes the bare-`uvx`-for-Windows clause of D-053; D-053 core + D-054 playbook stand).

## Summary

Repaired the Kimi Work desktop (daimon runtime) MCP wiring end-to-end, verified live on
the reporting machine (Win11 + WSL2). Five defects were fixed: (1) the Windows entry
composed a bare `uvx` that can never spawn (uvx.exe isn't bundled); (2) the registration
didn't persist across the app's project-switch `mcp.json` regeneration; (3) `doctor`
green-lit a broken entry on mere key-presence; (4) a WSL-hosted repo got a dead command
instead of guidance; (5) the server couldn't be pointed at a repo other than its cwd.
The fixes: host-topology-aware `.exe` composition, self-heal on init/doctor/status, a
live `initialize`-handshake smoke-test in doctor, refined UNC guidance, and a
`--repo`/`$CLAUDERIZER_REPO` surface.

## What worked

- **Empirical verification at every phase, against the real machine, not just tests.**
  Composition reproduced the user's hand-fixed verified-good entry byte-for-byte; a live
  wipe→`status`→restore proved self-heal; the doctor handshake ran against the real
  Windows `clauderizer-mcp.exe` (a genuinely separate, non-editable pipx install) in both
  directions (good→ok, bogus→fail). This is what turned "should work" into "does work."
- **Both open items resolved by evidence, not assumption.** O-01: searched the daimon
  tree and confirmed no persistent MCP source exists (the `.bak` proved the wipe). O-02:
  a WSL doctor *can* spawn the Windows exe via the `/mnt` interop path and handshake it —
  so the verdict is a real green, not a punt to "unverifiable."
- **Backward-compatibility by construction.** The macOS/Linux `uvx` path is byte-identical;
  `--repo` is inert when unset; the opt-out is intact. Cascades over both changed
  subsystems came back "no change needed," and Claude Code wiring was provably untouched.
- **The version-skew advisory earned its keep immediately** — it flagged that the user's
  Windows desktop install is still 1.9.1 vs the 1.10.0 WSL engine, a real skew, on its
  first real run.

## What didn't (root causes)

- **The version bump surfaced 12 transient test failures.** Root cause: the editable
  install's dist-info still reported 1.9.1 while source moved to 1.10.0, so doctor's
  version-parity check (correctly) failed. Fixed by `pip install -e` to refresh metadata.
  This is L-23/L-51 in miniature — the author's install is not the real artifact — and the
  check doing its job, not a bug.
- **The request literally listed "hook" as a self-heal entry point, which INVARIANT-06
  forbids.** Root cause: a genuine tension between the ask and a hard invariant (hooks are
  read-only). Reconciled (C-01): self-heal rides the write-permitted CLI entry points
  instead — which is also the *only* design that works, since a wiped host can't
  bootstrap its own MCP server to re-heal from within. Recorded, not silently dropped.

## Procedure improvements

- **cz_audit's clean-environment check is a standing pre-publish gate, not a close-out
  step.** This session verified in the editable install (+ a real separate Windows exe for
  the handshake) but did *not* do a fresh-venv/wheel or `uvx --refresh` install. That
  belongs immediately before the 1.10.0 PyPI publish (L-51 four-registry sweep + L-23
  fresh-install walk).
- **Doc-drift sweep (L-21) paid off** — CROSS-HOST's "writes a bare uvx" and TRUST's
  write-surface were caught and corrected. Keep running that sweep whenever a host's
  command shape or write-surface changes.

## Open threads

1. **Publish 1.10.0 to PyPI** with the full release ritual (fresh-install verification on
   every CI leg, four-registry version sweep — L-51). NOT done this session; the version
   is bumped and CHANGELOG'd but unreleased.
2. **`pipx upgrade clauderizer` on the user's Windows install** (currently 1.9.1) after
   1.10.0 ships — clears the doctor version-skew advisory and the self-heal will then
   compose/verify a 1.10.0 exe.
3. **True UNC-repo serving is still blocked upstream.** `--repo` is the enabling
   primitive, but the one repo-agnostic daimon file can't bake a per-repo `--repo`
   automatically; serving a WSL-hosted repo needs the app to spawn from a Windows-safe cwd
   (Moonshot-side, as D-054 noted). Guidance points at this; automation waits on the app.
4. **`docs/LESSONS.md` bloat persists (>20, now 22 with L-59).** Owned by the standing
   curator-loop gameplan — re-distill/obsolete superseded L-entries there.
