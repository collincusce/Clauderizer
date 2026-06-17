# Post-Mortem — 2026-06-10-beta-flip

> Closed: 2026-06-10, all three phases complete. **Clauderizer is Beta:**
> 0.10.0 live on PyPI with `Development Status :: 4 - Beta` verified on the
> published artifact's own metadata; all six gates B1–B6 carry dated
> artifacts in `docs/RELEASING.md`. Suite 264 → 270. The third consecutive
> zero-incident release. Closed back-to-back with the start of
> `semantic-recall` (the LEANN spike), so `active_gameplan` replaces rather
> than clears.

## What worked

1. **One release with three faces, shipped atomically (D1).** The
   ephemeral-wiring fix, the classifier flip, and the README maturity
   wording rode the same commit, so the published artifact described itself
   truthfully at publish time — beta classifier, beta prose, fixed wiring,
   all at once.
2. **The guard that waited was the proof (D1, the load-bearing idea).**
   quickstart.yml's cache-clean assertion had self-disarmed through the
   entire 0.9.0 era; the flip release armed it automatically, and its first
   green run against published 0.10.0 (`uv cache clean` → pure digest) was
   B6's in-band evidence — the wiring fix proven in the wild on the same run
   that proves the install path. No gate checked by assertion alone.
3. **The burn-down landed before the flip, so the artifact carries its own
   guards (D2).** The bare-IO tripwire proved itself on its first sweep —
   catching three real stragglers the B2 sed pass had missed — then went
   green and stayed a permanent tripwire. The engine-staleness nudge and the
   README-names-the-ritual check shipped alongside; the latter passed on its
   first real staging inside the flip's own release-check.
4. **Fourth consecutive clean release ritual.** Fresh four-registry sweep,
   push-first, release-check exit 0 (now nine checks) before any tag,
   Trusted Publishing with attestations. The machinery built across the
   prior gameplans is now just how releases go.

## What didn't (root causes)

1. **My PyPI-propagation Monitor never fired — L-10 violated by my own
   observability probe.** I armed a monitor to watch for 0.10.0 on the PyPI
   index; its grep matched `"version": "0.10.0"` (pretty-printed) while PyPI
   serves minified JSON (`"version":"0.10.0"`). The condition could never
   match; the monitor sat until timeout while propagation had long since
   completed. Caught only because the timeout prompted a direct `curl`.
   Root cause: I proved neither direction of the probe before trusting it —
   exactly what L-10 says to do, on a monitoring filter rather than a
   product guard. Reinforces L-10 on a new surface (your own tooling is a
   probe too); not minted as a separate lesson — promoting a near-duplicate
   would violate the "promote deliberately, not in bulk" discipline.
2. **Propagation lag briefly looked like a failure.** The first post-publish
   quickstart dispatch (run 27319935766, ~90s after publish) self-disarmed
   because the runner's index view still answered 0.9.0. This was the
   self-arming design working correctly — no false red, no false green, it
   said what it saw — but it cost a re-dispatch and a moment of "did the
   flip not take?" Record as a feature, not a defect: the disarm message is
   the system being honest about what it can't yet see.

## Friction log

1. **The PowerShell→wsl quote chain, one last time.** The classifier-check
   one-liner (`uvx … python -c "[c for c in …]"`) degenerated into a bash
   syntax error inside the PS→wsl `sh -lc` chain; the script-file pattern
   (`/tmp/check_classifier.sh`) ran clean. The rule held all session and
   held here: WSL shell logic goes in a file, never inline.
2. **PyPI index propagation is not instant** (seconds-to-minutes after a
   publish run reports success). Any post-release assertion against the
   index must tolerate lag — poll, or accept a self-disarm, never hard-fail
   on the first miss.

## Procedure improvements (concrete)

1. **Monitor filters are probes — prove they fire before arming.** Before
   trusting a `Monitor`/grep condition, confirm it matches a known-true
   sample (here: `curl` the real PyPI JSON once and eyeball the shape). An
   L-10 application; folded into the post-mortem rather than a new L-entry.
2. **Post-release index assertions tolerate propagation lag by design** —
   the self-arming pattern already does this; keep new release-time checks
   in that mold (report what you see, don't hard-fail on a not-yet-visible
   version).

## Carried forward

- **G6 — the one residual on the 1.0 runway**: a literal Claude Code cold
  start on a native-OS machine (not the windows-wsl reference host).
  Everything else in the 1.0 gate list (G1–G5, G7) reads satisfied; 1.0 is
  now an evidence-review away, not a build away.
- **No deferred burn-down items** — all three structural guards landed in
  Phase 0.

## Final state

Clauderizer 0.10.0 — **Beta** — live on PyPI and resolving fresh; classifier
verified on the artifact; six beta gates with dated artifacts; suite 270;
doctor exit 0; findings tracker all-resolved (H-01..H-09). Four releases
shipped across one day (0.8.0 → 0.10.0), thirteen distilled project lessons,
the release ritual now mechanical and boring. The next initiative —
`semantic-recall` — opens immediately after this close.
