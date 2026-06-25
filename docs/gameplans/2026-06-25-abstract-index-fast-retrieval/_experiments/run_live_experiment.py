#!/usr/bin/env python3
"""Phase-3 LIVE cost experiment — the gain-gate (gameplan abstract-index-fast-retrieval).

Wires the REAL abstract index + get_entry (the cz_get read path) into the Phase-0
cost harness and judges KEEP/DISCARD against the PRE-REGISTERED thresholds (D2,
frozen in PRE-REGISTRATION.md and cost.py: MIN_SAVING=0.30, accuracy
non-regression, MAX_ROUND_TRIPS=2). Deterministic, no live LLM (token proxy =
metrics.token_estimate, len//4).

Real lookups: every corpus entry (decision / invariant / finding / lesson) is
taken in turn as the needed answer, surfaced among its K-1 id-sorted neighbours (a
1-of-K window over the REAL corpus). The candidate surfaces each entry's
id + title + real abstract (abstract_index._cap(title) — exactly what cz_analyze
emits) and fetches ONLY the answer's body via the real get_entry; the baseline
materializes EVERY surfaced body (the status quo). The negative control
(noop_full) and the accuracy trap (starve) run on the SAME real lookups to
re-confirm the harness still discriminates on the live wiring (L-39/L-40) — a KEEP
is credible only if the controls are still rejected.

The candidate keeps the small title/abstract redundancy the real cz_analyze output
carries (it surfaces both `title` and `abstract`), so the measurement is
CONSERVATIVE — it understates the saving, the honest direction to err.

Run: .venv/bin/python docs/gameplans/2026-06-25-abstract-index-fast-retrieval/_experiments/run_live_experiment.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# docs/gameplans/<id>/_experiments/<this>; repo root is four parents up.
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from clauderizer import analyze  # noqa: E402  the real get_entry read path
from clauderizer import paths as P  # noqa: E402
from clauderizer.graph import abstract_index  # noqa: E402  the real index + _cap
from tests.benchmarks import cost  # noqa: E402  the frozen harness + thresholds

K = 5  # surfaced-set size per lookup (cz_analyze's top-k shape)


def build_live_lookups(paths) -> list[cost.Lookup]:
    """One 1-of-K lookup per real corpus entry: the entry is the needed answer,
    surfaced among its K-1 id-sorted neighbours, all carrying their REAL bodies
    (resolved through the real get_entry / cz_get read path)."""
    ids = sorted(abstract_index.build(paths)["entries"])
    full = {eid: analyze.get_entry(paths, eid) for eid in ids}
    n = len(ids)
    lookups: list[cost.Lookup] = []
    for i, eid in enumerate(ids):
        window = [ids[(i + j) % n] for j in range(min(K, n))]
        surfaced = tuple({"id": full[w]["id"], "title": full[w]["title"],
                          "body": full[w]["body"]} for w in window)
        lookups.append(cost.Lookup(query=eid, surfaced=surfaced, answer_ids=(eid,)))
    return lookups


def live_candidate(lk: cost.Lookup) -> dict:
    """The REAL feature: surface id + title + the entry's real abstract
    (abstract_index._cap(title), what cz_analyze emits) and fetch ONLY the answer
    body (the get_entry read path). One fetch per needed body; read-only."""
    surfaced = "\n".join(f"{e['id']} {e['title']} {abstract_index._cap(e['title'])}"
                         for e in lk.surfaced)
    answer = set(lk.answer_ids)
    present = answer & {e["id"] for e in lk.surfaced}
    fetched = "\n".join(e["body"] for e in lk.surfaced if e["id"] in present)
    payload = surfaced + ("\n" + fetched if fetched else "")
    return {"payload_tokens": cost.token_estimate(payload),
            "round_trips": 1 + len(present),
            "answered": answer <= present}


def _row(label: str, res: dict) -> str:
    return (f"  {label:<20} saving={res['mean_saving'] * 100:6.1f}%   "
            f"acc(cand/base)={res['candidate_accuracy']:.2f}/{res['baseline_accuracy']:.2f}   "
            f"rt(cand/base)={res['mean_round_trips_candidate']:.1f}/"
            f"{res['mean_round_trips_baseline']:.1f}   max_rt={res['max_round_trips_candidate']}"
            f"   ==> {cost.verdict(res)}")


def main() -> int:
    paths = P.resolve(_REPO_ROOT)
    lookups = build_live_lookups(paths)
    real = cost.evaluate(lookups, live_candidate)
    noop = cost.evaluate(lookups, cost.noop_full)
    trap = cost.evaluate(lookups, cost.starve)

    print("=" * 86)
    print("PHASE-3 LIVE cost experiment — real corpus + real abstract index / get_entry")
    print(f"corpus entries={real['n']}  K={K}  gate: saving>={cost.MIN_SAVING:.0%}, "
          f"accuracy non-regress, max_round_trips<={cost.MAX_ROUND_TRIPS}")
    print("=" * 86)
    print(_row("LIVE candidate", real))
    print(_row("noop (control)", noop))
    print(_row("starve (acc trap)", trap))
    print("-" * 86)
    discriminates = (noop["mean_saving"] < 0.02
                     and trap["candidate_accuracy"] < trap["baseline_accuracy"]
                     and cost.verdict(noop) == "DISCARD"
                     and cost.verdict(trap) == "DISCARD")
    print(f"  controls still discriminate on live wiring (L-39/L-40)? {discriminates}")
    v = cost.verdict(real)
    print(f"  PRE-REGISTERED VERDICT: {v}   "
          f"(saving {real['mean_saving'] * 100:.1f}% vs {cost.MIN_SAVING:.0%};  "
          f"acc {real['candidate_accuracy']:.2f} >= {real['baseline_accuracy']:.2f};  "
          f"max_rt {real['max_round_trips_candidate']} <= {cost.MAX_ROUND_TRIPS})")
    print("=" * 86)
    return 0 if (v == "KEEP" and discriminates) else 2


if __name__ == "__main__":
    raise SystemExit(main())
