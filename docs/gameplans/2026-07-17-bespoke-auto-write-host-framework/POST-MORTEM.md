# Post-Mortem — bespoke auto-write host framework (D-056)

**Gameplan:** `2026-07-17-bespoke-auto-write-host-framework`
**Shipped into:** the unreleased clauderizer **1.10.0** (no new version bump)
**Span:** 4 phases (0–3), all complete. Suite **873 → 889 passed**, 5 skipped (+16 tests).
**Governing decision:** D-056 (builds on D-055; supersedes nothing).

## Summary

Generalized the D-055 kimi-desktop wiring into a reusable framework so a future agent
host of the same shape (a per-user MCP config the app owns/regenerates, no hook surface)
is an *implementation, not a re-implementation*. Two host-agnostic primitives were
extracted — `mcp_probe` (the MCP `initialize`-handshake capability probe) and `winhost`
(Windows/WSL command composition) — and a `BespokeHost` base + `BESPOKE_HOSTS` registry
now carries the detect → merge → self-heal → verify → guide lifecycle. kimi-desktop
became the first implementation; `init`/`doctor`/`status`/`uninstall` iterate the
registry generically. The whole change is behavior-preserving for kimi-desktop.

## What worked

- **The L-41 identity-default discipline held.** Porting kimi-desktop onto the framework
  via thin module delegators (`wire`/`self_heal`/`detect_config` → `_HOST`) kept the
  entire existing API and test surface intact; the suite only ever *grew*, never
  churned, and live composition/handshake/doctor stayed byte-identical at every phase.
- **Genericity was proven, not asserted.** A second, test-only `BespokeHost` (a different
  `servers_key`, zero daimon code) runs the full lifecycle in `test_bespoke_hosts.py` —
  the real evidence the framework generalizes.
- **The user's "full framework" call was right despite the N=1 caution.** The abstraction
  fell out cleanly because kimi-desktop's variable-vs-shared split was already sharp after
  D-055; the base class is small and the registry is a plain dict (no plugin machinery).

## What didn't (root causes)

- **The registry was silently EMPTY in the real `clauderize doctor`.** Root cause: the
  registry is populated by kimidesktop's import side-effect, and after the rewire doctor
  no longer imported kimidesktop — so it iterated nothing and dropped the entire
  kimi-desktop section. The in-process tests **masked** it because conftest's autouse
  fixture imports kimidesktop, so the test process' import graph always had the registry
  populated. Caught only by running the *real* CLI (the clean-environment / real-leg
  discipline paying off). Fixed with a lazy `all_hosts()` accessor that imports the impl
  modules, plus a fresh-subprocess regression guard. Promoted as **L-60** (extends L-23).
- **A `_win_path_to_wsl`/`_spawn_target` split across two concerns.** Minor: the handshake
  needed the Windows→WSL translation that composition also needed, so `winhost` owns the
  translation and `mcp_probe` imports it — a clean dependency, but it took a beat to see
  the two primitives weren't one.

## Procedure improvements

- **Registry/plugin patterns need a fresh-process test by default** (L-60). Any "populate
  by import side-effect + iterate elsewhere" shape should ship with a subprocess guard,
  because the natural in-process test shares the masking import.
- **Run the real entry point, not just the suite, after a wiring rewire.** The bug was
  invisible to 888 green tests and obvious on the first real `doctor`. This is the same
  lesson as L-23, and it earned its keep again here.

## Open threads

1. **Publish 1.10.0 to PyPI** — this framework and the D-055 fixes both ride the still-
   unreleased 1.10.0. The release ritual (fresh-install verification per CI leg, four-
   registry version sweep — L-51) is still pending; it was never part of this session.
2. **`doctor --deep` is opt-in for the HOST_EMITTERS hosts** (O-01). If per-enabled-host
   handshakes ever become cheap enough (or a host proves flaky), revisit whether to make
   it default — but the current default (presence + session-host `verify_wiring`) is the
   right latency/coverage trade for now (L-07).
3. **The `docs/LESSONS.md` count keeps climbing** (now 23 with L-60). Still owned by the
   standing curator-loop gameplan — a re-distill pass there would consolidate the
   host-wiring cluster (L-25, L-58, L-59, L-60 all touch capability-verification / host
   config).
