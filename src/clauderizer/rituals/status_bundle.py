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
from ..markdown import lesson_state, sections, skill_state
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
# Skills surface FOCUSED by relevance (not all-carried like lessons), so the
# threshold is higher and the nudge is about pruning STALE skills, not handoff weight.
ACTIVE_SKILLS_WARN = 25

_LESSON_LINE_RE = lesson_state.LESSON_LINE_RE  # shared grammar — see markdown/lesson_state


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
    # Registered skills (skill-awareness Phase 2): counted for visibility; they
    # surface focused-by-relevance, so the count is not handoff weight.
    skills_active = 0
    skills_doc = paths.doc("SKILLS")
    if skills_doc.exists():
        sbody = sections.get_section(skills_doc.read_text(encoding="utf-8"), "Skills") or ""
        skills_active = sum(
            1 for ln in sbody.splitlines()
            if skill_state.SKILL_LINE_RE.search(ln) and skill_state.is_active(ln))
    warn_active = (config.active_lessons_warn if config is not None
                   else ACTIVE_LESSONS_WARN)
    warn_project = (config.project_lessons_warn if config is not None
                    else PROJECT_LESSONS_WARN)
    gauge = {
        "active_lessons": active,
        "obsolete_lessons": obsolete,
        "promoted_lessons": promoted,
        "project_lessons": project,
        "active_skills": skills_active,
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
    if skills_active > ACTIVE_SKILLS_WARN:
        warnings.append(
            f"{skills_active} registered skills (> {ACTIVE_SKILLS_WARN}) — skills "
            f"surface focused by relevance, so this is staleness not handoff weight: "
            f"cz_obsolete_skill any no longer available (cz_discover_skills shows "
            f"what's present)."
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
# The phase tag is written right after the id (add_open_item), so anchor it to the
# start — a `_(phase N)_` inside the item's prose must not read as the tag.
_OPEN_PHASE_RE = re.compile(r"\s*_\(phase ([^)]+)\)_")
# The resolved marker carries an ISO date; matching that shape (not a bare
# "_(resolved" substring) keeps item prose containing "_(resolved …" from reading
# as resolved. Shared with mutations.resolve_open_item.
_RESOLVED_RE = re.compile(r"_\(resolved \d{4}-\d{2}-\d{2}")


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
        pm = _OPEN_PHASE_RE.match(rest)
        items.append({
            "id": m.group(1),
            "phase": pm.group(1).strip() if pm else None,
            "resolved": bool(_RESOLVED_RE.search(rest)),
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


_EC_CHECK_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s*(.*)$")


def phase_block(breakdown_body: str, phase: str):
    """``(lines, start, end)`` of the ``### Phase N`` block within a Phase
    Breakdown body, or ``None``. ``end`` is the next ``### `` heading (or EOF)."""
    lines = breakdown_body.splitlines()
    pat = re.compile(rf"^###\s+Phase\s+{re.escape(str(phase))}\b")
    start = next((i for i, ln in enumerate(lines) if pat.match(ln.strip())), None)
    if start is None:
        return None
    end = next((j for j in range(start + 1, len(lines))
                if lines[j].startswith("### ")), len(lines))
    return lines, start, end


def exit_criteria(gameplan_dir: Path, phase: str) -> list[dict]:
    """Parse a phase's exit-criteria checkboxes into ``{checked, text}`` dicts (D-015)."""
    gp = gameplan_dir / "GAMEPLAN.md"
    if not gp.exists():
        return []
    body = sections.get_section(gp.read_text(encoding="utf-8"), "Phase Breakdown") or ""
    blk = phase_block(body, phase)
    if blk is None:
        return []
    lines, start, end = blk
    out = []
    for ln in lines[start:end]:
        m = _EC_CHECK_RE.match(ln)
        if m:
            text = m.group(2).strip()
            if sections.is_placeholder(text):  # ignore the scaffold "_(verifiable)_"
                continue
            out.append({"checked": m.group(1).lower() == "x", "text": text})
    return out


def unchecked_exit_criteria(gameplan_dir: Path, phase: str) -> list[dict]:
    """Exit criteria for ``phase`` still unchecked (``- [ ]``) — the surfacing input."""
    return [c for c in exit_criteria(gameplan_dir, phase) if not c["checked"]]


def _baseline_tests(index_text: str) -> str | None:
    m = re.search(r"baseline test count\D*(\d+)", index_text, re.IGNORECASE)
    return m.group(1) if m else None


def _dag_integrity_warnings(graph) -> list[str]:
    """Advisory warnings for structural DAG breaks: dangling depends_on edges
    and depends_on cycles (graph/validate). Deterministic; never raises —
    INVARIANT-05 (engine surfaces, agent decides; no enable/disable flag)."""
    try:
        from ..graph import validate
        issues = validate.validate(graph)
    except Exception:
        return []
    out = []
    for src, target in issues.dangling:
        out.append(f"dangling depends_on {src} -> {target}")
    for cycle in issues.cycles:
        # a -> b -> a reads the cycle back to its first member.
        out.append("depends_on cycle " + " -> ".join(cycle + cycle[:1]))
    return out


def _drift_warnings(paths: RepoPaths, rows: list) -> list[str]:
    """Surface silent drift. Two families, both best-effort and never raising:

    1. Phases marked complete while graph entities are still 'planned' (the
       status-transition step was skipped). Conservative on purpose — only fires
       when there *is* completed work AND untouched entities.
    2. Structural DAG breaks — dangling depends_on edges and cycles. Always
       checked (a broken graph is drift regardless of phase state); advisory and
       judgment-based per INVARIANT-05.
    """
    warnings: list[str] = []
    graph = None
    try:
        from ..graph import index
        graph = index.build(paths.docs)
    except Exception:
        graph = None

    completed = [r for r in rows if r.status == "complete"]
    if completed and graph is not None:
        planned = [e.id for e in graph.all()
                   if getattr(e, "status", None) == "planned"]
        if planned:
            sample = ", ".join(planned[:3]) + ("…" if len(planned) > 3 else "")
            noun = "entity" if len(planned) == 1 else "entities"
            warnings.append(
                f"{len(planned)} {noun} still 'planned' while {len(completed)} "
                f"phase(s) complete ({sample}) — cz_transition_status to reconcile.")

    if graph is not None:
        warnings.extend(_dag_integrity_warnings(graph))
    return warnings


# --- portfolio (the derived open-set across concurrent gameplans) -------------
# Multi-axis support (D2): a repo may have several open gameplans at once. The
# focus pointer (config.focus) is the single default-target that persists; the
# OPEN SET is DERIVED here from each gameplan's phase table, never stored.

_GP_KIND_RE = re.compile(r"^>\s*Kind:\s*(.+?)\s*$", re.M)


def gameplan_kind(gdir: Path) -> str:
    """A gameplan's kind from its GAMEPLAN.md ``> Kind:`` header (default
    ``driven`` when absent, so legacy gameplans need no rewrite). Phase 2 layers
    the full kind-definition (lexicon/preflight/template) on top of this parse."""
    gp = gdir / "GAMEPLAN.md"
    if gp.exists():
        m = _GP_KIND_RE.search(gp.read_text(encoding="utf-8"))
        if m:
            return m.group(1).strip()
    return "driven"


def _phase_rows(gdir: Path):
    src = gdir / "CHAT-HANDOFF-INDEX.md"
    if not src.exists():
        src = gdir / "PHASE-STATUS.md"
    if not src.exists():
        return []
    return _tables.parse_phase_table(src.read_text(encoding="utf-8"))


def _lifecycle(rows) -> str:
    """planning | executing | complete — derived from the phase table exactly as
    mutations._refresh_tracker_headers derives the GAMEPLAN.md ``> Status:`` header,
    so the two never disagree."""
    if not rows:
        return "planning"
    if all(r.status == "complete" for r in rows):
        return "complete"
    if any(r.status in ("in_progress", "complete", "blocked", "failed") for r in rows):
        return "executing"
    return "planning"


def gameplan_card(gdir: Path, focus_id: str | None) -> dict:
    """One portfolio entry: id, kind, lifecycle, the current/next phase, blocker
    and pending-cascade counts, the open flag, and whether it is the focus."""
    rows = _phase_rows(gdir)
    cur = next((r for r in rows if r.status == "in_progress"), None)
    nxt = next((r for r in rows if r.status in ("ready", "not_started")), None)
    lifecycle = _lifecycle(rows)
    if cur:
        phase = {"number": cur.number, "name": cur.name, "state": "in_progress"}
    elif nxt:
        phase = {"number": nxt.number, "name": nxt.name, "state": "ready"}
    else:
        phase = None
    gid = gdir.name
    return {
        "id": gid,
        "kind": gameplan_kind(gdir),
        "lifecycle": lifecycle,
        "open": lifecycle != "complete",
        "total_phases": len(rows),
        "phase": phase,
        "blockers": [r.name for r in rows if r.status == "blocked"],
        "pending_cascades": len(pending_cascades(gdir / "_cascade-reports")),
        "is_focus": gid == focus_id,
    }


def portfolio(paths: RepoPaths, config: Config, *, include_closed: bool = False) -> list[dict]:
    """All gameplans as portfolio cards (open by default), focus first then by id.
    The open set is derived from each gameplan's phase table — only the single
    focus pointer persists in config (D2)."""
    cards: list[dict] = []
    root = paths.gameplans
    if root.exists():
        for d in sorted(root.iterdir()):
            if not (d.is_dir() and (d / "GAMEPLAN.md").exists()):
                continue
            card = gameplan_card(d, config.focus)
            if include_closed or card["open"]:
                cards.append(card)
    cards.sort(key=lambda c: (not c["is_focus"], c["id"]))
    return cards


def _portfolio_lines(cards: list[dict]) -> list[str]:
    """Render portfolio cards as compact digest lines (focus marked ★)."""
    out = []
    for c in cards:
        mark = "★" if c["is_focus"] else "•"
        ph = c.get("phase")
        phase_str = (f' phase {ph["number"]}/{c["total_phases"]} "{ph["name"]}"'
                     if ph else f" {c['lifecycle']}")
        extra = ""
        if c["blockers"]:
            extra += f" (blocked: {', '.join(c['blockers'])})"
        if c["pending_cascades"]:
            extra += f" ({c['pending_cascades']} pending cascade)"
        out.append(f"  {mark} {c['id']} [{c['kind']}]{phase_str}{extra}")
    return out


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
    # The focus pointer + the derived open-set portfolio ride in every bundle
    # (cheap). render_digest expands the portfolio ONLY when >1 gameplan is open,
    # so a single-gameplan repo renders byte-identically to before (D6 golden gate).
    bundle["focus"] = gid
    bundle["portfolio"] = portfolio(paths, config)
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
    open_cards = [c for c in (bundle.get("portfolio") or []) if c.get("open")]
    if not bundle.get("active_gameplan"):
        # No focus set: still surface any open gameplans so they aren't lost (the
        # multi-axis case where focus was cleared), else the cold-start message.
        if open_cards:
            lines.append(
                f"[Clauderizer] No focus set; {len(open_cards)} open gameplan(s) — "
                f"cz_focus <id> to pick one:")
            lines += _portfolio_lines(open_cards)
        else:
            lines.append("[Clauderizer] No active gameplan. cz_create_gameplan to start.")
        return "\n".join(lines)
    lines.append(
        f"[Clauderizer] {bundle['summary']} "
        f"(size={bundle['size']}, profile={bundle['host_profile']})"
    )
    # The portfolio block expands only with >1 open gameplan (the multi-axis case);
    # a single open gameplan keeps the digest byte-identical to before (D6).
    if len(open_cards) > 1:
        lines.append(f"Portfolio ({len(open_cards)} open):")
        lines += _portfolio_lines(open_cards)
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
        mem_line = (f"Memory: {mem['active_lessons']} active lessons, "
                    f"{mem['project_lessons']} project")
        if mem.get("active_skills"):
            mem_line += f", {mem['active_skills']} skills"
        lines.append(mem_line + suffix)
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
