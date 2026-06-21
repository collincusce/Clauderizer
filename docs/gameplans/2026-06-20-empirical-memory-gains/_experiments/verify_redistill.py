"""Post-apply coverage proof for the LESSONS.md re-distillation.

Reads the LIVE docs/LESSONS.md (now 16 active + 9 obsolete), and for every
obsoleted source lesson confirms its concept is still retrievable from the ACTIVE
set via a synthesis. The query is built from the lesson's own text with the
provenance + "(obsolete ...: consolidated into L-NN)" marker stripped, so the
check cannot cheat by matching the synthesis id named in the marker.

Run: PYTHONPATH=. .venv/bin/python <this file>
"""
import re

from clauderizer import analyze
from clauderizer.markdown import lesson_state
from clauderizer.ops import repo_ctx

paths, _ = repo_ctx()
text = paths.doc("LESSONS").read_text(encoding="utf-8")

active: dict[str, str] = {}
obsolete: dict[str, str] = {}
for line in text.splitlines():
    s = line.strip()
    m = re.match(r"\*\*(L-\d+)\.\*\*", s)
    if not m:
        continue
    core = s.split("*(from")[0]                      # drop provenance + trailing markers
    body = re.sub(r"^\*\*L-\d+\.\*\*", "", core).strip()
    (active if lesson_state.is_active(s) else obsolete)[m.group(1)] = body

SYNTH = {"L-22", "L-23", "L-24", "L-25"}
active_entries = [{"id": i, "title": t, "body": t} for i, t in active.items()]

misses = []
for lid, body in obsolete.items():
    q = " ".join(sorted(analyze._tokens(body)))
    top3 = [r["id"] for r in analyze.rank_relevant(q, active_entries, k=3)]
    if not (set(top3) & SYNTH):
        misses.append((lid, top3))

print(f"active={len(active)} obsolete={len(obsolete)} syntheses={sorted(SYNTH & set(active))}")
print(f"obsoleted-concept coverage by an active synthesis: "
      f"{len(obsolete) - len(misses)}/{len(obsolete)}")
print("MISSES:", misses or "NONE")
print("VERDICT:", "COVERAGE PRESERVED" if not misses and len(active) == 16 else "REGRESSION")
