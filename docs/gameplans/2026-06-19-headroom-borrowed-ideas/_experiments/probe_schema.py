"""Probe the Claude Code transcript JSONL schema (Phase 3 feasibility).

Usage: .venv/bin/python .../probe_schema.py <transcript.jsonl>
"""
import collections
import json
import sys

p = sys.argv[1]
types = collections.Counter()
block_types = collections.Counter()
tool_use_names = collections.Counter()
err_results = 0
sample_user_text = None
sample_err = None
sample_tool_use = None

with open(p, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        types[r.get("type")] += 1
        msg = r.get("message") if isinstance(r.get("message"), dict) else None
        content = (msg or {}).get("content", r.get("content"))
        if isinstance(content, str):
            if r.get("type") == "user" and sample_user_text is None and content.strip():
                sample_user_text = content[:240]
        elif isinstance(content, list):
            for b in content:
                if not isinstance(b, dict):
                    continue
                bt = b.get("type")
                block_types[bt] += 1
                if bt == "tool_use":
                    tool_use_names[b.get("name")] += 1
                    if sample_tool_use is None:
                        sample_tool_use = {k: b.get(k) for k in ("type", "name", "id")}
                elif bt == "tool_result":
                    if b.get("is_error"):
                        err_results += 1
                        if sample_err is None:
                            sample_err = b

print("record types:", dict(types))
print("block types:", dict(block_types))
print("top tool_use names:", tool_use_names.most_common(12))
print("is_error tool_results:", err_results)
print("sample user text:", repr(sample_user_text))
print("sample tool_use:", sample_tool_use)
if sample_err:
    print("sample error keys:", list(sample_err.keys()))
    c = sample_err.get("content")
    print("sample error content:", repr(c)[:300])
