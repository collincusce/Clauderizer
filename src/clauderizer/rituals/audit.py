"""The work/release self-audit gate (D-051): after a gameplan, audit the actual
WORK PRODUCT and release-readiness — distinct from cz_critique, which audits the
gameplan's MEMORY coherence (coverage/grounding/anti-bias over lessons).

Read-only, stdlib-only, advisory (INVARIANT-05): the engine ASSEMBLES the
deterministic signals it can compute and prompts the agent to judge each — it
never scores or blocks. Grounded in real misses this very system made and did
NOT catch through its normal close-out:

  * a version bumped in pyproject.toml but left stale in ``__init__.py`` — masked
    by a STALE editable install whose metadata still matched the old value, so a
    local green was a false signal and only a clean install exposed it;
  * a consumer of a changed entity (an uninstall path) left orphaned because it
    was never re-audited after the entity was repointed;
  * docs/guides asserting capabilities that were never verified.

The mechanical checks catch the first class outright; the judgment checklist
surfaces the irreducibly-human ones (verify in a clean env; re-audit every
consumer; claim only what you verified) the same advisory way the analyze and
critique gates do. Every check is guarded so it fires on the real defect and
stays quiet on healthy work (L-25: prove a guard in both directions).
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

from ..config import Config
from ..paths import RepoPaths
from . import status_bundle as sb

_VERSION_RE = re.compile(r"""^__version__\s*=\s*['"]([^'"]+)['"]""", re.MULTILINE)
# First version-looking token in a top-level Markdown heading, e.g. "## [1.7.0]"
# or "## 1.7.0 — title". Deliberately loose: any "## ..." with an X.Y[.Z] token.
_CHANGELOG_HEADING_RE = re.compile(r"^##\s+\[?v?(\d+\.\d+(?:\.\d+)?)", re.MULTILINE)


def _run_git(args: list[str], root: Path) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", "-C", str(root), *args],
                           capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return r.returncode, r.stdout


def _pyproject_version(root: Path) -> tuple[str | None, str | None]:
    """``([project].version, [project].name)`` from pyproject.toml, or (None, None)."""
    p = root / "pyproject.toml"
    if not p.is_file():
        return None, None
    try:
        proj = tomllib.loads(p.read_text(encoding="utf-8")).get("project", {})
    except (tomllib.TOMLDecodeError, OSError):
        return None, None
    return proj.get("version"), proj.get("name")


def _dunder_version(root: Path, pkg_name: str | None) -> tuple[str | None, str | None]:
    """A package ``__version__`` and the file it lives in, best-effort.

    Prefers the package that matches pyproject's ``name`` (normalized), under a
    ``src/`` or flat layout; falls back to the first ``__init__.py`` under ``src/``
    that declares one. Returns (version, repo-relative path) or (None, None).
    """
    candidates: list[Path] = []
    if pkg_name:
        norm = pkg_name.replace("-", "_")
        candidates += [root / "src" / norm / "__init__.py", root / norm / "__init__.py"]
    candidates += sorted((root / "src").glob("*/__init__.py")) if (root / "src").is_dir() else []
    for c in candidates:
        if not c.is_file():
            continue
        m = _VERSION_RE.search(c.read_text(encoding="utf-8"))
        if m:
            try:
                rel = str(c.relative_to(root))
            except ValueError:
                rel = str(c)
            return m.group(1), rel
    return None, None


def _changelog_top_version(root: Path) -> str | None:
    for name in ("CHANGELOG.md", "CHANGELOG.rst", "CHANGELOG"):
        p = root / name
        if p.is_file():
            m = _CHANGELOG_HEADING_RE.search(p.read_text(encoding="utf-8"))
            return m.group(1) if m else None
    return None


def _release_signals(root: Path) -> list[str]:
    """Version single-sourcing: pyproject vs the package ``__version__`` vs the
    top CHANGELOG heading must agree. Each comparison is skipped when a side is
    absent, so non-Python or changelog-less repos simply get fewer signals."""
    out: list[str] = []
    proj_v, name = _pyproject_version(root)
    dunder_v, dunder_path = _dunder_version(root, name)
    changelog_v = _changelog_top_version(root)
    if proj_v and dunder_v and proj_v != dunder_v:
        out.append(
            f"version drift: pyproject.toml is {proj_v} but {dunder_path} "
            f"__version__ is {dunder_v} — a clean install disagrees with itself "
            f"(bump both in lockstep)"
        )
    if proj_v and changelog_v and proj_v != changelog_v:
        out.append(
            f"version drift: pyproject.toml is {proj_v} but the top CHANGELOG "
            f"entry is {changelog_v} — the changelog does not describe this version"
        )
    return out


def _git_signals(root: Path) -> list[str]:
    code, out = _run_git(["status", "--porcelain"], root)
    if code != 0:
        return []                                   # not a git repo → no signal
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if not lines:
        return []
    shown = ", ".join(ln[3:] for ln in lines[:6])
    more = f" (+{len(lines) - 6} more)" if len(lines) > 6 else ""
    return [f"working tree has {len(lines)} uncommitted path(s): {shown}{more} — "
            f"commit the gameplan's work before closing"]


def _graph_signals(paths: RepoPaths, gid: str | None) -> list[str]:
    if not gid:
        return []
    gdir = paths.gameplan_dir(gid)
    out: list[str] = []
    pc = sb.pending_cascades(gdir / "_cascade-reports")
    if pc:
        out.append(f"{len(pc)} pending cascade report(s) unresolved: {', '.join(pc)} "
                   f"— resolve with cz_resolve_cascade")
    for it in sb.unresolved_open_items(gdir, None):
        out.append(f"open item {it['id']} still unresolved: {it['text'][:70]}")
    return out


# The irreducibly-human checks — the failure modes this system's own close-out
# missed that no deterministic signal can fully prove. Surfaced for the agent to
# affirm or act on (advisory, INVARIANT-05), never auto-graded.
CHECKLIST: list[dict[str, str]] = [
    {"check": "clean-environment verification",
     "ask": "Did you reproduce the baseline/tests in a FRESH environment (new venv, "
            "clean build, cleared cache) — not just your working install? A stale "
            "editable install can match old metadata and hide a real defect."},
    {"check": "consumer re-audit",
     "ask": "For every entity you changed (a host, a subsystem, a shared function), "
            "did you re-check every CONSUMER of it — including untracked ones "
            "(uninstall, CLI, docs claims, downstream callers)? cz_cascade covers the "
            "tracked graph; you own the rest."},
    {"check": "claim honesty",
     "ask": "Do the docs, guides, and help text you wrote assert only capabilities you "
            "actually VERIFIED? Mark anything unconfirmed as unverified rather than "
            "stating it as fact."},
    {"check": "shipped-artifact reality",
     "ask": "Does every file or behavior you claimed to ship (in the CHANGELOG, a "
            "guide, an in-code hint) actually exist and do what it says?"},
]


def audit(paths: RepoPaths, config: Config) -> dict:
    """Assemble the work/release self-audit for the active gameplan's repo."""
    root = paths.root
    gid = config.active_gameplan
    scope = f"gameplan {gid}" if gid else "repo (no active gameplan)"

    release = _release_signals(root)
    git = _git_signals(root)
    graph = _graph_signals(paths, gid)
    finding_count = len(release) + len(git) + len(graph)

    if finding_count:
        summary = (f"self-audit ({scope}): {finding_count} mechanical finding(s) "
                   f"+ {len(CHECKLIST)} judgment check(s) to affirm")
    else:
        summary = (f"self-audit ({scope}): no mechanical findings — "
                   f"affirm the {len(CHECKLIST)} judgment check(s) and you are clear")

    prompt = (
        "Work/release self-audit (advisory, INVARIANT-05 — the engine surfaces, you "
        "decide). (1) Resolve every MECHANICAL finding above (version drift, "
        "uncommitted work, unresolved cascades/open items) or record why it is "
        "acceptable. (2) Affirm each JUDGMENT check — these are the failure modes a "
        "green suite does not catch; the clean-environment one exists because a stale "
        "editable install once hid a version-drift bug that only a fresh install "
        "exposed. This never blocks a close."
    )
    return {
        "ok": True,
        "scope": scope,
        "release": release,
        "git": git,
        "graph": graph,
        "checklist": CHECKLIST,
        "finding_count": finding_count,
        "summary": summary,
        "prompt": prompt,
    }
