#!/usr/bin/env python3
"""Phase-5 measuring stick — write-time near-duplicate-lesson advisory.

PRE-REGISTERED (before wiring anything into cz_add_lesson):

  HYPOTHESIS: a length-normalized token overlap (JACCARD of the new lesson's
  distinctive tokens vs an existing lesson's) flags genuine near-duplicate lessons
  while NOT flagging distinct-but-similar ones — beating the naive raw-overlap
  COUNT (what rank_relevant scores) which a long lesson trips by sheer size.

  PRINCIPLED detector: flag an existing lesson if jaccard(new, existing) >= J_KEEP.
  NAIVE strawman:       flag if the raw shared-token COUNT >= COUNT_FLAG.
  Both reuse analyze._tokens (no new metric — L-14).

  Pre-registered thresholds (committed BEFORE measuring; do NOT tune to the fixture):
      J_KEEP     = 0.40   # "shares >=40% of the combined distinctive vocabulary"
      COUNT_FLAG = 4      # the naive bar, set to catch the true dups

  KEEP BAR (all must hold, else DROP honestly — L-32/L-38):
    1. principled precision == 1.00 on the fixture (NO false positive, esp. on a near-miss)
    2. principled recall    >= 0.80 (catches the true dups)
    3. principled BEATS naive ON THE NEAR-MISSES: the naive false-positives >=1
       near-miss that the principled correctly rejects (a real mechanism, not a
       tautology — L-40). A win only over a no-check baseline does not count.

The fixture is labelled by hand; the near-misses are GENUINE distinct lessons that
happen to share topic vocabulary (authored for their content, then measured — if a
real near-miss scored high Jaccard, that would be an honest finding against the
mechanism, not a reason to reword it).

Run: .venv/bin/python docs/gameplans/2026-06-25-abstract-index-fast-retrieval/_experiments/lesson_dedup_measure.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from clauderizer import analyze  # noqa: E402  the real tokenizer (_tokens)

J_KEEP = 0.40
COUNT_FLAG = 4

# Existing lessons the new one is checked against.
EXISTING = {
    "L-A": ("Before an irreversible release, run the full test suite on every host leg "
            "the CI matrix covers; a green on one operating system is only a guess about "
            "the others, and the publish cannot be undone."),
    "L-B": ("A health check must verify capability, not mere presence; a green check on a "
            "setup that cannot actually launch is worse than no check at all."),
    "L-C": ("A dependency's footprint relative to the data it serves is a first-class go or "
            "no-go axis; two gigabytes of machine-learning stack to search one megabyte of "
            "markdown is an absurd ratio."),
    "L-D": ("Round-trip idempotency, where applying a mutation twice equals applying it once "
            "through the engine's own parser, is the load-bearing test for every structured write."),
}

# New lessons: (text, expected-flag, note). expected-flag True == should be surfaced
# as a near-duplicate. The NEAR-MISSes are distinct lessons that share vocabulary.
CASES = [
    ("Run the entire test suite across every operating system the CI matrix covers before "
     "any irreversible release; one platform passing does not prove the rest and a publish "
     "cannot be undone.", True, "true dup of L-A"),
    ("Before an irreversible release, run the release checklist and sweep the version across "
     "all four registries; the test suite passing is necessary but the registries must also "
     "agree or the publish is double-claimed.", False, "NEAR-MISS vs L-A (registry sweep, not test-every-OS)"),
    ("A green health check on a setup that cannot launch is worse than no check; verify "
     "capability rather than mere presence.", True, "true dup of L-B"),
    ("A health check should run the real launch command and read the in-band version it prints; "
     "a green exit code alone certifies that something ran, not that the launch produced the "
     "right thing.", False, "NEAR-MISS vs L-B (in-band identity, not capability-vs-presence)"),
    ("Prefer literal paths over shell command substitution when isolating a destructive "
     "operation, because dollar-paren expands in the outer shell and silently stays put.",
     False, "novel"),
    ("Markdown is canonical and the disposable index is rebuilt from it on disagreement.",
     False, "novel"),
    ("A tool's dependency weight relative to the data it serves is a go/no-go axis on its "
     "own; a two-gigabyte ML stack to search a megabyte of markdown is an absurd footprint "
     "ratio.", True, "true dup of L-C"),
]


def _scores(text: str):
    """(best_jaccard, best_count, best_id) of `text` vs EXISTING."""
    nt = analyze._tokens(text)
    best_j, best_c, best_id = 0.0, 0, None
    for eid, etext in EXISTING.items():
        et = analyze._tokens(etext)
        inter = len(nt & et)
        union = len(nt | et) or 1
        j = inter / union
        if j > best_j:
            best_j, best_id = j, eid
        best_c = max(best_c, inter)
    return best_j, best_c, best_id


def _metrics(flagged: list[bool], expected: list[bool]) -> dict:
    tp = sum(1 for f, e in zip(flagged, expected) if f and e)
    fp = sum(1 for f, e in zip(flagged, expected) if f and not e)
    fn = sum(1 for f, e in zip(flagged, expected) if not f and e)
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    return {"precision": precision, "recall": recall, "tp": tp, "fp": fp, "fn": fn}


def main() -> int:
    expected = [e for _, e, _ in CASES]
    principled, naive = [], []
    print("=" * 92)
    print(f"PHASE-5 lesson near-dup measuring stick   J_KEEP={J_KEEP}  COUNT_FLAG={COUNT_FLAG}")
    print("=" * 92)
    print(f"  {'case':<46} {'jac':>5} {'cnt':>4}  {'exp':>4}  prin/naiv  note")
    for (text, exp, note) in CASES:
        j, c, _bid = _scores(text)
        p_flag, n_flag = j >= J_KEEP, c >= COUNT_FLAG
        principled.append(p_flag)
        naive.append(n_flag)
        tag = f"{'F' if p_flag else '.'}/{'F' if n_flag else '.'}"
        print(f"  {text[:46]:<46} {j:>5.2f} {c:>4}  {str(exp):>5}   {tag:^7}  {note}")

    pm, nm = _metrics(principled, expected), _metrics(naive, expected)
    print("-" * 92)
    print(f"  principled: precision={pm['precision']:.2f} recall={pm['recall']:.2f} "
          f"(tp={pm['tp']} fp={pm['fp']} fn={pm['fn']})")
    print(f"  naive     : precision={nm['precision']:.2f} recall={nm['recall']:.2f} "
          f"(tp={nm['tp']} fp={nm['fp']} fn={nm['fn']})")

    # near-miss = expected-False cases; principled must reject the ones naive flags.
    near_miss_idx = [i for i, e in enumerate(expected) if not e]
    naive_fp_nearmiss = [i for i in near_miss_idx if naive[i]]
    prin_fp_nearmiss = [i for i in near_miss_idx if principled[i]]
    beats = len(naive_fp_nearmiss) >= 1 and len(prin_fp_nearmiss) == 0

    print(f"  near-misses naive false-positives: {len(naive_fp_nearmiss)}; "
          f"principled false-positives: {len(prin_fp_nearmiss)}")
    keep = (pm["precision"] == 1.0 and pm["recall"] >= 0.80 and beats)
    print("-" * 92)
    print(f"  VERDICT: {'KEEP' if keep else 'DROP'}  "
          f"(precision==1.0? {pm['precision'] == 1.0}; recall>=0.8? {pm['recall'] >= 0.80}; "
          f"beats naive on near-misses? {beats})")
    print("=" * 92)
    return 0 if keep else 2


if __name__ == "__main__":
    raise SystemExit(main())
