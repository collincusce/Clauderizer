"""Read-only handlers for the dispatched hook events (D-025, INVARIANT-06).

One handler per host hook event. Each takes the parsed hook payload (a dict, or
``None``) and returns the text to surface in session context, or ``None`` to stay
silent (quiet-when-empty — D3). None of them write: a hook never mutates docs or
blocks a session (INVARIANT-06), and the dispatcher guarantees exit 0 regardless
(INVARIANT-04). Whether a returned string actually reaches the model is the
host's contract, not ours (D1): Claude Code injects SessionStart/UserPromptSubmit
stdout and drops PreCompact/PostCompact stdout; kimi injects all of them.

Historically the only hook was SessionStart (hook/sessionstart.py). It now lives
here alongside the others; sessionstart.py is a back-compat shim and dispatch.py
is the router.
"""

from __future__ import annotations

from pathlib import Path

from ..config import Config
from ..paths import find_repo_root, resolve
from ..rituals import status_bundle
from ..tools_list import TOOL_NAMES


def repo_paths_config():
    """``(paths, config)`` for the clauderized repo at cwd, or ``None`` if this is
    not a clauderized repo (the handler then stays silent).

    The hook wrapper ``cd``-s into the repo before the engine runs, so cwd is the
    project even when the host launched the hook from elsewhere. Returning
    ``None`` from a non-repo cwd is therefore the *correct* silence the H-09
    anchor probe relies on (an un-anchored wrapper produces it; an anchored one
    does not)."""
    root = find_repo_root(Path.cwd())
    paths = resolve(root)
    if not paths.config_file.exists():
        return None
    return paths, Config.load(paths.config_file)


# Framing for a SessionStart/PostCompact that is really a post-compaction (or
# post-clear) re-entry. Claude Code passes source in {startup, resume, clear,
# compact}; kimi in {startup, resume}. startup/resume get the plain digest.
_SOURCE_NOTE = {
    "compact": "↻ Resumed after context compaction — working memory was "
               "summarized; durable state is intact in docs/. Where things stand:",
    "clear": "↻ Context cleared — re-establishing Clauderizer state:",
}


def build_digest(source: str | None = None) -> str | None:
    """The ``[Clauderizer]`` status digest, optionally framed by the session
    ``source``.

    Returns ``None`` only when this is not a clauderized repo (stay silent).
    On any internal error returns the visible "status unavailable" breadcrumb
    rather than nothing: a silent SessionStart failure is the dangerous kind
    (L-07), so the digest path is loud about its own failure."""
    rc = repo_paths_config()
    if rc is None:
        return None
    paths, config = rc
    try:
        bundle = status_bundle.compute(paths, config)
        digest = status_bundle.render_digest(bundle, tools=TOOL_NAMES)
    except Exception as exc:  # never break a session; surface why, on stdout
        return f"[Clauderizer] status unavailable: {exc} — run `clauderize doctor`"
    note = _SOURCE_NOTE.get((source or "").lower())
    return f"{note}\n{digest}" if note else digest


def session_start(payload: dict | None) -> str | None:
    """SessionStart: print the digest (source-aware). Always discoverable — it
    prints even with no active gameplan (the cold-start win) — and silent only
    when the repo is not clauderized."""
    source = (payload or {}).get("source")
    return build_digest(source if isinstance(source, str) else None)


def _active_bundle():
    """``bundle`` for an in-flight gameplan, or ``None`` when there is nothing to
    surface (not a clauderized repo, no active gameplan, or a compute error —
    advisory events stay silent on error rather than spamming every occurrence)."""
    rc = repo_paths_config()
    if rc is None:
        return None
    paths, config = rc
    try:
        bundle = status_bundle.compute(paths, config)
    except Exception:
        return None
    return bundle if bundle.get("active_gameplan") else None


def pre_compact(payload: dict | None) -> str | None:
    """Before the host summarizes context away: remind the agent to persist any
    durable state discovered this turn (the docs survive; working memory does
    not) and re-anchor where things stand. Silent unless a gameplan is active —
    with nothing in flight there is nothing to lose."""
    bundle = _active_bundle()
    if bundle is None:
        return None
    return (
        "[Clauderizer] Context is about to compact. Durable memory in docs/ is "
        "safe, but anything discovered this turn and not yet recorded will leave "
        "working memory. If you made a decision, lesson, or correction, or produced "
        "a concrete value, record it now (cz_add_decision / cz_add_lesson / "
        "cz_add_correction / cz_add_output) — and leave a dream note for the "
        f"dreamer (cz_add_dream). State: {bundle.get('summary', '')}"
    )


def post_compact(payload: dict | None) -> str | None:
    """After a compaction: re-inject the digest so the workflow survives the
    summary. This is the kimi path — kimi's SessionStart does not re-fire on
    compact; on Claude Code SessionStart(source=compact) already covers it.
    Silent when no gameplan is active."""
    if _active_bundle() is None:
        return None
    return build_digest("compact")


def user_prompt_submit(payload: dict | None) -> str | None:
    """On a user prompt: run the analyze gate (D-016/D-018) against the prompt and
    surface the most relevant recorded decisions/invariants + one-hop graph gaps
    — a pointer into canonical memory (D-013), ids not full text. Quiet-when-
    empty: prints nothing when nothing recorded is relevant (so trivial prompts
    stay silent). Read-only and fast — Claude Code caps this hook at 30s."""
    prompt = (payload or {}).get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        return None
    rc = repo_paths_config()
    if rc is None:
        return None
    paths, _config = rc
    try:
        from .. import analyze
        res = analyze.analyze(paths, prompt, k=3)
    except Exception:
        return None  # advisory: a broken analyze must not spam every prompt
    decisions = res.get("decisions") or []
    invariants = res.get("invariants") or []
    adjacent = res.get("adjacent") or []
    if not (decisions or invariants or adjacent):
        return None
    parts = []
    if decisions:
        parts.append("decisions " + ", ".join(d["id"] for d in decisions))
    if invariants:
        parts.append("invariants " + ", ".join(i["id"] for i in invariants))
    if adjacent:
        parts.append("unconnected " + ", ".join(a["id"] for a in adjacent))
    return (
        "[Clauderizer] Possibly relevant recorded memory — " + "; ".join(parts)
        + ". Run cz_analyze for detail before deciding (advisory, D-016)."
    )
