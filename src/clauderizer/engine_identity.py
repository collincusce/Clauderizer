"""Is the process answering this call the build the working tree describes? (H-27)

The failure this exists for, measured live on 2026-07-25: `.mcp.json` wires
``uvx --from clauderizer[mcp] clauderizer-mcp`` — correct and deliberate, because
the wiring must be machine-independent and committable. The consequence for a
session that *edits the engine* is that every ``cz_*`` write is served by the
released build from uv's cache while the fix sits green in the working tree. A
write guard was authored, tested at 26 tests, committed — and executed for zero
tool writes that day. It was found only when a malformed call produced exactly
the corruption the guard exists to prevent.

The existing staleness check cannot see this. ``status_bundle.engine_source_newer_than``
compares source mtimes against process start, which detects only the *editable*
case; an installed package's mtimes are install-time, so a uvx-served server
reports "not stale" with complete confidence while running a different build. It
answers *"did my files change since I started"* when the question is *"am I the
build this repo describes"*.

No handshake is needed for that question, because the process can introspect
itself: it knows where its own module was imported from and what version it
carries, and the repo's ``src/`` is right there on disk. That makes this cheap,
read-only and hook-safe (INVARIANT-06) — unlike ``doctor``'s spawn probe, which
answers the different and also-necessary question of whether some *other*
registered command is launchable (H-20/L-25).

Scope, stated plainly rather than implied. This reports on the process that
*executes it*, and nothing else. A session whose MCP server and whose hook run
different builds — the normal dogfooding case — gets an honest answer from each
independently, and neither can speak for the other. It is silent for an ordinary
consumer repo, which has no ``src/clauderizer`` to compare against.
"""

from __future__ import annotations

import re
from pathlib import Path

from .paths import RepoPaths

#: The tree's declared version, read as text rather than imported — importing it
#: would just re-import the *running* module and compare it against itself.
_VERSION_RE = re.compile(r"""^__version__\s*=\s*['"]([^'"]+)['"]""", re.M)


def tree_package_dir(paths: RepoPaths) -> Path | None:
    """``<root>/src/clauderizer`` when this repo actually contains the engine's
    source, else ``None`` — the signal that there is anything to compare."""
    pkg = paths.root / "src" / "clauderizer"
    return pkg if (pkg / "__init__.py").is_file() else None


def tree_version(paths: RepoPaths) -> str | None:
    """``__version__`` as declared in the working tree's source."""
    pkg = tree_package_dir(paths)
    if pkg is None:
        return None
    try:
        m = _VERSION_RE.search((pkg / "__init__.py").read_text(encoding="utf-8"))
    except OSError:
        return None
    return m.group(1) if m else None


def serving_build(paths: RepoPaths, *, module_file: str | Path | None = None,
                  running_version: str | None = None) -> dict | None:
    """The mismatch record when this process is NOT running the tree's source.

    Returns ``None`` — meaning "nothing to say" — in every ordinary case: a repo
    that does not contain the engine's source, or a process already running it.
    ``module_file`` / ``running_version`` are injectable so a test can model the
    uvx case without one.
    """
    pkg = tree_package_dir(paths)
    if pkg is None:
        return None                       # an ordinary consumer repo
    if module_file is None:
        import clauderizer
        module_file = clauderizer.__file__
    if running_version is None:
        from . import __version__ as running_version
    try:
        running_dir = Path(module_file).resolve().parent
        expected = pkg.resolve()
    except (OSError, ValueError):
        return None
    if running_dir == expected:
        return None                       # serving the working tree — correct
    return {
        "serving_path": str(running_dir),
        "serving_version": str(running_version),
        "tree_path": str(expected),
        "tree_version": tree_version(paths),
    }


def describe(mismatch: dict) -> str:
    """The one-line claim, shared by every surface so they cannot word it
    differently (the L-55 seam)."""
    sv, tv = mismatch["serving_version"], mismatch["tree_version"]
    versions = (f"{sv} vs the tree's {tv}" if tv and tv != sv
                else f"both report {sv}")
    return (
        f"this process is NOT running this repo's source — it imported "
        f"clauderizer from {mismatch['serving_path']} ({versions}). Edits under "
        f"{mismatch['tree_path']} do not affect it, so a fix made this session "
        f"is invisible here until the build it serves is updated. Use "
        f"`clauderize ops` (a fresh process on local source) for tracked writes, "
        f"or restart the session after installing the tree."
    )
