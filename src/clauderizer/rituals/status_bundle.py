"""Compute the current-state digest — the cold-start payload.

This is the data the SessionStart hook pushes into context and the ``cz_status``
tool returns on demand. It replaces the original system's hand-written reading
order: instead of "read these 6 files in order", the agent gets the live state.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..config import Config
from ..paths import RepoPaths
from . import _tables


def pending_cascades(reports_dir: Path) -> list[str]:
    """Reports whose 'Updates applied' section still holds the placeholder.

    A cascade is 'pending' until the agent records what it actually changed.
    This predicate is the single definition of "pending" — the status digest,
    the cascade_hygiene preflight check, and resolve_cascade all share it.
    """
    pending = []
    if not reports_dir.exists():
        return pending
    for report in sorted(reports_dir.glob("*.md")):
        text = report.read_text(encoding="utf-8")
        if "_(fill in concrete edits" in text or "_needs review_" in text:
            pending.append(report.name)
    return pending


# Backward-compatible alias (pre-0.4 name).
_pending_cascades = pending_cascades


def _baseline_tests(index_text: str) -> str | None:
    m = re.search(r"baseline test count\D*(\d+)", index_text, re.IGNORECASE)
    return m.group(1) if m else None


def _drift_warnings(paths: RepoPaths, rows: list) -> list[str]:
    """Surface the most common silent drift: phases marked complete while graph
    entities are still 'planned' (the status-transition step was skipped).

    Conservative on purpose — it only fires when there *is* completed work AND
    untouched entities, so it informs without crying wolf. Best-effort; never raises.
    """
    completed = [r for r in rows if r.status == "complete"]
    if not completed:
        return []
    try:
        from ..graph import index
        planned = [e.id for e in index.build(paths.docs).all()
                   if getattr(e, "status", None) == "planned"]
    except Exception:
        return []
    if not planned:
        return []
    sample = ", ".join(planned[:3]) + ("…" if len(planned) > 3 else "")
    noun = "entity" if len(planned) == 1 else "entities"
    return [f"{len(planned)} {noun} still 'planned' while {len(completed)} phase(s) "
            f"complete ({sample}) — cz_transition_status to reconcile."]


def compute(paths: RepoPaths, config: Config) -> dict:
    gid = config.active_gameplan
    bundle: dict = {
        "ok": True,
        "size": config.size,
        "host_profile": config.host_profile,
        "active_gameplan": gid,
        "phases": [],
        "current_phase": None,
        "next_phase": None,
        "baseline_tests": None,
        "pending_cascades": [],
        "blockers": [],
        "drift": [],
    }
    if not gid:
        bundle["summary"] = "No active gameplan. Use cz_create_gameplan to start one."
        return bundle

    gdir = paths.gameplan_dir(gid)
    index_file = gdir / "CHAT-HANDOFF-INDEX.md"
    status_file = gdir / "PHASE-STATUS.md"
    source = index_file if index_file.exists() else status_file
    if source.exists():
        text = source.read_text(encoding="utf-8")
        rows = _tables.parse_phase_table(text)
        bundle["phases"] = [
            {"number": r.number, "name": r.name, "status": r.status} for r in rows
        ]
        bundle["baseline_tests"] = _baseline_tests(text)
        current = next((r for r in rows if r.status == "in_progress"), None)
        if current:
            bundle["current_phase"] = {"number": current.number, "name": current.name}
        nxt = next(
            (r for r in rows if r.status in ("ready", "not_started")), None
        )
        if nxt:
            bundle["next_phase"] = {"number": nxt.number, "name": nxt.name}
        bundle["blockers"] = [r.name for r in rows if r.status == "blocked"]
        bundle["drift"] = _drift_warnings(paths, rows)

    bundle["pending_cascades"] = _pending_cascades(gdir / "_cascade-reports")

    cur = bundle["current_phase"]
    nxt = bundle["next_phase"]
    total = len(bundle["phases"])
    if cur:
        bundle["summary"] = (
            f"Gameplan {gid}: phase {cur['number']}/{total} IN PROGRESS — \"{cur['name']}\"."
        )
        bundle["next_action"] = "cz_preflight, then execute the phase tasks."
    elif nxt:
        bundle["summary"] = (
            f"Gameplan {gid}: next ready phase {nxt['number']}/{total} — \"{nxt['name']}\"."
        )
        bundle["next_action"] = "cz_next_phase_context, then cz_preflight."
    else:
        bundle["summary"] = f"Gameplan {gid}: no in-progress or ready phase found."
        bundle["next_action"] = "Review the gameplan or cz_add_phase."
    return bundle


def render_digest(bundle: dict, tools: list[str] | None = None) -> str:
    """Render the compact ``[Clauderizer]`` block the hook prints to stdout."""
    lines = []
    if not bundle.get("active_gameplan"):
        lines.append("[Clauderizer] No active gameplan. cz_create_gameplan to start.")
        return "\n".join(lines)
    lines.append(
        f"[Clauderizer] {bundle['summary']} "
        f"(size={bundle['size']}, profile={bundle['host_profile']})"
    )
    if bundle.get("baseline_tests"):
        lines.append(f"Baseline: {bundle['baseline_tests']} tests.")
    pc = bundle.get("pending_cascades") or []
    lines.append(f"Pending cascades: {len(pc)}." + (f" {', '.join(pc)}" if pc else ""))
    if bundle.get("blockers"):
        lines.append("Blocked: " + ", ".join(bundle["blockers"]))
    for warn in bundle.get("drift") or []:
        lines.append(f"⚠ Drift: {warn}")
    lines.append(f"Next: {bundle.get('next_action', '')}")
    if tools:
        lines.append("Tools: " + ", ".join(tools))
    return "\n".join(lines)
