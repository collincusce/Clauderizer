"""The engine-identity probe must execute on the REAL CLI leg, not only in-process.

L-60/L-23: a test process' import graph is not the CLI's. An in-process suite can
exercise ``mcp_probe.handshake_probe`` directly and stay green while the actual
``clauderize doctor`` command never reaches it — because the CLI imports a
different set of modules, or because a lazily-imported probe silently no-ops.
That is precisely the H-27 class this check exists to close, so verifying it
in-process only is close to verifying nothing.

Every test here spawns a fresh interpreter running the real entry point.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from clauderizer.scaffold.init import init


def _doctor(cwd) -> subprocess.CompletedProcess:
    """The real CLI, with the identity probe ENABLED.

    conftest sets CLAUDERIZER_NO_SPAWN_PROBE=1 suite-wide so tests never spawn
    real servers — and a subprocess inherits it, which would make these tests
    pass by measuring nothing. That guard is exactly why the probe was never
    exercised end-to-end. Only the spawn guard is lifted; NO_NETWORK stays, and
    the spawned server is a local console script.
    """
    env = dict(os.environ)
    env.pop("CLAUDERIZER_NO_SPAWN_PROBE", None)
    return subprocess.run([sys.executable, "-m", "clauderizer", "doctor"],
                          cwd=str(cwd), capture_output=True, text=True,
                          timeout=300, env=env)


@pytest.fixture
def wired_repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("# r\n", encoding="utf-8")
    init(root, spawn_test=False, host_target="claude-code")
    return root


def test_doctor_runs_the_identity_probe_on_the_cli_leg(wired_repo):
    """The load-bearing assertion: a FRESH process running the real command
    reaches the identity check. If the probe were unreachable from the CLI's
    import graph, doctor would still exit and this line would simply be absent."""
    r = _doctor(wired_repo)
    out = r.stdout + r.stderr
    assert "MCP server identity" in out, (
        "the real `clauderize doctor` never reached the engine-identity probe — "
        f"in-process tests would not catch this.\n{out}")


def test_the_cli_leg_reports_a_served_version_not_merely_launchable(wired_repo):
    """H-20/D-060: 'launchable' from a PATH lookup was the false green this
    replaced. The CLI leg must report identity, or say honestly it could not."""
    r = _doctor(wired_repo)
    out = r.stdout + r.stderr
    line = next((ln for ln in out.splitlines() if "MCP server identity" in ln), "")
    assert line, out
    assert ("serverInfo" in line or "unverifiable" in line.lower()), (
        f"identity line claims neither a served identity nor honest "
        f"unverifiability: {line!r}")


def test_the_probe_module_is_reachable_from_a_bare_cli_import_graph():
    """L-60's fresh-process guard, narrowed: importing only what the CLI entry
    point imports must be enough to reach the probe. A future refactor that
    moves the import under a test-only path fails here."""
    r = subprocess.run(
        [sys.executable, "-c",
         "import clauderizer.cli as c; from clauderizer import mcp_probe; "
         "print(callable(mcp_probe.handshake_probe))"],
        capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "True", r.stdout


def test_doctor_exits_with_a_defined_code_on_the_cli_leg(wired_repo):
    """Exit codes are the contract callers script against: 0 ok, 2 drift,
    3 unverifiable. A fresh process must produce one of them, never a traceback."""
    r = _doctor(wired_repo)
    assert r.returncode in (0, 2, 3), (
        f"doctor returned {r.returncode} from the real CLI leg\n"
        f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
    assert "Traceback" not in (r.stdout + r.stderr)
