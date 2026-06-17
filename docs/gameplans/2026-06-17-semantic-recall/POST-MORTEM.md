# Post-Mortem — 2026-06-17-semantic-recall

> Closed: 2026-06-17, **NO-GO on LEANN at Phase 0** (see D-014). The peer-server
> spike disqualified LEANN on install friction alone — ~2 GB of eagerly-imported
> torch ML stack (1.6 GB CPU / 5.1 GB CUDA install + a ~440 MB contriever model)
> to semantic-search a 1.2 MB / 134-file corpus. Retrieval quality was
> deliberately never measured: D1 made a friction no-go a cheap, legitimate
> outcome, and the user made that call. Phases 1–3 (gated on a GO) are dropped.
> Zero engine code written; suite unchanged at 266; spike torn down to zero
> footprint. No successor initiative — `active_gameplan` clears rather than
> replaces.

## What worked

1. **Spike-first with a pre-blessed no-go (D1) paid off exactly as designed.**
   The cheapest possible test needed zero Clauderizer code — run `leann_mcp` as
   a peer server over docs/ and just measure it. Because a no-go was a
   first-class outcome, we could stop the moment the friction axis was decisive,
   without building (or cleaning up) any integration. The idea cost only the
   spike.
2. **The spike stayed outside the repo, so the tree was never at risk.** The
   index was built in `~/leann-spike` (not `<repo>/.leann/`, which `.gitignore`
   doesn't cover), and nothing was written to the tracked `.mcp.json` (user
   scope was the plan). The working tree was pristine throughout, and teardown
   left zero footprint.
3. **The disqualifying evidence was cheap and unambiguous.** A handful of
   read-only probes produced the whole picture: 5.1 GB CUDA (uv auto-detected
   the RTX 5080) → 1.6 GB after `--torch-backend cpu` → +440 MB model on first
   build → torch eagerly imported even for search-only. The ~2 GB-to-1.2 MB
   ratio was clear long before any retrieval number.
4. **The decision was recorded where it can't be lost.** D-014 (DECISIONS.md)
   and L-14 (LESSONS.md) mean a future session asking "why not LEANN?" gets the
   answer from structured memory — the irony being that's the very capability
   LEANN would have provided.

## What didn't (root causes)

1. **The session opened with a WSL2 meltdown that cost the first attempt.**
   `\\wsl.localhost` returned EIO and `wsl.exe` failed at `getpwnam` (errno 5);
   a distro terminate escalated it to `Wsl/Service/CreateInstance/E_UNEXPECTED`
   ("Catastrophic failure") and `wsl --shutdown` itself returned exit 1. Only a
   full host reboot recovered it. Root cause: WSL2 VHD/mount instability at the
   VM↔disk boundary — host-level, unrelated to the gameplan — which also
   corrupted the user's pre-installed torch (a 0-byte `libtorch_global_deps.so`;
   uv flagged the whole tool "malformed"). Takeaway: on this host, an EIO at
   session start is a reboot, not a repo problem — escalate
   terminate→shutdown→reboot instead of chasing the symptom in-band.
2. **uv silently resolved the heaviest possible torch.** The user's verbatim
   README command (`uv tool install leann-core --with leann`) pulled CUDA torch
   (`2.12.0+cu130`) + ~4 GB NVIDIA runtime because uv auto-detected the GPU, so
   the install looked even worse than the portable case until the CPU number
   (1.6 GB) was derived with `--torch-backend cpu`. Root cause: uv GPU
   auto-detection × LEANN's unpinned torch, hidden behind a one-line install.

## Friction log

1. **PS→wsl quote chain — the standing rule held.** Every multi-step shell
   action went into a `/tmp/*.sh` file run via `tr -d '\015' < file | bash`
   (the CRLF guard neutralizing Windows-side Writes). No inline-quoting
   failures all session — the file-not-inline discipline from prior gameplans
   carried directly.
2. **Peer-server registration would not have been the README one-liner.** LEANN
   discovers indexes per-project by CWD, and your Claude Code runs on Windows
   while leann lives in WSL — so the server would have needed a `wsl.exe` shim
   with a forced CWD (mirroring the `clauderizer` server), not `claude mcp add
   -- leann_mcp`. Moot under the no-go, but captured for any future attempt.

## Procedure improvements (concrete)

1. **Pre-register a friction budget in dependency-spike handoffs.** The Phase 0
   handoff seeded a retrieval question set but no install-weight ceiling. A
   "max acceptable install footprint" line would make a friction no-go
   mechanical rather than a mid-spike judgment call. Generalized as L-14.
2. **Codify "spikes write outside the repo" as the default** for zero-engine-code
   spikes — building in `~/leann-spike` and registering nothing tracked kept the
   tree clean and made teardown trivial. Worth a one-line norm in
   GAMEPLAN-PROCEDURE.
3. **On GPU hosts, capture both the auto-resolved and the portable footprint.**
   The number that matters for a shippable extra is the portable (CPU) one; uv's
   GPU auto-detection can otherwise inflate the apparent cost by 3x+.

## Carried forward

- **Semantic recall is not dead — LEANN is.** If revisited, the path is a
  torch-free, low-footprint engine (fastembed/ONNX ~tens of MB, or static
  embeddings like model2vec ~30 MB) or lexical/BM25 over the curated markdown
  (the corpus has highly distinctive vocabulary — decision/lesson/hardening IDs
  — that lexical search handles well). D-014 + L-14 carry the reasoning.
- **The Phase 0 retrieval question set is a reusable fixture** (preserved in
  PHASE-0-HANDOFF.md) for evaluating any future semantic-recall engine on the
  same terms.

## Final state

NO-GO on LEANN (D-014). Gameplan closed at Phase 0 of 4; Phases 1–3 dropped.
Zero engine code written; the suite is unchanged at 266 (no `src/` touched —
only docs/ via cz tools and the config deactivation). Spike fully torn down:
`leann-core` uv tool uninstalled, `~/leann-spike` + `~/.leann` + contriever
model + `/tmp` scripts removed, uv cache pruned, repo working tree never
touched by the spike itself. L-14 promoted (14 distilled project lessons).
`active_gameplan` cleared — no initiative opens automatically; the next session
starts with no active gameplan.
