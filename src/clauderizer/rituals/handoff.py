"""Assemble a cumulative, self-contained phase handoff.

The original procedure's #2 anti-pattern is "incomplete lesson propagation":
a phase repeats a mistake an earlier phase already solved because the lesson
wasn't carried forward. The fix was the "self-contained handoff" rule — every
handoff carries ALL still-relevant lessons. Here that's an operation, not a
discipline: we read the single canonical lessons list and roll it up, pruning
only items explicitly marked obsolete/struck-through.

Relevance surfacing (idea #2) layers on top WITHOUT weakening that rule: the full
list still rides along, and a small ranked pointer block above it focuses the
agent on the lessons most relevant to the current phase (keyword + entity-id
overlap, no ML — D-018; a pointer into canonical memory, never an authority —
D-013).
"""

from __future__ import annotations

import re
from pathlib import Path

from .. import analyze
from ..config import Config
from ..graph.abstract_index import parse_lesson_line
from ..markdown import lesson_state, sections, skill_state
from ..paths import RepoPaths

_LESSON_LINE = re.compile(r"^\s*\*\*\d+\.\*\*")
_PROJECT_LESSON_LINE = re.compile(r"^\s*\*\*L-\d+\.\*\*")


def _gameplan_text(paths: RepoPaths, gid: str, name: str) -> str:
    p = paths.gameplan_dir(gid) / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def collect_lessons(index_text: str) -> tuple[str, int]:
    """Return ``(rolled_up_markdown, count)`` of still-relevant lessons.

    Preserves the category sub-headings; drops any lesson line marked
    ``(obsolete …)`` (written by ``cz_obsolete_lesson``), ``(promoted …)``
    (written by ``cz_promote_lesson`` — the project section carries it from
    then on), or wrapped in ``~~strikethrough~~``.
    """
    return _filter_lessons(sections.get_section(index_text, "Accumulated Lessons"),
                           _LESSON_LINE)


def collect_project_lessons(lessons_text: str) -> tuple[str, int]:
    """Roll up the active ``L-NN`` entries of ``docs/LESSONS.md``."""
    return _filter_lessons(sections.get_section(lessons_text, "Lessons"),
                           _PROJECT_LESSON_LINE)


def _filter_lessons(sec: str | None, line_re: re.Pattern) -> tuple[str, int]:
    if not sec or not sec.strip():
        return "_(no lessons recorded yet)_", 0
    out_lines: list[str] = []
    count = 0
    for line in sec.splitlines():
        stripped = line.strip()
        if line_re.match(stripped):
            # State is the trailing structured marker, never a substring —
            # a lesson whose text mentions "(obsolete" still rolls up (D8).
            if not lesson_state.is_active(stripped):
                continue
            count += 1
            out_lines.append(line)
        else:
            out_lines.append(line)
    # collapse blank runs
    rolled = re.sub(r"\n{3,}", "\n\n", "\n".join(out_lines)).strip()
    return rolled, count


def _phase_section(gameplan_text: str, phase_n: str) -> str | None:
    return sections.get_section(gameplan_text, f"Phase {phase_n}") or None


def _phase_query(gameplan_text: str, phase_n: str) -> str:
    """Text describing this phase, used to rank lesson relevance (idea #2).

    Prefers a top-level ``Phase N`` section; falls back to the ``### Phase N``
    block inside ``Phase Breakdown`` (name + goal + tasks + exit criteria) so the
    query is rich even when the phase lives only in the breakdown table.
    """
    direct = _phase_section(gameplan_text, phase_n)
    if direct and direct.strip():
        return direct
    from . import status_bundle  # lazy: status_bundle imports handoff (cycle guard)
    breakdown = sections.get_section(gameplan_text, "Phase Breakdown") or ""
    blk = status_bundle.phase_block(breakdown, phase_n)
    if blk is None:
        return ""
    lines, start, end = blk
    return "\n".join(lines[start:end])


# --- relevance surfacing (idea #2) -------------------------------------------
# Point at the lessons most relevant to the current phase WITHOUT reordering or
# dropping the canonical roll-up. Reuses the shared keyword + entity-id ranker
# (analyze.rank_relevant) — no ML (D-018) — and renders pointers into canonical
# memory, never an authority over it (D-013). The full list rides along unchanged
# (D-009 pressure-not-caps; the incomplete-propagation anti-pattern above).
_LESSON_NUM_RE = re.compile(r"^\s*\*\*(\d+)\.\*\*\s*(.*)$")
RELEVANCE_K = 5


def _active_lesson_entries(index_text: str) -> list[dict]:
    """Active lesson lines parsed as rank_relevant entries (``{id, title, body}``)."""
    sec = sections.get_section(index_text, "Accumulated Lessons") or ""
    entries: list[dict] = []
    for line in sec.splitlines():
        s = line.strip()
        if not _LESSON_LINE.match(s) or not lesson_state.is_active(s):
            continue
        m = _LESSON_NUM_RE.match(s)
        if m:
            entries.append({"id": m.group(1), "title": m.group(2).strip(), "body": ""})
    return entries


def relevant_lesson_pointer(index_text: str, query: str,
                            k: int = RELEVANCE_K) -> str | None:
    """Ranked pointers to the lessons most relevant to the current phase.

    Returns ``None`` when there is nothing to focus — no query, or the active
    lesson count is already ``<= k`` (the whole list is short enough to read).
    Pure surfacing: it never reorders or removes the canonical lessons.
    """
    if not query or not query.strip():
        return None
    entries = _active_lesson_entries(index_text)
    if len(entries) <= k:
        return None
    ranked = analyze.rank_relevant(query, entries, k=k)
    if not ranked:
        return None
    out = []
    for r in ranked:
        title = r["title"].rstrip()
        if len(title) > 100:
            title = title[:99].rstrip() + "…"
        out.append(f"- **#{r['id']}** — {title}")
    return "\n".join(out)


# --- focused project-lesson injection (gameplan empirical-memory-gains, Phase 1)
# The cumulative handoff carried ALL project lessons in full (measured: 87% of a
# 3137-tok handoff = the 21 L-NN). A focused-vs-full agent-eval showed focused
# top-k == full accuracy (5/6 each) at ~73% fewer tokens, with ranker recall@5 of
# 100% (the answer lesson is always in the top-k). So under memory pressure the
# handoff carries the top-k lessons most relevant to the phase + a pointer to the
# canonical full set — focus, never a drop from canonical memory (reconciles
# D-022: this is relevance-ranking + pointer-to-canonical, not tail truncation).
def _project_lesson_entries(lessons_text: str) -> list[dict]:
    """Active ``L-NN`` lessons parsed for ranking, keeping the original markdown
    line so the focused set re-renders byte-faithfully.

    The lesson-line grammar is single-sourced through
    ``abstract_index.parse_lesson_line`` (#5) — the handoff ranker and the
    abstract index can no longer disagree on what an ``L-NN`` line is."""
    sec = sections.get_section(lessons_text, "Lessons") or ""
    entries: list[dict] = []
    for line in sec.splitlines():
        s = line.strip()
        if not lesson_state.is_active(s):
            continue
        parsed = parse_lesson_line(s)
        if parsed:
            eid, title, body = parsed
            entries.append({"id": eid, "title": title, "body": body, "line": line})
    return entries


def focused_project_lessons(lessons_text: str, query: str,
                            k: int = RELEVANCE_K) -> tuple[str, int, int] | None:
    """Top-``k`` project lessons most relevant to the phase, ranked, full text.

    Returns ``(markdown, shown, total)`` when focusing applies (a real query AND
    more than ``k`` active project lessons), else ``None`` so the caller renders
    the full list unchanged (propagation-safe for small sets). The canonical set
    always stays in ``docs/LESSONS.md``; this only changes what rides in the
    handoff.
    """
    if not query or not query.strip():
        return None
    entries = _project_lesson_entries(lessons_text)
    total = len(entries)
    if total <= k:
        return None
    ranked = analyze.rank_relevant(query, entries, k=k)
    by_id = {e["id"]: e["line"] for e in entries}
    shown = [by_id[r["id"]] for r in ranked if r["id"] in by_id]
    if not shown:
        return None
    return "\n".join(shown), len(shown), total


# --- focused governing-invariant surfacing (Phase 6: trim-consistent steering) --
# A persistent always-injected "steering"/"constitution" doc (Spec-Kit) was DROPPED
# as redundant (CLAUDE.md is already auto-loaded; INVARIANTS.md + the analyze gate
# exist) and anti-trim (D-027). But a real gap remained: the must-hold INVARIANTS
# were never surfaced during phase work — the handoff carried lessons, not rules,
# and analyze only surfaces them when ADDING a decision. This is the trim-consistent
# fix: the top-k invariants whose text overlaps the phase, focused (never an
# always-injected dump), reusing the same lexical ranker Phase 1 validated.


def relevant_invariant_pointer(paths: RepoPaths, query: str,
                               k: int = RELEVANCE_K) -> tuple[str, int, int] | None:
    """The phase-relevant governing INVARIANTS, as focused pointers.

    Returns ``(markdown, shown, total)`` or ``None`` when there is no query, no
    invariants doc, or no invariant lexically relevant to this phase (an honest
    negative — irrelevant rules are not injected, per D-027 trim-first).
    """
    if not query or not query.strip():
        return None
    doc = paths.doc("INVARIANTS")
    if not doc.exists():
        return None
    entries = analyze.parse_entries(doc.read_text(encoding="utf-8"), "Invariants")
    if not entries:
        return None
    ranked = analyze.rank_relevant(query, entries, k=k)
    if not ranked:
        return None
    md = "\n".join(f"- **{r['id']}** — {r['title']}" for r in ranked)
    return md, len(ranked), len(entries)


# --- focused skill surfacing (skill-awareness Phase 2) -------------------------
# Skills are a MENU, not accumulated wisdom: unlike lessons (which all ride along,
# D-009 propagation), a project may register dozens of skills and dumping them all
# is the L-35 availability-not-use noise. So the handoff carries ONLY the skills
# whose trigger overlaps this phase (top-k via the same lexical ranker, no ML —
# D-018), or nothing when none are relevant. The full inventory stays canonical in
# docs/SKILLS.md (a pointer, never an authority — D-013).


def _active_skill_entries(skills_text: str) -> list[dict]:
    """Active SKILLS.md entries parsed for ranking: {id, title=name, body=description}."""
    sec = sections.get_section(skills_text, "Skills") or ""
    entries: list[dict] = []
    for line in sec.splitlines():
        e = skill_state.parse_entry(line)
        if e and e["state"] == skill_state.ACTIVE:
            entries.append({"id": e["id"], "title": e["name"], "body": e["description"]})
    return entries


def relevant_skill_pointer(paths: RepoPaths, query: str,
                           k: int = RELEVANCE_K) -> str | None:
    """The Agent Skills whose trigger overlaps this phase, as a focused menu.

    Renders ``- **name** — description`` for the top-``k`` active skills the
    lexical ranker scores against the phase text, or ``None`` when there is no
    query, no SKILLS.md, no registered skill, or none overlaps (an honest
    negative — irrelevant skills are not injected). Focused-only: the full
    inventory stays canonical in docs/SKILLS.md.
    """
    if not query or not query.strip():
        return None
    sdoc = paths.doc("SKILLS")
    if not sdoc.exists():
        return None
    entries = _active_skill_entries(sdoc.read_text(encoding="utf-8"))
    if not entries:
        return None
    ranked = analyze.rank_relevant(query, entries, k=k)
    if not ranked:
        return None
    by_id = {e["id"]: e for e in entries}
    out: list[str] = []
    for r in ranked:
        e = by_id.get(r["id"])
        if not e:
            continue
        desc = e["body"].rstrip()
        if len(desc) > 120:
            desc = desc[:119].rstrip() + "…"
        out.append(f"- **{e['title']}** — {desc}" if desc else f"- **{e['title']}**")
    return "\n".join(out) if out else None


def surfaced_ids(paths: RepoPaths, gid: str, phase_n: str) -> dict:
    """Which project lessons / gameplan lessons / invariants the handoff for this
    phase SURFACES as most relevant — the same deterministic keyword + entity-id
    ranker the handoff renders (no ML, D-018), returned as bare ids so
    cz_write_handoff can log them to telemetry. Read-only; a pointer into
    canonical memory, never an authority over it (D-013).
    """
    index_text = _gameplan_text(paths, gid, "CHAT-HANDOFF-INDEX.md")
    gameplan_text = _gameplan_text(paths, gid, "GAMEPLAN.md")
    query = _phase_query(gameplan_text, phase_n)
    if not query or not query.strip():
        return {"lessons": [], "gameplan_lessons": [], "invariants": []}
    gameplan_lessons = [r["id"] for r in analyze.rank_relevant(
        query, _active_lesson_entries(index_text), k=RELEVANCE_K)]
    project_lessons: list[str] = []
    lessons_doc = paths.doc("LESSONS")
    if lessons_doc.exists():
        project_lessons = [r["id"] for r in analyze.rank_relevant(
            query, _project_lesson_entries(lessons_doc.read_text(encoding="utf-8")),
            k=RELEVANCE_K)]
    invariants: list[str] = []
    inv_doc = paths.doc("INVARIANTS")
    if inv_doc.exists():
        invariants = [r["id"] for r in analyze.rank_relevant(
            query, analyze.parse_entries(inv_doc.read_text(encoding="utf-8"), "Invariants"),
            k=RELEVANCE_K)]
    return {"lessons": project_lessons, "gameplan_lessons": gameplan_lessons,
            "invariants": invariants}


# The engine owns only this marker-delimited region of a handoff file (D-008).
# Everything outside it — agent enrichment — is preserved byte-for-byte when
# the handoff is regenerated.
MARKER = "clauderizer:handoff"

# Pre-marker handoffs written by this generator carry this line; such files are
# engine skeletons and are safe to replace wholesale on migration.
_GENERATED_FINGERPRINT = "> Generated by: cz_write_handoff"

_AGENT_SCAFFOLD = """\

## Phase Notes (agent-owned)

_(Enrich here: what exists / what does not yet, key constraints, captured
source-of-truth values for this phase. Everything outside the marker block
above survives `cz_write_handoff` regeneration.)_
"""


def _merge(existing: str, core: str) -> tuple[str, str]:
    """Combine the engine ``core`` with what's already on disk.

    Returns ``(merged_text, mode)`` where mode describes what happened:
    ``created`` (fresh file, scaffold added), ``merged`` (marker block replaced,
    rest byte-preserved), ``migrated`` (legacy generated skeleton replaced), or
    ``preserved`` (unrecognized file kept verbatim below the block).
    """
    if existing and sections.has_marker_block(existing, MARKER):
        return sections.upsert_marker_block(existing, MARKER, core), "merged"
    block = sections.upsert_marker_block("", MARKER, core)
    if not existing:
        return block + _AGENT_SCAFFOLD, "created"
    if _GENERATED_FINGERPRINT in existing:
        return block + _AGENT_SCAFFOLD, "migrated"
    return block + "\n" + existing, "preserved"


def _consumes_section(paths: RepoPaths, gid: str) -> str:
    """Render this gameplan's cross-gameplan consumes (the gameplan.<gid> node's
    depends_on) as a markdown list with each consumed entity's current status, or
    "" when the gameplan declared none (cz_consumes)."""
    from ..graph import index

    g = index.load_or_rebuild(paths.docs, paths.index_file)
    node = g.get(f"gameplan.{gid}")
    if node is None or not node.depends_on:
        return ""
    lines = []
    for pin in node.depends_on:
        dep = g.get(str(pin.target))
        if dep is None:
            note = " — _(not found in graph)_"
        else:
            note = f" (status: {dep.status})" if dep.status else ""
        lines.append(f"- **{pin.target}**{note}")
    return "\n".join(lines)


def assemble(paths: RepoPaths, config: Config, gid: str, phase_n: str, *, write: bool = True) -> dict:
    index_text = _gameplan_text(paths, gid, "CHAT-HANDOFF-INDEX.md")
    gameplan_text = _gameplan_text(paths, gid, "GAMEPLAN.md")
    # Display-only lexicon (D3): the kind's heading word for "phase" (e.g. Stage
    # for a campaign). Identity for driven, so every driven handoff stays
    # byte-identical. These headings live INSIDE the regenerated marker block, so
    # relabeling them never affects parsing or the agent-owned notes outside it.
    from . import status_bundle as _sb
    from .. import kinds

    P = kinds.resolve(_sb.gameplan_kind(paths.gameplan_dir(gid)),
                      paths.kinds_dir).label("phase").capitalize()
    lessons_md, lessons_count = collect_lessons(index_text)
    phase_body = _phase_section(gameplan_text, phase_n)
    # Idea #2: surface the lessons most relevant to THIS phase as pointers above
    # the (unchanged) cumulative list — focus without dropping anything.
    pointer = relevant_lesson_pointer(index_text, _phase_query(gameplan_text, phase_n))
    # Phase 6 (trim-consistent steering): surface the phase-relevant governing
    # invariants — the must-hold rules the handoff never carried before.
    invariants_focus = relevant_invariant_pointer(paths, _phase_query(gameplan_text, phase_n))
    # Phase 2 (skill-awareness): the registered skills whose trigger overlaps this
    # phase — a focused menu, or nothing when none are relevant (L-35).
    skills_focus = relevant_skill_pointer(paths, _phase_query(gameplan_text, phase_n))

    # Distilled project lessons (docs/LESSONS.md) ride along in every handoff,
    # across gameplans — that's what promotion buys (D-009).
    project_lessons_md, project_count = "", 0
    project_focus = None
    lessons_doc = paths.doc("LESSONS")
    if lessons_doc.exists():
        lessons_text = lessons_doc.read_text(encoding="utf-8")
        project_lessons_md, project_count = collect_project_lessons(lessons_text)
        project_focus = focused_project_lessons(
            lessons_text, _phase_query(gameplan_text, phase_n))

    parts = [
        f"# {P} {phase_n} Handoff",
        "",
        "> For: next Clauderizer session",
        f"> Gameplan: {gid}",
        f"> Generated by: cz_write_handoff",
        "",
        f"## What This {P} Does",
        "",
        (phase_body.strip() if phase_body else "_(see GAMEPLAN.md for the phase definition)_"),
        "",
        "## Pre-Flight Verification (MANDATORY)",
        "",
        "Run `cz_preflight` before touching code. All enabled checks must pass.",
        "",
        "## Key Files You Must Read",
        "",
        f"- `docs/gameplans/{gid}/GAMEPLAN.md`",
        f"- `docs/gameplans/{gid}/PHASE-STATUS.md`",
        "- `CLAUDE.md`",
        "",
    ]
    consumes_md = _consumes_section(paths, gid)
    if consumes_md:
        parts += [
            "## Consumes (Cross-Gameplan)",
            "",
            "_(Entities produced on OTHER axes that this gameplan depends on, "
            "declared via cz_consumes. Memory scoping: project invariants/ADRs are "
            "shared by every gameplan; this gameplan's own decisions/lessons are "
            "local; these are explicit cross-gameplan reads — if one changes, its "
            "cascade fans a pending cross-ref into this gameplan.)_",
            "",
            consumes_md,
            "",
        ]
    if invariants_focus:
        inv_md, inv_shown, inv_total = invariants_focus
        parts += [
            f"## Governing Invariants for This {P}",
            "",
            f"_({inv_shown} of {inv_total} surfaced — the must-hold rules whose text "
            "overlaps this phase (keyword + entity-id, no ML). Honor these; the full "
            "set is in `docs/INVARIANTS.md`.)_",
            "",
            inv_md,
            "",
        ]
    if pointer:
        parts += [
            f"## Most Relevant Lessons for This {P}",
            "",
            "_(Ranked pointers into the full list below — keyword + entity-id "
            "overlap with this phase, no ML, no drops. The cumulative list is "
            "unchanged.)_",
            "",
            pointer,
            "",
        ]
    if skills_focus:
        parts += [
            f"## Skills for This {P}",
            "",
            "_(Agent Skills registered for this project whose trigger overlaps "
            "this phase — invoke the relevant ones. The full inventory is in "
            "`docs/SKILLS.md`; discover more with cz_discover_skills, register "
            "with cz_register_skill.)_",
            "",
            skills_focus,
            "",
        ]
    parts += [
        f"## Accumulated Lessons (Cumulative — All Prior {P}s)",
        "",
        lessons_md,
        "",
    ]
    if project_count and project_focus:
        focused_md, shown, total = project_focus
        parts += [
            f"## Project Lessons (most relevant to this {P.lower()})",
            "",
            f"_({shown} of {total} shown — ranked by keyword + entity-id overlap "
            "with this phase, no ML. The full set is canonical in "
            "`docs/LESSONS.md`; the handoff focuses under memory pressure without "
            "dropping anything from canonical memory.)_",
            "",
            focused_md,
            "",
        ]
    elif project_count:
        parts += [
            "## Project Lessons (distilled — survive across gameplans)",
            "",
            project_lessons_md,
            "",
        ]
    parts += [
        "## Ending Protocol",
        "",
        "1. `cz_transition_phase` the finished phase to complete.",
        "2. `cz_add_output` each concrete produced value; `cz_add_phase_summary` "
        "the recap; `cz_add_correction` / `cz_add_lesson` as earned.",
        "3. `cz_transition_status` on touched entities (fires cascade); "
        "`cz_resolve_cascade` the verdicts.",
        "4. `cz_write_handoff` for the next phase.",
        "5. Run exit verification; report the test count.",
        "",
    ]
    core = "\n".join(parts)
    out_path = paths.gameplan_dir(gid) / "handoffs" / f"PHASE-{phase_n}-HANDOFF.md"
    existing = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    # The merged view is computed even for write=False so a context fetch
    # (cz_next_phase_context) includes any agent enrichment already on disk.
    text, mode = _merge(existing, core)
    if write:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        summary = (f"wrote handoff for phase {phase_n} ({mode}): "
                   f"{lessons_count} lessons rolled up")
    else:
        summary = f"assembled phase {phase_n} context: {lessons_count} lessons rolled up (not written)"
    return {
        "ok": True,
        "path": str(out_path) if write else None,
        "written": write,
        "mode": mode,
        "handoff_md": text,
        "lessons_rolled_up": lessons_count,
        "project_lessons": project_count,
        "summary": summary,
    }
