#!/usr/bin/env python3
"""Phase-0 cost-harness discrimination demo (gameplan abstract-index-fast-retrieval).

Runs the deterministic cost harness on the synthetic 1-of-N fixture for three
strategies and prints their saving / accuracy / round-trips and the pre-registered
verdict. The point is to show — BEFORE the real feature exists (L-40) — that the
harness:

  * reports ~0 saving for a no-op (negative control)         -> DISCARD
  * reports a large saving for the real mechanism            -> KEEP
  * rejects a token-cheap-but-WRONG strategy (accuracy guard) -> DISCARD

This is provenance, not the gate; the gate is the CI self-test in
tests/benchmarks/test_cost.py and D2's rule in PRE-REGISTRATION.md.

Run:  .venv/bin/python docs/gameplans/2026-06-25-abstract-index-fast-retrieval/_experiments/run_cost_harness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# This script lives at docs/gameplans/<id>/_experiments/run_cost_harness.py; the
# repo root is four parents up. Put it on sys.path so `tests` imports whether or
# not the cwd is the repo root (matches the ranker-spike script).
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tests.benchmarks import cost  # noqa: E402


def _row(label: str, res: dict) -> str:
    return (f"  {label:<22} saving={res['mean_saving']*100:6.1f}%   "
            f"acc(cand/base)={res['candidate_accuracy']:.2f}/{res['baseline_accuracy']:.2f}   "
            f"round-trips(cand/base)={res['mean_round_trips_candidate']:.1f}/"
            f"{res['mean_round_trips_baseline']:.1f}   "
            f"==> {cost.verdict(res)}")


def main() -> int:
    print("=" * 80)
    print("COST HARNESS — Phase-0 discrimination demo (abstract-index-fast-retrieval)")
    print(f"fixture: {len(cost.COST_LOOKUPS)} lookups, 1-of-{len(cost.COST_LOOKUPS[0].surfaced)} "
          f"surfaced   |   gate: saving>={cost.MIN_SAVING:.0%}, "
          f"accuracy non-regress, round-trips<={cost.MAX_ROUND_TRIPS}")
    print("=" * 80)

    real = cost.evaluate(cost.COST_LOOKUPS, cost.abstract_then_fetch)
    ctrl = cost.evaluate(cost.COST_LOOKUPS, cost.noop_full)
    trap = cost.evaluate(cost.COST_LOOKUPS, cost.starve)

    print(_row("real mechanism", real))
    print(_row("noop (control)", ctrl))
    print(_row("starve (acc trap)", trap))

    print("-" * 80)
    gap = real["mean_saving"] - ctrl["mean_saving"]
    print(f"  discrimination gap (real - control) = {gap*100:.1f} percentage points")
    ok = (cost.verdict(real) == "KEEP"
          and cost.verdict(ctrl) == "DISCARD"
          and cost.verdict(trap) == "DISCARD")
    print(f"  harness discriminates as designed? {ok}")
    print("  (synthetic fixture — Phase 3 swaps in the REAL corpus + abstract index)")
    print("-" * 80)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
