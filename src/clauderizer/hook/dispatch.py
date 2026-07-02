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

# Native cross-host event names (the ones hosttargets.HOOK_GUIDE_HOSTS tells each
# host to wire) normalized to the canonical handler vocabulary, so a host wired per
# its OWN setup guide routes to the RIGHT handler instead of the SessionStart
# fallback. The load-bearing one is windsurf's `pre_user_prompt` — a prompt-submit
# event: without this it falls through to session_start and emits the full
# cold-start digest on EVERY prompt instead of the light analyze pointer. The
# session-start analogues are listed explicitly so the cross-host event contract is
# documented in one place (they would fall back to session_start anyway).
_EVENT_ALIASES = {
    "pre_user_prompt": "UserPromptSubmit",  # windsurf
    "BeforeAgent": "SessionStart",          # gemini-cli (pre-run = cold start)
    "TaskStart": "SessionStart",            # cline
    "session.start": "SessionStart",        # amp
    "agent.start": "SessionStart",          # amp (per-agent start)
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
    from .._stdio import harden_stdio

    harden_stdio()  # digest glyphs (⚙/⚠/★) must degrade on cp1252, never crash
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
        event = payload.get("hook_event_name")
        # A non-str event name (an unhashable list/dict, an int, None) must reach
        # the graceful SessionStart fallback, NOT raise inside dict.get and trip the
        # error breadcrumb (L-24 robustness class: tolerate every malformed shape).
        if not isinstance(event, str):
            event = None
        event = _EVENT_ALIASES.get(event, event)  # native host event -> canonical
        handler = EVENT_HANDLERS.get(event, handlers.session_start)
        out = handler(payload)
    except Exception as exc:  # last-resort net: a hook must never break a session
        print(f"[Clauderizer] hook error: {exc} — run `clauderize doctor`")
        return 0
    if out:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
