# semantic-recall — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-17

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Peer-server spike: prove retrieval quality and install friction before any engine code | ✅ COMPLETE | 2026-06-17 | 2026-06-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | The optional extra: clauderizer[semantic] + cz_recall over curated docs/ | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Scrollback search: transcripts as a distinct, explicitly non-authoritative layer | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Dogfood consolidation, trust/docs, and the 1.0-implications call | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
spike-verdict: NO-GO on LEANN (see D-014). Disqualified on the install-friction axis alone; retrieval quality deliberately not measured (friction was decisive, per D1 a cheap no-go).
install-weight: CPU path 1.6 GB (torch 2.12.1+cpu 714 MB + sentence-transformers 5.6.0 + transformers + sklearn/scipy via `--torch-backend cpu`); CUDA path 5.1 GB (torch 2.12.0+cu130 + ~4 GB NVIDIA runtime) auto-resolved by uv on the RTX 5080 host.
first-build-model: ~440 MB facebook/contriever pulled from HuggingFace on first `leann build`. Defaults: embedding-mode=sentence-transformers, embedding-model=facebook/contriever, backend=hnsw.
torch-mandatory: leann eagerly imports torch at package load (leann/__init__ → api → chat). Torch is unavoidable even for search-only use, so the D2 embedding-backend choice (ollama/openai) cannot slim the install.
corpus-served: docs/ = 134 markdown files, 1.2 MB — i.e. ~2 GB of mandatory ML stack to search 1.2 MB of text (~1700x dependency-to-data ratio).
teardown: Zero footprint: leann-core uv tool uninstalled, ~/leann-spike + ~/.leann + contriever HF model + /tmp scripts removed, uv cache pruned. Repo working tree never touched by the spike (index built outside the repo; nothing registered in tracked .mcp.json).
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
