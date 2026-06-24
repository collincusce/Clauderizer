#!/usr/bin/env python3
"""Measuring stick for the CALM anti-bias checks added to cz_critique (D1).

Runs the labeled fixture (fixture.json) through THREE detectors per axis:

  * principled — the shipped classifier (_evidence_is_authority /
    _resolution_is_hollow / _overclaims), which pairs a fingerprint with an
    in-repo-anchor guard;
  * naive — a fingerprint-only strawman with no anchor guard / a length
    threshold, included to show the adversarial near-misses are non-trivial
    (the gain is precision the naive detector lacks, NOT "prior had no check");
  * prior — the rubric BEFORE this change, which had no bias axis at all and so
    scored every degenerate case clean (detection 0 by construction).

Honest-gate framing (L-39 / L-32): a single author writing both the fixture and
the detector cannot fully escape confirmation bias. The result is only credible
because (a) the principled detector must beat the naive one on the near-misses,
and (b) the prior rubric provably missed every degenerate case. Run:

    .venv/bin/python docs/gameplans/2026-06-24-critique-bias-hardening/_experiments/measure.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from clauderizer.rituals import critique as C

HERE = Path(__file__).resolve().parent
FIXTURE = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))

# --- principled detectors (the shipped code) ---------------------------------
def principled_authority(ev: str) -> bool:
    return C._evidence_is_authority(ev)

def principled_hollow(note: str) -> bool:
    return C._resolution_is_hollow(note)

def principled_overclaim(prose: str) -> bool:
    return bool(C._overclaims(prose))

# --- naive strawmen (fingerprint only, no anchor guard) ----------------------
_NAIVE_AUTH = re.compile(
    r"arxiv:|doi:|https?://|verified|confirmed|et al|literature|"
    r"standard practice|official doc|established|obviously", re.I)
_NAIVE_OVER = re.compile(r"all.*criteria|verif|complete|done|comprehensive", re.I)

def naive_authority(ev: str) -> bool:
    return bool(_NAIVE_AUTH.search(ev))                 # no in-repo-anchor guard

def naive_hollow(note: str) -> bool:
    return len(note.strip()) < 25                       # pure length threshold

def naive_overclaim(prose: str) -> bool:
    return bool(_NAIVE_OVER.search(prose))

# --- prior rubric: no bias axis existed --------------------------------------
def prior_none(_: str) -> bool:
    return False

AXES = {
    "authority":        ("authority", principled_authority, naive_authority),
    "hollow_resolution":("hollow_resolution", principled_hollow, naive_hollow),
    "overclaim":        ("overclaim", principled_overclaim, naive_overclaim),
}
FIELD = {"authority": "evidence", "hollow_resolution": "note", "overclaim": "prose"}
POSITIVE = {"degenerate", "overclaim"}   # labels for which a flag is expected


def confusion(cases, field, detector):
    tp = fp = tn = fn = 0
    rows = []
    for c in cases:
        expected = c["label"] in POSITIVE
        got = detector(c[field])
        kind = ("TP" if expected and got else "FN" if expected else "FP" if got else "TN")
        tp += kind == "TP"; fp += kind == "FP"; tn += kind == "TN"; fn += kind == "FN"
        rows.append((c["id"], c["label"], c.get("near_miss", False), expected, got, kind))
    det = tp / (tp + fn) if (tp + fn) else 1.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 1.0
    return dict(tp=tp, fp=fp, tn=tn, fn=fn, detection=det, fp_rate=fpr,
                precision=prec, rows=rows)


def main() -> None:
    print("=" * 78)
    print("critique-bias-hardening — detection measurement")
    print("=" * 78)
    summary = {}
    near_miss_log = []
    for axis_key, (axis_name, principled, naive) in AXES.items():
        block = FIXTURE["axes"][axis_key]
        cases = block["cases"]
        field = FIELD[axis_key]
        P = confusion(cases, field, principled)
        N = confusion(cases, field, naive)
        R = confusion(cases, field, prior_none)
        summary[axis_key] = {
            "n": len(cases),
            "principled": {k: P[k] for k in ("tp","fp","tn","fn","detection","fp_rate","precision")},
            "naive":      {k: N[k] for k in ("tp","fp","tn","fn","detection","fp_rate","precision")},
            "prior":      {k: R[k] for k in ("tp","fp","tn","fn","detection","fp_rate","precision")},
        }
        print(f"\n## axis: {axis_name}  ({len(cases)} cases)")
        print(f"   principled : detection {P['detection']:.0%}  "
              f"FP-rate {P['fp_rate']:.0%}  precision {P['precision']:.0%}  "
              f"(TP {P['tp']} FP {P['fp']} TN {P['tn']} FN {P['fn']})")
        print(f"   naive      : detection {N['detection']:.0%}  "
              f"FP-rate {N['fp_rate']:.0%}  precision {N['precision']:.0%}  "
              f"(TP {N['tp']} FP {N['fp']} TN {N['tn']} FN {N['fn']})")
        print(f"   prior      : detection {R['detection']:.0%}  "
              f"(no bias axis existed — degenerate cases scored clean)")
        # spotlight: cases the two detectors disagree on
        for (cid, label, nm, exp, gotP), gotN in zip(
                [(r[0], r[1], r[2], r[3], r[4]) for r in P["rows"]],
                [r[4] for r in N["rows"]]):
            if gotP != gotN:
                mark = "near-miss" if nm else ""
                verdictP = "OK " if (gotP == exp) else "ERR"
                verdictN = "OK " if (gotN == exp) else "ERR"
                print(f"     - {cid:<3} [{label:<10}] {mark:<9}  "
                      f"principled={int(gotP)}({verdictP})  naive={int(gotN)}({verdictN})")
                near_miss_log.append(dict(axis=axis_key, id=cid, label=label,
                                          near_miss=nm, principled=gotP, naive=gotN,
                                          expected=exp))

    # --- aggregate over the whole fixture ---
    tot_tp = sum(s["principled"]["tp"] for s in summary.values())
    tot_fn = sum(s["principled"]["fn"] for s in summary.values())
    tot_fp = sum(s["principled"]["fp"] for s in summary.values())
    tot_tn = sum(s["principled"]["tn"] for s in summary.values())
    overall_det = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) else 1.0
    overall_fpr = tot_fp / (tot_fp + tot_tn) if (tot_fp + tot_tn) else 0.0
    n_near = sum(1 for ax in FIXTURE["axes"].values() for c in ax["cases"] if c.get("near_miss"))
    naive_nearmiss_err = sum(
        1 for e in near_miss_log if e["near_miss"] and e["naive"] != e["expected"])

    print("\n" + "=" * 78)
    print(f"AGGREGATE (principled): detection {overall_det:.0%} on planted bias "
          f"({tot_tp}/{tot_tp+tot_fn}),  false-positives {tot_fp} on sound "
          f"(FP-rate {overall_fpr:.0%}).")
    print(f"NEAR-MISSES: {n_near} adversarial cases; the naive baseline gets "
          f"{naive_nearmiss_err} of them wrong, the principled detector gets "
          f"{sum(1 for e in near_miss_log if e['near_miss'] and e['principled']!=e['expected'])} wrong.")
    verdict = ("KEEP-SIGNAL" if (overall_det >= 0.9 and tot_fp == 0 and naive_nearmiss_err > 0)
               else "DISCARD-SIGNAL")
    print(f"GATE: {verdict}  "
          f"(KEEP needs high detection + zero FP on sound + naive demonstrably worse)")
    print("=" * 78)

    out = dict(axes=summary,
               aggregate=dict(detection=overall_det, fp_rate=overall_fpr,
                              tp=tot_tp, fp=tot_fp, tn=tot_tn, fn=tot_fn,
                              n_near_miss=n_near,
                              naive_near_miss_errors=naive_nearmiss_err),
               verdict=verdict)
    (HERE / "results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {HERE / 'results.json'}")


if __name__ == "__main__":
    main()
