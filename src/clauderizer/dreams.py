"""The dream journal — append-only, local-only experiential telemetry (D-058).

Mechanical telemetry (``telemetry.py``) records what the engine can observe:
which lessons a handoff surfaced, whether a phase passed. Dream notes record
what only the RESPONDING AGENT can observe — friction, gaps, surprises,
corrections, ritual drift — as 2–4 sentence notes appended after each
substantive exchange. The offline dreamer (Phase 2+: ``cz_dream``) later mines
the accumulated notes into advisory proposals; full transcripts are never
retained (token cost + PII risk — the whole point of the substrate).

Constitution (mirrors telemetry.py):
  * append-only (INVARIANT-03) — every note is a new line in
    ``.clauderizer/dreams.jsonl``; prior lines untouched;
  * local-only — gitignored, per-environment churn, never committed; accepted
    proposals become tracked memory later via blessed writes, and THAT review
    is the PII boundary (D-059);
  * validated BEFORE append — INVARIANT-03 makes retroactive redaction
    impossible, so oversize notes and PII-shaped content (emails, secret-token
    shapes, absolute home paths) are rejected, never scrubbed;
  * written ONLY from the blessed write-locked mutation (``mutations.add_dream``
    → ``cz_add_dream``) — never from a hook handler (INVARIANT-06);
  * deterministic & stdlib-only (D-018) — the only non-determinism is the
    date, injectable (``today=``) for tests.
"""

from __future__ import annotations

import json
import re

from .paths import RepoPaths
from .proposals import proposal_id
# One append/read substrate for every engine journal: the sorted-key JSONL
# appender and the torn-line-tolerant reader are telemetry.py's (D-058).
from .telemetry import _append, _today, read_events

# What a note can be about. Deliberately small; validated at write time so the
# dreamer clusters over a closed vocabulary. Tune from dogfood data (O-03).
KINDS = ("friction", "gap", "surprise", "correction", "drift", "win")

# A dream note is a distillate, not a transcript: hard char cap plus a
# sentence cap (naive terminator split — the char cap is the real bound).
MAX_NOTE_CHARS = 600
MAX_NOTE_SENTENCES = 4
MAX_REFS = 8

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Conservative deny-list of PII/secret SHAPES. False negatives are survivable
# (the D-059 review boundary still stands before anything becomes tracked
# memory); false positives just ask the agent to rephrase — so patterns stay
# high-precision: emails, well-known token prefixes, absolute home paths
# (usernames). Repo-relative paths are the house convention anyway (D-031).
_PII_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    ("email address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("secret-token shape", re.compile(
        r"\b(?:sk|pk)-[A-Za-z0-9]{8,}"          # OpenAI/Stripe style
        r"|\bgh[pousr]_[A-Za-z0-9]{20,}"         # GitHub tokens
        r"|\bgithub_pat_[A-Za-z0-9_]{20,}"
        r"|\bAKIA[0-9A-Z]{16}\b"                 # AWS access key id
        r"|\bxox[baprs]-[A-Za-z0-9-]{10,}"       # Slack
        r"|-----BEGIN [A-Z ]*PRIVATE KEY"
        r"|\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}")),  # JWT-ish
    ("absolute home path", re.compile(
        r"/home/[A-Za-z0-9_.-]+"
        r"|/Users/[A-Za-z0-9_.-]+"
        r"|[A-Za-z]:\\Users\\[^\\\s\"']+"
        r"|\\\\wsl\.localhost\\")),
)


def note_id(gameplan: str, phase: str, kind: str, note: str) -> str:
    """Stable content-derived id (``dream:<12-hex>``, same scheme as proposal
    ids). Whitespace-collapsed so a re-paste with different wrapping dedupes;
    gameplan+phase are part of the identity so the same observation recurring
    in a LATER phase is a genuinely new signal, not a duplicate."""
    collapsed = " ".join(note.split())
    return proposal_id("dream", gameplan, phase, kind, collapsed)


def validate(kind: str, note: str, refs: list[str] | None) -> list[str]:
    """All the reasons this note must not be appended (empty list = clean)."""
    problems: list[str] = []
    if kind not in KINDS:
        problems.append(f"unknown kind {kind!r} — one of {', '.join(KINDS)}")
    text = (note or "").strip()
    if not text:
        problems.append("note is empty")
    if len(text) > MAX_NOTE_CHARS:
        problems.append(
            f"note is {len(text)} chars (max {MAX_NOTE_CHARS}) — a dream note "
            f"is a distillate, not a transcript")
    sentences = [s for s in _SENTENCE_SPLIT.split(text) if s]
    if len(sentences) > MAX_NOTE_SENTENCES:
        problems.append(
            f"note has ~{len(sentences)} sentences (max {MAX_NOTE_SENTENCES})")
    for label, pat in _PII_PATTERNS:
        if pat.search(text):
            problems.append(
                f"note matches a {label} — dream notes are PII-free by "
                f"construction (append-only journal, no retroactive redaction); "
                f"rephrase without it (use repo-relative paths, id references)")
    for r in refs or []:
        if not isinstance(r, str) or not r.strip() or len(r) > 64:
            problems.append(f"ref {r!r} is not a short id string")
    if refs and len(refs) > MAX_REFS:
        problems.append(f"{len(refs)} refs (max {MAX_REFS})")
    return problems


def read_notes(paths: RepoPaths) -> list[dict]:
    """All dream notes in append order; tolerant of partial/garbled lines."""
    return read_events(paths.dreams_file)


def add_note(paths: RepoPaths, *, gameplan: str, phase: str, kind: str,
             note: str, refs: list[str] | None = None,
             today: str | None = None) -> dict:
    """Validate-then-append one dream note; duplicate content is a no-op.

    Caller holds the H-05 write lock (``mutations.add_dream``) — the dedupe
    read and the append are one read-modify-write.
    """
    problems = validate(kind, note, refs)
    if problems:
        return {"ok": False, "appended": False,
                "error": "dream note rejected — nothing was appended",
                "problems": problems,
                "summary": f"rejected: {problems[0]}"}
    text = note.strip()
    nid = note_id(gameplan, phase, kind, text)
    existing = read_notes(paths)
    if any(e.get("id") == nid for e in existing):
        return {"ok": True, "appended": False, "deduped": True, "id": nid,
                "count": len(existing),
                "summary": f"duplicate dream note ({nid}) — journal unchanged"}
    rec = {
        "id": nid,
        "date": _today(today),
        "gameplan": gameplan,
        "phase": str(phase),
        "kind": kind,
        "note": text,
        "refs": sorted({str(r).strip() for r in (refs or [])}),
    }
    _append(paths.dreams_file, rec)
    return {"ok": True, "appended": True, "deduped": False, "id": nid,
            "record": rec, "count": len(existing) + 1,
            "path": str(paths.dreams_file),
            "summary": f"dream note {nid} appended ({kind}, "
                       f"{len(existing) + 1} in journal)"}


# --- the dreamer's assembly side (D-059, A-001) -----------------------------------
#
# Engine assembles, agent judges (INVARIANT-05): cz_dream never writes. The gate
# has two conditions (A-001): no previously staged dream proposals may sit
# untriaged (else dreaming just piles proposals on unactioned ones), and enough
# unconsumed notes must have accumulated to be worth a distillation pass.

# Dream only when this many unconsumed notes wait. A plain constant, tuned from
# dogfood data in Phase 5 (O-03) — never a config on/off switch (D-015).
RIPENESS_NOTES = 10
# A-001: the bundle is bounded — top-K clusters, exemplar-only full text.
BUNDLE_MAX_CLUSTERS = 8
CLUSTER_MAX_EXEMPLARS = 3
# Token-set Jaccard at/above which two notes belong to one cluster: RELATED
# grouping, deliberately looser than the near-duplicate-LESSON threshold
# (analyze._LESSON_DUP_JACCARD = 0.40). Same canonical tokenizer either way
# (INVARIANT-09) — a different threshold for a different concept, single-sourced
# here for any future dream-related overlap computation.
CLUSTER_JACCARD = 0.25

WATERMARK_NAME = "dreams.watermark.json"
PROPOSALS_NAME = "proposals.dream.jsonl"


def watermark_path(paths: RepoPaths):
    return paths.clauderizer_dir / WATERMARK_NAME


def proposals_path(paths: RepoPaths):
    return paths.clauderizer_dir / PROPOSALS_NAME


def consumed_ids(paths: RepoPaths) -> set[str]:
    """Note ids already distilled into a durable proposal batch (the Phase 3
    watermark, advanced only AFTER proposals are written — resumable by
    construction). Absent/corrupt watermark reads as nothing consumed."""
    p = watermark_path(paths)
    if not p.exists():
        return set()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return set()
    if not isinstance(data, dict):
        return set()
    return {str(x) for x in data.get("consumed", [])}


def unconsumed_notes(paths: RepoPaths) -> list[dict]:
    done = consumed_ids(paths)
    return [n for n in read_notes(paths) if n.get("id") not in done]


def read_proposals(paths: RepoPaths) -> list[dict]:
    """Raw dream-proposal records in append order (jsonl, same substrate)."""
    return read_events(proposals_path(paths))


def pending_proposals(paths: RepoPaths, today: str | None = None) -> list[dict]:
    """Dream proposals awaiting triage: not handled (terminal marker record),
    not dismissed, not still-deferred — through the SAME producer-agnostic
    ledger filter modernize proposals use (D-052/D-059)."""
    from .proposals import filter_pending, load_ledger

    records = read_proposals(paths)
    handled = {str(r.get("id")) for r in records if r.get("handled")}
    live, seen = [], set()
    for r in records:
        rid = str(r.get("id"))
        if r.get("handled") or rid in handled or rid in seen:
            continue
        seen.add(rid)
        live.append(r)
    return filter_pending(live, load_ledger(paths), today)


def _cluster(notes: list[dict]) -> list[dict]:
    """Greedy, order-stable token-set clustering over kind + note text."""
    from .analyze import _tokens  # THE tokenizer (INVARIANT-09)
    from .telemetry import _jaccard

    groups: list[dict] = []
    for n in notes:
        toks = _tokens(f"{n.get('kind', '')} {n.get('note', '')}")
        target = None
        for g in groups:
            if _jaccard(toks, g["_tokens"]) >= CLUSTER_JACCARD:
                target = g
                break
        if target is None:
            groups.append({"_tokens": set(toks), "members": [n]})
        else:
            target["_tokens"] |= toks
            target["members"].append(n)
    groups.sort(key=lambda g: (-len(g["members"]), g["members"][0].get("id", "")))
    out = []
    for g in groups:
        members = g["members"]
        out.append({
            "size": len(members),
            "kinds": sorted({m.get("kind", "") for m in members}),
            "note_ids": [m.get("id") for m in members],
            # Full text only for the exemplars; the rest stay ids (D-013/A-001).
            "exemplars": [
                {k: m.get(k) for k in ("id", "date", "phase", "kind", "note", "refs")}
                for m in members[:CLUSTER_MAX_EXEMPLARS]
            ],
        })
    return out


_ENTITY_REF = re.compile(r"^[a-z][a-z0-9_-]*\.[a-z0-9._-]+$")


def _adjacency(paths: RepoPaths, notes: list[dict]) -> dict:
    """One-hop graph neighborhood for entity-shaped refs across the notes."""
    refs = sorted({r for n in notes for r in (n.get("refs") or [])
                   if _ENTITY_REF.match(str(r))})[:8]
    if not refs:
        return {}
    from .graph import index as _gindex
    from .graph import query as _gquery

    graph = _gindex.load_or_rebuild(paths.docs, paths.index_file)
    out = {}
    for r in refs:
        if _gquery.lookup(graph, r) is None:
            continue
        out[r] = {"dependents": _gquery.dependents(graph, r),
                  "dependencies": _gquery.dependencies(graph, r)}
    return out


def assemble(paths: RepoPaths, *, today: str | None = None) -> dict:
    """The dream bundle — or the reason there isn't one. Read-only."""
    from .telemetry import corpus_health, lesson_health

    pending = pending_proposals(paths, today)
    if pending:
        ids = [str(p.get("id")) for p in pending]
        return {"ok": True, "state": "blocked_on_triage", "pending": ids,
                "summary": (f"{len(ids)} dream proposal(s) await triage — "
                            f"handle/dismiss/defer them first (A-001); "
                            f"dreaming never piles onto unactioned output")}
    notes = unconsumed_notes(paths)
    if len(notes) < RIPENESS_NOTES:
        return {"ok": True, "state": "not_ripe",
                "unconsumed": len(notes), "ripeness": RIPENESS_NOTES,
                "summary": (f"{len(notes)}/{RIPENESS_NOTES} unconsumed notes — "
                            f"not ripe; keep capturing (cz_add_dream)")}
    clusters = _cluster(notes)
    dropped = max(0, len(clusters) - BUNDLE_MAX_CLUSTERS)
    health = corpus_health(paths, today=today)
    lh = lesson_health(paths)
    flags = [s for s in lh.get("scores", []) if s.get("signal")]
    bundle = {
        "ok": True,
        "state": "ripe",
        "unconsumed": len(notes),
        "clusters": clusters[:BUNDLE_MAX_CLUSTERS],
        "clusters_dropped": dropped,  # no silent caps — the tail is named
        "corpus_health": {k: health.get(k) for k in
                          ("active_lessons", "redundant_pairs", "never_surfaced",
                           "pass_rate") if k in health},
        "lesson_flags": flags,
        "adjacent": _adjacency(paths, notes),
        "prompt": (
            "Judge each cluster: does it indicate a durable memory change — a "
            "lesson, a correction, a decision, a doc/glossary gap, a procedure "
            "drift? You decide; the engine only assembled (INVARIANT-05). Then "
            "call cz_dream_propose ONCE with every proposal you stage ({detail, "
            "op, args, evidence: note ids}) AND reviewed_note_ids = all note ids "
            "across these clusters — clusters judged not durable are consumed "
            "too, so they never re-ripen. Staged proposals surface at next "
            "session start for triage (handle/dismiss/defer) and gate further "
            "dreaming until triaged."),
    }
    est = len(json.dumps(bundle, sort_keys=True, ensure_ascii=False)) // 4
    bundle["est_tokens"] = est  # A-001: the bundle reports its own weight
    bundle["summary"] = (f"ripe: {len(notes)} notes in "
                         f"{len(bundle['clusters'])} cluster(s)"
                         + (f" (+{dropped} dropped by cap)" if dropped else "")
                         + f", ~{est} tok bundle")
    return bundle


# --- staging judged proposals + the consumption watermark (Phase 3, D-059) --------


def _pii_hits(text: str) -> list[str]:
    """Labels of PII/secret shapes present in ``text`` (shared deny-list)."""
    return [label for label, pat in _PII_PATTERNS if pat.search(text or "")]


def _validate_proposals(proposals: list) -> list[str]:
    problems: list[str] = []
    if not isinstance(proposals, list):
        return ["proposals must be a list of {detail, op?, args?, evidence?}"]
    for i, p in enumerate(proposals):
        if not isinstance(p, dict):
            problems.append(f"proposal[{i}] is not an object")
            continue
        detail = str(p.get("detail") or "").strip()
        if not detail:
            problems.append(f"proposal[{i}] has no detail")
        if len(detail) > MAX_NOTE_CHARS:
            problems.append(
                f"proposal[{i}] detail is {len(detail)} chars "
                f"(max {MAX_NOTE_CHARS}) — a proposal is a pointer, not an essay")
        for label in _pii_hits(detail):
            problems.append(
                f"proposal[{i}] detail matches a {label} — proposals surface in "
                f"sessions and their accepted writes become tracked memory; "
                f"rephrase (repo-relative paths, id references)")
        if p.get("op") is not None and not isinstance(p.get("op"), str):
            problems.append(f"proposal[{i}] op is not a string")
        if p.get("args") is not None and not isinstance(p.get("args"), dict):
            problems.append(f"proposal[{i}] args is not an object")
        ev = p.get("evidence") or []
        if not isinstance(ev, list) or any(not isinstance(e, str) for e in ev):
            problems.append(f"proposal[{i}] evidence is not a list of note ids")
    return problems


def dream_proposal_id(op: str, detail: str, evidence: list[str]) -> str:
    collapsed = " ".join(str(detail).split())
    return proposal_id("dreamprop", op or "", collapsed, *sorted(evidence or []))


def _write_watermark(paths: RepoPaths, consumed: set[str], today: str | None) -> None:
    # Operational state, not memory: a small rewritable JSON (like the triage
    # ledger), NOT an append-only log — INVARIANT-03 governs memory, and the
    # journal itself stays untouched.
    watermark_path(paths).write_text(
        json.dumps({"consumed": sorted(consumed), "advanced": _today(today)},
                   sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")


def stage_proposals(paths: RepoPaths, *, proposals: list, reviewed_note_ids=None,
                    today: str | None = None) -> dict:
    """Durably stage judged dream proposals, THEN consume the reviewed notes.

    The ordering is the resumability contract (A-001): proposals are appended
    before the watermark advances, so a crash between the two re-mines nothing
    already staged (content-hash dedupe) and loses nothing unstaged (watermark
    unadvanced). An empty ``proposals`` with ``reviewed_note_ids`` is a valid
    "dreamed, found nothing durable" pass — it only consumes. Caller holds the
    H-05 lock (mutations.stage_dream_proposals).
    """
    problems = _validate_proposals(proposals)
    if problems:
        return {"ok": False, "staged": 0,
                "error": "dream proposals rejected — nothing was staged",
                "problems": problems, "summary": f"rejected: {problems[0]}"}
    existing = {str(r.get("id")) for r in read_proposals(paths)}
    staged_ids, deduped = [], 0
    for p in proposals:
        detail = str(p.get("detail")).strip()
        ev = sorted({str(e) for e in (p.get("evidence") or [])})
        pid = dream_proposal_id(str(p.get("op") or ""), detail, ev)
        if pid in existing:
            deduped += 1
            continue
        rec = {"id": pid, "created": _today(today), "detail": detail,
               "op": str(p.get("op") or ""), "args": p.get("args") or {},
               "evidence": ev}
        _append(proposals_path(paths), rec)
        existing.add(pid)
        staged_ids.append(pid)
    reviewed = {str(x) for x in (reviewed_note_ids or [])}
    for p in proposals:
        reviewed |= {str(e) for e in (p.get("evidence") or [])}
    consumed_total = consumed_ids(paths) | reviewed
    if reviewed:
        _write_watermark(paths, consumed_total, today)
    return {"ok": True, "staged": len(staged_ids), "deduped": deduped,
            "ids": staged_ids, "consumed": len(reviewed),
            "consumed_total": len(consumed_total),
            "path": str(proposals_path(paths)),
            "summary": (f"staged {len(staged_ids)} dream proposal(s)"
                        + (f", {deduped} duplicate(s) skipped" if deduped else "")
                        + f"; {len(reviewed)} note(s) consumed")}


def mark_handled(paths: RepoPaths, *, proposal_id: str,
                 today: str | None = None) -> dict:
    """Retire a dream proposal after its work was done: append the terminal
    ``{"id", "handled"}`` marker (append-only — the original record stays).
    Caller holds the H-05 lock (mutations.handle_dream_proposal)."""
    records = read_proposals(paths)
    known = {str(r.get("id")) for r in records if not r.get("handled")}
    done = {str(r.get("id")) for r in records if r.get("handled")}
    pid = str(proposal_id)
    if pid in done:
        return {"ok": True, "id": pid, "changed": False,
                "summary": f"{pid} already handled — no-op"}
    if pid not in known:
        return {"ok": False, "id": pid,
                "error": f"unknown dream proposal id {pid!r} (cz_dream / the "
                         f"digest show pending ids)",
                "summary": f"unknown id {pid}"}
    _append(proposals_path(paths), {"id": pid, "handled": _today(today)})
    return {"ok": True, "id": pid, "changed": True,
            "summary": f"dream proposal {pid} marked handled"}


# --- the dream schedule + the session-start plea (Phase 6, A-004) ------------------
#
# Capture is ambient, but nothing used to drive ADOPTION of the dreaming half:
# a journal that never gets dreamed helps no one. The plea (rendered by the
# status digest, INVARIANT-08) begs the user to schedule the loop — in plain
# English, with exact commands — whenever notes accumulate with no schedule
# registered and nothing already pending triage. Registration is a per-user,
# gitignored self-report (the engine cannot see crontabs or host routines);
# method="manual" is a legitimate quieting verdict in the D-052 ledger spirit —
# a USER verdict, never a feature toggle: the loop, gauges, and skill stay
# fully active either way.

SCHEDULE_NAME = "dreams.schedule.toml"
_SCHEDULE_FIELD_MAX = 200


def schedule_path(paths: RepoPaths):
    return paths.clauderizer_dir / SCHEDULE_NAME


def schedule_info(paths: RepoPaths) -> dict | None:
    """The registered dream schedule, or None. Missing/malformed reads as None
    (the plea is best-effort advisory — never fatal)."""
    p = schedule_path(paths)
    if not p.exists():
        return None
    import tomllib
    try:
        with p.open("rb") as fh:
            raw = tomllib.load(fh)
    except (OSError, ValueError):  # TOMLDecodeError is a ValueError
        return None
    sched = raw.get("schedule") if isinstance(raw, dict) else None
    if not isinstance(sched, dict) or not str(sched.get("method") or "").strip():
        return None
    return {k: str(sched.get(k) or "") for k in
            ("method", "cadence", "command", "registered")}


def register_schedule(paths: RepoPaths, *, method: str, cadence: str = "",
                      command: str = "", today: str | None = None) -> dict:
    """Record (or clear, with an empty method) the dream-schedule self-report.

    Caller holds the H-05 lock (mutations.register_dream_schedule). The file is
    per-user operational state like the triage ledger — rewritable, gitignored,
    never memory."""
    method = str(method or "").strip()
    if not method:
        existed = schedule_path(paths).exists()
        if existed:
            schedule_path(paths).unlink()
        return {"ok": True, "registered": False, "cleared": existed,
                "summary": ("dream schedule cleared — the session-start plea "
                            "returns when notes accumulate" if existed
                            else "no dream schedule was registered — nothing to clear")}
    fields = {"method": method, "cadence": str(cadence or "").strip(),
              "command": str(command or "").strip()}
    for key, val in fields.items():
        if len(val) > _SCHEDULE_FIELD_MAX:
            return {"ok": False, "registered": False,
                    "error": f"{key} is {len(val)} chars (max {_SCHEDULE_FIELD_MAX})",
                    "summary": f"rejected: {key} too long"}
    def _q(v: str) -> str:
        # TOML basic-string escaping — a scheduled command legitimately carries
        # double quotes (claude -p "/clauderizer-dream").
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'

    lines = [
        "# Clauderizer dream-schedule self-report — per-user, gitignored (A-004).",
        "# Records HOW the dreaming loop runs on this machine so the session-start",
        '# plea retires. method="manual" means you run /clauderizer-dream yourself.',
        "",
        "[schedule]",
        f"method = {_q(fields['method'])}",
        f"cadence = {_q(fields['cadence'])}",
        f"command = {_q(fields['command'])}",
        f"registered = {_q(_today(today))}",
    ]
    schedule_path(paths).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "registered": True, "method": fields["method"],
            "path": str(schedule_path(paths)),
            "summary": (f"dream schedule registered ({fields['method']}"
                        + (f", {fields['cadence']}" if fields["cadence"] else "")
                        + ") — the session-start plea retires")}


def plea_state(paths: RepoPaths, today: str | None = None) -> dict | None:
    """The dream plea's render data, or None when it must stay quiet: quiet
    when a schedule is registered, when the journal has nothing unconsumed,
    or when staged proposals are pending (the triage line owns that state)."""
    if schedule_info(paths) is not None:
        return None
    unconsumed = len(unconsumed_notes(paths))
    if not unconsumed:
        return None
    if pending_proposals(paths, today):
        return None
    return {"unconsumed": unconsumed, "ripeness": RIPENESS_NOTES}
