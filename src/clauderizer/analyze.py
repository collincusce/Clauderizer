"""The analyze gate (D-016/D-018): surface the existing invariants/decisions most
relevant to a piece of text — and the one-hop graph neighbors it touches but has
not connected — for the AGENT to judge contradiction, supersession, or a gap.

Judgment-based, exactly like ``cz_cascade``: the engine ASSEMBLES candidates and
prompts; it never decides. Relevance is keyword + entity-id overlap (O-01:
dependency-light, no embeddings — L-14), ranked and capped so the agent sees the
right few, not the whole file. The gap-finder is the structural complement
(D-018): it walks the project graph's own edges one hop out from what the text
already names, so "related but unconnected" needs no embeddings either.
"""

from __future__ import annotations

import re

from .graph import index as graph_index, query as graph_query
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
    # Keep distinctive alphanumeric identifiers (s3, v2, h2, k8) regardless of
    # length — they are exactly the jargon that signals a conflict — alongside
    # ordinary words (>= 4 chars); stopwords drop at any length.
    return {w for w in _WORD_RE.findall(text.lower())
            if w not in _STOP and (len(w) >= 4 or any(c.isdigit() for c in w))}


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
        elif cur is not None and not ln.lstrip().startswith("### "):
            cur["body"] += ln + "\n"  # don't fold a stray non-entry heading into the body
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


# --- gap-finder: one-hop graph adjacency (D-018) ---------------------------------
#
# The keyword ranker above answers "what might this CONTRADICT?"; the gap-finder
# answers the complementary "what have I NOT connected?" — Co-STORM's moderator
# move, surfacing relevant-but-unmentioned context. It is structural, not semantic
# (consistent with D-013/D-014): the signal is the project graph's own edges,
# walked one hop from what the text already touches. Two seed sources feed it —
# graph entities NAMED verbatim in the text, and graph entities a top-ranked
# decision INTRODUCED (the ``introduced_by`` bridge, the only structural link from
# a DECISIONS.md entry to a graph node). Neighbors already named or seeded are
# dropped; an empty result is an honest negative (nothing in the graph relates).


def _mentioned(text: str, ids) -> set[str]:
    """Entity ids that appear verbatim in ``text``, matched on id boundaries.

    Ids are dotted/hyphenated (``subsys.rituals``, ``feat.init-cli``); the boundary
    guard keeps ``subsys.graph`` from matching inside ``subsys.graph-index``.
    """
    # Lookbehind blocks a longer id to the left; lookahead blocks a word/hyphen
    # continuation to the right (so `subsys.graph` does not match inside
    # `subsys.graph-index`) but allows a trailing `.` — an id ending a sentence
    # ("…subsys.graph.") or naming a dotted child still counts as a mention.
    return {eid for eid in ids
            if re.search(rf"(?<![\w.-]){re.escape(eid)}(?![\w-])", text)}


def adjacent_entities(paths: RepoPaths, text: str, decision_ids,
                      k: int = 8) -> list[dict]:
    """One-hop graph neighbors of what ``text`` touches but has not named (D-018).

    Seeds = entities named in ``text`` plus entities ``introduced_by`` a surfaced
    decision. Returns each seed's direct dependencies + dependents, minus the seeds
    themselves and anything already named — ``{id, type, status, via}``. Empty when
    nothing in the graph relates (an honest negative, never a failure).
    """
    graph = graph_index.build(paths.docs)
    if not graph.entities:
        return []
    decision_ids = set(decision_ids)
    seeds: dict[str, str] = {sid: "named in text"
                             for sid in _mentioned(text, graph.entities.keys())}
    for e in graph.all():
        intro = str(e.raw.get("introduced_by") or "")
        if intro and intro in decision_ids:
            seeds.setdefault(e.id, f"introduced by {intro}")
    seen = set(seeds)
    out: list[dict] = []
    for sid in sorted(seeds):
        reason = seeds[sid]
        for dep in sorted(graph_query.dependencies(graph, sid)):
            e = graph.get(dep)
            if e is not None and dep not in seen:
                seen.add(dep)
                out.append({"id": dep, "type": e.type, "status": e.status,
                            "via": f"{sid} depends on it ({reason})"})
        for dependent in graph_query.dependents(graph, sid):
            e = graph.get(dependent)
            if e is not None and dependent not in seen:
                seen.add(dependent)
                out.append({"id": dependent, "type": e.type, "status": e.status,
                            "via": f"depends on {sid} ({reason})"})
    out.sort(key=lambda a: a["id"])
    return out[:k]


def analyze(paths: RepoPaths, text: str, k: int = 5,
            exclude_ids: tuple[str, ...] = ()) -> dict:
    """Surface the most relevant decisions + invariants for ``text``, plus the
    one-hop graph neighbors it has not yet connected (the gap-finder, D-018)."""
    decisions = rank_relevant(
        text, parse_entries(writer.full_text(paths.doc("DECISIONS")), "Decisions"),
        k=k, exclude_ids=exclude_ids)
    invariants = rank_relevant(
        text, parse_entries(writer.full_text(paths.doc("INVARIANTS")), "Invariants"),
        k=k, exclude_ids=exclude_ids)
    adjacent = adjacent_entities(paths, text, {d["id"] for d in decisions})
    return {"decisions": decisions, "invariants": invariants, "adjacent": adjacent}
