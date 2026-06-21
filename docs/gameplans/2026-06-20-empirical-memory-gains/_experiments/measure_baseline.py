"""Phase 0 baseline capture for 2026-06-20-empirical-memory-gains.

Provenance only (not CI). Measures the real repo's injected-context sizes and the
in-memory ranker baseline; the numbers are recorded in PHASE-STATUS.md via
cz_add_output as the figures later phases must beat.

Run from repo root:
  PYTHONPATH=. .venv/bin/python \
    docs/gameplans/2026-06-20-empirical-memory-gains/_experiments/measure_baseline.py
"""
from clauderizer.ops import repo_ctx
from tests.benchmarks import corpora, harness

paths, config = repo_ctx()
ctx = harness.measure_context_tokens(paths, config)
rank = harness.run_ranker(corpora.RANKER_ENTRIES, corpora.RANKER_PROBES, k=3)
rank = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in rank.items()}
print("CONTEXT_TOKENS", ctx)
print("RANKER", rank)
