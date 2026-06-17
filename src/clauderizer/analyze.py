"""The analyze gate (D-016): surface the existing invariants/decisions most
relevant to a piece of text, for the AGENT to judge contradiction or supersession.

Judgment-based, exactly like ``cz_cascade``: the engine ASSEMBLES candidates and
prompts; it never decides. Relevance is keyword + entity-id overlap (O-01:
dependency-light, no embeddings — L-14), ranked and capped so the agent sees the
right few, not the whole file.
"""

from __future__ import annotations

import re

from .markdown import sections, writer
from .paths import RepoPaths

# Entry anchors as written by mutations.add_decision / add_invariant: "### D-001 — title",
# "### INVARIANT-05 — title" (em dash). Gameplan-internal "D1" never lands in these docs.
_ENTRY_RE = re.compile(r"^###\s+([A-Z][A-Z0-9]*-\d+)\s+—\s+(.+)$")
_ID_RE = re.compile(r"\b([A-Z][A-Z0-9]*-\d+)\b")
_WORD_RE = re.compile(r"[a-z0-9]+")

# Drop ADR boilerplate (in every entry) + very common words, so overlap reflects
# the distinctive content, not the template.
_STOP = {
    "context", "decision", "consequences", "supersedes", "gameplan", "phase",
    "clauderizer", "that", "this", "with", "from", "into", "have", "will", "must",
    "never", "always", "every", "each", "when", "then", "than", "they", "them",
    "their", "your", "via", "per", "used", "using", "use", "the", "and", "for",
    "not", "but", "are", "was", "were", "has", "had", "would", "should", "could",
    "any", "all", "one", "two", "new", "now", "only", "also", "its", "ever", "such",
}


def _tokens(text: str) -> set[str]:
    return {w for w in _WORD_RE.findall(text.lower()) if len(w) >= 4 and w not in _STOP}


def parse_entries(doc_text: str, section: str) -> list[dict]:
    """Parse ``### ID — title`` blocks under ``section`` into ``{id, title, body}``."""
    body = sections.get_section(doc_text, section) or ""
    entries: list[dict] = []
    cur: dict | None = None
    for ln in body.splitlines():
        m = _ENTRY_RE.match(ln.strip())
        if m:
            if cur:
                entries.append(cur)
            cur = {"id": m.group(1), "title": m.group(2).strip(), "body": ""}
        elif cur is not None:
            cur["body"] += ln + "\n"
    if cur:
        entries.append(cur)
    return entries


def rank_relevant(query: str, entries: list[dict], k: int = 5,
                  exclude_ids: tuple[str, ...] = ()) -> list[dict]:
    """Rank ``entries`` by keyword + entity-id overlap with ``query``.

    Returns the top ``k`` with a positive score: ``{id, title, score}``. An
    explicit id mention in the query (e.g. "supersedes D-007") boosts that entry.
    """
    qtok = _tokens(query)
    qids = set(_ID_RE.findall(query))
    scored = []
    for e in entries:
        if e["id"] in exclude_ids:
            continue
        score = len(qtok & _tokens(f"{e['title']} {e['body']}")) + (3 if e["id"] in qids else 0)
        if score > 0:
            scored.append({"id": e["id"], "title": e["title"], "score": score})
    scored.sort(key=lambda x: (-x["score"], x["id"]))
    return scored[:k]


def analyze(paths: RepoPaths, text: str, k: int = 5,
            exclude_ids: tuple[str, ...] = ()) -> dict:
    """Surface the most relevant existing decisions + invariants for ``text``."""
    decisions = rank_relevant(
        text, parse_entries(writer.full_text(paths.doc("DECISIONS")), "Decisions"),
        k=k, exclude_ids=exclude_ids)
    invariants = rank_relevant(
        text, parse_entries(writer.full_text(paths.doc("INVARIANTS")), "Invariants"),
        k=k, exclude_ids=exclude_ids)
    return {"decisions": decisions, "invariants": invariants}
