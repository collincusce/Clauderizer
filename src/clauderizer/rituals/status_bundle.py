"""Compute the current-state digest — the cold-start payload.

This is the data the SessionStart hook pushes into context and the ``cz_status``
tool returns on demand. It replaces the original system's hand-written reading
order: instead of "read these 6 files in order", the agent gets the live state.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from ..config import Config
from ..markdown import lesson_state, sections
from ..paths import RepoPaths
from . import _tables

# When this process imported the engine. A long-lived MCP server holds the
# modules it imported at session start; if the engine SOURCE changes after
# that (the dogfooding case: editing clauderizer inside a clauderized
# session), every cz_* call silently runs the older build. cz_status compares
# source mtimes against this and nudges — restart is the last mile,
# `clauderize ops` always runs fresh.
PROCESS_STARTED = time.time()


def engine_source_newer_than(started: float) -> bool:
    """True when any engine source file was modified after ``started``.

    Meaningful only for long-lived processes (the MCP server): a fresh CLI
    process imports after any edit, so it never sees ``True``. For installed
    (non-editable) packages, file mtimes are install-time — also never newer.
    """
    import clauderizer

    root = Path(clauderizer.__file__).parent
    try:
        return any(p.stat().st_mtime > started for p in root.rglob("*.py"))
    except OSError:
        return False

# Defaults for the consolidation nudges (D-009 is pressure + visibility, not
# caps — nothing is ever auto-pruned). Configurable per repo since O1/O2:
# `[memory] active_lessons_warn / project_lessons_warn` in config.toml; these
# constants remain the fallback when no config is in hand.
ACTIVE_LESSONS_WARN = 12
PROJECT_LESSONS_WARN = 20

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
            state, _ = lesson_state.parse_state(s)
            if state == lesson_state.PROMOTED:
                promoted += 1
            elif state == lesson_state.OBSOLETE:
                obsolete += 1
            else:
                active += 1
    project = 0
    lessons_doc = paths.doc("LESSONS")
    if lessons_doc.exists():
        from .handoff import collect_project_lessons

        _, project = collect_project_lessons(lessons_doc.read_text(encoding="utf-8"))
    warn_active = (config.active_lessons_warn if config is not None
                   else ACTIVE_LESSONS_WARN)
    warn_project = (config.project_lessons_warn if config is not None
                    else PROJECT_LESSONS_WARN)
    gauge = {
        "active_lessons": active,
        "obsolete_lessons": obsolete,
        "promoted_lessons": promoted,
        "project_lessons": project,
        "handoff_est_tokens": None,
        "warning": None,
    }
    warnings = []
    if active > warn_active:
        warnings.append(
            f"{active} active lessons (> {warn_active}) — every handoff "
            f"carries all of them. cz_consolidate_lessons the overlapping, "
            f"cz_promote_lesson the enduring, cz_obsolete_lesson the stale."
        )
    if project > warn_project:
        # O2: project lessons ride in every handoff across ALL gameplans —
        # past the line, re-distill: obsolete the superseded L-entries
        # (cz_obsolete_lesson "L-NN") and promote a tighter synthesis.
        warnings.append(
            f"{project} project lessons (> {warn_project}) — docs/LESSONS.md "
            f"rides in every handoff across gameplans. Re-distill: "
            f"cz_obsolete_lesson the superseded L-entries and promote a "
            f"tighter synthesis."
        )
    if warnings:
        gauge["warning"] = " | ".join(warnings)
    return gauge


# A report name is date + entity + optional zero-padded sequence; legacy
# unsuffixed names count as sequence 0, so they order before the -01 written
# beside them (chronological truth, even though '.' sorts after '-').
_REPORT_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.*?)(?:-(\d{2,}))?\.md$")


def report_sort_key(name: str) -> tuple[str, int, str]:
    m = _REPORT_NAME_RE.match(name)
    if not m:
        return ("", 0, name)
    return (m.group(1), int(m.group(3) or 0), name)


def pending_cascades(reports_dir: Path) -> list[str]:
    """Reports whose 'Updates applied' section still holds the placeholder.

    A cascade is 'pending' until the agent records what it actually changed.
    This predicate is the single definition of "pending" — the status digest,
    the cascade_hygiene preflight check, and resolve_cascade all share it.
    Ordered chronologically (date, then same-day sequence), so the last entry
    is the newest — what resolve_cascade's report default targets.
    """
    pending = []
    if not reports_dir.exists():
        return pending
    for report in sorted(reports_dir.glob("*.md"), key=lambda p: report_sort_key(p.name)):
        text = report.read_text(encoding="utf-8")
        if "_(fill in concrete edits" in text or "_needs review_" in text:
            pending.append(report.name)
    return pending


# Backward-compatible alias (pre-0.4 name).
_pending_cascades = pending_cascades


_OPEN_ITEM_RE = re.compile(r"^\*\*(O-\d+)\.\*\*(.*)$")
_OPEN_PHASE_RE = re.compile(r"_\(phase ([^)]+)\)_")


def open_items(gameplan_dir: Path) -> list[dict]:
    """Parse a gameplan's Open Items into ``{id, phase, resolved, text}`` dicts.

    Open items are ``**O-NN.**`` lines in GAMEPLAN.md's "Open Items" section
    (the clarify gate, D-015). An item is resolved once its line carries a
    ``_(resolved …)_`` marker; ``_(phase N)_`` tags it to a phase.
    """
    gp = gameplan_dir / "GAMEPLAN.md"
    if not gp.exists():
        return []
    body = sections.get_section(gp.read_text(encoding="utf-8"), "Open Items") or ""
    items: list[dict] = []
    for line in body.splitlines():
        m = _OPEN_ITEM_RE.match(line.strip())
        if not m:
            continue
        rest = m.group(2)
        pm = _OPEN_PHASE_RE.search(rest)
        items.append({
            "id": m.group(1),
            "phase": pm.group(1).strip() if pm else None,
            "resolved": "_(resolved" in rest,
            "text": rest.strip(),
        })
    return items


def unresolved_open_items(gameplan_dir: Path, phase: str | None = None) -> list[dict]:
    """Unresolved open items, optionally only those relevant to ``phase``
    (tagged to it, or untagged — the trivial Phase-0 relevance rule)."""
    out = []
    for it in open_items(gameplan_dir):
        if it["resolved"]:
            continue
        if phase is None or it["phase"] is None or str(it["phase"]) == str(phase):
            out.append(it)
    return out


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
        "open_items": [],
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
    bundle["open_items"] = [it["id"] for it in unresolved_open_items(gdir)]

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
        # No next phase means no handoff to size — say so instead of silently
        # dropping the figure the CHANGELOG promises (H-03).
        bundle["memory"]["handoff_note"] = "n/a: gameplan complete"
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
        note = mem.get("handoff_note")
        if tok:
            suffix = f" (~{tok} tok handoff)."
        elif note:
            suffix = f" (handoff {note})."
        else:
            suffix = "."
        lines.append(
            f"Memory: {mem['active_lessons']} active lessons, "
            f"{mem['project_lessons']} project" + suffix
        )
        if mem.get("warning"):
            lines.append(f"⚠ Memory: {mem['warning']}")
    pc = bundle.get("pending_cascades") or []
    lines.append(f"Pending cascades: {len(pc)}." + (f" {', '.join(pc)}" if pc else ""))
    oi = bundle.get("open_items") or []
    if oi:
        lines.append(f"Open items: {len(oi)} unresolved ({', '.join(oi)}).")
    if bundle.get("blockers"):
        lines.append("Blocked: " + ", ".join(bundle["blockers"]))
    for warn in bundle.get("drift") or []:
        lines.append(f"⚠ Drift: {warn}")
    if bundle.get("engine_stale"):
        lines.append(
            "⚠ Engine: source changed since this server started — cz_* tools run "
            "the older build; restart the session, or use `clauderize ops` "
            "(fresh process) for writes."
        )
    lines.append(f"Next: {bundle.get('next_action', '')}")
    if tools:
        lines.append("Tools: " + ", ".join(tools))
    return "\n".join(lines)
