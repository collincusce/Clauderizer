"""The 7-check pre-flight verification — run for real, not claimed.

The original system listed seven checks a session was *supposed* to run before
writing code (CHECK 3 "tests pass", CHECK 4 "build passes", etc.) but nothing
enforced them — anti-pattern #3 is literally "session claims vs reality". Here
each check is an actual operation: tests and build run the host profile's real
commands; git checks shell out to git; cascade hygiene reads the report dir.

Commands come from the host *profile* (data), so the engine never hardcodes a
language. A command runner is injectable so tests can stub it without a real
toolchain.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..config import Config
from ..locking import LockHeld, write_lock
from ..markdown import writer
from ..paths import RepoPaths
from ..profiles.detect import Profile
from . import _tables, status_bundle

_BASELINE_LABEL = "Current baseline test count"


def _write_back_baseline(paths: RepoPaths, config: Config, count: str) -> str | None:
    """Refresh the tracked baseline with the count preflight just measured.

    Anti-pattern #7 (stale references) applied to the system itself: the index's
    baseline line was written once at scaffold time and rotted while preflight
    measured the real number on every run and discarded it. Preflight is the
    writer now — returns the old value when it changed something, else ``None``
    (no active gameplan, no baseline line, or already current).
    """
    gid = config.active_gameplan
    if not gid or not count:
        return None
    idx = paths.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md"
    if not idx.exists():
        return None
    m = re.search(rf"\*\*{_BASELINE_LABEL}\*\*\s*:\s*(\d+)", idx.read_text(encoding="utf-8"))
    if m is None or m.group(1) == count:
        return None
    # One tracked write inside an otherwise read-only ritual: serialize it with
    # every other writer (H-05). The lock wraps just this write — never the
    # long-running test commands — and a contended lock skips the refresh
    # rather than failing preflight: the value self-heals on the next green run.
    try:
        with write_lock(paths.write_lock_file):
            writer.set_labeled_value(idx, _BASELINE_LABEL, count)
    except LockHeld:
        return None
    return m.group(1)

# (exit_code, combined_output)
Runner = Callable[[str, Path], tuple[int, str]]


def _command_env() -> dict[str, str]:
    """Environment for profile commands: the running interpreter's bin
    directory leads PATH, so a venv-installed engine resolves its own
    toolchain (pytest, ruff, …) without shell activation. Observed live
    (A-001): the engine launched by absolute venv path got 'pytest: not
    found' from the inherited PATH while .venv/bin/pytest existed.
    """
    env = os.environ.copy()
    bin_dir = str(Path(sys.executable).parent)
    env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
    return env


def _default_runner(cmd: str, cwd: Path) -> tuple[int, str]:
    # encoding pinned (not text=True): on win32 the locale codec would decode
    # tool output as cp1252 — and raise outright on undecodable bytes.
    proc = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, timeout=600,
        encoding="utf-8", errors="replace", env=_command_env(),
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


@dataclass
class Check:
    n: int
    name: str
    status: str  # pass | fail | skip
    detail: str = ""


@dataclass
class PreflightResult:
    checks: list[Check] = field(default_factory=list)
    passed: bool = True
    baseline_tests: str | None = None

    def to_dict(self) -> dict:
        return {
            "ok": True,
            "passed": self.passed,
            "baseline_tests": self.baseline_tests,
            "checks": [vars(c) for c in self.checks],
            "summary": self._summary(),
        }

    def _summary(self) -> str:
        n_pass = sum(1 for c in self.checks if c.status == "pass")
        n_fail = sum(1 for c in self.checks if c.status == "fail")
        n_skip = sum(1 for c in self.checks if c.status == "skip")
        verdict = "PASS" if self.passed else "FAIL"
        return f"preflight {verdict}: {n_pass} passed, {n_fail} failed, {n_skip} skipped"


def _git(args: str, cwd: Path, runner: Runner) -> tuple[int, str]:
    return runner(f"git {args}", cwd)


def _git_branch_state(root: Path, runner: Runner) -> tuple[str, str]:
    """One of ('branch', name) | ('detached','') | ('unborn','') | ('none','').

    ``rev-parse --abbrev-ref HEAD`` fails BOTH outside a repo and on a fresh
    ``git init`` with zero commits (unborn branch) — and the unborn case is
    the very first thing a brand-new adopter runs preflight on, so it must
    not be misdiagnosed as "not a git repo" (found live in the node-profile
    loop proof, alpha-to-beta-evidence Phase 3).
    """
    code, out = _git("rev-parse --abbrev-ref HEAD", root, runner)
    if code == 0:
        name = out.strip()
        return ("detached", "") if name == "HEAD" else ("branch", name)
    inside, _ = _git("rev-parse --is-inside-work-tree", root, runner)
    if inside == 0:
        return ("unborn", "")
    return ("none", "")


def _missing_expected_handoffs(gdir: Path) -> tuple[bool, list[str]]:
    """Handoff files the phase table implies SHOULD exist on disk but don't.

    A handoff is written when its phase would have begun — ``PHASE-0`` at scaffold,
    ``PHASE-N`` when phase ``N-1`` completes — so a handoff is expected for the
    first phase and for any phase whose predecessor is COMPLETE. Future
    not-started phases are NOT required, so a healthy mid-flight gameplan stays
    clean (no false positives on phases that simply haven't run yet).

    Returns ``(had_table, missing_filenames)``; ``had_table`` is False when there
    is no phase table to judge against, so the caller can skip rather than fail.
    """
    src = gdir / "CHAT-HANDOFF-INDEX.md"
    if not src.exists():
        src = gdir / "PHASE-STATUS.md"
    if not src.exists():
        return (False, [])
    rows = _tables.parse_phase_table(src.read_text(encoding="utf-8"))
    if not rows:
        return (False, [])
    missing: list[str] = []
    for i, row in enumerate(rows):
        if i == 0 or rows[i - 1].status == "complete":
            fname = f"PHASE-{row.number}-HANDOFF.md"
            if not (gdir / "handoffs" / fname).exists():
                missing.append(fname)
    return (True, missing)


def run(
    paths: RepoPaths,
    config: Config,
    profile: Profile,
    *,
    runner: Runner | None = None,
) -> PreflightResult:
    runner = runner or _default_runner
    root = paths.root
    result = PreflightResult()
    enabled = config.preflight_checks or ["clean_tree", "tests"]
    advisory = set(config.preflight_advisory or [])
    n = 0

    def add(name: str, status: str, detail: str = "") -> None:
        nonlocal n
        # An advisory check is informational: a failure is downgraded to "warn"
        # and never fails preflight — so a docs/audit workflow can keep e.g.
        # clean_tree visible without crying wolf (a dirty tree is normal there).
        if status == "fail" and name in advisory:
            status, detail = "warn", f"(advisory) {detail}"
        n += 1
        result.checks.append(Check(n, name, status, detail))
        if status == "fail":
            result.passed = False

    if "branch_base" in enabled:
        state, branch = _git_branch_state(root, runner)
        if state == "none":
            add("branch_base", "skip", "not a git repo")
        elif state == "unborn":
            add("branch_base", "skip",
                "git repo has no commits yet (unborn branch) — commit the "
                "scaffold to enable branch checks")
        elif state == "detached":
            add("branch_base", "fail", "detached HEAD — check out a branch")
        else:
            add("branch_base", "pass", f"on branch {branch}")

    if "clean_tree" in enabled:
        code, out = _git("status --porcelain", root, runner)
        if code != 0:
            add("clean_tree", "skip", "not a git repo")
        elif out.strip():
            add("clean_tree", "fail", f"working tree dirty:\n{out.strip()[:400]}")
        else:
            add("clean_tree", "pass", "clean working tree")

    if "tests" in enabled:
        cmd = profile.command("test")
        if not cmd:
            add("tests", "skip", f"no test command for profile '{profile.name}'")
        else:
            code, out = runner(cmd, root)
            count = None
            if profile.baseline_test_regex:
                m = re.search(profile.baseline_test_regex, out)
                if m and m.groups():
                    count = m.group(1)
                    result.baseline_tests = count
            if code == 0:
                detail = f"`{cmd}` ok" + (f" ({count} tests)" if count else "")
                # Green run with a measured count: keep the tracked baseline fresh.
                old = _write_back_baseline(paths, config, count) if count else None
                if old is not None:
                    detail += f"; baseline updated {old} -> {count}"
                add("tests", "pass", detail)
            else:
                add("tests", "fail", f"`{cmd}` exit {code}\n{out.strip()[:400]}")

    if "build" in enabled:
        cmd = profile.command("build")
        if not cmd:
            add("build", "skip", f"no build command for profile '{profile.name}'")
        else:
            code, out = runner(cmd, root)
            add("build", "pass" if code == 0 else "fail", f"`{cmd}` exit {code}")

    if "deps_spotcheck" in enabled:
        gid = config.active_gameplan
        gp = paths.gameplan_dir(gid) / "GAMEPLAN.md" if gid else None
        if gp and gp.exists():
            add("deps_spotcheck", "pass", f"active gameplan {gid} present on disk")
        else:
            add("deps_spotcheck", "fail", "active gameplan GAMEPLAN.md not found on disk")

    if "branch_creation" in enabled:
        state, branch = _git_branch_state(root, runner)
        if state == "branch":
            add("branch_creation", "pass", f"current branch: {branch}")
        elif state == "detached":
            add("branch_creation", "pass", "current branch: HEAD (detached)")
        elif state == "unborn":
            add("branch_creation", "skip", "no commits yet (unborn branch)")
        else:
            add("branch_creation", "skip", "not a git repo")

    if "cascade_hygiene" in enabled:
        gid = config.active_gameplan
        pending = (
            status_bundle._pending_cascades(paths.gameplan_dir(gid) / "_cascade-reports")
            if gid else []
        )
        if pending:
            add("cascade_hygiene", "fail", f"pending cascade reports: {', '.join(pending)}")
        else:
            add("cascade_hygiene", "pass", "no pending cascade reports")

    if "handoff_presence" in enabled:
        gid = config.active_gameplan
        if not gid:
            add("handoff_presence", "skip", "no active gameplan")
        else:
            had_table, missing = _missing_expected_handoffs(paths.gameplan_dir(gid))
            if not had_table:
                add("handoff_presence", "skip", "no phase table to check")
            elif missing:
                add("handoff_presence", "fail",
                    "expected handoff(s) missing on disk: " + ", ".join(missing)
                    + ". These rebuild losslessly from the canonical graph, so a "
                    "crashed session that never wrote one is recoverable. To unblock, "
                    "reply 'regenerate' to rebuild each via cz_write_handoff(phase_n=…), "
                    "or 'proceed anyway' to waive it once; for an intentionally "
                    "single-session gameplan, add 'handoff_presence' to preflight_advisory.")
            else:
                add("handoff_presence", "pass", "all expected phase handoffs present")

    return result
