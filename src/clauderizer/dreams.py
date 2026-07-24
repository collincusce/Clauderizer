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
            "drift? You decide; the engine only assembled (INVARIANT-05). Stage "
            "one dream proposal per real signal for next-session triage "
            "(Phase 3's blessed writer; until it ships, apply judgments "
            "directly via cz_add_lesson / cz_add_correction / cz_add_decision) "
            "and skip clusters with nothing durable. The consumption watermark "
            "advances only when proposals are durably written."),
    }
    est = len(json.dumps(bundle, sort_keys=True, ensure_ascii=False)) // 4
    bundle["est_tokens"] = est  # A-001: the bundle reports its own weight
    bundle["summary"] = (f"ripe: {len(notes)} notes in "
                         f"{len(bundle['clusters'])} cluster(s)"
                         + (f" (+{dropped} dropped by cap)" if dropped else "")
                         + f", ~{est} tok bundle")
    return bundle
