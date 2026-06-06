"""Structured, graph-aware writes — the mutation tools' implementations.

Every function here routes through ``markdown.writer`` (the single mutation
path) and auto-assigns IDs from what's already in the doc, so frontmatter stays
valid and numbering never collides. These back the ``cz_add_*`` / ``cz_upsert_*``
/ ``cz_transition_status`` MCP tools.
"""

from __future__ import annotations

import re
from datetime import date as _date
from pathlib import Path

from . import assets
from .config import Config
from .graph import cascade, index
from .markdown import sections
from .markdown import writer
from .model import next_numbered_id
from .paths import RepoPaths


def _today(today: str | None) -> str:
    return today or _date.today().isoformat()


def kebab(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower())
    return s.strip("-")


# --- gameplans ----------------------------------------------------------------


def create_gameplan(
    paths: RepoPaths,
    name: str,
    *,
    first_phase: str = "Bootstrap",
    today: str | None = None,
) -> dict:
    today = _today(today)
    gid = f"{today}-{kebab(name)}"
    gdir = paths.gameplan_dir(gid)
    sub = {"name": name, "date": today, "first_phase": first_phase}
    files = []
    for fname in ("GAMEPLAN.md", "CHAT-HANDOFF-INDEX.md", "PHASE-STATUS.md"):
        text = assets.render(f"gameplan/{fname}", **sub)
        path = gdir / fname
        if writer.create_if_absent(path, text):
            files.append(str(path))
    # handoffs/ + _cascade-reports/ + _template/
    (gdir / "handoffs").mkdir(parents=True, exist_ok=True)
    reports = gdir / "_cascade-reports"
    reports.mkdir(parents=True, exist_ok=True)
    writer.create_if_absent(reports / ".gitkeep", "")
    tmpl = assets.template_text("gameplan/handoff.md")
    writer.create_if_absent(gdir / "_template" / "handoff.md", tmpl)
    return {
        "ok": True,
        "gameplan_id": gid,
        "dir": str(gdir),
        "files_changed": files,
        "summary": f"created gameplan {gid}",
    }


# --- append-only numbered logs ------------------------------------------------


def _ensure_doc(path: Path, doc_name: str) -> None:
    if not path.exists():
        tmpl = assets.doc_template(doc_name)
        if tmpl is not None:
            writer.create_if_absent(path, tmpl)


def add_decision(
    paths: RepoPaths,
    *,
    title: str,
    context: str,
    decision: str,
    consequences: str,
    scope: str = "project",
    gameplan_id: str | None = None,
    supersedes: str | None = None,
    today: str | None = None,
) -> dict:
    if scope == "gameplan":
        if not gameplan_id:
            return {"ok": False, "error": "gameplan scope requires gameplan_id"}
        path = paths.gameplan_dir(gameplan_id) / "GAMEPLAN.md"
        prefix, width = "D", 0  # gameplan-internal: D1, D2
    else:
        path = paths.doc("DECISIONS")
        _ensure_doc(path, "DECISIONS")
        prefix, width = "D", 3  # project-wide: D-001

    text = writer.full_text(path)
    new_id = next_numbered_id(text, prefix, sep=("" if width == 0 else "-"), width=width)
    sup = f"\n**Supersedes**: {supersedes}" if supersedes else ""
    entry = (
        f"### {new_id} — {title}\n\n"
        f"**Context**: {context}\n"
        f"**Decision**: {decision}\n"
        f"**Consequences**: {consequences}{sup}"
    )
    writer.append_to_section(path, "Decisions", entry)
    return {"ok": True, "id": new_id, "path": str(path),
            "files_changed": [str(path)], "summary": f"added decision {new_id}"}


def add_invariant(
    paths: RepoPaths, *, text: str, introduced_by: str | None = None
) -> dict:
    path = paths.doc("INVARIANTS")
    _ensure_doc(path, "INVARIANTS")
    doc = writer.full_text(path)
    new_id = next_numbered_id(doc, "INVARIANT", sep="-", width=2)
    intro = f"\n**Introduced by**: {introduced_by}" if introduced_by else ""
    # First line becomes the title; remainder the body.
    title = text.strip().split("\n", 1)[0]
    entry = f"### {new_id} — {title}{intro}\n\n{text.strip()}"
    writer.append_to_section(path, "Invariants", entry)
    return {"ok": True, "id": new_id, "path": str(path),
            "files_changed": [str(path)], "summary": f"added {new_id}"}


def add_finding(
    paths: RepoPaths,
    *,
    title: str,
    severity: str,
    impact: str,
    affected: str = "",
    invariant: str = "",
    preconditions: str = "",
    root_cause: str = "",
    reproduction: str = "",
    recommendation: str = "",
    regression_tests: str = "",
    status: str = "open",
    today: str | None = None,
) -> dict:
    """Append a security finding (``H-NN``) to the append-only HARDENING tracker.

    Also exported as :func:`add_risk`. HARDENING.md is a permanent audit trail:
    findings are append-only and "resolved" by updating their status + a date,
    never deleted. ``severity`` and ``impact`` are always recorded; the richer
    audit fields (affected code, the invariant violated, exploit preconditions,
    root cause, a safe reproduction, the recommended fix, regression tests) are
    rendered only when supplied, so a finding can be logged fast then enriched.
    """
    path = paths.doc("HARDENING")
    _ensure_doc(path, "HARDENING")
    doc = writer.full_text(path)
    new_id = next_numbered_id(doc, "H", sep="-", width=2)
    fields = [
        ("Severity", severity, True),
        ("Status", f"{status.strip()} ({_today(today)})", True),
        ("Affected", affected, False),
        ("Invariant violated", invariant, False),
        ("Preconditions", preconditions, False),
        ("Impact", impact, True),
        ("Root cause", root_cause, False),
        ("Reproduction", reproduction, False),
        ("Recommended fix", recommendation, False),
        ("Regression tests", regression_tests, False),
    ]
    body = "\n".join(
        f"- **{label}**: {str(value).strip()}"
        for label, value, required in fields
        if required or str(value).strip()
    )
    entry = f"### {new_id} — {title.strip()}\n\n{body}"
    writer.append_to_section(path, "Risks", entry)
    return {"ok": True, "id": new_id, "path": str(path),
            "files_changed": [str(path)], "summary": f"added finding {new_id} ({severity.strip()})"}


# ``cz_add_risk`` is an accepted alias for the same operation.
add_risk = add_finding


def resolve_finding(paths: RepoPaths, *, finding_id: str, status: str = "resolved",
                    note: str | None = None, today: str | None = None) -> dict:
    """Update a finding's status (and an optional dated resolution note) in place.

    HARDENING is append-only — findings are "resolved by updating status + a date,
    never deleted". Without this, doing so means a forbidden hand-edit of a tracked
    log. Updates the ``**Status**`` line of the ``H-NN`` block and upserts a
    ``**Resolution**`` line; the entry itself is never removed.
    """
    path = paths.doc("HARDENING")
    text = writer.full_text(path)
    sec = sections.get_section(text, "Risks")
    if sec is None or f"### {finding_id} " not in sec:
        return {"ok": False, "summary": f"finding {finding_id} not found in HARDENING.md"}
    today = _today(today)
    lines = sec.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith(f"### {finding_id} "))
    end = next((j for j in range(start + 1, len(lines)) if lines[j].startswith("### ")),
               len(lines))
    block = lines[start:end]
    new_status = f"- **Status**: {status.strip()} ({today})"
    res_line = f"- **Resolution**: {note.strip()}" if note else None
    new_block, did_status, did_res = [], False, False
    for ln in block:
        st = ln.strip()
        if st.startswith("- **Status**:"):
            new_block.append(new_status); did_status = True
        elif st.startswith("- **Resolution**:") and res_line:
            new_block.append(res_line); did_res = True
        else:
            new_block.append(ln)
    if not did_status:
        new_block.insert(1, new_status)
    if res_line and not did_res:
        while new_block and not new_block[-1].strip():
            new_block.pop()
        new_block.append(res_line)
    writer.upsert_section(path, "Risks", "\n".join(lines[:start] + new_block + lines[end:]))
    return {"ok": True, "id": finding_id, "path": str(path), "files_changed": [str(path)],
            "summary": f"{finding_id} → {status.strip()}"}


def add_lesson(
    paths: RepoPaths, *, gameplan_id: str, text: str, category: str = "Process"
) -> dict:
    path = paths.gameplan_dir(gameplan_id) / "CHAT-HANDOFF-INDEX.md"
    full = writer.full_text(path)
    body = sections.get_section(full, "Accumulated Lessons") or ""
    nums = [int(m.group(1)) for m in re.finditer(r"\*\*(\d+)\.\*\*", body)]
    n = (max(nums) + 1) if nums else 1
    lesson_line = f"**{n}.** {text.strip()}"
    new_section = _insert_under_category(body, category, lesson_line)
    writer.upsert_section(path, "Accumulated Lessons", new_section)
    return {"ok": True, "number": n, "path": str(path),
            "files_changed": [str(path)], "summary": f"added lesson #{n} ({category})"}


def _insert_under_category(section_body: str, category: str, lesson_line: str) -> str:
    heading = f"### Category: {category}"
    lines = section_body.splitlines()
    if heading in section_body:
        # insert at the end of that category block (before next ### or EOF)
        start = next(i for i, ln in enumerate(lines) if ln.strip() == heading)
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if lines[j].startswith("### "):
                end = j
                break
        # drop trailing blanks within the block, then append
        block = lines[start:end]
        while block and not block[-1].strip():
            block.pop()
        block += ["", lesson_line]
        new_lines = lines[:start] + block + [""] + lines[end:]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(new_lines)).strip()
    # category absent: append a new block
    base = section_body.rstrip()
    # remove a leading placeholder if present
    base = re.sub(r"_\(none yet\)_", "", base).rstrip()
    return f"{base}\n\n{heading}\n\n{lesson_line}".strip()


def add_correction(
    paths: RepoPaths,
    *,
    gameplan_id: str,
    phase: str,
    gameplan_said: str,
    actually: str,
    why: str,
    lesson: str | None = None,
    category: str = "Process",
) -> dict:
    path = paths.gameplan_dir(gameplan_id) / "PHASE-STATUS.md"
    doc = writer.full_text(path)
    new_id = next_numbered_id(doc, "C", sep="-", width=2)
    entry = (
        f"### {new_id} — Phase {phase}\n\n"
        f"**Phase**: {phase}\n"
        f"**What gameplan said**: {gameplan_said}\n"
        f"**What was actually correct**: {actually}\n"
        f"**Why**: {why}"
    )
    if lesson:
        entry += f"\n**Lesson**: {lesson}"
    writer.append_to_section(path, "Corrections Log", entry)
    files = [str(path)]
    lesson_result = None
    if lesson:
        lesson_result = add_lesson(paths, gameplan_id=gameplan_id, text=lesson, category=category)
        files += lesson_result["files_changed"]
    return {"ok": True, "id": new_id, "files_changed": files,
            "lesson": lesson_result, "summary": f"added correction {new_id}"}


def add_phase(
    paths: RepoPaths,
    *,
    gameplan_id: str,
    name: str,
    goal: str,
    depends_on_phases: list[str] | None = None,
) -> dict:
    gp = paths.gameplan_dir(gameplan_id) / "GAMEPLAN.md"
    doc = writer.full_text(gp)
    existing = [int(m.group(1)) for m in re.finditer(r"^###\s+Phase\s+(\d+)", doc, re.M)]
    n = (max(existing) + 1) if existing else 0
    deps = ", ".join(depends_on_phases) if depends_on_phases else (f"Phase {n-1}" if n else "nothing")
    entry = (
        f"### Phase {n}: {name}\n\n"
        f"**Goal**: {goal}\n"
        f"**Depends on**: {deps}.\n\n"
        f"| Task | Description | Effort |\n|------|-------------|--------|\n"
        f"| {n}.1 | _(describe)_ | _(est)_ |\n\n"
        f"**Exit criteria**:\n- [ ] _(verifiable)_"
    )
    writer.append_to_section(gp, "Phase Breakdown", entry, level=2)
    files = [str(gp)]
    # add a status row to the trackers
    row = f"| {n} | {name} | ⬜ NOT STARTED | — | — | handoffs/PHASE-{n}-HANDOFF.md |"
    for fname, heading in (
        ("CHAT-HANDOFF-INDEX.md", "Phase Status Table"),
        ("PHASE-STATUS.md", "Phase Status"),
    ):
        path = paths.gameplan_dir(gameplan_id) / fname
        if path.exists():
            sec = sections.get_section(writer.full_text(path), heading) or ""
            if f"| {n} |" not in sec:
                writer.append_to_section(path, heading, row)
                files.append(str(path))
    return {"ok": True, "phase": n, "files_changed": files,
            "summary": f"added Phase {n}: {name}"}


# Phase status lives in the markdown phase tables (not the entity graph), so it
# needs its own blessed mutation — without this, advancing a phase means a
# forbidden hand-edit, and cz_status freezes at "Phase 0" on finished work.
_PHASE_DISPLAY = {
    "not_started": "⬜ NOT STARTED",
    "ready": "🟢 READY",
    "in_progress": "🟡 IN PROGRESS",
    "complete": "✅ COMPLETE",
    "blocked": "⚠️ BLOCKED",
    "failed": "🔴 FAILED",
}
_PHASE_ALIASES = {
    "start": "in_progress", "started": "in_progress", "active": "in_progress",
    "wip": "in_progress", "begin": "in_progress",
    "done": "complete", "completed": "complete", "finish": "complete", "finished": "complete",
    "todo": "not_started", "pending": "not_started", "block": "blocked", "fail": "failed",
}


def _set_phase_row(path, heading: str, phase_n: str, display: str, norm: str,
                   today: str) -> bool:
    """Rewrite the status (and dates) of one phase row in a tracker table."""
    text = writer.full_text(path)
    sec = sections.get_section(text, heading)
    if sec is None:
        return False
    out, changed = [], False
    for line in sec.splitlines():
        s = line.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 6 and cells[0] == phase_n:
                cells[2] = display
                if norm in ("in_progress", "complete") and cells[3] in ("—", ""):
                    cells[3] = today
                if norm == "complete":
                    cells[4] = today
                rebuilt = "| " + " | ".join(cells) + " |"
                if rebuilt != s:
                    line, changed = rebuilt, True
        out.append(line)
    if changed:
        writer.upsert_section(path, heading, "\n".join(out))
    return changed


def transition_phase(paths: RepoPaths, *, gameplan_id: str, phase_n: str,
                     to_status: str, today: str | None = None) -> dict:
    """Move a phase's lifecycle status in the gameplan trackers.

    ``to_status`` accepts the normalized words (not_started, ready, in_progress,
    complete, blocked, failed) or friendly aliases (start, done, block, …).
    Starting/completing stamps the Started/Completed dates. This is the write
    that keeps ``cz_status`` / ``cz_next_phase_context`` honest.
    """
    norm = _PHASE_ALIASES.get(to_status.strip().lower(), to_status.strip().lower())
    if norm not in _PHASE_DISPLAY:
        return {"ok": False,
                "summary": f"unknown phase status {to_status!r}; use one of: "
                           f"{', '.join(_PHASE_DISPLAY)}"}
    today = _today(today)
    display = _PHASE_DISPLAY[norm]
    files: list[str] = []
    for fname, heading in (("CHAT-HANDOFF-INDEX.md", "Phase Status Table"),
                           ("PHASE-STATUS.md", "Phase Status")):
        path = paths.gameplan_dir(gameplan_id) / fname
        if path.exists() and _set_phase_row(path, heading, str(phase_n), display, norm, today):
            files.append(str(path))
    if not files:
        return {"ok": False,
                "summary": f"phase {phase_n} not found (or already {norm}) in trackers"}
    return {"ok": True, "phase": str(phase_n), "to_status": norm,
            "files_changed": files, "summary": f"Phase {phase_n} → {norm}"}


def add_amendment(
    paths: RepoPaths,
    *,
    gameplan_id: str,
    title: str,
    affected_sections: str,
    affected_phases: str,
    triggered_by: str,
    what: str,
    why: str,
    today: str | None = None,
) -> dict:
    today = _today(today)
    gp = paths.gameplan_dir(gameplan_id) / "GAMEPLAN.md"
    doc = writer.full_text(gp)
    new_id = next_numbered_id(doc, "A", sep="-", width=3)
    entry = (
        f"### {new_id} — {title}\n\n"
        f"- **Date**: {today}\n"
        f"- **Affected sections in GAMEPLAN.md**: {affected_sections}\n"
        f"- **Affected phases**: {affected_phases}\n"
        f"- **Triggered by**: {triggered_by}\n"
        f"- **What changed**: {what}\n"
        f"- **Why**: {why}\n"
        f"- **Cascade report**: _cascade-reports/{today}-{new_id}.md"
    )
    writer.append_to_section(gp, "Amendments", entry)
    return {"ok": True, "id": new_id, "files_changed": [str(gp)],
            "summary": f"added amendment {new_id}"}


# --- entities + status --------------------------------------------------------

_TYPE_DIR = {
    "subsystem": ("subsystems", "subsys"),
    "feature": ("features", "feat"),
    "external-service": ("datasources", "ext"),
    "capability": ("capabilities", "cap"),
}


def _entity_path(paths: RepoPaths, entity_id: str, type_: str) -> Path:
    folder, _ = _TYPE_DIR.get(type_, ("entities", ""))
    slug = entity_id.split(".", 1)[-1]
    return paths.docs / folder / f"{slug}.md"


def upsert_entity(
    paths: RepoPaths,
    *,
    id: str,
    type: str,
    version: str | None = None,
    status: str | None = None,
    depends_on: list[str] | None = None,
    fields: dict | None = None,
    today: str | None = None,
) -> dict:
    path = _entity_path(paths, id, type)
    data: dict = {"id": id, "type": type}
    if version:
        data["version"] = version
    if status:
        data["status"] = status
    if depends_on is not None:
        data["depends_on"] = depends_on
    data["last_verified"] = _today(today)
    if fields:
        data.update(fields)
    existed = path.exists()
    body = "" if existed else f"\n# {id.split('.', 1)[-1].replace('-', ' ').title()}\n\n_(describe.)_\n"
    writer.write_entity(path, data, body=body, preserve_body=True)
    return {"ok": True, "id": id, "path": str(path), "created": not existed,
            "files_changed": [str(path)],
            "summary": f"{'updated' if existed else 'created'} {id}"}


def transition_status(
    paths: RepoPaths,
    config: Config,
    *,
    id: str,
    to_status: str,
    run_cascade: bool = True,
    today: str | None = None,
) -> dict:
    graph = index.load_or_rebuild(paths.docs, paths.index_file)
    entity = graph.get(id)
    if entity is None:
        return {"ok": False, "error": f"unknown entity {id}"}
    from_status = entity.status
    writer.set_frontmatter_fields(
        entity.path, {"status": to_status, "last_verified": _today(today)}
    )
    result: dict = {
        "ok": True, "id": id, "from": from_status, "to": to_status,
        "files_changed": [str(entity.path)],
        "summary": f"{id}: {from_status} -> {to_status}",
    }
    if run_cascade and config.ritual_enabled("cascade") and config.active_gameplan:
        graph = index.load_or_rebuild(paths.docs, paths.index_file)  # refresh
        reports_dir = paths.gameplan_dir(config.active_gameplan) / "_cascade-reports"
        casc = cascade.run(graph, id, f"status {from_status} -> {to_status}", reports_dir)
        result["cascade"] = casc
        result["files_changed"].append(casc["report_path"])
    return result
