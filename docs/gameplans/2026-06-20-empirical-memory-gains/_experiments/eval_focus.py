"""Phase 1 experiment: focused-vs-full project-lesson injection.

Stage 1 (deterministic, here): does the lexical ranker surface the ANSWER lesson
in top-k? That is the ceiling for the focused arm — if retrieval misses, focusing
cannot help, so we learn it cheaply before spending agent-eval tokens.
Stage 2 (reading): emit focused/full prompts for the agent-eval workflow.

Run from repo root:
  PYTHONPATH=. .venv/bin/python \
    docs/gameplans/2026-06-20-empirical-memory-gains/_experiments/eval_focus.py
"""
import json
import re

from clauderizer import analyze
from clauderizer.ops import repo_ctx
from tests.benchmarks import agent_eval, metrics

paths, _ = repo_ctx()
text = paths.doc("LESSONS").read_text(encoding="utf-8")

# Parse "**L-NN.** body  *(from ...)*" into ranker entries (strip the provenance).
entries: list[dict] = []
for m in re.finditer(r"\*\*(L-\d+)\.\*\*\s*(.+)", text):
    body = re.sub(r"\*\(from.*?\)\*", "", m.group(2)).strip()
    entries.append({"id": m.group(1), "title": body, "body": body})

# Memory-dependent questions, each answerable by exactly one known lesson.
PROBES = [
    ("How should I verify a borrowed idea before shipping it?", "L-17"),
    ("What must I do before an irreversible release across the version registries?", "L-08"),
    ("Why can a health check pass on a setup that is actually broken?", "L-02"),
    ("How should I handle malformed or non-UTF-8 external input in a parser?", "L-19"),
    ("Where do I edit generated content like the CLAUDE.md stanza or the skills?", "L-16"),
    ("How do I keep reference docs from drifting when the tool surface changes?", "L-21"),
]

K = 5
hits = 0
payload = []
for q, ans in PROBES:
    ranked = [r["id"] for r in analyze.rank_relevant(q, entries, k=K)]
    hit = ans in ranked
    hits += int(hit)
    focused = [e for e in entries if e["id"] in set(ranked)]
    payload.append({
        "q": q, "answer": ans, "ranker_hit": hit, "ranked": ranked,
        "focused_prompt": agent_eval.make_prompt(agent_eval.render_entries(focused), q),
        "full_prompt": agent_eval.make_prompt(agent_eval.render_entries(entries), q),
    })

full_tok = metrics.token_estimate(agent_eval.render_entries(entries))
foc_tok = metrics.token_estimate(agent_eval.render_entries(entries[:K]))
print(f"entries={len(entries)}  RANKER recall@{K} = {hits}/{len(PROBES)} = {hits/len(PROBES):.2f}")
print(f"full_lessons_tok~{full_tok}  focused_topk_tok~{foc_tok}  reduction~{100*(1-foc_tok/full_tok):.0f}%")
for p in payload:
    print(f"  {p['answer']}: ranker_hit={p['ranker_hit']}  top5={p['ranked']}")
import os

_base = "docs/gameplans/2026-06-20-empirical-memory-gains/_experiments"
with open(f"{_base}/eval_focus_payload.json", "w", encoding="utf-8") as f:
    json.dump(payload, f)
# One file per probe x arm so each agent sees ONLY its arm (no cross-arm leakage).
_arms = f"{_base}/arms"
os.makedirs(_arms, exist_ok=True)
for i, p in enumerate(payload):
    with open(f"{_arms}/p{i}_focused.txt", "w", encoding="utf-8") as f:
        f.write(p["focused_prompt"])
    with open(f"{_arms}/p{i}_full.txt", "w", encoding="utf-8") as f:
        f.write(p["full_prompt"])
print(f"payload -> {_base}/eval_focus_payload.json ; {2 * len(payload)} arm files -> {_arms}")
