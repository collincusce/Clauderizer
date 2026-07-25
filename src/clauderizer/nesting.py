"""Nested clauderized installs — two repos, one session, two contradicting digests.

``/home/ccusce`` is itself a clauderized repo containing ``/home/ccusce/Clauderizer``,
so TWO SessionStart hooks fire and the OUTER one announces "No active gameplan"
about a repo that is mid-release. That was the first thing in the executing
session's context, and it was read past for an entire release before a second,
colder session flagged it (H-23).

INVARIANT-08's at-most-once guarantee is enforced by an in-memory, per-process
signal, which nesting defeats *structurally*: these are two separate processes,
each perfectly correct about its own repo. A shared flag would be the wrong fix —
that is persisted cross-process state, which INVARIANT-05/08 rule out.

The right frame is **ownership**. For any session cwd, exactly one clauderized
repo owns it: the nearest clauderized ancestor. An install that is not the owner
of the session it was fired for stays silent. That is decided fresh from the hook
payload on every event — no flag, no file, nothing to fall out of date.

Nothing here writes; the whole module is read-only path arithmetic plus a bounded
directory scan, so a hook may call it (INVARIANT-06).
"""

from __future__ import annotations

from pathlib import Path

from .paths import find_repo_root

# Bounds for the descendant scan (doctor's report). A clauderized install nested
# more deeply than this is not the pathology H-23 describes, and an unbounded
# walk of a home directory is not something `doctor` may do.
MAX_SCAN_DEPTH = 4

# Directories never worth descending for a nested install: heavy vendor trees and
# anything hidden (a `.clauderizer` is FOUND by probing a candidate's child, never
# by walking into dot-directories).
_SKIP_DIRS = frozenset({
    "node_modules", "venv", "env", "target", "build", "dist", "vendor",
    "__pycache__", "site-packages", "Library", "AppData", "snap",
})


def is_clauderized(d: Path) -> bool:
    """True when ``d`` is the root of a clauderized repo."""
    try:
        return (d / ".clauderizer" / "config.toml").is_file()
    except OSError:
        return False


def owner_of(cwd: Path | str | None) -> Path | None:
    """The clauderized repo that OWNS ``cwd`` — its nearest clauderized ancestor
    — or ``None`` when no install covers it."""
    if not cwd:
        return None
    try:
        start = Path(cwd).resolve()
    except (OSError, ValueError):
        return None
    if not start.exists():
        return None
    root = find_repo_root(start)
    return root if is_clauderized(root) else None


def outranked_by(anchored_root: Path, session_cwd: Path | str | None) -> Path | None:
    """The nested install that should speak INSTEAD of the one anchored at
    ``anchored_root``, or ``None`` when this install is the right one to speak.

    Returns a path only in the H-23 shape: the session's owner is a *proper
    descendant* of this install's root. A session outside this repo entirely is
    deliberately NOT covered — silencing that case would change behavior for
    anyone who wired a hook globally on purpose, and INVARIANT-07 makes
    cross-host parity regressions a release blocker. Additive only.
    """
    owner = owner_of(session_cwd)
    if owner is None:
        return None
    try:
        anchored = Path(anchored_root).resolve()
    except (OSError, ValueError):
        return None
    if owner == anchored:
        return None
    return owner if owner.is_relative_to(anchored) else None


def nested_installs(root: Path, *, max_depth: int = MAX_SCAN_DEPTH) -> list[Path]:
    """Clauderized repos strictly BENEATH ``root``, nearest first.

    Bounded and pruned: a nested install's own subtree is not descended (the
    finding is the install, not everything under it), hidden and vendor
    directories are skipped, and depth is capped. Unreadable directories are
    skipped rather than raised — doctor reports what it can see.
    """
    try:
        root = Path(root).resolve()
    except (OSError, ValueError):
        return []
    found: list[Path] = []
    frontier = [(root, 0)]
    while frontier:
        current, depth = frontier.pop(0)
        if depth >= max_depth:
            continue
        try:
            children = sorted(p for p in current.iterdir() if p.is_dir())
        except OSError:
            continue
        for child in children:
            name = child.name
            if name.startswith(".") or name in _SKIP_DIRS or child.is_symlink():
                continue
            if is_clauderized(child):
                found.append(child)      # do NOT descend into a found install
                continue
            frontier.append((child, depth + 1))
    return found


def clauderized_ancestors(root: Path) -> list[Path]:
    """Clauderized repos strictly ABOVE ``root``, nearest first — what makes an
    ``init`` here a *nested* install rather than a fresh one."""
    try:
        root = Path(root).resolve()
    except (OSError, ValueError):
        return []
    return [p for p in root.parents if is_clauderized(p)]


def describe_nested(root: Path, nested: list[Path]) -> str:
    """The doctor line naming detected nested installs by path. Their wiring and
    stanzas rot invisibly — nothing else in the engine reports them."""
    rel = []
    for p in nested:
        try:
            rel.append(str(p.relative_to(root)))
        except ValueError:
            rel.append(str(p))
    return (
        f"{len(nested)} nested clauderized install(s) beneath this repo: "
        f"{', '.join(rel)}. Each carries its own hook, stanza and MCP wiring that "
        f"rot independently of this one. A session inside a nested repo is owned "
        f"by that repo — this install stays silent for it (H-23) — so its wiring "
        f"is only exercised, and only repairable, from inside it: run "
        f"`clauderize doctor` there."
    )


def describe_ancestors(root: Path, ancestors: list[Path]) -> str:
    """The init warning: this would be a SECOND install under an existing one."""
    return (
        f"this repo sits inside an existing clauderized repo ({ancestors[0]}) — "
        f"initializing here creates a SECOND, independent install. That is "
        f"supported (a session in this repo is owned by this repo and the outer "
        f"install stays quiet for it, H-23), but the two corpora never merge and "
        f"each must be maintained separately. If you meant to work inside the "
        f"outer repo's memory, run `clauderize status` from {ancestors[0]} instead."
    )
