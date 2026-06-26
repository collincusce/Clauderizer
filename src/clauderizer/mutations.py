"""Structured, graph-aware writes — the mutation tools' implementations.

Every function here routes through ``markdown.writer`` (the single mutation
path) and auto-assigns IDs from what's already in the doc, so frontmatter stays
valid and numbering never collides. These back the ``cz_add_*`` / ``cz_upsert_*``
/ ``cz_transition_status`` MCP tools.
"""

from __future__ import annotations

import functools
import re
from datetime import date as _date
from pathlib import Path

from . import assets
from .config import Config
from .graph import cascade, index
from .locking import write_lock
from .markdown import lesson_state
from .markdown import sections
from .markdown import skill_state
from .markdown import tables
from .markdown import writer
from .model import next_numbered_id
from .paths import RepoPaths


def _today(today: str | None) -> str:
    return today or _date.today().isoformat()


def kebab(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower())
    return s.strip("-")


def _locked(fn):
    """Serialize the whole mutation across processes (H-05, gameplan D1).

    IDs are allocated from a read that the final section write trusts, so the
    lock must span the full read-modify-write — it wraps the public function,
    not the individual ``markdown.writer`` calls. Reentrant: mutations that
    compose other mutations (``consolidate_lessons`` -> ``add_lesson``) take
    the lock once. Read tools never acquire it (L-03).
    """

    @functools.wraps(fn)
    def wrapper(paths, *args, **kwargs):
        with write_lock(paths.write_lock_file):
            return fn(paths, *args, **kwargs)

    return wrapper


# --- gameplans ----------------------------------------------------------------


@_locked
def create_gameplan(
    paths: RepoPaths,
    name: str,
    *,
    first_phase: str = "Bootstrap",
    kind: str = "driven",
    today: str | None = None,
) -> dict:
    today = _today(today)
    gid = f"{today}-{kebab(name)}"
    gdir = paths.gameplan_dir(gid)
    # kind: "driven" (finite phase DAG, terminal post-mortem) or "loop" (a standing
    # iterative maintenance gameplan — see GAMEPLAN-PROCEDURE.md "Loop Gameplans").
    sub = {"name": name, "date": today, "first_phase": first_phase, "kind": kind}
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


@_locked
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
    evidence: str | None = None,
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

    today = _today(today)
    text = writer.full_text(path)
    new_id = next_numbered_id(text, prefix, sep=("" if width == 0 else "-"), width=width)
    sup = f"\n**Supersedes**: {supersedes}" if supersedes else ""
    ev = f"\n**Evidence**: {evidence.strip()}" if evidence and evidence.strip() else ""
    # A new decision is born active (Phase 4 supersession lifecycle): the Status field
    # makes a decision's place in its lifecycle machine-readable, so the analyze ranker
    # can keep a superseded predecessor from outranking it.
    entry = (
        f"### {new_id} — {title}\n\n"
        f"**Context**: {context}\n"
        f"**Decision**: {decision}\n"
        f"**Consequences**: {consequences}{sup}{ev}\n"
        f"**Status**: active ({today})"
    )
    writer.append_to_section(path, "Decisions", entry)
    result = {"ok": True, "id": new_id, "path": str(path),
              "files_changed": [str(path)], "summary": f"added decision {new_id}"}
    # Bidirectional supersession (INVARIANT-03: memory is never deleted — the
    # predecessor is annotated IN PLACE, never removed). Forward-only "Supersedes"
    # leaves a stale decision with no pointer to its replacement; this writes the
    # back-ref + flips the predecessor's Status to superseded so it is navigable and
    # demoted. Best-effort and idempotent — surfaces only when the target is found.
    if supersedes:
        back = _mark_superseded(path, "Decisions", supersedes.strip(), new_id, today)
        if back:
            result["superseded"] = supersedes.strip()
            result["summary"] += f" (supersedes {supersedes.strip()})"
    # Analyze gate (D-016): surface related / possibly-superseded existing entries so a
    # conflict is noticed at write time. Best-effort, judgment-based, never blocks.
    try:
        from . import analyze as _analyze

        rel = _analyze.analyze(paths, f"{title}. {decision} {context}", k=3,
                               exclude_ids=(new_id,))
        related = rel["decisions"] + rel["invariants"]
        if related:
            result["related"] = related
            result["advisory"] = (
                "Related existing entries — check for contradiction/supersession: "
                + ", ".join(f"{r['id']} ({r['title']})" for r in related)
            )
    except Exception:
        pass
    return result


def _mark_superseded(path: Path, section: str, target_id: str, new_id: str,
                     today: str) -> bool:
    """Annotate decision ``target_id`` in place as superseded by ``new_id`` (D-018 / Phase 4).

    Append-only safe (INVARIANT-03: memory is never deleted): the predecessor entry
    is never removed — its block gains a ``**Superseded by**: <new_id> (<date>)``
    pointer and its ``**Status**`` line is flipped to ``superseded (<date>)``. Both
    fields are *upserted* (replaced if already present), so re-applying the same
    supersession is a no-op — idempotent. Returns ``True`` if the block was found and
    written, ``False`` if ``target_id`` is not an entry in ``section`` (advisory: the
    caller treats a miss as "nothing to back-ref", never an error).
    """
    body = sections.get_section(writer.full_text(path), section)
    if body is None:
        return False
    lines = body.splitlines()
    anchor = f"### {target_id} "
    start = next((i for i, ln in enumerate(lines) if ln.startswith(anchor)), None)
    if start is None:
        return False
    end = next((j for j in range(start + 1, len(lines)) if lines[j].startswith("### ")),
               len(lines))
    block = lines[start:end]
    status_line = f"**Status**: superseded ({today})"
    backref_line = f"**Superseded by**: {new_id} ({today})"
    new_block, did_status, did_backref = [], False, False
    for ln in block:
        st = ln.strip()
        if st.startswith("**Status**:"):
            new_block.append(status_line); did_status = True
        elif st.startswith("**Superseded by**:"):
            new_block.append(backref_line); did_backref = True
        else:
            new_block.append(ln)
    if not did_status:
        # No Status line yet (older entry): append one, after the back-ref.
        new_block.append(status_line)
    if not did_backref:
        # Insert the back-ref directly before the Status line for a stable field order.
        si = next((i for i, ln in enumerate(new_block)
                   if ln.strip().startswith("**Status**:")), len(new_block))
        new_block.insert(si, backref_line)
    new_body = "\n".join(lines[:start] + new_block + lines[end:])
    return writer.upsert_section(path, section, new_body)


@_locked
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


@_locked
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


@_locked
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


@_locked
def add_lesson(
    paths: RepoPaths, *, gameplan_id: str, text: str, category: str = "Process",
    evidence: str | None = None,
) -> dict:
    path = paths.gameplan_dir(gameplan_id) / "CHAT-HANDOFF-INDEX.md"
    full = writer.full_text(path)
    body = sections.get_section(full, "Accumulated Lessons") or ""
    # Line-anchored like next_numbered_id: a lesson *text* mentioning "**3.**"
    # must not shift the sequence.
    nums = [int(m.group(1)) for m in re.finditer(r"^\s*\*\*(\d+)\.\*\*", body, re.M)]
    n = (max(nums) + 1) if nums else 1
    lesson_line = f"**{n}.** {text.strip()}"
    # Provenance rides inline so it survives every handoff rollup. The trailing
    # italic marker is NOT a lesson-state marker (lesson_state reads an
    # (obsolete|promoted …) marker at line end), so state parsing is unaffected.
    if evidence and evidence.strip():
        lesson_line += f" *(evidence: {evidence.strip()})*"
    new_section = _insert_under_category(body, category, lesson_line)
    writer.upsert_section(path, "Accumulated Lessons", new_section)
    result = {"ok": True, "number": n, "path": str(path),
              "files_changed": [str(path)], "summary": f"added lesson #{n} ({category})"}
    # Write-time near-duplicate advisory (Phase 5, the SimpleMem online-synthesis
    # borrow): surface existing PROJECT lessons this one strongly overlaps so the
    # agent can consolidate instead of appending — the symmetric write-time
    # enrichment add_decision already has. Best-effort, judgment-based, NEVER blocks
    # (INVARIANT-05); the lesson is already appended (INVARIANT-03 append-only) — this
    # only nudges. Length-normalized (Jaccard), validated to beat a naive count
    # strawman on adversarial near-misses (Phase-5 measuring stick, L-40).
    try:
        from . import analyze as _analyze

        dups = _analyze.near_duplicate_lessons(paths, text)
        if dups:
            result["related_lessons"] = dups
            result["advisory"] = (
                "This lesson strongly overlaps existing project lesson(s) — consider "
                "consolidating instead of appending (cz_consolidate_lessons / "
                "cz_obsolete_lesson): "
                + ", ".join(f"{d['id']} (Jaccard {d['jaccard']})" for d in dups)
            )
    except Exception:
        pass
    return result


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


@_locked
def obsolete_lesson(
    paths: RepoPaths,
    *,
    gameplan_id: str,
    number: int | str,
    reason: str | None = None,
    today: str | None = None,
) -> dict:
    """Mark lesson ``number`` obsolete — never delete it.

    The index header documents the convention ("mark with '(obsolete)' rather
    than deleting") and the handoff roll-up prunes marked lessons; this is the
    blessed write for that marker, so pruning no longer means a forbidden
    hand-edit of a tracked log. Idempotent: re-marking is a no-op.

    ``number`` may be a gameplan lesson number (``4``) or a project lesson id
    (``L-04``), curating ``docs/LESSONS.md`` with the same rules.
    """
    n = str(number).strip()
    if n.upper().startswith("L-"):
        n = n.upper()
        path = paths.doc("LESSONS")
        section, label = "Lessons", f"project lesson {n}"
    else:
        path = paths.gameplan_dir(gameplan_id) / "CHAT-HANDOFF-INDEX.md"
        section, label = "Accumulated Lessons", f"lesson #{n}"
    body = sections.get_section(writer.full_text(path), section)
    if body is None:
        return {"ok": False, "summary": f"no {section} section found"}
    prefix = f"**{n}.**"
    lines = body.splitlines()
    idx = next((i for i, ln in enumerate(lines) if ln.strip().startswith(prefix)), None)
    if idx is None:
        return {"ok": False, "summary": f"{label} not found"}
    if lesson_state.parse_state(lines[idx])[0] == lesson_state.OBSOLETE:
        return {"ok": True, "number": n, "already_obsolete": True,
                "files_changed": [], "summary": f"{label} already obsolete"}
    lines[idx] = lesson_state.mark(lines[idx], "obsolete", _today(today),
                                   (reason or "").strip())
    writer.upsert_section(path, section, "\n".join(lines))
    return {"ok": True, "number": n, "already_obsolete": False,
            "files_changed": [str(path)],
            "summary": f"{label} marked obsolete"}


@_locked
def promote_lesson(
    paths: RepoPaths,
    *,
    gameplan_id: str,
    number: int | str,
    text: str | None = None,
    category: str | None = None,
    today: str | None = None,
) -> dict:
    """Promote a gameplan lesson into the project-level ``docs/LESSONS.md``.

    The enduring half of D-009: lessons that should outlive their gameplan get
    an ``L-NN`` entry (with provenance) in a compact project doc that every
    future handoff carries; the source line is marked ``(promoted <date>: L-NN)``
    and stops rolling up individually, so nothing is carried twice. ``text``
    overrides the wording (promotion is a chance to distill); ``category``
    defaults to the source lesson's category block.
    """
    n = str(number).strip()
    idx_path = paths.gameplan_dir(gameplan_id) / "CHAT-HANDOFF-INDEX.md"
    body = sections.get_section(writer.full_text(idx_path), "Accumulated Lessons")
    if body is None:
        return {"ok": False, "summary": "no Accumulated Lessons section found"}
    prefix = f"**{n}.**"
    lines = body.splitlines()
    pos = next((i for i, ln in enumerate(lines) if ln.strip().startswith(prefix)), None)
    if pos is None:
        return {"ok": False, "summary": f"lesson #{n} not found"}
    line = lines[pos].strip()
    if not lesson_state.is_active(line):
        return {"ok": False, "summary": f"lesson #{n} is already obsolete/promoted"}
    if category is None:
        category = next(
            (lines[j].strip().removeprefix("### Category:").strip()
             for j in range(pos, -1, -1) if lines[j].strip().startswith("### Category:")),
            "Process",
        )
    lesson_text = (text or line[len(prefix):]).strip()

    ldoc = paths.doc("LESSONS")
    _ensure_doc(ldoc, "LESSONS")
    new_id = next_numbered_id(writer.full_text(ldoc), "L", sep="-", width=2)
    entry = f"**{new_id}.** {lesson_text} *(from {gameplan_id})*"
    lessons_body = sections.get_section(writer.full_text(ldoc), "Lessons") or ""
    writer.upsert_section(ldoc, "Lessons", _insert_under_category(lessons_body, category, entry))

    lines[pos] = lesson_state.mark(lines[pos], "promoted", _today(today), new_id)
    writer.upsert_section(idx_path, "Accumulated Lessons", "\n".join(lines))
    return {"ok": True, "id": new_id, "number": n, "category": category,
            "files_changed": [str(ldoc), str(idx_path)],
            "summary": f"lesson #{n} promoted to {new_id} ({category})"}


@_locked
def consolidate_lessons(
    paths: RepoPaths,
    *,
    gameplan_id: str,
    numbers: list[int | str],
    text: str,
    category: str = "Process",
    today: str | None = None,
) -> dict:
    """Synthesize several lessons into one — the anti-bloat write (D-009).

    Adds ``text`` as a new lesson, then marks every source lesson
    ``(obsolete <date>: consolidated into #N)``. Nothing is deleted: the
    handoff roll-up shrinks by ``len(numbers) - 1`` while the log keeps the
    full trail. All sources are validated before anything is written.
    """
    uniq = list(dict.fromkeys(str(n) for n in numbers))
    if len(uniq) < 2:
        return {"ok": False, "summary": "consolidation needs at least two distinct lessons"}
    path = paths.gameplan_dir(gameplan_id) / "CHAT-HANDOFF-INDEX.md"
    body = sections.get_section(writer.full_text(path), "Accumulated Lessons") or ""
    lines = body.splitlines()
    problems = []
    for n in uniq:
        line = next((ln for ln in lines if ln.strip().startswith(f"**{n}.**")), None)
        if line is None:
            problems.append(f"#{n} not found")
        elif not lesson_state.is_active(line):
            problems.append(f"#{n} already obsolete/promoted")
    if problems:
        return {"ok": False, "summary": "cannot consolidate: " + "; ".join(problems)}

    added = add_lesson(paths, gameplan_id=gameplan_id, text=text.strip(), category=category)
    new_n = added["number"]
    files = list(added["files_changed"])
    for n in uniq:
        obsolete_lesson(paths, gameplan_id=gameplan_id, number=n,
                        reason=f"consolidated into #{new_n}", today=today)
    return {
        "ok": True,
        "number": new_n,
        "consolidated": [int(n) for n in uniq],
        "files_changed": files,
        "summary": f"consolidated lessons {', '.join('#' + n for n in uniq)} into #{new_n}",
    }


# --- skills (skill-awareness D1; mirror the lesson lifecycle) ------------------


@_locked
def register_skill(
    paths: RepoPaths, *, name: str, description: str,
    source: str | None = None, category: str = "General",
) -> dict:
    """Register an Agent Skill into the project-level ``docs/SKILLS.md``.

    Mirrors promoted lessons: a line-entry (``**S-NN.** name -- description``)
    under a category in a compact, append-only doc that handoffs surface by
    relevance (Phase 2). ``source`` cites where the SKILL.md lives. Idempotent
    on ``name`` (an already-active skill of the same name is a no-op), so
    confirming the same cz_discover_skills proposal twice never duplicates.
    """
    sdoc = paths.doc("SKILLS")
    _ensure_doc(sdoc, "SKILLS")
    body = sections.get_section(writer.full_text(sdoc), "Skills") or ""
    want = name.strip().lower()
    for ln in body.splitlines():
        e = skill_state.parse_entry(ln)
        if e and e["state"] == skill_state.ACTIVE and e["name"].lower() == want:
            return {"ok": True, "id": e["id"], "already_registered": True,
                    "files_changed": [],
                    "summary": f"skill {name.strip()!r} already registered ({e['id']})"}
    new_id = next_numbered_id(writer.full_text(sdoc), "S", sep="-", width=2)
    entry = skill_state.format_entry(new_id, name, description, source)
    writer.upsert_section(sdoc, "Skills", _insert_under_category(body, category, entry))
    return {"ok": True, "id": new_id, "path": str(sdoc),
            "files_changed": [str(sdoc)],
            "summary": f"registered skill {new_id} ({name.strip()})"}


@_locked
def obsolete_skill(
    paths: RepoPaths, *, skill_id: str, reason: str | None = None,
    today: str | None = None,
) -> dict:
    """Mark skill ``skill_id`` (``S-NN``) obsolete in ``docs/SKILLS.md`` -- never delete.

    The blessed write for pruning a skill that is no longer available/relevant;
    the handoff roll-up stops carrying marked skills. Idempotent: re-marking is
    a recognized no-op.
    """
    sid = str(skill_id).strip().upper()
    sdoc = paths.doc("SKILLS")
    body = sections.get_section(writer.full_text(sdoc), "Skills")
    if body is None:
        return {"ok": False, "summary": "no Skills section found in SKILLS.md"}
    prefix = f"**{sid}.**"
    lines = body.splitlines()
    idx = next((i for i, ln in enumerate(lines) if ln.strip().startswith(prefix)), None)
    if idx is None:
        return {"ok": False, "summary": f"skill {sid} not found"}
    if skill_state.parse_state(lines[idx])[0] != skill_state.ACTIVE:
        return {"ok": True, "id": sid, "already_obsolete": True,
                "files_changed": [], "summary": f"skill {sid} already obsolete"}
    lines[idx] = skill_state.mark(lines[idx], "obsolete", _today(today), (reason or "").strip())
    writer.upsert_section(sdoc, "Skills", "\n".join(lines))
    return {"ok": True, "id": sid, "already_obsolete": False,
            "files_changed": [str(sdoc)], "summary": f"skill {sid} marked obsolete"}


@_locked
def add_output(
    paths: RepoPaths,
    *,
    gameplan_id: str,
    phase: str,
    key: str,
    value: str,
) -> dict:
    """Record a concrete produced value in the PHASE-STATUS Outputs Registry.

    The registry is the cross-phase memory for real captured values (ids,
    counts, paths) — the anti-pattern-#9 fix, finally a blessed write. One
    fenced block per phase; upserting an existing key rewrites its line, so
    corrections never stack.
    """
    path = paths.gameplan_dir(gameplan_id) / "PHASE-STATUS.md"
    if not path.exists():
        return {"ok": False, "summary": f"no PHASE-STATUS.md for {gameplan_id}"}
    body = sections.get_section(writer.full_text(path), "Outputs Registry")
    if body is None:
        return {"ok": False, "summary": "no Outputs Registry section"}
    key, value = key.strip(), str(value).strip()
    sub = f"### Phase {phase} Outputs"
    lines = [] if (not body.strip() or sections.is_placeholder(body)) else body.splitlines()
    h = next((i for i, ln in enumerate(lines) if ln.strip() == sub), None)
    action = "recorded"
    if h is None:
        if lines:
            lines.append("")
        lines += [sub, "", "```", f"{key}: {value}", "```"]
    else:
        nxt = next((i for i in range(h + 1, len(lines)) if lines[i].startswith("### ")),
                   len(lines))
        o = next((i for i in range(h + 1, nxt) if lines[i].strip().startswith("```")), None)
        if o is None:
            lines[h + 1:h + 1] = ["", "```", f"{key}: {value}", "```"]
        else:
            c = next((i for i in range(o + 1, nxt) if lines[i].strip().startswith("```")), None)
            if c is None:
                c = nxt
                lines.insert(c, "```")
            for i in range(o + 1, c):
                if lines[i].split(":", 1)[0].strip() == key:
                    lines[i] = f"{key}: {value}"
                    action = "updated"
                    break
            else:
                lines.insert(c, f"{key}: {value}")
    writer.upsert_section(path, "Outputs Registry", "\n".join(lines))
    return {"ok": True, "phase": str(phase), "key": key, "action": action,
            "files_changed": [str(path)],
            "summary": f"output {key} {action} for phase {phase}"}


@_locked
def add_phase_summary(
    paths: RepoPaths,
    *,
    gameplan_id: str,
    phase: str,
    text: str,
    today: str | None = None,
) -> dict:
    """Record a phase's completion summary in the handoff index.

    One block per phase under "Per-Phase Completion Summaries" — the
    at-a-glance record of what each phase actually shipped, previously stuck
    at its scaffold placeholder for want of a blessed write. Re-recording a
    phase's summary replaces its block.
    """
    path = paths.gameplan_dir(gameplan_id) / "CHAT-HANDOFF-INDEX.md"
    if not path.exists():
        return {"ok": False, "summary": f"no CHAT-HANDOFF-INDEX.md for {gameplan_id}"}
    body = sections.get_section(writer.full_text(path), "Per-Phase Completion Summaries")
    if body is None:
        return {"ok": False, "summary": "no Per-Phase Completion Summaries section"}
    from .rituals.status_bundle import phase_block

    block = f"### Phase {phase} — completed {_today(today)}\n\n{text.strip()}"
    replaced = False
    if not body.strip() or sections.is_placeholder(body):
        new_body = block
    else:
        blk = phase_block(body, phase)  # shared ### Phase N block finder
        if blk is None:
            new_body = body.rstrip() + "\n\n" + block
        else:
            lines, start, end = blk
            new_body = "\n".join(lines[:start] + block.splitlines() + lines[end:])
            replaced = True
    writer.upsert_section(path, "Per-Phase Completion Summaries", new_body)
    return {"ok": True, "phase": str(phase), "replaced": replaced,
            "files_changed": [str(path)],
            "summary": f"phase {phase} summary {'replaced' if replaced else 'recorded'}"}


_NEEDS_REVIEW = "_needs review_"
_APPLIED_PLACEHOLDER = "_(fill in concrete edits"


@_locked
def resolve_cascade(
    paths: RepoPaths,
    *,
    gameplan_id: str,
    report: str = "",
    verdicts: dict[str, str] | None = None,
    updates_applied: str = "",
    updates_deferred: str = "",
) -> dict:
    """Fill a cascade report's verdicts — the blessed write that unblocks
    ``cascade_hygiene``.

    The cascade engine writes each dependent as "checked: _needs review_" and
    leaves placeholder sections; deciding what was actually affected is the
    agent's job, and this records those decisions without a hand-edit.
    ``verdicts`` maps entity id -> what was done ("no change needed", "updated
    pin to ^2.0.0", …). ``report`` defaults to the most recent pending report.
    Partial resolution is fine: the report stays pending until no placeholder
    remains (same predicate cz_status and preflight use).
    """
    from .rituals.status_bundle import pending_cascades

    reports_dir = paths.gameplan_dir(gameplan_id) / "_cascade-reports"
    if report:
        name = report if report.endswith(".md") else f"{report}.md"
        path = reports_dir / name
        if not path.exists():
            return {"ok": False, "summary": f"cascade report {name} not found"}
    else:
        pending = pending_cascades(reports_dir)
        if not pending:
            return {"ok": False, "summary": "no pending cascade reports"}
        path = reports_dir / pending[-1]

    files_changed: list[str] = []
    resolved: list[str] = []
    already: list[str] = []
    seen_ids: set[str] = set()
    if verdicts:
        body = sections.get_section(writer.full_text(path), "Affected entities") or ""
        lines = body.splitlines()
        for i, ln in enumerate(lines):
            m = re.match(r"\s*-\s+\*\*(.+?)\*\*", ln)
            if not m:
                continue
            eid = m.group(1)
            seen_ids.add(eid)
            if eid not in verdicts:
                continue
            if _NEEDS_REVIEW in ln:
                lines[i] = ln.replace(_NEEDS_REVIEW, verdicts[eid].strip())
                resolved.append(eid)
            else:
                already.append(eid)
        if resolved:
            writer.upsert_section(path, "Affected entities", "\n".join(lines))
    unknown = sorted(set(verdicts or {}) - seen_ids)

    if updates_applied.strip():
        writer.upsert_section(path, "Updates applied", updates_applied.strip())
    if updates_deferred.strip():
        writer.upsert_section(path, "Updates deferred", updates_deferred.strip())
    if resolved or updates_applied.strip() or updates_deferred.strip():
        files_changed.append(str(path))

    text = writer.full_text(path)
    needs_verdict = _NEEDS_REVIEW in text
    needs_updates = _APPLIED_PLACEHOLDER in text
    still_pending = needs_verdict or needs_updates
    # Say exactly what is still missing — recording verdicts alone leaves the
    # "Updates applied" placeholder, and that requirement was non-obvious (F9).
    if not still_pending:
        state = "resolved"
    elif needs_verdict and needs_updates:
        state = ('still pending: some flagged dependents have no verdict yet, and the '
                 '"Updates applied" summary is empty — pass the remaining verdicts plus '
                 'updates_applied (a one-line summary of edits, or "none") or updates_deferred')
    elif needs_verdict:
        state = "still pending: some flagged dependents have no verdict yet — pass them in verdicts"
    else:
        state = ('still pending: every dependent has a verdict; now pass updates_applied '
                 '(a one-line summary of the edits, or "none") or updates_deferred to close it')
    return {
        "ok": True,
        "report": path.name,
        "resolved": resolved,
        "already_resolved": already,
        "unknown_ids": unknown,
        "pending": still_pending,
        "files_changed": files_changed,
        "summary": f"cascade report {path.name}: {len(resolved)} verdict(s) recorded — {state}",
    }


@_locked
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


@_locked
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
    # add a status row to the trackers — through the table-aware write, so the
    # row joins the table block instead of fracturing it (H-02 / gameplan D3)
    row = f"| {n} | {name} | ⬜ NOT STARTED | — | — | handoffs/PHASE-{n}-HANDOFF.md |"
    for fname, heading in (
        ("CHAT-HANDOFF-INDEX.md", "Phase Status Table"),
        ("PHASE-STATUS.md", "Phase Status"),
    ):
        path = paths.gameplan_dir(gameplan_id) / fname
        if path.exists() and writer.upsert_table_row(path, heading, row):
            files.append(str(path))
    files += _refresh_tracker_headers(paths, gameplan_id, _today(None))
    return {"ok": True, "phase": n, "files_changed": list(dict.fromkeys(files)),
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
    """Rewrite the status (and dates) of one phase row in a tracker table.

    The rewritten section is re-normalized into a contiguous table block
    (gameplan D3), so a tracker fractured by historical paragraph appends
    heals on any blessed touch — including a same-status transition.
    """
    text = writer.full_text(path)
    sec = sections.get_section(text, heading)
    if sec is None:
        return False
    out, found = [], False
    for line in sec.splitlines():
        s = line.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 6 and cells[0] == phase_n:
                found = True
                cells[2] = display
                if norm in ("in_progress", "complete") and cells[3] in ("—", ""):
                    cells[3] = today
                if norm == "complete":
                    cells[4] = today
                line = "| " + " | ".join(cells) + " |"
        out.append(line)
    if not found:
        return False
    new_sec = tables.normalize("\n".join(out))
    if new_sec == sec:
        return False
    writer.upsert_section(path, heading, new_sec)
    return True


def _refresh_tracker_headers(paths: RepoPaths, gameplan_id: str, today: str) -> list[str]:
    """Write the tracker header lines back from the live phase table (D7).

    ``> Status:`` and ``> Last updated:`` rotted on two closed gameplans
    because no blessed write owned them. Every phase mutation now refreshes
    them — the same self-healing the baseline test count got in
    discipline-seams D5, generalized.
    """
    from .rituals import _tables

    gdir = paths.gameplan_dir(gameplan_id)
    src = next((gdir / n for n in ("CHAT-HANDOFF-INDEX.md", "PHASE-STATUS.md")
                if (gdir / n).exists()), None)
    rows = _tables.parse_phase_table(writer.full_text(src)) if src else []
    total = len(rows)
    cur = next((r for r in rows if r.status == "in_progress"), None)
    nxt = next((r for r in rows if r.status in ("ready", "not_started")), None)
    if not total:
        tracker = "Planning"
    elif all(r.status == "complete" for r in rows):
        tracker = f"All {total} phases complete"
    elif cur:
        tracker = f"Phase {cur.number} of {total} in progress"
    elif nxt:
        tracker = f"Phase {nxt.number} ready"
    else:
        tracker = "Executing"
    started = ("in_progress", "complete", "blocked", "failed")
    if total and all(r.status == "complete" for r in rows):
        gp_status = "Complete"
    elif any(r.status in started for r in rows):
        gp_status = "Executing"
    else:
        gp_status = "Planning"
    files: list[str] = []
    for fname in ("CHAT-HANDOFF-INDEX.md", "PHASE-STATUS.md"):
        p = gdir / fname
        if not p.exists():
            continue
        changed_status = writer.set_blockquote_field(p, "Status", tracker)
        changed_date = writer.set_blockquote_field(p, "Last updated", today)
        if changed_status or changed_date:
            files.append(str(p))
    gp = gdir / "GAMEPLAN.md"
    if gp.exists() and writer.set_blockquote_field(gp, "Status", gp_status):
        files.append(str(gp))
    return files


@_locked
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
    files += _refresh_tracker_headers(paths, gameplan_id, today)
    result = {"ok": True, "phase": str(phase_n), "to_status": norm,
              "files_changed": list(dict.fromkeys(files)),
              "summary": f"Phase {phase_n} → {norm}"}
    # Advisory surfacing (D-015 / INVARIANT-05): completing a phase surfaces its
    # unresolved open items so they aren't silently left behind. It NEVER blocks
    # — the agent rules. Shared `advisories` shape reused by later gates.
    if norm == "complete":
        from .rituals.status_bundle import (
            _baseline_tests, unchecked_exit_criteria, unresolved_open_items,
        )

        gdir = paths.gameplan_dir(gameplan_id)
        advisories: list[dict] = []
        pending = unresolved_open_items(gdir, phase=str(phase_n))
        if pending:
            ids = [it["id"] for it in pending]
            advisories.append({
                "kind": "open_items",
                "ids": ids,
                "message": (
                    f"{len(ids)} unresolved open item(s) relevant to phase {phase_n} "
                    f"({', '.join(ids)}) — resolve with cz_resolve_open_item, or "
                    f"confirm they don't belong to this phase, before relying on it as done."
                ),
            })
        unchecked = unchecked_exit_criteria(gdir, str(phase_n))
        if unchecked:
            idx = gdir / "CHAT-HANDOFF-INDEX.md"
            baseline = _baseline_tests(idx.read_text(encoding="utf-8")) if idx.exists() else None

            def _annot(t: str) -> str:
                # Intelligence (D-015): link a test-ish criterion to the measured signal.
                # Word-boundary so "attest" / "establishes" don't trip the heuristic.
                if baseline and re.search(r"\b(tests?|suite|baseline)\b", t, re.I):
                    return f"{t} [measured: baseline {baseline} tests]"
                return t

            items = [_annot(c["text"]) for c in unchecked]
            advisories.append({
                "kind": "exit_criteria",
                "items": items,
                "message": (
                    f"{len(items)} unchecked exit criteria for phase {phase_n} — verify each "
                    f"and cz_check_exit_criterion it, or confirm done: " + "; ".join(items)
                ),
            })
        if advisories:
            result["advisories"] = advisories
    if norm in ("complete", "failed"):
        # Telemetry (Phase 0): log the phase outcome + its exit-criteria
        # checked/total so 'which surfaced lessons preceded a pass/fail' becomes
        # computable. We already hold the H-05 write lock (@_locked); the append
        # is append-only (INVARIANT-03) and never auto-acted-on (INVARIANT-05).
        from . import telemetry
        from .rituals.status_bundle import exit_criteria
        crits = exit_criteria(paths.gameplan_dir(gameplan_id), str(phase_n))
        telemetry.record_outcome(
            paths.telemetry_file, gameplan=gameplan_id, phase=str(phase_n),
            status=norm, criteria_total=len(crits),
            criteria_checked=sum(1 for c in crits if c["checked"]), today=today)
        result["telemetry"] = "outcome"
    return result


@_locked
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
    amendments_ritual: bool = False,
    today: str | None = None,
) -> dict:
    today = _today(today)
    # Callers sometimes pass these as lists; render a readable inline list rather
    # than a Python literal like ['Phase Breakdown', 'Subsystems Touched'] (F12).
    if isinstance(affected_sections, (list, tuple)):
        affected_sections = ", ".join(str(s) for s in affected_sections)
    if isinstance(affected_phases, (list, tuple)):
        affected_phases = ", ".join(str(s) for s in affected_phases)
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
        f"- **Why**: {why}"
    )
    if amendments_ritual:
        # The cascade line only when the rituals.amendments discipline applies
        # (INVARIANT-13 adopters) — and as an honest pending pointer: cascade
        # reports are per-entity files, so no `<date>-A-NNN.md` ever exists.
        # A-001 in engine-structural-robustness dangled on exactly that name.
        entry += (
            f"\n- **Cascade**: if this amendment changed a tracked entity, run "
            f"`cz_cascade` for it (reports land in `_cascade-reports/`)"
        )
    writer.append_to_section(gp, "Amendments", entry)
    return {"ok": True, "id": new_id, "files_changed": [str(gp)],
            "summary": f"added amendment {new_id}"}


# --- open items (the clarify gate, D-015) -------------------------------------
#
# Blockers and cross-phase questions, auto-numbered O-NN so cz_status can report
# them and cz_transition_phase can surface the unresolved ones (advisory, never
# blocking — INVARIANT-05). They live as ``**O-NN.**`` lines in the GAMEPLAN
# "Open Items" section: a next_numbered_id-compatible anchor (same as lessons),
# kept human-readable, no new schema (gameplan D1). Resolved in place with a
# ``_(resolved <date>: …)_`` marker — never deleted (append-only memory).


@_locked
def add_open_item(
    paths: RepoPaths,
    *,
    gameplan_id: str,
    text: str,
    phase: str | None = None,
) -> dict:
    """Append an auto-numbered open item (``O-NN``) to a gameplan's Open Items.

    An optional ``phase`` tags the item to a phase so transition surfacing can
    judge relevance. The first item replaces the section's scaffold placeholder.
    """
    if not gameplan_id:
        return {"ok": False, "error": "open items require a gameplan_id"}
    path = paths.gameplan_dir(gameplan_id) / "GAMEPLAN.md"
    if not path.exists():
        return {"ok": False, "summary": f"no GAMEPLAN.md for {gameplan_id}"}
    doc = writer.full_text(path)
    new_id = next_numbered_id(doc, "O", sep="-", width=2)
    p = "" if phase is None or str(phase).strip() == "" else str(phase).strip()
    tag = f" _(phase {p})_" if p else ""
    entry = f"**{new_id}.**{tag} {text.strip()}"
    writer.append_to_section(path, "Open Items", entry)
    return {"ok": True, "id": new_id, "path": str(path),
            "files_changed": [str(path)], "summary": f"added open item {new_id}"}


@_locked
def resolve_open_item(
    paths: RepoPaths,
    *,
    gameplan_id: str,
    id: str,
    resolution: str,
    today: str | None = None,
) -> dict:
    """Mark an open item resolved in place — never delete it (append-only).

    Appends a ``_(resolved <date>: <resolution>)_`` marker to the ``O-NN`` line.
    Idempotent: re-resolving an already-resolved item is a no-op.
    """
    if not gameplan_id:
        return {"ok": False, "error": "open items require a gameplan_id"}
    oid = id.strip()
    path = paths.gameplan_dir(gameplan_id) / "GAMEPLAN.md"
    body = sections.get_section(writer.full_text(path), "Open Items")
    if body is None:
        return {"ok": False, "summary": "no Open Items section"}
    from .rituals.status_bundle import _RESOLVED_RE

    lines = body.splitlines()
    prefix = f"**{oid}.**"
    idx = next((i for i, ln in enumerate(lines) if ln.strip().startswith(prefix)), None)
    if idx is None:
        return {"ok": False, "summary": f"open item {oid} not found"}
    if _RESOLVED_RE.search(lines[idx]):  # the marker's ISO-date shape, not bare prose
        return {"ok": True, "id": oid, "already_resolved": True,
                "files_changed": [], "summary": f"open item {oid} already resolved"}
    lines[idx] = lines[idx].rstrip() + f" _(resolved {_today(today)}: {resolution.strip()})_"
    writer.upsert_section(path, "Open Items", "\n".join(lines))
    return {"ok": True, "id": oid, "already_resolved": False,
            "files_changed": [str(path)], "summary": f"open item {oid} resolved"}


# --- exit criteria (the exit-criteria gate, D-015) ----------------------------
#
# Phase exit criteria live as ``- [ ]`` checkboxes inside each ``### Phase N``
# block of GAMEPLAN.md "Phase Breakdown" (gameplan D1: reuse what's there). Two
# blessed writes — set (author/replace the list; no hand-edit) and check (toggle
# one) — make them machine-trackable; cz_transition_phase surfaces the unchecked
# ones on completion (advisory, never blocking — INVARIANT-05). The shared
# checkbox regex `_EC_CHECK_RE` (group 1 = state, group 2 = text) lives in
# status_bundle and is imported where used.


@_locked
def set_exit_criteria(
    paths: RepoPaths, *, gameplan_id: str, phase: str, criteria: list[str],
) -> dict:
    """Author/replace a phase's exit criteria as ``- [ ]`` checkboxes.

    Replaces the phase block's ``**Exit criteria**:`` list (placeholder or prior
    items) with ``criteria``, preserving the checked state of any item whose text
    is unchanged.
    """
    if not gameplan_id:
        return {"ok": False, "error": "exit criteria require a gameplan_id"}
    from .rituals.status_bundle import _EC_CHECK_RE, phase_block

    path = paths.gameplan_dir(gameplan_id) / "GAMEPLAN.md"
    body = sections.get_section(writer.full_text(path), "Phase Breakdown")
    if body is None:
        return {"ok": False, "summary": "no Phase Breakdown section"}
    blk = phase_block(body, phase)
    if blk is None:
        return {"ok": False, "summary": f"phase {phase} not found in Phase Breakdown"}
    lines, start, end = blk
    block = lines[start:end]
    prior = {}
    for ln in block:
        m = _EC_CHECK_RE.match(ln)
        if m:
            prior[m.group(2).strip()] = m.group(1).lower() == "x"
    items = [c.strip() for c in criteria if c.strip()]
    new_items = [f"- [{'x' if prior.get(c, False) else ' '}] {c}" for c in items]
    ec = next((i for i, ln in enumerate(block)
               if ln.strip().startswith("**Exit criteria**")), None)
    if ec is None:
        while block and not block[-1].strip():
            block.pop()
        block += ["", "**Exit criteria**:"] + new_items + [""]
    else:
        # Replace only the contiguous checkbox run after the header; preserve any
        # content that follows the criteria within the phase block (data-loss fix:
        # a block may hold notes/sub-lists after the list, not just the list).
        j = ec + 1
        while j < len(block) and not block[j].strip():
            j += 1
        k = j
        while k < len(block) and _EC_CHECK_RE.match(block[k]):
            k += 1
        tail = block[k:]
        block = block[:ec + 1] + new_items + (tail if tail else [""])
    new_lines = lines[:start] + block + lines[end:]
    changed = writer.upsert_section(path, "Phase Breakdown", "\n".join(new_lines))
    return {"ok": True, "phase": str(phase), "count": len(new_items),
            "files_changed": [str(path)] if changed else [],
            "summary": f"set {len(new_items)} exit criteria for phase {phase}"}


@_locked
def check_exit_criterion(
    paths: RepoPaths, *, gameplan_id: str, phase: str, criterion: str,
    checked: bool = True,
) -> dict:
    """Check/uncheck one exit criterion (matched by substring) under a phase.

    Idempotent: toggling to the state it already holds is a no-op (files_changed=[]).
    """
    if not gameplan_id:
        return {"ok": False, "error": "exit criteria require a gameplan_id"}
    from .rituals.status_bundle import _EC_CHECK_RE, phase_block

    path = paths.gameplan_dir(gameplan_id) / "GAMEPLAN.md"
    body = sections.get_section(writer.full_text(path), "Phase Breakdown")
    if body is None:
        return {"ok": False, "summary": "no Phase Breakdown section"}
    blk = phase_block(body, phase)
    if blk is None:
        return {"ok": False, "summary": f"phase {phase} not found in Phase Breakdown"}
    lines, start, end = blk
    want = "x" if checked else " "
    target = criterion.strip().lower()
    matches = []
    for i in range(start, end):
        m = _EC_CHECK_RE.match(lines[i])  # group 1 = state, group 2 = text
        if m and target in m.group(2).strip().lower():
            matches.append((i, m))
    if not matches:
        return {"ok": False, "summary": f"no exit criterion matching {criterion!r} in phase {phase}"}
    # Prefer an exact (case-insensitive) match; a substring must be unique, or we'd
    # silently toggle the wrong box when one criterion's text contains another's.
    exact = [(i, m) for i, m in matches if m.group(2).strip().lower() == target]
    if exact:
        i, m = exact[0]
    elif len(matches) == 1:
        i, m = matches[0]
    else:
        hits = "; ".join(m.group(2).strip() for _, m in matches)
        return {"ok": False, "summary": f"{criterion!r} matches {len(matches)} criteria in "
                f"phase {phase} ({hits}) — pass the exact criterion text"}
    text = m.group(2).strip()
    already = (m.group(1).lower() == "x") if checked else (m.group(1) == " ")
    if already:
        return {"ok": True, "phase": str(phase), "criterion": text,
                "checked": checked, "changed": False, "files_changed": [],
                "summary": f"exit criterion already {'checked' if checked else 'unchecked'}"}
    lines[i] = re.sub(r"\[[ xX]\]", f"[{want}]", lines[i], count=1)  # flip the box only
    writer.upsert_section(path, "Phase Breakdown", "\n".join(lines))
    return {"ok": True, "phase": str(phase), "criterion": text,
            "checked": checked, "changed": True, "files_changed": [str(path)],
            "summary": f"exit criterion {'checked' if checked else 'unchecked'}"}


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


@_locked
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


@_locked
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
