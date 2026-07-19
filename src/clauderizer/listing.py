"""Listing reads over the append-only registers (PhaseKeep m0 asks, O-06..O-14).

The write side of every register (open items, decisions, invariants, findings,
lessons, corrections, amendments, cascade reports, approvals) predates its read
side: at 1.11.0 the registry held 33 write ops against 15 reads, and every
register was reachable only by knowing an id in advance (``cz_get``) or not at
all. This module is the read side: pure parsers over the same markdown the
mutation layer writes, single-sourcing each grammar from the writer that emits
it. Everything here is read-only and lock-free (L-03).

External clients render from these outputs (INVARIANT-01 territory: they must
never parse the markdown themselves), so shapes are additive-stable under the
``contract.CONTRACT_SCHEMA_VERSION`` rules.
"""

from __future__ import annotations

import re
from pathlib import Path

from .config import Config
from .markdown import frontmatter, lesson_state, sections
from .paths import RepoPaths
from .rituals import _tables, status_bundle


def _gameplan_dirs(paths: RepoPaths, gameplan_id: str = "") -> list[Path]:
    """The gameplan directories to walk: one when filtered, else every gameplan
    on disk (open and closed — resolution state is data, not a filter here)."""
    root = paths.gameplans
    if gameplan_id:
        d = root / gameplan_id
        return [d] if (d / "GAMEPLAN.md").exists() else []
    if not root.exists():
        return []
    return [d for d in sorted(root.iterdir())
            if d.is_dir() and (d / "GAMEPLAN.md").exists()]


# --- open items (O-06) --------------------------------------------------------

# The resolve marker as mutations.resolve_open_item writes it:
#   _(resolved 2026-07-19: <resolution text>)_
# Greedy body + end-of-line anchor so resolutions containing ")" survive.
_RESOLUTION_RE = re.compile(r"_\(resolved (\d{4}-\d{2}-\d{2}):?\s*(.*)\)_\s*$")


def open_items(paths: RepoPaths, gameplan_id: str = "",
               include_resolved: bool = True) -> list[dict]:
    """Every tracked open item as a full record:
    ``{gameplan, id, phase, text, resolved, resolved_date, resolution}``.

    ``text`` is the item prose with the phase tag and resolution marker
    stripped — clients get fields, not markers to re-parse."""
    out: list[dict] = []
    for gdir in _gameplan_dirs(paths, gameplan_id):
        for item in status_bundle.open_items(gdir):
            rest = item["text"]
            resolved_date = resolution = None
            m = _RESOLUTION_RE.search(rest)
            if m:
                resolved_date, resolution = m.group(1), m.group(2).strip()
                rest = rest[:m.start()].rstrip()
            pm = status_bundle._OPEN_PHASE_RE.match(rest)
            if pm:
                rest = rest[pm.end():].strip()
            if item["resolved"] and not include_resolved:
                continue
            out.append({
                "gameplan": gdir.name,
                "id": item["id"],
                "phase": item["phase"],
                "text": rest,
                "resolved": item["resolved"],
                "resolved_date": resolved_date,
                "resolution": resolution,
            })
    return out


# --- corpus registers: decisions / invariants / findings (O-07, O-08) ---------

_SUPERSEDES_RE = re.compile(r"^\s*\*\*Supersedes\*\*\s*:\s*(\S+)", re.M)
# The back-ref _mark_superseded upserts: **Superseded by**: D-NNN (date)
_SUPERSEDED_BY_RE = re.compile(r"^\s*\*\*Superseded by\*\*\s*:\s*(\S+)", re.M)
_STATUS_LINE_RE = re.compile(
    r"^\s*\*\*Status\*\*\s*:\s*([a-z]+)\s*(?:\(([^)]*)\))?", re.M | re.I)
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _entry_record(entry: dict, include_bodies: bool) -> dict:
    """Common projection for a ``### ID — title`` corpus entry."""
    from .graph.abstract_index import parse_audience_meta, parse_scope

    body = entry.get("body", "")
    rec = {
        "id": entry["id"],
        "title": entry["title"],
        "status": entry.get("status", "active"),
        "scope": parse_scope(body),
        "audience": parse_audience_meta(body) or None,
        "date": None,
        "supersedes": None,
        "superseded_by": None,
    }
    sm = _STATUS_LINE_RE.search(body)
    if sm:
        detail = sm.group(2) or ""
        dm = _DATE_RE.search(detail)
        if dm:
            rec["date"] = dm.group(0)
    bm = _SUPERSEDED_BY_RE.search(body)
    if bm:
        rec["superseded_by"] = bm.group(1)
    sup = _SUPERSEDES_RE.search(body)
    if sup:
        rec["supersedes"] = sup.group(1).rstrip(".,;")
    if include_bodies:
        rec["body"] = body.strip()
    return rec


def _corpus_entries(paths: RepoPaths, doc_name: str, section: str,
                    include_bodies: bool) -> list[dict]:
    from . import analyze

    doc = paths.doc(doc_name)
    if not doc.exists():
        return []
    text = doc.read_text(encoding="utf-8")
    return [_entry_record(e, include_bodies)
            for e in analyze.parse_entries(text, section)]


def decisions(paths: RepoPaths, include_bodies: bool = False) -> list[dict]:
    """The project decision log (D-NNN) with supersession links both ways —
    the data a client needs to render chains as chains."""
    return _corpus_entries(paths, "DECISIONS", "Decisions", include_bodies)


def invariants(paths: RepoPaths, include_bodies: bool = False) -> list[dict]:
    """The invariant register (INVARIANT-NN) with scope and audience."""
    return _corpus_entries(paths, "INVARIANTS", "Invariants", include_bodies)


def findings(paths: RepoPaths, include_bodies: bool = False) -> list[dict]:
    """The hardening/risk register (H-NN)."""
    return _corpus_entries(paths, "HARDENING", "Risks", include_bodies)


# --- lessons (O-09) -----------------------------------------------------------

_CATEGORY_RE = re.compile(r"^###\s+Category:\s*(.+?)\s*$")
_GP_LESSON_RE = re.compile(r"^\*\*(\d+)\.\*\*\s*(.*)$")
_EVIDENCE_TAG_RE = re.compile(r"\*\(evidence:\s*(.*?)\)\*")
_FROM_TAG_RE = re.compile(r"\*\(from\s+(.*?)\)\*")


def _lesson_records(text: str, section: str, line_re: re.Pattern,
                    origin: str) -> list[dict]:
    from .graph.abstract_index import parse_audience

    body = sections.get_section(text, section) or ""
    category = None
    out: list[dict] = []
    for raw in body.splitlines():
        line = raw.strip()
        cm = _CATEGORY_RE.match(line)
        if cm:
            category = cm.group(1)
            continue
        m = line_re.match(line)
        if not m:
            continue
        state, detail = lesson_state.parse_state(line)
        lesson_text = m.group(2).strip()
        ev = _EVIDENCE_TAG_RE.search(lesson_text)
        frm = _FROM_TAG_RE.search(lesson_text)
        out.append({
            "id": m.group(1),
            "origin": origin,
            "category": category,
            "state": state,
            "state_detail": detail or None,
            "audience": parse_audience(line) or None,
            "evidence": ev.group(1) if ev else None,
            "from_gameplan": frm.group(1) if frm else None,
            "text": lesson_text,
        })
    return out


def lessons(paths: RepoPaths, config: Config, gameplan_id: str = "") -> list[dict]:
    """The lesson corpus with curation state (active/obsolete/promoted).

    Project lessons (``L-NN`` in docs/LESSONS.md) plus the accumulated lessons
    of one gameplan — the focus by default. ``origin`` says which register a
    record came from; gameplan lesson ids are the per-gameplan numbers."""
    out: list[dict] = []
    project_doc = paths.doc("LESSONS")
    if project_doc.exists():
        out += _lesson_records(
            project_doc.read_text(encoding="utf-8"), "Lessons",
            re.compile(r"^\*\*(L-\d+)\.\*\*\s*(.*)$"), "project")
    gid = gameplan_id or (config.focus or "")
    if gid:
        idx = paths.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md"
        if idx.exists():
            recs = _lesson_records(
                idx.read_text(encoding="utf-8"), "Accumulated Lessons",
                _GP_LESSON_RE, "gameplan")
            for r in recs:
                r["gameplan"] = gid
            out += recs
    return out


# --- corrections (O-10) -------------------------------------------------------

_CORRECTION_HEAD_RE = re.compile(r"^###\s+(C-\d+)(?:\s+—\s+(.*))?$")
_FIELD_RE = re.compile(r"^\*\*([^*]+)\*\*\s*:\s*(.*)$")

_CORRECTION_FIELD_KEYS = {
    "Phase": "phase",
    "What gameplan said": "gameplan_said",
    "What was actually correct": "actually",
    "Why": "why",
    "Lesson": "lesson",
}


def corrections(paths: RepoPaths, gameplan_id: str = "") -> list[dict]:
    """The correction log (C-NN) as structured records, portfolio-wide by
    default — parsed from the same PHASE-STATUS.md entries
    ``mutations.add_correction`` writes."""
    out: list[dict] = []
    for gdir in _gameplan_dirs(paths, gameplan_id):
        tracker = gdir / "PHASE-STATUS.md"
        if not tracker.exists():
            continue
        body = sections.get_section(
            tracker.read_text(encoding="utf-8"), "Corrections Log") or ""
        cur: dict | None = None
        cur_field: str | None = None
        for raw in body.splitlines():
            line = raw.rstrip()
            hm = _CORRECTION_HEAD_RE.match(line.strip())
            if hm:
                cur = {"gameplan": gdir.name, "id": hm.group(1),
                       "heading": (hm.group(2) or "").strip() or None}
                cur_field = None
                out.append(cur)
                continue
            if cur is None:
                continue
            fm = _FIELD_RE.match(line.strip())
            if fm and fm.group(1) in _CORRECTION_FIELD_KEYS:
                cur_field = _CORRECTION_FIELD_KEYS[fm.group(1)]
                cur[cur_field] = fm.group(2).strip()
            elif cur_field and line.strip() and not line.strip().startswith("###"):
                cur[cur_field] += "\n" + line.strip()
    return out


# --- amendments (O-13) --------------------------------------------------------

_AMENDMENT_HEAD_RE = re.compile(r"^###\s+(A-\d+)\s+—\s+(.*)$")
_AMENDMENT_BULLET_RE = re.compile(r"^-\s*\*\*([^*]+)\*\*\s*:\s*(.*)$")

_AMENDMENT_FIELD_KEYS = {
    "Date": "date",
    "Affected sections in GAMEPLAN.md": "affected_sections",
    "Affected phases": "affected_phases",
    "Triggered by": "triggered_by",
    "What changed": "what",
    "Why": "why",
}


def amendments(paths: RepoPaths, gameplan_id: str = "") -> list[dict]:
    """Gameplan amendments (A-NNN) as structured records — the read side of
    ``mutations.add_amendment``'s bullet grammar."""
    out: list[dict] = []
    for gdir in _gameplan_dirs(paths, gameplan_id):
        body = sections.get_section(
            (gdir / "GAMEPLAN.md").read_text(encoding="utf-8"), "Amendments") or ""
        cur: dict | None = None
        for raw in body.splitlines():
            line = raw.strip()
            hm = _AMENDMENT_HEAD_RE.match(line)
            if hm:
                cur = {"gameplan": gdir.name, "id": hm.group(1),
                       "title": hm.group(2).strip()}
                out.append(cur)
                continue
            if cur is None:
                continue
            bm = _AMENDMENT_BULLET_RE.match(line)
            if bm and bm.group(1) in _AMENDMENT_FIELD_KEYS:
                cur[_AMENDMENT_FIELD_KEYS[bm.group(1)]] = bm.group(2).strip()
    return out


# --- phase detail (O-11) ------------------------------------------------------

_ASSIGNED_LINE_RE = re.compile(r"^\*\*Assigned\*\*\s*:\s*(.+?)\s*$", re.M)
_GP_ASSIGNEE_RE = re.compile(r"^>\s*Assignee:\s*(.+?)\s*$", re.M)
_GOAL_LINE_RE = re.compile(r"^\*\*Goal\*\*\s*:\s*(.+?)\s*$", re.M)


def gameplan_assignee(gdir: Path) -> str | None:
    """The gameplan-level default assignee from the ``> Assignee:`` header
    (the O-02 provisional shape; absent means unassigned)."""
    gp = gdir / "GAMEPLAN.md"
    if gp.exists():
        m = _GP_ASSIGNEE_RE.search(gp.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    return None


def _phase_section_fields(gp_text: str, number: str) -> dict:
    """Per-phase fields read from the GAMEPLAN.md phase block: goal and the
    ``**Assigned**:`` override line."""
    body = sections.get_section(gp_text, "Phase Breakdown") or ""
    blk = status_bundle.phase_block(body, number)
    if blk is None:
        return {"goal": None, "assigned": None}
    lines, start, end = blk
    chunk = "\n".join(lines[start:end])
    gm = _GOAL_LINE_RE.search(chunk)
    am = _ASSIGNED_LINE_RE.search(chunk)
    return {"goal": gm.group(1) if gm else None,
            "assigned": am.group(1) if am else None}


def phase_detail(paths: RepoPaths, config: Config, gameplan_id: str = "") -> list[dict]:
    """Every gameplan's full phase table with per-phase exit-criteria state,
    approvals (computed, staleness included), dates, handoff path, and
    assignment — the read the reconciliation strip and gameplan drill-in
    views cannot exist without (O-11)."""
    out: list[dict] = []
    for gdir in _gameplan_dirs(paths, gameplan_id):
        gp_text = (gdir / "GAMEPLAN.md").read_text(encoding="utf-8")
        rows = _tables.parse_phase_table_full(_tracker_text(gdir))
        default_assignee = gameplan_assignee(gdir)
        phases = []
        for row in rows:
            fields = _phase_section_fields(gp_text, row.number)
            phases.append({
                "number": row.number,
                "name": row.name,
                "status": row.status,
                "started": row.started,
                "completed": row.completed,
                "handoff": row.handoff,
                "goal": fields["goal"],
                "assigned": fields["assigned"] or default_assignee,
                "exit_criteria": status_bundle.exit_criteria(gdir, row.number),
            })
        card = status_bundle.gameplan_card(gdir, config.focus, paths.kinds_dir)
        out.append({
            "gameplan": gdir.name,
            "kind": card["kind"],
            "lifecycle": card["lifecycle"],
            "assignee": default_assignee,
            "phases": phases,
        })
    return out


def _tracker_text(gdir: Path) -> str:
    src = gdir / "CHAT-HANDOFF-INDEX.md"
    if not src.exists():
        src = gdir / "PHASE-STATUS.md"
    return src.read_text(encoding="utf-8") if src.exists() else ""


# --- cascade reports (O-12) ---------------------------------------------------

_REPORT_TITLE_RE = re.compile(r"^#\s+Cascade Report:\s*(.*)$", re.M)
_DEPENDENT_LINE_RE = re.compile(
    r"^-\s+\*\*(?P<id>\S+)\*\*"          # - **entity.id**
    r"(?:\s+\(status:\s*(?P<status>[^)]*)\))?"
    r".*?—\s*(?:checked:\s*)?(?P<verdict>.*)$")


def cascade_reports(paths: RepoPaths, gameplan_id: str = "",
                    include_resolved: bool = True) -> list[dict]:
    """Cascade reports as data: trigger, per-dependent verdicts (or pending
    ``needs_review``), the updates-applied/deferred text, and the same
    pending predicate the digest and preflight use."""
    out: list[dict] = []
    for gdir in _gameplan_dirs(paths, gameplan_id):
        reports_dir = gdir / "_cascade-reports"
        if not reports_dir.exists():
            continue
        pending_names = set(status_bundle.pending_cascades(reports_dir))
        for report in sorted(reports_dir.glob("*.md"),
                             key=lambda p: status_bundle.report_sort_key(p.name)):
            text = report.read_text(encoding="utf-8")
            pending = report.name in pending_names
            if pending is False and not include_resolved:
                continue
            tm = _REPORT_TITLE_RE.search(text)
            dependents = []
            for kind, heading in (("direct", "Direct dependents"),
                                  ("transitive", "Transitive dependents")):
                body = sections.get_section(text, heading) or ""
                for line in body.splitlines():
                    dm = _DEPENDENT_LINE_RE.match(line.strip())
                    if not dm:
                        continue
                    verdict = dm.group("verdict").strip()
                    needs_review = "_needs review_" in verdict
                    dependents.append({
                        "entity": dm.group("id"),
                        "kind": kind,
                        "status": (dm.group("status") or "").strip() or None,
                        "needs_review": needs_review,
                        "verdict": None if needs_review else verdict.strip("_ ") or None,
                    })
            out.append({
                "gameplan": gdir.name,
                "report": report.name,
                "trigger": tm.group(1).strip() if tm else None,
                "pending": pending,
                "dependents": dependents,
                "updates_applied": _clean_section(text, "Updates applied"),
                "updates_deferred": _clean_section(text, "Updates deferred"),
            })
    return out


def _clean_section(text: str, heading: str) -> str | None:
    body = (sections.get_section(text, heading) or "").strip()
    if not body or body.startswith("_("):
        return None
    return body


# --- docs (O-14) --------------------------------------------------------------


def docs_index(paths: RepoPaths) -> list[dict]:
    """The canonical-document index for a Docs view: top-level docs/*.md, the
    procedure, and every gameplan's handoffs and post-mortem. Names are paths
    relative to docs/ and are the ids ``doc()`` accepts."""
    out: list[dict] = []
    if not paths.docs.exists():
        return out

    def add(p: Path) -> None:
        try:
            stat = p.stat()
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return
        _fm, body = frontmatter.parse(text)
        title = next((ln.lstrip("# ").strip() for ln in body.splitlines()
                      if ln.startswith("# ")), None)
        out.append({
            "name": str(p.relative_to(paths.docs)),
            "title": title,
            "bytes": stat.st_size,
            "mtime": int(stat.st_mtime),
        })

    for p in sorted(paths.docs.glob("*.md")):
        add(p)
    if paths.procedure_file.exists():
        add(paths.procedure_file)
    for gdir in _gameplan_dirs(paths):
        for p in sorted((gdir / "handoffs").glob("*.md")) if (gdir / "handoffs").exists() else []:
            add(p)
        pm = gdir / "POST-MORTEM.md"
        if pm.exists():
            add(pm)
    return out


def doc(paths: RepoPaths, name: str) -> dict:
    """One canonical document's body, frontmatter-stripped — the front-door
    read that lets a client render docs without parsing repo files
    (INVARIANT-01). ``name`` is relative to docs/ (``VISION`` or
    ``VISION.md`` or ``gameplans/<id>/handoffs/PHASE-0-HANDOFF.md``)."""
    if not name.endswith(".md"):
        name += ".md"
    target = (paths.docs / name).resolve()
    docs_root = paths.docs.resolve()
    if docs_root not in target.parents:
        return {"ok": False, "name": name,
                "error": "doc name must resolve inside docs/"}
    if not target.is_file():
        return {"ok": False, "name": name, "error": f"no such doc: {name}"}
    _fm, body = frontmatter.parse(target.read_text(encoding="utf-8"))
    title = next((ln.lstrip("# ").strip() for ln in body.splitlines()
                  if ln.startswith("# ")), None)
    return {"ok": True, "name": name, "title": title, "body": body}


# --- assignments (O-02) -------------------------------------------------------


def assignments(paths: RepoPaths, config: Config, gameplan_id: str = "") -> dict:
    """The assignment surface in one read: the manager role plus every
    gameplan's default assignee and per-phase overrides (provisional shape,
    revisitable when PhaseKeep m3 builds the first consumer)."""
    gameplans = []
    for gdir in _gameplan_dirs(paths, gameplan_id):
        gp_text = (gdir / "GAMEPLAN.md").read_text(encoding="utf-8")
        default_assignee = gameplan_assignee(gdir)
        phases = []
        for row in _tables.parse_phase_table(_tracker_text(gdir)):
            fields = _phase_section_fields(gp_text, row.number)
            if fields["assigned"]:
                phases.append({"number": row.number, "assigned": fields["assigned"]})
        gameplans.append({"gameplan": gdir.name, "assignee": default_assignee,
                          "phases": phases})
    return {"manager": config.manager or None, "gameplans": gameplans}
