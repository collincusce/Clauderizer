"""Interrupted-session detection — work landed, the closing writes never ran.
(D-070, intent-postmortem-with-backstop-landings)

The complement of :mod:`memory_lag` on the other side of the phase gate:
memory-lag fires when the tracker claims NO work began on a phase git says is
being worked; this detector fires when a phase IS ``in_progress`` and real
commits landed, but every closing write of the Ending Protocol is absent —
no next-phase handoff, no completion summary, no outputs block. That is the
shape of a session that died (or was abandoned) mid-phase: the work exists,
the memory is behind the repo, and nothing else will ever say so.

Fire-quiet geometry errs SILENT (binding vetting condition, INVARIANT-08):
fire only when the phase is ``in_progress`` AND at least one non-docs commit
landed since the tracker anchor AND every closing residue is absent AND the
session ledger cannot vouch for the claimant. A provably ALIVE claimant (or
this very process) is ordinary mid-phase work; a provably DEAD claimant is
:mod:`stranded`'s finding — this detector speaks only where the ledger cannot
grade (no stamp, inconclusive probe), which keeps exactly one voice per repo
state and an active session's own digest byte-identical while it works. Any
closing artifact — a phase summary, an outputs block, the next phase's
handoff (post-mortem for the last phase) — also keeps it quiet, so a
legitimately multi-session phase mid-work is never nagged. Evidence is derived from git and the tracked files, never from
the tracker asserting itself (D-065); no anchor, no git, or zero work commits
means no claim.

Advisory only (INVARIANT-05): the wording is adoption guidance — a backstop
is a signal, not a license to skip the steps. Read-only and
exception-swallowed for hook safety (INVARIANT-06); reuses memory_lag's
bounded ``_git`` (10s timeout). The two detectors are disjoint by predicate
(unstarted vs in_progress states), so they can never speak over each other.
"""

from __future__ import annotations

from ..paths import RepoPaths
from . import _tables, memory_lag


def _phase_rows(paths: RepoPaths, gid: str):
    gdir = paths.gameplan_dir(gid)
    for name in memory_lag.TRACKER_FILES:
        p = gdir / name
        if p.exists():
            try:
                return _tables.parse_phase_table(p.read_text(encoding="utf-8"))
            except OSError:
                return []
    return []


def _closing_residues(paths: RepoPaths, gid: str, num: str) -> list[str]:
    """The Ending-Protocol writes for phase ``num`` that are ABSENT — named by
    the blessed op that would have produced each. Empty list = the protocol ran
    (at least partially) and the detector must stay quiet."""
    gdir = paths.gameplan_dir(gid)
    missing: list[str] = []

    rows = _phase_rows(paths, gid)
    nums = [r.number for r in rows]
    nxt = None
    if num in nums:
        i = nums.index(num)
        nxt = nums[i + 1] if i + 1 < len(nums) else None
    if nxt is not None and not (gdir / "handoffs" / f"PHASE-{nxt}-HANDOFF.md").exists():
        missing.append("cz_write_handoff")
    elif nxt is None:
        # Last phase: the closing artifact is the post-mortem, not a handoff.
        if not (gdir / "POST-MORTEM.md").exists():
            missing.append("post-mortem")

    idx = gdir / "CHAT-HANDOFF-INDEX.md"
    summary_present = False
    if idx.exists():
        try:
            text = idx.read_text(encoding="utf-8")
            summary_present = f"### Phase {num}" in text.split(
                "Per-Phase Completion Summaries", 1)[-1]
        except OSError:
            summary_present = False
    if not summary_present:
        missing.append("cz_add_phase_summary")

    status_doc = gdir / "PHASE-STATUS.md"
    outputs_present = False
    if status_doc.exists():
        try:
            outputs_present = (f"### Phase {num} Outputs"
                               in status_doc.read_text(encoding="utf-8"))
        except OSError:
            outputs_present = False
    if not outputs_present:
        missing.append("cz_add_output")

    return missing


# The full residue set that must ALL be absent for the detector to fire.
_CORE_RESIDUES = 3


def detect(paths: RepoPaths, gid: str, target: dict | None,
           status: str | None) -> dict | None:
    """The interrupted-session record, or ``None`` when there is no evidence.

    Returns ``{phase, name, commits, anchor, anchor_date, never_ran, scratch}``
    only when work landed after the anchor and NO closing write exists.
    """
    if not gid or not target or status != "in_progress":
        return None
    # Liveness gate (one voice per repo state): a claimant that is provably
    # ALIVE — or is this very process — means ordinary mid-phase work, not an
    # interruption; a claimant that is provably DEAD is stranded.py's finding
    # and its judgment menu already covers adoption. This detector speaks only
    # for the cases the ledger cannot grade: no stamp (legacy repo, crash
    # before stamping) or an inconclusive probe (cli transport, other host).
    import os as _os

    from .. import session_ledger

    entry = session_ledger.last_stamp(paths, gid, str(target.get("number")))
    if entry:
        if entry.get("pid") == _os.getpid():
            return None
        if session_ledger.probe(entry) in ("alive", "dead"):
            return None
    anchored = memory_lag.tracker_anchor(paths, gid)
    if anchored is None:
        return None
    sha, date = anchored
    n = memory_lag.work_commits_since(paths, sha)
    if n <= 0:
        return None
    num = str(target.get("number"))
    never_ran = _closing_residues(paths, gid, num)
    if len(never_ran) < _CORE_RESIDUES:
        return None                    # any closing artifact present -> quiet
    from .status_bundle import pending_cascades

    if pending_cascades(paths.gameplan_dir(gid) / "_cascade-reports"):
        never_ran.append("cz_resolve_cascade")
    code, out = memory_lag._git(paths.root, "status", "--porcelain")
    scratch = bool(code == 0 and out.strip())
    return {
        "phase": num,
        "name": target.get("name"),
        "commits": n,
        "anchor": sha,
        "anchor_date": date,
        "never_ran": never_ran,
        "scratch": scratch,
    }


def describe(rec: dict) -> str:
    """The single adoption wording every surface shares (L-55 seam). Subsumes
    the memory-lag claim (the memory is behind the repo) and explains the two
    downstream frictions so no surface needs a second phrasing: a dirty tree
    FAILs pre-flight's clean_tree, and do-phase STOPs and reports on any failed
    pre-flight."""
    plural = "commit" if rec["commits"] == 1 else "commits"
    scratch = (" Uncommitted scratch is present — treat it as unverified "
               "prior-session work; a dirty tree FAILs pre-flight's clean_tree "
               "until adopted or stashed, and do-phase STOPs and reports on a "
               "failed pre-flight by design." if rec.get("scratch") else "")
    return (
        f"phase {rec['phase']} \"{rec['name']}\" is in_progress with "
        f"{rec['commits']} non-docs {plural} since the tracker was last written "
        f"({rec['anchor']}, {rec['anchor_date']}), and its closing writes never "
        f"ran ({', '.join(rec['never_ran'])}) — likely an interrupted session; "
        f"the memory is behind the repo. Adopt the work: review the diff as "
        f"prior-session work, continue the phase, then run the FULL Ending "
        f"Protocol — a backstop is a signal, not a license to skip steps."
        f"{scratch}"
    )
