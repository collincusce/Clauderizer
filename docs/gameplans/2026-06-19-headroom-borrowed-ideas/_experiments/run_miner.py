"""Run the failure-miner over the project's transcript corpus and print proposals
for manual precision labeling (Phase 3 keep/discard evidence)."""
import os
import sys
from collections import Counter

from clauderizer import learn

# Pass the transcript dir as argv[1], or set CLAUDERIZER_TRANSCRIPT_CORPUS —
# no machine-specific home-dir/username literal in the repo.
DIR = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
    "CLAUDERIZER_TRANSCRIPT_CORPUS", "")

res = learn.mine_dir(DIR)
total = 0
kinds = Counter()
for fname, props in res.items():
    if not props:
        continue
    print(f"\n===== {fname} : {len(props)} proposals =====")
    for i, p in enumerate(props):
        total += 1
        kinds[p["kind"]] += 1
        print(f"[{i + 1}] {p['kind']} | {p['evidence']}")
        print(f"     {p['error_excerpt']}")

print(f"\n##### files with proposals: {sum(1 for v in res.values() if v)}"
      f" / {len(res)} | TOTAL proposals: {total} | by kind: {dict(kinds)} #####")
