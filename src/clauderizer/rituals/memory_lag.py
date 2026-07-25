"""Memory-lag detection — has the tracker fallen behind the repo? (H-22, D-069)

Every other discipline in this engine already has a detector: cascade hygiene,
unchecked exit criteria, unresolved open items, corpus redundancy, wiring drift.
The one discipline that keeps the tracker current had none — so 1.14.0
implemented, tested and pushed two entire phases across eight commits while its
phase table still read "not started", and nothing anywhere emitted a signal. It
was caught only because the user happened to announce a session switch.

The claim this module makes is derived from git, never from the tracker
asserting itself (D-065):

    anchor  the last commit that touched this gameplan's phase-status tracker.
            That IS "the last recorded state change" — read as evidence, rather
            than trusted as a date some writer typed into a cell.
    work    commits after the anchor touching anything outside the docs tree and
            .clauderizer/ — i.e. outside the paths Clauderizer itself owns.
    lag     the tracker's last write left the phase the gameplan is AT still
            unstarted (not_started / ready), yet ``work`` is non-empty.

The phase-state gate is what keeps this quiet enough to be worth reading. An
in_progress phase is SUPPOSED to accumulate commits, so the detector never fires
there; it fires only when the tracker claims no work has begun on the very phase
git says is being worked on. That is exactly the shape of the 1.14.0 failure, and
it is a falsifiable claim rather than a vague staleness score. The cost of the
gate is honest and worth stating: a phase left marked in_progress long after it
was really finished is NOT detected, because git cannot distinguish "still being
worked on" from "done but unrecorded".

Advisory only (INVARIANT-05) — it never blocks a mutation or a transition.
Read-only and exception-swallowing so a hook may call it (INVARIANT-06), and
silent when there is no lag so an unaffected digest stays byte-identical
(INVARIANT-08).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..paths import RepoPaths

# Bounded like release_check._git: a hook must never hang on a wedged git.
_GIT_TIMEOUT = 10

# The tracker files a phase table may live in, newest-convention first. Both are
# consulted because _phase_rows reads either one.
TRACKER_FILES = ("CHAT-HANDOFF-INDEX.md", "PHASE-STATUS.md")

# Phase states that assert NO work has begun. Commits landing while the tracker
# says this are the drift signal; any other state is expected to accrue commits.
UNSTARTED_STATES = frozenset({"not_started", "ready"})


def _git(root: Path, *args: str) -> tuple[int, str]:
    """``(exit_code, stdout)`` — never raises, so a broken or absent git is just
    "no evidence" rather than a dead digest (INVARIANT-04/06)."""
    try:
        r = subprocess.run(["git", *args], cwd=str(root), capture_output=True,
                           encoding="utf-8", errors="replace", timeout=_GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return r.returncode, r.stdout.strip()


def _owned_prefixes(paths: RepoPaths) -> list[str]:
    """Repo-relative directories Clauderizer itself writes — a commit touching
    ONLY these is bookkeeping, not work the tracker should have known about.
    Derived from the resolved paths, so a repo with a custom ``docs_rel`` excludes
    its real docs tree rather than a hardcoded "docs"."""
    out = [".clauderizer"]
    try:
        rel = paths.docs.resolve().relative_to(paths.root.resolve()).as_posix()
    except ValueError:  # docs configured outside the repo root
        rel = ""
    if rel and rel != ".":
        out.append(rel)
    return out


def tracker_anchor(paths: RepoPaths, gid: str) -> tuple[str, str] | None:
    """``(short_sha, iso_date)`` of the last commit to touch ``gid``'s phase
    tracker, or ``None`` when git has never seen one (fresh gameplan, no git,
    untracked docs). No anchor means no claim — the detector stays silent."""
    gdir = paths.gameplan_dir(gid)
    rel: list[str] = []
    for name in TRACKER_FILES:
        try:
            rel.append((gdir / name).resolve().relative_to(paths.root.resolve()).as_posix())
        except ValueError:
            continue
    if not rel:
        return None
    code, out = _git(paths.root, "log", "-1", "--format=%h %cs", "--", *rel)
    if code != 0 or not out:
        return None
    sha, _, date = out.partition(" ")
    return (sha, date.strip())


def work_commits_since(paths: RepoPaths, anchor: str) -> int:
    """Count commits after ``anchor`` that touch anything Clauderizer does not
    own. ``-1`` when git could not answer (distinguishable from a real zero)."""
    excludes = [f":(exclude){p}" for p in _owned_prefixes(paths)]
    code, out = _git(paths.root, "rev-list", "--count", f"{anchor}..HEAD",
                     "--", ".", *excludes)
    if code != 0 or not out.isdigit():
        return -1
    return int(out)


def detect(paths: RepoPaths, gid: str, target: dict | None,
           status: str | None) -> dict | None:
    """The lag record for a gameplan, or ``None`` when memory is current.

    ``target`` is the phase the gameplan is AT (``current_phase or next_phase``
    as the digest already computes it) and ``status`` that phase's normalized
    state. Returns ``{phase, name, state, commits, anchor, anchor_date}``.
    """
    if not gid or not target or status not in UNSTARTED_STATES:
        return None
    anchored = tracker_anchor(paths, gid)
    if anchored is None:
        return None
    sha, date = anchored
    n = work_commits_since(paths, sha)
    if n <= 0:
        return None
    return {
        "phase": target.get("number"),
        "name": target.get("name"),
        "state": status,
        "commits": n,
        "anchor": sha,
        "anchor_date": date,
    }


def describe(lag: dict) -> str:
    """The one-line human claim, shared by the digest and the pre-flight check so
    the two can never word the same finding differently (L-55 seam)."""
    plural = "commit" if lag["commits"] == 1 else "commits"
    return (
        f"phase {lag['phase']} \"{lag['name']}\" still reads "
        f"{lag['state'].replace('_', ' ')}, but {lag['commits']} non-docs "
        f"{plural} landed since the tracker was last written "
        f"({lag['anchor']}, {lag['anchor_date']}) — the memory is behind the "
        f"repo. cz_transition_phase to record where the work actually is."
    )
