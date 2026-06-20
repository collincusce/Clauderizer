"""The hook event dispatcher — the single entry behind the ``clauderizer-hook``
console script (D-025).

It reads the host's hook payload (JSON on stdin), routes on ``hook_event_name``
to a read-only handler, prints whatever the handler returns, and ALWAYS exits 0
(INVARIANT-04/06). Backward compatible in two ways the hardened probes depend on:

- ``--version``/``--help`` answer the identity probe BEFORE any stdin or repo
  read, so init/doctor get the engine identity, fast (L-09/L-10).
- empty / garbage / non-object stdin falls back to the SessionStart digest —
  exactly the shape the no-arg digest probe (``hook_digest_probe``) sends, so the
  generalization leaves that green leg untouched.
"""

from __future__ import annotations

import json
import sys

from .. import __version__
from . import handlers

# hook_event_name -> handler. A missing or unrecognized event falls back to the
# SessionStart digest: a host that adds an event we do not special-case still
# gets the durable pointer rather than silence.
EVENT_HANDLERS = {
    "SessionStart": handlers.session_start,
    "PreCompact": handlers.pre_compact,
    "PostCompact": handlers.post_compact,
    "UserPromptSubmit": handlers.user_prompt_submit,
}


def read_payload() -> dict:
    """Parse the hook payload from stdin, tolerating every malformed shape
    (L-18/L-19): empty input, non-UTF-8 bytes, a leading BOM, CRLF, or valid JSON
    that is not an object. Returns ``{}`` for anything that is not a JSON object —
    the caller then routes to the SessionStart default. The guard wraps the whole
    pipeline (the raw read, the decode, and the parse), because each layer has its
    own failure mode. ``utf-8-sig`` strips a leading BOM; ``errors='replace'``
    survives arbitrary bytes."""
    try:
        raw = sys.stdin.buffer.read()
    except Exception:
        # No readable byte stream (e.g. stdin replaced with a non-buffer object).
        return {}
    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8-sig", "replace"))
    except (ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    # Identity probe path: answer before reading stdin or the repo (L-09/L-10).
    if "--version" in args or "-V" in args:
        print(f"clauderizer {__version__}")
        return 0
    if "--help" in args or "-h" in args:
        print(
            "clauderizer-hook — dispatch a host hook event to its read-only "
            "handler.\n"
            "Reads JSON on stdin (hook_event_name routes); empty/unknown → the "
            "SessionStart digest.\n"
            "Events: " + ", ".join(EVENT_HANDLERS) + ".\n"
            "Flags: --version, --help. Always exits 0."
        )
        return 0
    try:
        payload = read_payload()
        handler = EVENT_HANDLERS.get(payload.get("hook_event_name"), handlers.session_start)
        out = handler(payload)
    except Exception as exc:  # last-resort net: a hook must never break a session
        print(f"[Clauderizer] hook error: {exc} — run `clauderize doctor`")
        return 0
    if out:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
