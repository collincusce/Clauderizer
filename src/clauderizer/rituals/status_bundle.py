"""Compute the current-state digest — the cold-start payload.

This is the data the SessionStart hook pushes into context and the ``cz_status``
tool returns on demand. It replaces the original system's hand-written reading
order: instead of "read these 6 files in order", the agent gets the live state.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..config import Config
from ..markdown import sections
from ..paths import RepoPaths
from . import _tables

# Above this many active lessons, the digest nudges toward consolidation (D-009
# is pressure + visibility, not caps — nothing is ever auto-pruned). A documented
# constant for now; promote it to config if real projects need different lines.
ACTIVE_LESSONS_WARN = 12

_LESSON_LINE_RE = re.compile(r"\*\*\d+\.\*\*")


def _memory_gauge(paths: RepoPaths, config: Config, index_text: str) -> dict:
    """Measure the cumulative memory so bloat is a visible state, not a silent one.

    Counts the gameplan's lessons by state, the distilled project lessons, and
    estimates the assembled handoff bundle size (chars/4 ≈ tokens).
    """
    active = obsolete = promoted = 0
    sec = sections.get_section(index_text, "Accumulated Lessons") or ""
    for line in sec.splitlines():
        s = line.strip()
        if _LESSON_LINE_RE.match(s):
            low = s.lower()
            if "(promoted" in low:
                promoted += 1
            elif "(obsolete" in low or s.startswith("~~"):
                obsolete += 1
            else:
                active += 1
    project = 0
    lessons_doc = paths.doc("LESSONS")
    if lessons_doc.exists():
        from .handoff import collect_project_lessons

        _, project = collect_project_lessons(lessons_doc.read_text(encoding="utf-8"))
    gauge = {
        "active_lessons": active,
        "obsolete_lessons": obsolete,
        "promoted_lessons": promoted,
        "project_lessons": project,
        "handoff_est_tokens": None,
        "warning": None,
    }
    if active > ACTIVE_LESSONS_WARN:
        gauge["warning"] = (
            f"{active} active lessons (> {ACTIVE_LESSONS_WARN}) — every handoff "
            f"carries all of them. cz_consolidate_lessons the overlapping, "
            f"cz_promote_lesson the enduring, cz_obsolete_lesson the stale."
        )
    return gauge


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
        "memory": None,
    }
    if not gid:
        bundle["summary"] = "No active gameplan. Use cz_create_gameplan to start one."
        return bundle

    gdir = paths.gameplan_dir(gid)
    index_file = gdir / "CHAT-HANDOFF-INDEX.md"
    status_file = gdir / "PHASE-STATUS.md"
    source = index_file if index_file.exists() else status_file
    index_text = index_file.read_text(encoding="utf-8") if index_file.exists() else ""
    bundle["memory"] = _memory_gauge(paths, config, index_text)
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
    target = cur or nxt
    if target:
        # Size what the next session would actually load (in-memory; no write).
        from . import handoff as handoff_mod

        try:
            ctx = handoff_mod.assemble(paths, config, gid, target["number"], write=False)
            bundle["memory"]["handoff_est_tokens"] = len(ctx["handoff_md"]) // 4
        except Exception:
            pass  # the gauge is best-effort; never break the digest
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
    elif total and all(p["status"] == "complete" for p in bundle["phases"]):
        # A finished gameplan is a success state, not a confusing dead end.
        bundle["summary"] = f"Gameplan {gid}: all {total} phase(s) COMPLETE. 🎉"
        bundle["next_action"] = (
            "Close out the gameplan (post-mortem, final cascade), or "
            "cz_create_gameplan to start the next initiative."
        )
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
    mem = bundle.get("memory")
    if mem:
        tok = mem.get("handoff_est_tokens")
        lines.append(
            f"Memory: {mem['active_lessons']} active lessons, "
            f"{mem['project_lessons']} project"
            + (f" (~{tok} tok handoff)." if tok else ".")
        )
        if mem.get("warning"):
            lines.append(f"⚠ Memory: {mem['warning']}")
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
