"""Per-entry abstract index over the append-only corpus — a disposable cache.

The fast-retrieval layer (gameplan 2026-06-25-abstract-index-fast-retrieval): a
compact, addressable record per corpus entry so a consumer (Phase 2: ``cz_get`` +
abstracts on ``cz_analyze``) can read exactly the entry it needs instead of loading
a whole corpus file. Deterministic, no ML, no new dependency (reuses
``analyze._tokens`` — L-14). Markdown stays canonical; this cache is rebuilt from it
on demand and is always safe to discard (INVARIANT-01).

Each record is ``{id, title, abstract, anchor, token_set, content_hash, status,
kind}``:
  * ``abstract`` — a bounded one-line summary (O-01: the entry title, or for a
    lesson its first sentence, capped at :data:`ABSTRACT_CAP`).
  * ``anchor``   — ``docs/<FILE>.md:<line>`` of the entry, recomputed every build
    so line drift self-heals.
  * ``token_set``/``content_hash`` — distinctive tokens and a stable
    ``sha256(title + "\\n" + body)`` for relevance reuse and change detection.

Mirrors :mod:`graph.index` (build / write_cache / load_or_rebuild) with three D1
refinements: the freshness mtime is scoped to ONLY the four corpus files (not all
of ``docs/``); the cache is gated on a ``schema_version`` field as well as mtime
(so a schema bump refreshes the cache file even when mtime is unchanged — the gap
``graph/index.py`` leaves open, O-02, which is harmless THERE only because it always
re-parses); and the write is atomic (``.tmp`` then ``os.replace``).

The DUAL parser is the subtle part (O-03): DECISIONS/INVARIANTS/HARDENING are
``### ID — title`` blocks (reusing ``analyze._ENTRY_RE``); LESSONS are single
``**L-NN.**`` lines whose state lives in a trailing ``lesson_state`` marker — the
``**N.**`` matcher in ``lesson_state`` would miss every ``L-NN`` line, so lessons
get their own line regex here (sibling of ``handoff._PROJECT_LESSON_NUM_RE``).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from ..markdown import lesson_state, writer
from ..paths import RepoPaths

# Bump when the record shape changes; load_or_rebuild refreshes the cache file on a
# mismatch even if no markdown changed (D1 — the gate graph/index.py lacks).
SCHEMA_VERSION = 1

# Bound on a surfaced abstract (chars). The payload-budget knob; Phase 3 may tune it.
ABSTRACT_CAP = 200

# The four corpus docs: (doc name, section heading, entry kind). LESSONS is parsed
# separately (single-line **L-NN.** entries, not ### ID — title blocks).
_EMDASH_CORPUS = (
    ("DECISIONS", "Decisions", "decision"),
    ("INVARIANTS", "Invariants", "invariant"),
    ("HARDENING", "Risks", "finding"),
)
_LESSONS_DOC = "LESSONS"

# kind -> (corpus doc, section heading) for resolving a single entry's body on
# demand (the cz_get read path, analyze.get_entry). Derived from the corpus tables
# above so this mapping can never drift from what build() actually indexes.
_DOC_SECTION_BY_KIND: dict[str, tuple[str, str]] = {
    kind: (name, section) for name, section, kind in _EMDASH_CORPUS
}
_DOC_SECTION_BY_KIND["lesson"] = (_LESSONS_DOC, "Lessons")

# A LESSONS.md entry line: ``**L-39.** text…`` (sibling of handoff._PROJECT_LESSON_NUM_RE).
_LESSON_LINE_RE = re.compile(r"^\*\*(L-\d+)\.\*\*\s*(.*)$")
# Entry lifecycle status, tolerating the decisions form (``**Status**: active``) and
# the hardening form (``- **Status**: resolved (date)``). First word after the label.
_STATUS_RE = re.compile(r"^\s*(?:-\s*)?\*\*Status\*\*\s*:\s*([a-z]+)", re.M | re.I)


def _corpus_mtime(paths: RepoPaths) -> float:
    """Max mtime across ONLY the four corpus files (scoped, unlike the graph index's
    whole-``docs/`` scan), so an unrelated entity-doc edit never busts this cache."""
    latest = 0.0
    for name in ("DECISIONS", "LESSONS", "INVARIANTS", "HARDENING"):
        p = paths.doc(name)
        try:
            latest = max(latest, p.stat().st_mtime)
        except OSError:
            continue
    return latest


def _cap(text: str) -> str:
    one = " ".join(text.split())
    if len(one) <= ABSTRACT_CAP:
        return one
    return one[:ABSTRACT_CAP].rsplit(" ", 1)[0] + "…"


def _record(eid: str, title: str, body: str, line: int, status: str, kind: str,
            rel_path: str) -> dict:
    from .. import analyze  # lazy: analyze imports graph.index, avoid an import cycle

    content = f"{title}\n{body}".strip()
    return {
        "id": eid,
        "title": title,
        "abstract": _cap(title),
        "anchor": f"{rel_path}:{line}",
        "token_set": sorted(analyze._tokens(f"{title} {body}")),
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "status": status,
        "kind": kind,
    }


def _emdash_records(text: str, section: str, kind: str, rel_path: str) -> list[dict]:
    """Parse ``### ID — title`` blocks under ``section`` with absolute line anchors.

    Walks the whole file (tracking 1-based line numbers and section membership)
    rather than ``analyze.parse_entries`` (which drops line info), but reuses
    ``analyze._ENTRY_RE`` so the entry grammar stays single-sourced.
    """
    from .. import analyze  # lazy (see _record)

    out: list[dict] = []
    in_section = False
    cur: dict | None = None

    def flush() -> None:
        if cur is not None:
            out.append(_record(cur["id"], cur["title"], cur["body"].strip(),
                               cur["line"], _status(cur["body"]), kind, rel_path))

    for i, raw in enumerate(text.splitlines(), start=1):
        s = raw.strip()
        if s.startswith("## "):
            flush()
            cur = None
            in_section = s[3:].strip() == section
            continue
        if not in_section:
            continue
        m = analyze._ENTRY_RE.match(s)
        if m:
            flush()
            cur = {"id": m.group(1), "title": m.group(2).strip(), "body": "", "line": i}
        elif cur is not None and not s.startswith("### "):
            cur["body"] += raw + "\n"
    flush()
    return out


def parse_lesson_line(line: str) -> tuple[str, str, str] | None:
    """``(id, title, body)`` for a ``**L-NN.**`` lesson line, or ``None`` if the
    line is not one.

    ``title`` is the first sentence (so a surfaced abstract stays compact) and
    ``body`` is the remainder. Single-sources the lesson-line grammar so the index
    and the cz_get read path (:func:`analyze.get_entry`) can never disagree on what
    a lesson line means — the same single-source-the-matcher discipline that keeps
    the dual parser honest (O-03).
    """
    m = _LESSON_LINE_RE.match(line.strip())
    if not m:
        return None
    eid, line_text = m.group(1), m.group(2).strip()
    first, _, rest = line_text.partition(". ")
    title = first + ("." if first and not first.endswith(".") else "")
    return eid, title, rest.strip()


def _lesson_records(text: str, rel_path: str) -> list[dict]:
    """Parse single-line ``**L-NN.**`` lessons under ``## Lessons`` (O-03).

    The line's first sentence becomes the title (so the abstract stays compact);
    the remainder is the body. Status comes from the trailing ``lesson_state``
    marker — never a substring match.
    """
    out: list[dict] = []
    in_section = False
    for i, raw in enumerate(text.splitlines(), start=1):
        s = raw.strip()
        if s.startswith("## "):
            in_section = s[3:].strip() == "Lessons"
            continue
        if not in_section:
            continue
        parsed = parse_lesson_line(s)
        if parsed is None:
            continue
        eid, title, body = parsed
        status, _detail = lesson_state.parse_state(s)
        out.append(_record(eid, title, body, i, status, "lesson", rel_path))
    return out


def _status(body: str) -> str:
    """Lifecycle status from an entry body's ``**Status**`` line; ``active`` default."""
    m = _STATUS_RE.search(body)
    return m.group(1).lower() if m else "active"


def build(paths: RepoPaths) -> dict:
    """Build the abstract index from the four corpus files. Missing files are
    skipped (an empty corpus yields an empty index, never an error)."""
    entries: dict[str, dict] = {}
    for name, section, kind in _EMDASH_CORPUS:
        p = paths.doc(name)
        if not p.exists():
            continue
        rel = f"docs/{name}.md"
        for rec in _emdash_records(writer.full_text(p), section, kind, rel):
            entries[rec["id"]] = rec
    lessons = paths.doc(_LESSONS_DOC)
    if lessons.exists():
        for rec in _lesson_records(writer.full_text(lessons), f"docs/{_LESSONS_DOC}.md"):
            entries[rec["id"]] = rec
    return {
        "schema_version": SCHEMA_VERSION,
        "corpus_mtime": _corpus_mtime(paths),
        "entries": entries,
    }


def write_cache(index: dict, cache_file: Path) -> None:
    """Serialize the index atomically (write a sibling ``.tmp`` then ``os.replace``)
    so a concurrent reader never sees a torn file. Refuses a symlinked target (H-13)."""
    writer.refuse_if_symlink(cache_file)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache_file.with_name(cache_file.name + ".tmp")
    tmp.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, cache_file)


def load_or_rebuild(paths: RepoPaths) -> dict:
    """Return a fresh index, rewriting the cache only when it is stale.

    Always re-parses markdown (cheap, and the freshness guarantee — INVARIANT-01);
    the cache is consulted only to decide whether to skip the WRITE. The write is
    skipped only when the cached ``schema_version`` AND ``corpus_mtime`` both match
    — so a schema bump refreshes the cache file even with mtime unchanged (D1). A
    corrupt/undecodable/missing cache simply triggers a rebuild, never an error
    (L-24: guard the decode and the shape).
    """
    cache_file = paths.abstract_index_file
    index = build(paths)
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            fresh = (int(cached.get("schema_version", -1)) == SCHEMA_VERSION
                     and abs(float(cached.get("corpus_mtime", -1.0))
                             - index["corpus_mtime"]) < 1e-6)
            if fresh:
                return index  # cache current — skip the write
        except (json.JSONDecodeError, OSError, ValueError, TypeError, AttributeError):
            pass  # corrupt/unreadable -> fall through and rewrite
    write_cache(index, cache_file)
    return index
