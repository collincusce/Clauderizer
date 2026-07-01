"""Standing conditions (gameplan 2026-07-01, decision D3) — declared per
gameplan, evaluated LAZILY inside tool calls, never fired.

A loop or campaign gameplan may declare threshold-shaped triggers in
``.clauderizer/conditions.<gameplan-id>.toml``::

    [conditions]
    backlog_low = "test $(ls campaigns/shorts/approved | wc -l) -lt 3"
    weekly_due  = "python tools/cadence_due.py"

Each condition is a shell probe: exit 0 means MET, which the engine surfaces as
"iteration proposed" in cz_status / cz_preflight / cz_loop_step results (and one
digest line). The engine never schedules, never auto-runs an iteration, and the
read-only hooks never evaluate probes (INVARIANT-05/06) — calendar cadence
belongs to the host's scheduler, which simply opens a session that asks for
status. Same command-gate primitive as per-kind preflight wiring.
"""

from __future__ import annotations

import subprocess
import tomllib

from ..paths import RepoPaths

# A condition is a cheap probe, not a build — cap it hard.
PROBE_TIMEOUT_S = 30


def load_conditions(paths: RepoPaths, gid: str) -> dict[str, str]:
    """``{condition_name: shell command}`` from conditions.<gid>.toml's
    ``[conditions]`` table. Missing or malformed file -> ``{}`` (declaring
    nothing is the normal state, never an error)."""
    if not gid:
        return {}
    p = paths.clauderizer_dir / f"conditions.{gid}.toml"
    if not p.exists():
        return {}
    try:
        with p.open("rb") as fh:
            raw = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    conds = raw.get("conditions", {})
    return {str(k): str(v) for k, v in conds.items() if str(v).strip()}


def evaluate(paths: RepoPaths, gid: str) -> list[dict]:
    """Run the gameplan's declared probes: ``[{name, met, detail}]``.

    Called ONLY from tool/CLI code paths (cz_status, cz_preflight,
    cz_loop_step) — status_bundle.compute defaults to NOT evaluating, so the
    read-only hook digest can never spawn a probe subprocess. A probe that
    times out or errors reports unmet with the reason; corpus files are never
    touched."""
    out: list[dict] = []
    for name, cmd in load_conditions(paths, gid).items():
        try:
            proc = subprocess.run(cmd, shell=True, cwd=paths.root,
                                  capture_output=True, text=True,
                                  timeout=PROBE_TIMEOUT_S)
            met = proc.returncode == 0
            first = (proc.stdout or proc.stderr).strip().splitlines()
            detail = first[0][:160] if first else ""
        except subprocess.TimeoutExpired:
            met, detail = False, f"probe timed out ({PROBE_TIMEOUT_S}s)"
        except OSError as e:
            met, detail = False, f"probe failed: {e}"
        out.append({"name": name, "met": met, "detail": detail})
    return out
