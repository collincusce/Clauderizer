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

# --- approval criteria (gameplan 2026-07-01, decision D1) -------------------------
# An exit criterion may bind a HUMAN APPROVAL to a content hash:
#     - [ ] APPROVAL: briefs/shot-spec.md — human signs off the shot spec
# cz_approve_gate records the artifact's short sha256 in a trailing marker:
#     _(approved 2026-07-01 sha256:a1b2c3d4e5f6 — note)_
# Satisfaction is COMPUTED at read time, never enforced: a recorded hash that no
# longer matches the artifact means the approval is STALE and the criterion
# reports unsatisfied — surfaced by every reader (check / transition / preflight /
# status), never blocking anything (INVARIANT-05). Hash-derived authority adapted
# to a passive ask-time layer: edit the artifact and the old approval stops
# counting, with no daemon and no lockout.
_APPROVAL_TEXT_RE = re.compile(r"^APPROVAL:\s*(\S+)(?:\s*—\s*(.*?))?\s*$")
_APPROVED_MARKER_RE = re.compile(
    r"_\(approved (\d{4}-\d{2}-\d{2}) sha256:([0-9a-f]{8,64})((?:[^)])*)\)_\s*$")
APPROVAL_HASH_LEN = 12


def artifact_hash(root: Path, rel_path: str) -> str | None:
    """Short sha256 of a repo file's bytes, or ``None`` when it is not a file
    (missing artifacts surface as a state, never an exception)."""
    import hashlib

    try:
        p = root / rel_path
        if not p.is_file():
            return None
        return hashlib.sha256(p.read_bytes()).hexdigest()[:APPROVAL_HASH_LEN]
    except OSError:
        return None


def split_approval(text: str) -> tuple[str, str, dict | None] | None:
    """Parse a criterion text as an approval row.

    Returns ``(base_text, artifact, approval)`` — ``approval`` is
    ``{date, hash, note}`` from the trailing marker, or ``None`` when not yet
    approved. Returns ``None`` when the text is not an APPROVAL row at all."""
    m = _APPROVED_MARKER_RE.search(text)
    base = text[:m.start()].rstrip() if m else text
    am = _APPROVAL_TEXT_RE.match(base)
    if not am:
        return None
    approval = None
    if m:
        approval = {"date": m.group(1), "hash": m.group(2),
                    "note": (m.group(3) or "").strip(" —-")}
    return base, am.group(1), approval


def _evaluate_approval(entry: dict, gameplan_dir: Path) -> dict:
    """Fold computed approval state into an exit-criteria entry (D1).

    For an APPROVAL row, ``checked`` becomes the COMPUTED satisfaction — a
    checkbox glyph without a current recorded hash does not count. Non-approval
    rows pass through untouched."""
    parsed = split_approval(entry["text"])
    if parsed is None:
        return entry
    base, artifact, approval = parsed
    entry["kind"] = "approval"
    entry["artifact"] = artifact
    # gameplan_dir is <root>/docs/gameplans/<gid> (paths.gameplan_dir), so the
    # repo root — which artifact paths are relative to — is two levels up.
    current = artifact_hash(gameplan_dir.parents[2], artifact)
    if approval is None:
        entry["state"], entry["checked"] = "unapproved", False
        entry["detail"] = (f"approval for '{artifact}' not recorded — "
                           "record it with cz_approve_gate")
    elif current is None:
        entry["state"], entry["checked"] = "missing", False
        entry["detail"] = f"approved artifact '{artifact}' is missing on disk"
    elif current == approval["hash"]:
        entry["state"], entry["checked"] = "approved", True
        entry["detail"] = f"approved {approval['date']} (sha256 {approval['hash']})"
    else:
        entry["state"], entry["checked"] = "stale", False
        entry["detail"] = (f"approval stale — '{artifact}' changed since "
                           f"{approval['date']} (sha256 {approval['hash']} → {current})")
    return entry


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
            out.append(_evaluate_approval(
                {"checked": m.group(1).lower() == "x", "text": text}, gameplan_dir))
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


def gameplan_card(gdir: Path, focus_id: str | None,
                  kinds_overlay: Path | None = None) -> dict:
    """One portfolio entry: id, kind, lifecycle, the current/next phase, blocker
    and pending-cascade counts, the open flag, and whether it is the focus.
    ``phase_label`` is the kind's display word for "phase" (D3 lexicon, e.g.
    "stage" for a campaign) — display-only; the on-disk table still says Phase."""
    from .. import kinds

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
    kind_name = gameplan_kind(gdir)
    return {
        "id": gid,
        "kind": kind_name,
        "phase_label": kinds.resolve(kind_name, kinds_overlay).label("phase"),
        "lifecycle": lifecycle,
        "open": lifecycle != "complete",
        "total_phases": len(rows),
        "phase": phase,
        "blockers": [r.name for r in rows if r.status == "blocked"],
        "pending_cascades": len(pending_cascades(gdir / "_cascade-reports")),
        "is_focus": gid == focus_id,
    }


def deliverables_for(paths: RepoPaths, gid: str) -> list[dict]:
    """Tracked deliverable entities owned by gameplan ``gid`` (D2): docs/entities/
    docs with ``type: deliverable`` + ``gameplan: <gid>`` frontmatter, as
    ``{id, status, version}`` sorted by id. Deliverables are a campaign's
    execution units (a flagship film, a pillar short) — never individual
    rendered asset files."""
    from ..markdown import frontmatter

    ent_dir = paths.docs / "entities"
    out: list[dict] = []
    if not ent_dir.exists():
        return out
    for p in sorted(ent_dir.glob("*.md")):
        try:
            data, _body = frontmatter.parse(p.read_text(encoding="utf-8"))
        except OSError:
            continue
        if (str(data.get("type", "")) == "deliverable"
                and str(data.get("gameplan", "")) == gid):
            out.append({"id": str(data.get("id", p.stem)),
                        "status": str(data.get("status", "planned")),
                        "version": str(data.get("version", ""))})
    return out


def deliverable_matrix_md(delivs: list[dict], lifecycle: list[str]) -> str:
    """The deliverables×lifecycle board as a markdown table — DETAIL views only,
    never the injected digest (D-027/INVARIANT-08). Without a kind-defined
    lifecycle it falls back to a plain status list; a status outside the
    lifecycle renders beside the id instead of a column (advisory model)."""
    if not delivs:
        return "_(no deliverables tracked)_"
    if not lifecycle:
        return "\n".join(f"- {d['id']}: {d['status']}" for d in delivs)
    header = "| deliverable | " + " | ".join(lifecycle) + " |"
    sep = "|" + "---|" * (len(lifecycle) + 1)
    rows = []
    for d in delivs:
        label = d["id"] if d["status"] in lifecycle else f"{d['id']} ({d['status']})"
        cells = ["●" if d["status"] == s else "" for s in lifecycle]
        rows.append("| " + label + " | " + " | ".join(cells) + " |")
    return "\n".join([header, sep] + rows)


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
            card = gameplan_card(d, config.focus, paths.kinds_dir)
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
        plabel = c.get("phase_label", "phase")  # D3 lexicon (display-only)
        phase_str = (f' {plabel} {ph["number"]}/{c["total_phases"]} "{ph["name"]}"'
                     if ph else f" {c['lifecycle']}")
        extra = ""
        if c["blockers"]:
            extra += f" (blocked: {', '.join(c['blockers'])})"
        if c["pending_cascades"]:
            extra += f" ({c['pending_cascades']} pending cascade)"
        out.append(f"  {mark} {c['id']} [{c['kind']}]{phase_str}{extra}")
    return out


def compute(paths: RepoPaths, config: Config, *, conditions: bool = False) -> dict:
    """``conditions=True`` additionally evaluates the focus gameplan's standing
    conditions (D3) — shell probes, so ONLY tool calls pass it; the default
    keeps the read-only hook digest free of subprocesses (INVARIANT-06)."""
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
    # Modernization staleness (D-042): the LIGHT check only — a version-string
    # compare against the config stamp, read-only and hook-safe. The full
    # detector suite (probes, pairwise scans) lives in cz_modernize.
    from .. import PROCEDURE_VERSION as _engine_procedure

    if (config.procedure_version or "") != _engine_procedure:
        bundle["modernization"] = {
            "corpus": config.procedure_version or None,
            "engine": _engine_procedure,
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
    # Display-only lexicon (D3): the focus kind's word for "phase"/"gameplan"
    # (e.g. stage/campaign). Identity for driven, so the golden single-gameplan
    # digest stays byte-identical. The on-disk tables/headings are untouched.
    from .. import kinds

    _k = kinds.resolve(gameplan_kind(gdir), paths.kinds_dir)
    ph_w, gp_w = _k.label("phase"), _k.label("gameplan")
    bundle["kind"] = _k.name
    # Deliverable rollup (D2): present ONLY when this gameplan tracks deliverable
    # entities — a repo without them renders its digest exactly as before.
    delivs = deliverables_for(paths, gid)
    if delivs:
        done_status = _k.lifecycle[-1] if _k.lifecycle else ""
        bundle["deliverables"] = {
            "total": len(delivs),
            "done": sum(1 for d in delivs if d["status"] == done_status),
            "done_label": done_status,
        }
    if conditions:
        from . import conditions as _cond

        conds = _cond.evaluate(paths, gid)
        if conds:
            bundle["standing_conditions"] = conds
    if cur:
        bundle["summary"] = (
            f"Gameplan {gid}: {ph_w} {cur['number']}/{total} IN PROGRESS — \"{cur['name']}\"."
        )
        bundle["next_action"] = f"cz_preflight, then execute the {ph_w} tasks."
    elif nxt:
        bundle["summary"] = (
            f"Gameplan {gid}: next ready {ph_w} {nxt['number']}/{total} — \"{nxt['name']}\"."
        )
        bundle["next_action"] = "cz_next_phase_context, then cz_preflight."
    elif total and all(p["status"] == "complete" for p in bundle["phases"]):
        # A finished gameplan is a success state, not a confusing dead end.
        bundle["summary"] = f"Gameplan {gid}: all {total} {ph_w}(s) COMPLETE. 🎉"
        bundle["next_action"] = (
            f"Close out the {gp_w} (post-mortem, final cascade), or "
            "cz_create_gameplan to start the next initiative."
        )
        # No next phase means no handoff to size — say so instead of silently
        # dropping the figure the CHANGELOG promises (H-03).
        bundle["memory"]["handoff_note"] = "n/a: gameplan complete"
    else:
        bundle["summary"] = f"Gameplan {gid}: no in-progress or ready {ph_w} found."
        bundle["next_action"] = f"Review the {gp_w} or cz_add_phase."
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
    dl = bundle.get("deliverables")
    if dl and dl.get("total"):
        # One rollup line, focused gameplan only (D2); the full board lives in
        # cz_gameplans' detail view, never the injected digest (D-027).
        if dl.get("done_label"):
            lines.append(f"Deliverables: {dl['done']}/{dl['total']} {dl['done_label']}.")
        else:
            lines.append(f"Deliverables: {dl['total']} tracked.")
    met = [c["name"] for c in (bundle.get("standing_conditions") or []) if c.get("met")]
    if met:
        # One line, only when a declared condition is actually met (D3); the
        # engine proposes, the agent decides — nothing runs by itself.
        lines.append("⏰ Standing condition met: " + ", ".join(met)
                     + " — iteration proposed (cz_loop_step).")
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
    mz = bundle.get("modernization")
    if mz:
        # "carries" on purpose: the PROCEDURE version is the methodology
        # document's own line, not the engine's package version — the two
        # near-collide numerically (engine 1.4.x carries procedure 1.5.x) and
        # the earlier "vs engine" phrasing read as a version skew.
        where = (f"corpus is at procedure {mz['corpus']}" if mz.get("corpus")
                 else "corpus has no procedure stamp yet")
        lines.append(
            f"⚙ Modernization: {where}; this engine carries procedure "
            f"{mz['engine']} — `clauderize upgrade` applies the mechanical "
            "updates; cz_modernize lists the advisory proposals.")
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
