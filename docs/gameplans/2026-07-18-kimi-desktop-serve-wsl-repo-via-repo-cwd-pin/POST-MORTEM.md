# Post-Mortem — serve a WSL repo from the Kimi desktop via a --repo + cwd pin (D-057)

**Gameplan:** `2026-07-18-kimi-desktop-serve-wsl-repo-via-repo-cwd-pin`
**Shipped:** clauderizer **1.11.0** — live on PyPI.
**Span:** 4 phases (0–3), all complete. Suite **889 → 907 passed**, 5 skipped (+18 tests).
**Governing decision:** D-057 (builds on D-055 `--repo`, D-056 BespokeHost self-heal, D-054 UNC playbook).

## Summary

Turned the D-055 "`--repo` forward path (not yet automatic)" into a working, opt-in feature:
`clauderize init --serve-wsl-here` pins the Kimi Work desktop to serve a WSL-hosted repo by
composing `{command: clauderizer-mcp.exe, args: ["--repo", "\\wsl.localhost\…"], cwd: "C:\Users\…"}`
— the daimon runtime honors a per-server `cwd`, so the server spawns from a Windows-safe cwd and
reads the repo over its UNC path (file I/O over UNC works; only the process *cwd* may not be UNC).
The pin is recorded in a durable sidecar so it survives the app wiping its own `mcp.json`; `doctor`
reports which repo it serves and the single-repo tradeoff; `uninstall` clears it. It is strictly
opt-in — the repo-agnostic default is unchanged.

## What worked

- **Hypothesis → verified, not assumed.** The whole feature rested on a claim (another agent's, then
  mine): "the daimon honors a per-server `cwd`." It was confirmed two ways before building — grepping
  the app bundle's config normalizer/spawn site, and a live `initialize`+`cz_status` handshake that
  served the real `clauderizer-site` over UNC. The tempting alternative (an in-WSL `executor`) was
  *ruled out* by reading the bundle's validated executor set, not guessed.
- **The compose primitive matched reality exactly.** Phase 0's composed pin was byte-identical to the
  entry the desktop agent had already verified end-to-end — the strongest possible unit-level anchor.
- **Live dogfood at every phase.** Applying the pin to the real machine (serving clauderizer-site,
  surviving 2/2 app-wipe→`status` cycles, doctor reporting the pin) is what proved the feature, and
  it delivered the user's actual goal (clauderizer-site works in the desktop after a restart).
- **The BespokeHost framework (D-056) paid off.** The pin slotted in through `pinned_repo`/`clear_pin`
  hooks and the existing self-heal/compose seam; the generic entry points needed almost no new code.

## What didn't (root causes)

- **The original Phase 1 design was wrong, and a live read caught it.** I planned "self-heal preserves
  the existing `--repo`." Mid-phase I read the live daimon config and found it wiped to `{}` again
  (the app's regenerate-on-switch, O-01) — so there is no `--repo` left to read after a wipe (recorded
  as **C-01**). Root cause: I'd reasoned about durability without re-checking the adversary (the app)
  in its current state. Fix: a durable **sidecar** the app doesn't touch, with self-heal recomposing
  from it. Promoted as **L-61**.
- **An f-string brace bug shipped into a phase and was caught by the suite.** The guide's JSON example
  used single `{}` inside `setup_guide()`'s f-string → runtime `NameError` on every test that renders
  the guide. Caught immediately (7 red), fixed by doubling the braces. Cheap, but a reminder that
  prose-in-code has code failure modes.

## Procedure improvements

- **Re-check the adversary's *current* state before designing durability against it.** The C-01 miss
  came from assuming the config still held the pin; one `cat` of the live file falsified it. When a
  feature's correctness depends on an external actor's behavior, observe that actor freshly, not from
  memory of an earlier turn.
- **Live dogfood remains the highest-value verification for host-integration work** — the same lesson
  as the last three gameplans, earned again.

## Open threads

1. **`pipx upgrade clauderizer` on the Windows side.** The desktop's `clauderizer-mcp.exe` is a
   separate install; `doctor`'s version-skew advisory will flag it until it's on 1.11.0. (It was on
   1.10.0 during this work.)
2. **The pin serves one repo per machine.** That's inherent to the single per-user daimon file. If a
   user needs several WSL repos in the desktop, the only real fix is upstream (per-workspace MCP
   config, or the app spawning via `wsl.exe` inside the distro) — out of clauderizer's hands.
3. **`docs/LESSONS.md` is at 24 (now L-61).** The standing curator-loop gameplan owns re-distilling the
   host-wiring cluster (L-25, L-58, L-59, L-60, L-61 all touch capability-verification / host config).
