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
    read-only hook digest can never spawn a probe subprocess. Corpus files are
    never touched.

    Epistemics (D-070, D-065/D-069 lineage): a probe that could not RUN
    (timeout / OS error) is a DIFFERENT CLAIM from a probe that ran and exited
    nonzero. The former carries additive ``unevaluable: True`` — an armed guard
    whose probe cannot run can never trip, and the surfaces disclose that
    instead of reporting a measured-looking "unmet". ``met`` stays a boolean
    (False) in both cases so external ``if c.get("met")`` consumers are
    untouched (INVARIANT-07)."""
    out: list[dict] = []
    for name, cmd in load_conditions(paths, gid).items():
        try:
            proc = subprocess.run(cmd, shell=True, cwd=paths.root,
                                  capture_output=True, text=True,
                                  timeout=PROBE_TIMEOUT_S)
            met = proc.returncode == 0
            first = (proc.stdout or proc.stderr).strip().splitlines()
            detail = first[0][:160] if first else ""
            out.append({"name": name, "met": met, "detail": detail})
        except subprocess.TimeoutExpired:
            out.append({"name": name, "met": False, "unevaluable": True,
                        "detail": f"probe could not run: timed out ({PROBE_TIMEOUT_S}s)"})
        except OSError as e:
            out.append({"name": name, "met": False, "unevaluable": True,
                        "detail": f"probe could not run: {e}"})
    return out
