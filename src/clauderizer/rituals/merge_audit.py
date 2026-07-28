"""Merge-integrity audit for canonical docs (2.0 P4) — git evidence ONLY.

Tracked markdown is the memory; a bad merge is memory corruption. Two defect
classes are detectable from git alone: a three-way LOST UPDATE (the merge result
kept one parent's version of a docs file while silently discarding the other
side's change) and COMMITTED CONFLICT MARKERS (a `<<<<<<<`/`=======`/`>>>>>>>`
triad that made it into a tracked doc). Both are read off merge parents +
merge-base + blob comparison at audit time — there is NO writer-side audit
ledger and NO persisted finding state anywhere (revision.py is explicit that no
audit log exists; a tracked ledger would recreate the revision.json
merge-conflict failure D-067 removed). Findings therefore self-clear the moment
the history no longer shows the defect (D-065/D-069: claims derive from
evidence actually read).

SQUASH BLIND SPOT — stated here and in every user-facing wording: a squash
commit has ONE parent, so `git log --merges` lists zero entries for it and this
audit sees TRUE MERGE COMMITS only. A squash that flattened away a teammate's
docs change is invisible here; do not describe this audit as catching that
scenario.

Cost discipline: the compute path runs from the SessionStart digest, so the
subprocess count is O(1) — capped at the SINGLE most recent docs-touching merge
with one batched ``ls-tree -r`` per commit (merge, both parents, merge-base)
plus one ``git grep`` for marker candidates; marker-content fetches are capped
at :data:`_MAX_MARKER_FILES`. Advisory throughout (INVARIANT-05): surfaced via
cz_audit / cz_preflight / cz_status only — no new MCP tool — and silent on a
healthy history (zero findings add zero bytes, INVARIANT-08).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from ..paths import RepoPaths

#: Marker-content fetches per audit — bounds the only per-finding subprocess.
_MAX_MARKER_FILES = 4

_MARKER_OPEN = re.compile(r"^<{7} ")
_MARKER_MID = re.compile(r"^={7}$")
_MARKER_CLOSE = re.compile(r"^>{7} ")
_FENCE = re.compile(r"^\s*(```|~~~)")


def _git(root: Path, *args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", "-C", str(root), *args],
                           capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return r.returncode, r.stdout


def _blob_map(root: Path, commit: str, docs_rel: str) -> dict[str, str] | None:
    """``{repo-relative path: blob sha}`` for the docs tree at ``commit`` — one
    batched ``ls-tree -r`` per commit, never a per-file spawn."""
    code, out = _git(root, "ls-tree", "-r", commit, "--", docs_rel)
    if code != 0:
        return None
    blobs: dict[str, str] = {}
    for line in out.splitlines():
        # "<mode> blob <sha>\t<path>"
        try:
            meta, path = line.split("\t", 1)
            _mode, kind, sha = meta.split()
        except ValueError:
            continue
        if kind == "blob":
            blobs[path] = sha
    return blobs


def _unfenced_triad(text: str) -> bool:
    """True when a full conflict-marker triad appears IN ORDER outside fenced
    code blocks. Docs that QUOTE markers inside ``` fences — a lesson about this
    very audit, say — are exempt by construction; the behavior is pinned by
    test. A lone ``=======`` (an ASCII banner) never counts: all three lines
    are required, in order."""
    state = 0  # 0 want open, 1 want mid, 2 want close
    fenced = False
    for line in text.splitlines():
        if _FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if state == 0 and _MARKER_OPEN.match(line):
            state = 1
        elif state == 1 and _MARKER_MID.match(line):
            state = 2
        elif state == 2 and _MARKER_CLOSE.match(line):
            return True
    return False


def compute(paths: RepoPaths) -> dict | None:
    """Audit the single most recent docs-touching merge; None when quiet.

    Quiet means: no such merge exists, the repo is not a git repo, the merge is
    an octopus (more than two parents — out of scope, noted in the result when
    findings exist elsewhere), or the merge shows neither defect class. Never
    raises; every git failure degrades to quiet (a hook must not die here,
    INVARIANT-06)."""
    root = paths.root
    try:
        docs_rel = str(paths.docs.relative_to(root))
    except ValueError:
        return None

    # --full-history is load-bearing: default history SIMPLIFICATION drops a
    # merge that is TREESAME to one parent for the path — which is EXACTLY the
    # lost-update shape (the result kept one side verbatim). Without the flag
    # the audit is blind to precisely the merges it exists to catch.
    code, out = _git(root, "log", "--full-history", "--merges", "-1",
                     "--format=%H", "--", docs_rel)
    merge = out.strip().splitlines()[0].strip() if code == 0 and out.strip() else ""
    if not merge:
        return None
    code, out = _git(root, "rev-list", "--parents", "-n", "1", merge)
    parts = out.split() if code == 0 else []
    if len(parts) != 3:          # octopus or unreadable — out of scope
        return None
    _m, p1, p2 = parts
    code, out = _git(root, "merge-base", p1, p2)
    base = out.strip() if code == 0 and out.strip() else None

    findings: list[dict] = []

    # --- lost-update class (true merges only; squashes are invisible here) ----
    if base:
        maps = {c: _blob_map(root, c, docs_rel) for c in (merge, p1, p2, base)}
        if all(m is not None for m in maps.values()):
            bm, m1, m2, mm = maps[base], maps[p1], maps[p2], maps[merge]
            for f in sorted(set(bm) | set(m1) | set(m2) | set(mm)):
                b, a1, a2, r = bm.get(f), m1.get(f), m2.get(f), mm.get(f)
                if a1 == a2:
                    continue          # sides agree — nothing to lose
                # side-2 changed f vs base, but the merge kept side-1 verbatim
                if a2 != b and r == a1 and a1 != a2:
                    findings.append({
                        "kind": "lost_update", "path": f, "merge": merge[:12],
                        "dropped_side": "second parent",
                        "detail": (f"{f}: merge {merge[:12]} kept the first "
                                   f"parent's version while the second parent had "
                                   f"changed it since the merge-base — the change "
                                   f"was silently discarded"),
                    })
                elif a1 != b and r == a2 and a1 != a2:
                    findings.append({
                        "kind": "lost_update", "path": f, "merge": merge[:12],
                        "dropped_side": "first parent",
                        "detail": (f"{f}: merge {merge[:12]} kept the second "
                                   f"parent's version while the first parent had "
                                   f"changed it since the merge-base — the change "
                                   f"was silently discarded"),
                    })

    # --- committed-conflict-marker class -------------------------------------
    code, out = _git(root, "grep", "-l", "-E", "^<{7} ", merge, "--", docs_rel)
    if code == 0 and out.strip():
        # "<commit>:<path>" per line; content fetch capped, fence-aware.
        hits = [ln.split(":", 1)[1] for ln in out.strip().splitlines()
                if ":" in ln][:_MAX_MARKER_FILES]
        for f in hits:
            code, content = _git(root, "show", f"{merge}:{f}")
            if code == 0 and _unfenced_triad(content):
                findings.append({
                    "kind": "conflict_markers", "path": f, "merge": merge[:12],
                    "detail": (f"{f}: a conflict-marker triad is committed in the "
                               f"docs tree at merge {merge[:12]} — the merge was "
                               f"recorded with the conflict unresolved"),
                })

    if not findings:
        return None
    return {
        "merge": merge[:12],
        "findings": findings,
        "summary": describe(findings),
    }


def describe(findings: list[dict]) -> str:
    """The one shared wording (L-55): every surface renders this sentence, and
    the squash blind spot is stated to the USER, not just in the docstring."""
    n = len(findings)
    kinds = sorted({f["kind"] for f in findings})
    what = " + ".join(k.replace("_", " ") for k in kinds)
    files = ", ".join(sorted({f["path"] for f in findings})[:3])
    return (f"{n} merge-integrity finding(s) [{what}] in the most recent "
            f"docs-touching merge ({files}) — reconcile the canonical docs by "
            f"hand or re-merge; note this audit sees true merges only, squash "
            f"merges are invisible to it")
