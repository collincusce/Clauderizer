"""Phase 7 follow-up: GATE the re-distillation of docs/LESSONS.md before applying it.

Re-distilling curated, append-only memory risks silently dropping a nuance. This
proves a NET GAIN first: for EVERY original lesson, auto-derive a query from its
own distinctive tokens (no hand-picked probes), and require that after
consolidation that query still surfaces the lesson's synthesis in the ranker
top-k. Coverage preserved + rollup shrinks == net gain. Any miss => the synthesis
dropped something => do not apply.

Run from repo root:
  PYTHONPATH=. .venv/bin/python \
    docs/gameplans/2026-06-20-empirical-memory-gains/_experiments/redistill_lessons.py
"""
import re

from clauderizer import analyze
from clauderizer.ops import repo_ctx
from tests.benchmarks import metrics

paths, _ = repo_ctx()
text = paths.doc("LESSONS").read_text(encoding="utf-8")

orig: dict[str, str] = {}
for m in re.finditer(r"\*\*(L-\d+)\.\*\*\s*(.+)", text):
    body = re.sub(r"\*\((from|evidence:).*?\)\*", "", m.group(2)).strip()
    orig[m.group(1)] = body

# 4 conservative clusters — only the tightest overlaps. Each synthesis preserves
# every sub-nuance of its sources (verified by the coverage probe below).
CLUSTERS = {
    "round-trip + render-validity testing": (["L-01", "L-06"],
        "Round-trip idempotency (apply-twice == apply-once) through the engine's own "
        "parser is the load-bearing test for every mutation - but it is necessary, NOT "
        "sufficient: an engine can read its own corruption indefinitely, so also assert "
        "render-validity for EXTERNAL readers (contiguous tables, valid markdown)."),
    "prove it on the real artifact, not a proxy": (["L-12", "L-13"],
        "The author's environment never exercises the real thing - a monkeypatched-platform "
        "test is not the platform, and an editable venv is not uvx --from PyPI. Execute the "
        "real surface: preview a foreign CI cell in a native venv on the target OS (one local "
        "cycle caught every win32 defect nine months of mocked-platform tests missed), and walk "
        "the published install/distribution path from a fresh environment (the README first "
        "command was broken in four places while every test passed). Then pin each as a CI job "
        "that runs the doc-exact text, with assertions that self-arm when the fix they guard is "
        "unreleased."),
    "malformed-input robustness": (["L-18", "L-19"],
        "A 'degrades gracefully' claim is only as strong as the input diversity it was tested "
        "against (non-dict valid JSON, BOM/CRLF, unicode, empty), AND tolerance must wrap the "
        "WHOLE pipeline, not just json.loads: guard the file decode before it (non-UTF-8 -> "
        "UnicodeDecodeError) and the shape after it (unhashable key, non-str field), and net "
        "per-item in any batch loop so one bad input never aborts the run. Corollary: a regex "
        "encoding a domain rule must encode it precisely ([1-9]\\d* failed, not \\d+ failed). "
        "Adversarial-input tests belong in the same phase that makes the robustness claim."),
    "prove a probe witnesses what it claims": (["L-02", "L-09", "L-10"],
        "A health check / guard must verify CAPABILITY, not presence - a green check on a "
        "non-launchable setup is worse than none. Prove every probe at the granularity it "
        "reports, in BOTH directions (it must fire on the failure it exists for and stay green "
        "on health, per matrix cell / per argument), and prefer in-band identity (the output "
        "must claim who and what version ran) over exit codes: locally-sound guards compose "
        "into false green (a wrapper that always exits 0 defeats a spawn probe that reads exit "
        "0 as launchable). The probe must traverse the consumer's exact execution leg, shell "
        "quirks included."),
}

merged: dict[str, str] = {}      # source L-id -> synthesis key
synth_entries: list[dict] = []
for key, (srcs, syn) in CLUSTERS.items():
    for s in srcs:
        merged[s] = key
    synth_entries.append({"id": key, "title": syn, "body": syn})

before = [{"id": i, "title": t, "body": t} for i, t in orig.items()]
after = [{"id": i, "title": t, "body": t} for i, t in orig.items() if i not in merged]
after += synth_entries

K = 3
rb = ra = 0
fails = []
for i, t in orig.items():
    q = " ".join(sorted(analyze._tokens(t)))   # the lesson's OWN distinctive tokens
    target = merged.get(i, i)                    # its synthesis, or itself if unchanged
    if i in {r["id"] for r in analyze.rank_relevant(q, before, k=K)}:
        rb += 1
    after_ids = {r["id"] for r in analyze.rank_relevant(q, after, k=K)}
    if target in after_ids:
        ra += 1
    else:
        fails.append((i, target, sorted(after_ids)))

tok_before = metrics.token_estimate("\n".join(orig.values()))
tok_after = metrics.token_estimate("\n".join(e["body"] for e in after))
print(f"active lessons: {len(before)} -> {len(after)}  (net {len(after) - len(before)})")
print(f"coverage recall@{K}: before {rb}/{len(orig)}  after {ra}/{len(orig)}")
print(f"rollup tokens: {tok_before} -> {tok_after}  ({100 * (1 - tok_after / tok_before):.0f}% cut)")
if fails:
    print("COVERAGE FAILS (a source whose synthesis is not in top-k for its own query):")
    for i, tgt, got in fails:
        print(f"  {i} -> expected {tgt}, top-{K} was {got}")
net = ra >= rb and not fails and tok_after < tok_before and ra == len(orig)
print("VERDICT:", "NET GAIN" if net else "NOT PROVEN - DO NOT APPLY")
