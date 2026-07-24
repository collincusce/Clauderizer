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
