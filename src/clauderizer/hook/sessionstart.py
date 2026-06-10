"""Print the current gameplan digest to stdout at session start.

Claude Code injects a SessionStart hook's stdout into the session context. That
makes the cold-start automatic: a fresh agent learns where things stand and what
to do next without any reading-order ritual. Always exits 0 — a memory tool must
never block a session, so errors degrade to a single warning line.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .. import __version__
from ..config import Config
from ..paths import find_repo_root, resolve
from ..rituals import status_bundle
from ..tools_list import TOOL_NAMES


def main(argv: list[str] | None = None) -> int:
    # Deterministic probe path (D3): init/doctor spawn-test the hook with
    # --version; answer it without reading the repo so the probe is fast and
    # its output is the engine identity, not a status digest.
    args = sys.argv[1:] if argv is None else argv
    if "--version" in args or "-V" in args:
        print(f"clauderizer {__version__}")
        return 0
    if "--help" in args or "-h" in args:
        print("clauderizer-hook — print the gameplan digest for SessionStart.\n"
              "Flags: --version, --help. Always exits 0.")
        return 0
    try:
        root = find_repo_root(Path.cwd())
        paths = resolve(root)
        if not paths.config_file.exists():
            return 0  # not a clauderized repo; stay silent
        config = Config.load(paths.config_file)
        bundle = status_bundle.compute(paths, config)
        print(status_bundle.render_digest(bundle, tools=TOOL_NAMES))
    except Exception as exc:  # never break a session
        # Print to STDOUT (not stderr) so the failure is visible in session
        # context — a silent hook failure is the dangerous kind. Still exit 0.
        print(f"[Clauderizer] status unavailable: {exc} — run `clauderize doctor`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
