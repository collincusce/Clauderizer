"""``clauderize release-check`` — the release preflight ritual (O3, D-011).

A version number is a claim across four registries that never sync — source
(pyproject), remote git tags, GitHub Releases, and the PyPI index — plus one
ordering invariant: origin must hold the staged release commit BEFORE any tag
or Release exists, because a GitHub-UI release tags the REMOTE branch head
and any locally-authored guard is unpushed by construction at that moment
(L-08; v0.7.0 and v0.8.0 were both double-claimed this way in one day, H-07).

...and one more claim the registries cannot see: whether the code being
released actually PASSES on every platform it says it supports (H-28). L-51
sweep (2) has always said to run the suite on every host leg the CI matrix
covers, because a green on one OS is a guess about the others and the publish
cannot be undone — but until 1.14.4 that was discipline, not a gate. 0.14.0
and 1.14.2 both shipped with Windows cells red. The check is at JOB
granularity on purpose: GitHub reports a workflow as ``success`` when a matrix
cell is *skipped*, so a workflow-level conclusion is exactly the false green
this module exists to refuse.

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

# G7 between sibling docs: the README's release section once contradicted
# RELEASING.md for months (it omitted the check entirely). If a README
# exists, it must at least name the ritual it claims to follow.
RITUAL_MARKER = "clauderize release-check"

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
                           encoding="utf-8", errors="replace", timeout=_GIT_TIMEOUT)
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


#: Job conclusions that are anything other than a clean pass. `skipped` is here
#: deliberately and is the whole point of H-28: a skipped matrix cell leaves the
#: workflow conclusion `success`, so the cell that would have caught the defect
#: is invisible at every granularity above this one. A repo with genuinely
#: conditional jobs will see them named in the failure detail — that is
#: actionable, where a silent pass is not.
_BAD_JOB_CONCLUSIONS = ("failure", "cancelled", "timed_out", "action_required",
                        "skipped", "stale", "startup_failure", "neutral")


def _gh_json(root: Path, args: list[str]) -> object | None:
    """Run a ``gh ... --json`` query and parse it. ``None`` on any failure —
    missing ``gh``, no auth, network, a rate limit, or unparseable output."""
    if shutil.which("gh") is None:
        return None
    import json

    try:
        r = subprocess.run(["gh", *args], cwd=str(root), capture_output=True,
                           text=True, timeout=_GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout or "null")
    except ValueError:
        return None


def _ci_runs_and_jobs(root: Path, sha: str) -> tuple[list[dict], list[dict]] | None:
    """``(runs, jobs)`` for the exact commit ``sha``, or ``None`` when this host
    cannot ask at all.

    Every job of every run is enumerated — the workflow-level conclusion is
    never consulted, because that is the field that hides a skipped cell.
    """
    runs = _gh_json(root, ["run", "list", "--commit", sha, "--limit", "20",
                           "--json", "databaseId,name,status,conclusion"])
    if not isinstance(runs, list):
        return None
    jobs: list[dict] = []
    for r in runs:
        if not isinstance(r, dict) or r.get("databaseId") is None:
            continue
        detail = _gh_json(root, ["run", "view", str(r["databaseId"]), "--json", "jobs"])
        if not isinstance(detail, dict):
            return None  # a run we could not open is not evidence of green
        for j in detail.get("jobs") or []:
            jobs.append({"workflow": r.get("name") or "?", "job": j.get("name") or "?",
                         "status": j.get("status") or "", "conclusion": j.get("conclusion") or ""})
    return runs, jobs


def _ci_check(root: Path, sha: str) -> Check:
    """Did CI pass on THIS commit, at job granularity? (H-28)"""
    label = "CI green on this commit (every job)"
    if not (root / ".github" / "workflows").is_dir():
        return Check(label, "skip", "no GitHub workflows in this repo")
    if not sha:
        return Check(label, "unverifiable", "could not resolve HEAD")

    got = _ci_runs_and_jobs(root, sha)
    if got is None:
        return Check(label, "unverifiable",
                     "gh unavailable or the API query failed — check the Actions "
                     "page for this commit manually; a release on unverified CI is "
                     "how 0.14.0 shipped three Windows cells red")
    runs, jobs = got

    if not runs:
        return Check(label, "fail",
                     f"no workflow run found for {sha[:9]} — CI has not run on the "
                     f"commit you are about to tag (push first, or wait for it to "
                     f"start); tagging now releases code no matrix cell has seen")

    unfinished = [f"{r.get('name') or '?'} ({r.get('status')})" for r in runs
                  if r.get("status") != "completed"]
    if unfinished:
        return Check(label, "fail",
                     f"still running on {sha[:9]}: {', '.join(sorted(unfinished))} — "
                     f"wait for CI to finish before tagging")

    if not jobs:
        return Check(label, "unverifiable",
                     f"{len(runs)} completed run(s) on {sha[:9]} but no jobs were "
                     f"returned — cannot certify at job granularity")

    bad = [j for j in jobs if j["conclusion"] in _BAD_JOB_CONCLUSIONS]
    if bad:
        named = ", ".join(sorted(f"{j['workflow']}/{j['job']} ({j['conclusion']})"
                                 for j in bad))
        skipped = [j for j in bad if j["conclusion"] == "skipped"]
        hint = ("" if not skipped else
                " — a SKIPPED job leaves the workflow conclusion `success`, which "
                "is exactly the false green this check exists to refuse; make the "
                "job unconditional or verify that cell another way")
        return Check(label, "fail", f"{len(bad)} of {len(jobs)} job(s) not green: {named}{hint}")

    return Check(label, "ok",
                 f"{len(jobs)} job(s) across {len(runs)} run(s) on {sha[:9]}")


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

    # H-28: the registries below say whether the VERSION is claimed; none of them
    # says whether the CODE passes. Enumerated per job, never per workflow.
    checks.append(_ci_check(root, head))

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
                else "a Release already exists (possibly never published to PyPI)")

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
            f"publish.yml lacks the '{GATE_MARKER}' guard — a skewed "
            f"Release would build the wrong artifacts")

    readme = root / "README.md"
    if not readme.exists():
        add("README names the ritual", "skip", "no README.md in this repo")
    elif RITUAL_MARKER in readme.read_text(encoding="utf-8", errors="replace"):
        add("README names the ritual", "ok")
    else:
        add("README names the ritual", "fail",
            f"README.md never mentions `{RITUAL_MARKER}` — its release section "
            f"has drifted from the ritual it claims to follow; fix the doc "
            f"before staging")

    if any(c.status == "fail" for c in checks):
        return 2, checks
    if any(c.status == "unverifiable" for c in checks):
        return 3, checks
    return 0, checks


def remote_claims(root: Path, version: str) -> dict[str, bool | None]:
    """Is ``version`` claimed on each REMOTE registry? (H-19's reusable core)

    ``{registry: True | False | None}`` where ``None`` means unknowable from
    here — offline, no ``gh``, no remote. Never raises, never guesses: an
    unreachable registry is reported as unverified rather than as absent, because
    a green that means "I could not look" is the failure this exists to close
    (L-25).

    The three checks in ``audit._release_signals`` all read files that one commit
    edits together, so they agree by construction. These are the legs that can
    disagree — and 1.13.0 sat locally consistent and released nowhere while a
    commit titled "ship 1.13.0" was already two commits back (H-19).
    """
    tag = f"v{version}"
    out: dict[str, bool | None] = {}
    rc, res, _err = _git(root, "ls-remote", "--tags", "origin", f"refs/tags/{tag}")
    out["remote git tag"] = bool(res.strip()) if rc == 0 else None
    out["GitHub Release"] = _gh_release_exists(root, tag)
    name, _v = _project(root)
    out["PyPI"] = _pypi_claimed(name, version) if name else None
    return out
