"""Memory-eval harness (gameplan 2026-06-20-empirical-memory-gains, Phase 0).

A deterministic, stdlib-only benchmark + agent-eval framework that gates every
feature in this gameplan: a change lands only if it beats the captured baseline
on a pre-registered metric (D: empirical gain-gate). Methodology follows the
LongMemEval three-stage ablation (index / retrieval / reading) and five-ability
taxonomy (extraction, multi-session, temporal, knowledge-updates, abstention).
See README.md in this directory.
"""
