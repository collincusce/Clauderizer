"""Back-compat shim for the original SessionStart-only hook entry.

The hook is now event-dispatched (D-025): the ``clauderizer-hook`` console script
points at :mod:`clauderizer.hook.dispatch`, and the SessionStart handler plus the
shared digest builder live in :mod:`clauderizer.hook.handlers`. This module
re-exports them and keeps a ``main`` that delegates to the dispatcher, so any code
or wiring that still references ``clauderizer.hook.sessionstart:main`` behaves
identically (the digest on empty/SessionStart input, the ``--version`` identity
on probe).
"""

from __future__ import annotations

from .handlers import build_digest, session_start  # noqa: F401  (re-exported API)


def main(argv: list[str] | None = None) -> int:
    from . import dispatch

    return dispatch.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
