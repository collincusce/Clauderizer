"""``clauderize release-check`` — the release preflight ritual (O3, D-011).

A version number is a claim across four registries that never sync — source
(pyproject), remote git tags, GitHub Releases, and the PyPI index — plus one
ordering invariant: origin must hold the staged release commit BEFORE any tag
or Release exists, because a GitHub-UI release tags the REMOTE branch head
and any locally-authored guard is unpushed by construction at that moment
(L-08; v0.7.0 and v0.8.0 were both double-claimed this way in one day, H-07).

Verdicts follow doctor's three-state honesty (D3/D-010): ``ok`` shows its
evidence, ``fail`` is red, and a registry this host cannot query is
``unverifiable`` — never a false green. Exit 0 clean / 2 any fail / 3 clean
but with unverifiable checks.
"""

from __future__ import annotations

import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# The H-07 guard step in publish.yml; release-check refuses to bless a
# publish workflow that lost it. tests pin this against the real file.
GATE_MARKER = "Release tag must match pyproject version"

_GIT_TIMEOUT = 30.0
_NET_TIMEOUT = 10.0


@dataclass
class Check:
    label: str
    status: str  # "ok" | "fail" | "unverifiable" | "skip"
    detail: str = ""


def _git(root: Path, *args: str) -> tuple[int, str, str]:
    try:
        r = subprocess.run(["git", *args], cwd=str(root), capture_output=True,
                           text=True, timeout=_GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, "", str(exc)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _project(root: Path) -> tuple[str | None, str | None]:
    """``(name, version)`` from pyproject's [project] table, else Nones."""
    pp = root / "pyproject.toml"
    if not pp.exists():
        return None, None
    import tomllib

    try:
        data = tomllib.loads(pp.read_text(encoding="utf-8"))
    except Exception:
        return None, None
    proj = data.get("project") or {}
    version = proj.get("version")
    return proj.get("name"), (str(version) if version else None)


def _pypi_claimed(name: str, version: str) -> bool | None:
    """Is ``name==version`` on the PyPI index? ``None`` when unknowable.

    Queried directly and fresh — uvx/uv answer from cache and can hide a
    recent failed publish attempt (L-08).
    """
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=_NET_TIMEOUT):
            return True
    except urllib.error.HTTPError as exc:
        return False if exc.code == 404 else None
    except Exception:
        return None


def _gh_release_exists(root: Path, tag: str) -> bool | None:
    """Does a GitHub Release exist for ``tag``? ``None`` when unknowable.

    A Release can exist for a version PyPI never accepted (H-07) — the
    Releases registry must be swept independently of tags.
    """
    if shutil.which("gh") is None:
        return None
    try:
        r = subprocess.run(["gh", "release", "view", tag, "--json", "name"],
                           cwd=str(root), capture_output=True, text=True,
                           timeout=_GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode == 0:
        return True
    if "not found" in (r.stderr or "").lower():
        return False
    return None


def run(start: Path) -> tuple[int, list[Check]]:
    checks: list[Check] = []

    def add(label: str, status: str, detail: str = "") -> None:
        checks.append(Check(label, status, detail))

    rc, top, err = _git(start, "rev-parse", "--show-toplevel")
    if rc != 0:
        add("git repository", "fail", err or "not a git repository")
        return 2, checks
    root = Path(top)

    rc, out, _ = _git(root, "status", "--porcelain")
    if rc != 0 or out:
        add("clean tree", "fail",
            f"{len(out.splitlines())} uncommitted change(s)" if out else "git status failed")
    else:
        add("clean tree", "ok")

    # Ordering invariant (L-08): origin/<branch> must already BE the staged
    # release commit — the GitHub UI tags the remote head, not your tree.
    _, head, _ = _git(root, "rev-parse", "HEAD")
    _, branch, _ = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    label = f"push-then-release (origin/{branch} == HEAD)"
    rc, remote_out, err = _git(root, "ls-remote", "origin", f"refs/heads/{branch}")
    if rc != 0:
        add(label, "unverifiable", f"ls-remote failed: {err.splitlines()[0] if err else 'unknown'}")
    elif not remote_out:
        add(label, "fail", f"origin has no branch '{branch}' — push it first")
    else:
        remote_sha = remote_out.split()[0]
        if remote_sha == head:
            add(label, "ok", head[:9])
        else:
            add(label, "fail",
                f"HEAD {head[:9]} vs origin/{branch} {remote_sha[:9]} — push before "
                f"any tag or Release exists (a UI release tags the REMOTE head)")

    name, version = _project(root)
    if not version:
        add("version source (pyproject)", "skip",
            "no [project].version — registry sweep skipped")
    else:
        add("version source (pyproject)", "ok", f"{name or '<unnamed>'} {version}")
        tag = f"v{version}"

        _, out, _ = _git(root, "tag", "-l", tag)
        add(f"local tag {tag} unclaimed", "ok" if not out else "fail",
            "" if not out else "already exists locally — this version was staged before")

        rc, out, err = _git(root, "ls-remote", "--tags", "origin", f"refs/tags/{tag}")
        if rc != 0:
            add(f"remote tag {tag} unclaimed", "unverifiable",
                f"ls-remote failed: {err.splitlines()[0] if err else 'unknown'}")
        else:
            add(f"remote tag {tag} unclaimed", "ok" if not out else "fail",
                "" if not out
                else f"claimed remotely at {out.split()[0][:9]} (tags can exist remote-only)")

        ex = _gh_release_exists(root, tag)
        if ex is None:
            add(f"GitHub Release {tag} unclaimed", "unverifiable",
                "gh unavailable or query failed — check the Releases page manually")
        else:
            add(f"GitHub Release {tag} unclaimed", "ok" if not ex else "fail",
                "" if not ex
                else "a Release already exists (possibly never published to PyPI — H-07)")

        if name:
            claimed = _pypi_claimed(name, version)
            if claimed is None:
                add(f"PyPI {name}=={version} unclaimed", "unverifiable",
                    f"index query failed — check https://pypi.org/project/{name}/ "
                    f"directly (uvx answers from cache; never trust it for this)")
            else:
                add(f"PyPI {name}=={version} unclaimed",
                    "ok" if not claimed else "fail",
                    "" if not claimed else "version already on the index")

    wf = root / ".github" / "workflows" / "publish.yml"
    if not wf.exists():
        add("publish gate (publish.yml)", "skip", "no publish workflow in this repo")
    elif GATE_MARKER in wf.read_text(encoding="utf-8", errors="replace"):
        add("publish gate (tag==source)", "ok")
    else:
        add("publish gate (tag==source)", "fail",
            f"publish.yml lacks the '{GATE_MARKER}' guard (H-07) — a skewed "
            f"Release would build the wrong artifacts")

    if any(c.status == "fail" for c in checks):
        return 2, checks
    if any(c.status == "unverifiable" for c in checks):
        return 3, checks
    return 0, checks
