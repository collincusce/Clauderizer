"""Crash-proof console output for glyph-heavy CLIs on Windows.

Native Windows consoles frequently default to cp1252, which cannot encode the
✓ / ✗ / ⚙ / ⚠ glyphs the CLI and hook print — ``print()`` then raises
``UnicodeEncodeError``, including inside error handlers, taking the whole
command down (field report, 2026-07-02, first native-Windows install). The fix
is not to force UTF-8 (a genuinely cp1252 console would garble) but to switch
the ERROR MODE: unencodable characters degrade to ``?`` and the command keeps
working. Kept in its own tiny module so both entry points (``clauderize`` and
``clauderizer-hook``) can use it without pulling anything heavy; the MCP server
is deliberately untouched — its stdio is a JSON protocol channel, not a console.
"""

from __future__ import annotations

import sys


def harden_stdio() -> None:
    """Make stdout/stderr survive unencodable glyphs (degrade, never crash)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if stream is not None and hasattr(stream, "reconfigure"):
                stream.reconfigure(errors="replace")
        except Exception:
            # A stream that can't be reconfigured (captured, closed, exotic
            # host) is left as-is — hardening must never introduce a crash.
            pass
