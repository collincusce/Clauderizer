"""The pre-flight verification — run for real, not claimed.

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
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .. import kinds
from ..config import Config
from ..locking import LockHeld, write_lock
from ..markdown import writer
from ..paths import RepoPaths
from ..profiles.detect import Profile
from . import _tables, status_bundle

_BASELINE_LABEL = "Current baseline test count"

# The built-in structural checks (git state, gameplan/cascade/handoff hygiene).
# Every OTHER enabled check name is a "command gate": a named shell command that
# passes/fails by exit code (D9). tests/build are command gates whose command
# falls back to the host profile; campaign-style gates (virality, brand_lint, …)
# are wired by the user in .clauderizer/preflight.<kind>.toml and skip-with-hint
# until wired. Clauderizer ships the mechanism, never the QA logic.
_STRUCTURAL_CHECKS = frozenset({
    "branch_base", "clean_tree", "deps_spotcheck",
    "branch_creation", "cascade_hygiene", "handoff_presence",
})


def _load_preflight_gates(paths: RepoPaths, kind_name: str) -> dict[str, str]:
    """Read ``.clauderizer/preflight.<kind>.toml`` -> ``{gate_name: shell command}``
    from its ``[gates]`` table (the per-kind/per-repo gate wiring). Missing or
    malformed file -> ``{}`` (the gate then skips-with-hint, never fails)."""
    p = paths.clauderizer_dir / f"preflight.{kind_name}.toml"
    if not p.exists():
        return {}
    try:
        with p.open("rb") as fh:
            raw = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    gates = raw.get("gates", {})
    return {str(k): str(v) for k, v in gates.items() if str(v).strip()}


def _generic_profile_hint(root, kind: str):
    """F5: when the locked profile is 'generic' (so the test/build command is
    empty) but the repo now looks like a real language, return an advisory that
    points at re-detection — instead of a silent skip. Read-only and advisory
    (INVARIANT-05); it never edits a user's profile.lock."""
    from ..profiles import detect

    try:
        detected, _ = detect.detect(root)
    except Exception:
        return None
    if detected.name != "generic" and detected.command(kind):
        return (f"no {kind} command for profile 'generic', but this looks like a "
                f"'{detected.name}' project — set the {kind} command in "
                f".clauderizer/profile.lock, or delete it and re-run `clauderize init` "
                f"to auto-detect, to enable this gate")
    return None


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


def _venv_bin_dirs(root: Path) -> list[str]:
    """Project-local virtualenv bin dirs to LEAD PATH for profile commands, so a
    repo's test runner resolves even when the ENGINE was launched from a DIFFERENT
    environment (uvx / pipx / global) than the project's venv — the case the
    engine-bin prepend alone misses (A-001 covered only the venv-launched engine).
    POSIX ``bin`` and Windows ``Scripts``; the standard ``.venv`` / ``venv`` dir
    names; existing dirs only, in priority order.
    """
    out: list[str] = []
    for name in (".venv", "venv"):
        for sub in ("bin", "Scripts"):
            d = root / name / sub
            if d.is_dir():
                out.append(str(d))
    return out


def _command_env(root: Path | None = None) -> dict[str, str]:
    """Environment for profile commands. PATH is led by (1) the project's own
    virtualenv bin dir when ``root`` has one, then (2) the running interpreter's
    bin directory — so the host's test runner resolves whether the engine was
    launched from the project venv (editable install) OR from a separate env
    (uvx/pipx/global) while the project keeps its toolchain in a local ``.venv``.
    Observed live (A-001): a venv-path-launched engine got 'pytest: not found'
    from the inherited PATH; the uvx-launched + project-``.venv`` case (preflight
    exit 127 while ``.venv/bin/pytest`` existed) needs the project venv too.
    """
    env = os.environ.copy()
    lead = _venv_bin_dirs(root) if root is not None else []
    lead.append(str(Path(sys.executable).parent))
    # De-dup preserving order (editable install: project venv == engine bin).
    seen: set[str] = set()
    ordered = [d for d in lead if not (d in seen or seen.add(d))]
    env["PATH"] = os.pathsep.join(ordered) + os.pathsep + env.get("PATH", "")
    return env


def _default_runner(cmd: str, cwd: Path) -> tuple[int, str]:
    # encoding pinned (not text=True): on win32 the locale codec would decode
    # tool output as cp1252 — and raise outright on undecodable bytes.
    proc = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, timeout=600,
        encoding="utf-8", errors="replace", env=_command_env(cwd),
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
        n_warn = sum(1 for c in self.checks if c.status == "warn")
        # A warn never fails preflight, but it must not read as a clean green
        # (#6a: a campaign QA gate that was DECLARED but never ran). Surface it in
        # the verdict so the result can't be misread as all-clear.
        if not self.passed:
            verdict = "FAIL"
        elif n_warn:
            verdict = "PASS WITH WARNINGS"
        else:
            verdict = "PASS"
        parts = f"{n_pass} passed, {n_fail} failed, {n_skip} skipped"
        if n_warn:
            parts += f", {n_warn} warned"
        return f"preflight {verdict}: {parts}"


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
    advisory = set(config.preflight_advisory or [])
    gid = config.active_gameplan

    # The check LIST comes from the focus gameplan's KIND when it defines one
    # (e.g. a campaign's QA gates); otherwise from config.preflight_checks (so a
    # driven gameplan — empty kind list — behaves EXACTLY as before). O-02: a
    # kind's list wins when present; to override a kind's checks per-repo, edit the
    # kind overlay (.clauderizer/kinds/<kind>.toml). The gate commands come from
    # .clauderizer/preflight.<kind>.toml, resolved per kind.
    kind_name = (status_bundle.gameplan_kind(paths.gameplan_dir(gid))
                 if gid else "driven")
    kind = kinds.resolve(kind_name, paths.kinds_dir)
    enabled = kind.preflight_checks or config.preflight_checks or ["clean_tree", "tests"]
    gates = _load_preflight_gates(paths, kind_name)
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

    def _gate_command(name: str) -> str:
        """Resolve a command gate's shell command: the per-kind wiring file first,
        then the host profile for the canonical tests/build gates."""
        if name in gates:
            return gates[name]
        if name == "tests":
            return profile.command("test")
        if name == "build":
            return profile.command("build")
        return ""

    def check_branch_base() -> None:
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

    def check_clean_tree() -> None:
        code, out = _git("status --porcelain", root, runner)
        if code != 0:
            add("clean_tree", "skip", "not a git repo")
        elif out.strip():
            add("clean_tree", "fail", f"working tree dirty:\n{out.strip()[:400]}")
        else:
            add("clean_tree", "pass", "clean working tree")

    def check_deps_spotcheck() -> None:
        gp = paths.gameplan_dir(gid) / "GAMEPLAN.md" if gid else None
        if gp and gp.exists():
            add("deps_spotcheck", "pass", f"active gameplan {gid} present on disk")
        else:
            add("deps_spotcheck", "fail", "active gameplan GAMEPLAN.md not found on disk")

    def check_branch_creation() -> None:
        state, branch = _git_branch_state(root, runner)
        if state == "branch":
            add("branch_creation", "pass", f"current branch: {branch}")
        elif state == "detached":
            add("branch_creation", "pass", "current branch: HEAD (detached)")
        elif state == "unborn":
            add("branch_creation", "skip", "no commits yet (unborn branch)")
        else:
            add("branch_creation", "skip", "not a git repo")

    def check_cascade_hygiene() -> None:
        pending = (
            status_bundle._pending_cascades(paths.gameplan_dir(gid) / "_cascade-reports")
            if gid else []
        )
        if pending:
            add("cascade_hygiene", "fail", f"pending cascade reports: {', '.join(pending)}")
        else:
            add("cascade_hygiene", "pass", "no pending cascade reports")

    def check_handoff_presence() -> None:
        if not gid:
            add("handoff_presence", "skip", "no active gameplan")
            return
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

    def check_command_gate(name: str) -> None:
        """A named shell-command gate: pass/fail by exit code. tests/build keep
        their profile fallback + (for tests) baseline parse/writeback; a campaign
        gate with no wired command skips with a hint rather than failing."""
        cmd = _gate_command(name)
        if not cmd:
            if name in ("tests", "build"):
                kind_cmd = "test" if name == "tests" else "build"
                hint = (_generic_profile_hint(root, kind_cmd)
                        if profile.name == "generic" else None)
                add(name, "skip",
                    hint or f"no {kind_cmd} command for profile '{profile.name}'")
            else:
                # #6a false-green fix: a gate the gameplan's KIND declared but with
                # no wired command did NOT run — a campaign must not read a clean
                # green on QA that never executed. WARN (visible, lowers the verdict
                # to "PASS WITH WARNINGS") rather than SKIP (silent), but not FAIL:
                # the engine ships the gate-running mechanism, never the QA logic, so
                # the user isn't forced to implement e.g. virality tooling to get
                # past preflight (INVARIANT-05 advisory spirit). Wiring it clears it.
                add(name, "warn",
                    f"gate '{name}' is declared by kind '{kind_name}' but no command "
                    f"is wired — this QA gate did NOT run. Wire it under [gates] in "
                    f".clauderizer/preflight.{kind_name}.toml (see the shipped "
                    f".clauderizer/preflight.{kind_name}.toml.example) to enable it.")
            return
        code, out = runner(cmd, root)
        if name == "tests":
            count = None
            if profile.baseline_test_regex:
                m = re.search(profile.baseline_test_regex, out)
                if m and m.groups():
                    count = m.group(1)
                    result.baseline_tests = count
            if code == 0:
                detail = f"`{cmd}` ok" + (f" ({count} tests)" if count else "")
                old = _write_back_baseline(paths, config, count) if count else None
                if old is not None:
                    detail += f"; baseline updated {old} -> {count}"
                add("tests", "pass", detail)
            else:
                add("tests", "fail", f"`{cmd}` exit {code}\n{out.strip()[:400]}")
        elif name == "build":
            add("build", "pass" if code == 0 else "fail", f"`{cmd}` exit {code}")
        elif code == 0:
            add(name, "pass", f"`{cmd}` ok")
        else:
            add(name, "fail", f"`{cmd}` exit {code}\n{out.strip()[:400]}")

    structural = {
        "branch_base": check_branch_base,
        "clean_tree": check_clean_tree,
        "deps_spotcheck": check_deps_spotcheck,
        "branch_creation": check_branch_creation,
        "cascade_hygiene": check_cascade_hygiene,
        "handoff_presence": check_handoff_presence,
    }
    # Iterate the enabled list in order so the report order = the kind/config order
    # (driven's config order is unchanged, so its output is byte-identical).
    for name in enabled:
        handler = structural.get(name)
        if handler is not None:
            handler()
        else:
            check_command_gate(name)

    def check_approval_gates() -> None:
        """Appended ONLY when the current phase declares APPROVAL criteria, so a
        repo without them keeps a byte-identical check list (INVARIANT-07).
        Stale or missing-artifact approvals WARN, never fail (INVARIANT-05) —
        the spend/ship decision stays with the agent, visibly."""
        if not gid:
            return
        cur = status_bundle.compute(paths, config).get("current_phase")
        if not cur:
            return
        crits = status_bundle.exit_criteria(paths.gameplan_dir(gid), str(cur["number"]))
        approvals = [c for c in crits if c.get("kind") == "approval"]
        if not approvals:
            return
        bad = [c for c in approvals if c.get("state") in ("stale", "missing")]
        pending = [c for c in approvals if c.get("state") == "unapproved"]
        if bad:
            add("approval_gates", "warn",
                "; ".join(c["detail"] for c in bad)
                + " — review and re-record with cz_approve_gate")
        elif pending:
            add("approval_gates", "pass",
                f"{len(pending)} approval(s) pending (not yet recorded), "
                f"{len(approvals) - len(pending)} current")
        else:
            add("approval_gates", "pass", f"all {len(approvals)} approval(s) current")

    check_approval_gates()
    return result
