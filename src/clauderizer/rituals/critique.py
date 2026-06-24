"""The self-critique gate (D-019): assemble a reference-free coverage/coherence/
grounding rubric for a target (a phase or the whole gameplan) by composing the
deterministic signals the engine already computes, and surface it for the AGENT
to grade.

Read-only and advisory like the analyze gate (D-016): the engine ASSEMBLES the
gaps it can detect deterministically and prompts; it never scores or blocks
(INVARIANT-05). Reference-free (no gold standard — fitting, since a coherence-
retention system has no gold artifact to diff against) and stdlib-only (no
embeddings). STORM grades drafts with a reference-free rubric over Interest /
Coherence / Relevance / Coverage; adapted to Clauderizer's grain, the dimensions
are Coverage / Coherence / Grounding, each backed by signals that already exist.

Two further axes (D1) port CALM's (Ye et al.) anti-bias checklist: because the
target is always SELF-AUTHORED, Self-enhancement (gaps closed by hollow notes,
completion claims that outrun a live gap) and Authority (deference to a citation
that does not resolve in-repo) are the standing failure modes of a self-judge.
They surface the same way — deterministic, advisory, stdlib-only — and stay
quiet on sound work by guarding every fingerprint with an in-repo-anchor check.
"""

from __future__ import annotations

import re

from ..config import Config
from ..markdown import lesson_state, sections
from ..paths import RepoPaths
from . import _tables, status_bundle as sb

# Provenance marker written by mutations.add_lesson (D-017). A lesson without it
# is un-grounded — the Grounding dimension's signal.
_EVIDENCE_RE = re.compile(r"\*\(evidence:", re.IGNORECASE)
_LESSON_NUM_RE = re.compile(r"^\*\*(\d+)\.\*\*\s*(.*)")


def _lessons_without_evidence(index_text: str) -> list[str]:
    """Active accumulated-lesson lines carrying no provenance marker (D-017)."""
    sec = sections.get_section(index_text, "Accumulated Lessons") or ""
    out: list[str] = []
    for line in sec.splitlines():
        s = line.strip()
        if not lesson_state.LESSON_LINE_RE.match(s) or not lesson_state.is_active(s):
            continue
        if _EVIDENCE_RE.search(s):
            continue
        m = _LESSON_NUM_RE.match(s)
        if m:
            body = m.group(2)
            out.append(f"lesson #{m.group(1)} has no evidence: "
                       + body[:60] + ("…" if len(body) > 60 else ""))
    return out


# --- CALM anti-bias checks (D1) ----------------------------------------------
# The critique target is ALWAYS self-authored, so self-enhancement bias (a judge
# over-rating its own work — CALM, Ye et al.) is the standing risk; authority
# bias is deference to a citation that never resolves. Both enter the SAME way
# as the rubric above: deterministic, reference-free, stdlib `re` only — no new
# dependency, no enable/disable flag, advisory (the agent grades, INVARIANT-05).
# Each check pairs an *appeal/filler fingerprint* with an *in-repo-anchor guard*:
# what makes a citation or a closure trustworthy is provenance that resolves in
# this repo (commit, path, count, metric), so a fingerprint with no anchor is
# the tell. The anchor guard is what keeps the checks quiet on sound work — a
# paper citation that is ALSO anchored, or a terse note that cites a commit, is
# not flagged (D-013: a citation is a pointer to canonical provenance, never an
# authority in itself).

# A concrete, in-repo, checkable anchor. Its PRESENCE makes a citation/closure
# verifiable — the precision guard shared by both checks.
_INREPO_ANCHOR_RE = re.compile(
    r"""(?xi)
      \b[0-9a-f]{7,40}\b                                 # commit SHA
    | \b(?:src|docs|tests|benchmarks)/[\w./-]+           # tracked path
    | \b[\w-]+\.(?:py|md|toml|json|txt|cfg|ya?ml)\b      # file.ext (:line may follow)
    | \b\d+\s*tests?\b | \bsuite\s+\d+\b                 # test/suite count
    | \b(?:ndcg|mrr|recall|precision|f1|bleu|rouge)\b    # measured metric
    | \bphase\s+\d+\b                                    # phase reference
    | \b\d{4}-\d{2}-\d{2}\b                              # ISO date / gameplan id
    | \b\d+/\d+\b                                        # N/M run ratio
    | \b(?:ubuntu|macos|windows)-[\d.]+\b                # pinned CI leg
    """
)

# External / unverifiable-authority appeals (CALM authority bias).
_AUTHORITY_APPEAL_RE = re.compile(
    r"""(?xi)
      \barxiv:\S+ | \bdoi:\S+ | https?://                # paper / external URL
    | \bet\s+al\.? | \bthe\s+literature\b | \baccording\s+to\b
    | \b(?:standard|best)\s+practice\b | \bwell[-\s]+(?:known|established)\b
    | \bobviously\b | \bof\s+course\b | \bofficial\s+doc\w*
    | \bverified\b | \bconfirmed\b | \btrust\s+me\b | \bestablished\b
    """
)

# Self-serving filler that closes an open item without substance (the CALM
# self-enhancement "graded uncritically high" tell). Length is NOT the signal.
_HOLLOW_FILLER_RE = re.compile(
    r"""(?xi)
      ^\s*(?:done|resolved|fixed|handled|addressed|sorted|completed?
            |ok(?:ay)?|n/?a|fine|good|looks?\s+good)\b
    | \bno\s+longer\s+an?\s+issue\b | \btaken\s+care\s+of\b
    | \bworking\s+as\s+expected\b | \ball\s+(?:good|set|fine)\b
    | \bnothing\s+to\s+(?:do|see|fix)\b
    """
)

# Self-congratulatory completion intensifiers (CALM self-enhancement). A factual
# report of completion ("phase 0 done, 622 tests green") is NOT an over-claim.
_OVERCLAIM_RE = re.compile(
    r"""(?xi)
      \bfully\s+verified\b
    | \bno\s+(?:gaps?|issues?|problems?)\s+(?:remain\w*|left)\b
    | \bflawless(?:ly)?\b | \bready\s+to\s+(?:ship|merge|release|go)\b
    | \bproduction[-\s]+ready\b | \b100\s*%
    | \beverything\s+(?:just\s+)?(?:passes|works|is\s+fine)\b
    | \bcomplete\s+and\s+correct\b | \bcomprehensive(?:ly)?\b
    | \bnothing\s+left\s+to\s+do\b
    """
)

_EVIDENCE_CAPTURE_RE = re.compile(r"\*\(evidence:\s*(.+?)\)\*", re.IGNORECASE | re.DOTALL)
_RESOLVED_NOTE_RE = re.compile(r"_\(resolved \d{4}-\d{2}-\d{2}:\s*(.+?)\)_")


def _has_inrepo_anchor(text: str) -> bool:
    """Whether ``text`` cites something that resolves in this repo."""
    return bool(_INREPO_ANCHOR_RE.search(text))


def _evidence_is_authority(evidence: str) -> bool:
    """Evidence that appeals to an external/unverifiable authority and offers no
    in-repo anchor to resolve it against (CALM authority bias)."""
    return bool(_AUTHORITY_APPEAL_RE.search(evidence)) and not _has_inrepo_anchor(evidence)


def _resolution_is_hollow(note: str) -> bool:
    """A resolved open item whose note is self-serving filler with nothing
    concrete behind it (CALM self-enhancement: a gap closed by fiat)."""
    return bool(_HOLLOW_FILLER_RE.search(note)) and not _has_inrepo_anchor(note)


def _overclaims(prose: str) -> list[str]:
    """The self-congratulatory completion phrases in ``prose`` (CALM self-
    enhancement). Empty when the prose merely reports facts."""
    return [m.group(0).strip() for m in _OVERCLAIM_RE.finditer(prose)]


def _authority_flags(index_text: str) -> list[str]:
    """Active lessons whose evidence appeals to an unverifiable authority with no
    in-repo anchor. The prior Grounding check passes these — the evidence marker
    IS present — so the authority bias slips through clean (D-017 evidence field).
    """
    sec = sections.get_section(index_text, "Accumulated Lessons") or ""
    out: list[str] = []
    for line in sec.splitlines():
        s = line.strip()
        if not lesson_state.LESSON_LINE_RE.match(s) or not lesson_state.is_active(s):
            continue
        m = _EVIDENCE_CAPTURE_RE.search(s)
        if not m or not _evidence_is_authority(m.group(1)):
            continue
        num = _LESSON_NUM_RE.match(s)
        label = f"lesson #{num.group(1)}" if num else "a lesson"
        ev = m.group(1).strip()
        out.append(f"{label} cites an unverifiable authority (no in-repo anchor): "
                   + ev[:60] + ("…" if len(ev) > 60 else ""))
    return out


def _self_enhancement_flags(gameplan_dir, phase: str | None,
                            summary_text: str, has_objective_gap: bool) -> list[str]:
    """Self-enhancement tells on a self-authored target: a gap closed by a hollow
    note (the prior Coverage check only flags UNRESOLVED items, so a hollow
    closure reads as clean), and a completion claim that outruns a live gap."""
    out: list[str] = []
    for it in sb.open_items(gameplan_dir):
        if not it["resolved"]:
            continue
        if phase is not None and it["phase"] is not None and str(it["phase"]) != str(phase):
            continue
        nm = _RESOLVED_NOTE_RE.search(it["text"])
        note = nm.group(1).strip() if nm else ""
        if note and _resolution_is_hollow(note):
            out.append(f"open item {it['id']} closed with a hollow note: "
                       + note[:60] + ("…" if len(note) > 60 else ""))
    if has_objective_gap and summary_text:
        claims = _overclaims(summary_text)
        if claims:
            out.append(f"completion claim \"{claims[0]}\" while objective gaps remain "
                       "(see Coverage/Coherence)")
    return out


def _resolve_phase(target: str | None, rows: list) -> str | None:
    """Map a target to a phase number (or None for the whole gameplan).

    None / "" / "gameplan"  -> whole gameplan
    "handoff"               -> the current in-progress phase (the one being handed off)
    "<n>"                   -> that phase
    """
    t = (target or "").strip().lower()
    if t in ("", "gameplan"):
        return None
    if t == "handoff":
        cur = next((r for r in rows if r.status == "in_progress"), None)
        return cur.number if cur else None
    return str(target).strip()


def critique(paths: RepoPaths, config: Config, target: str | None = None) -> dict:
    """Assemble the Coverage/Coherence/Grounding rubric for ``target``."""
    gid = config.active_gameplan
    if not gid:
        return {"ok": True, "target": None, "dimensions": [], "gap_count": 0,
                "summary": "no active gameplan to critique",
                "prompt": "Nothing to critique — no active gameplan."}
    gdir = paths.gameplan_dir(gid)
    index_file = gdir / "CHAT-HANDOFF-INDEX.md"
    status_file = gdir / "PHASE-STATUS.md"
    # Read the index once — it carries both the phase table and the lessons.
    # Fall back to PHASE-STATUS.md for the phase table only when no index exists.
    index_text = index_file.read_text(encoding="utf-8") if index_file.exists() else ""
    if index_file.exists():
        source_text = index_text
    elif status_file.exists():
        source_text = status_file.read_text(encoding="utf-8")
    else:
        source_text = ""
    rows = _tables.parse_phase_table(source_text)

    phase = _resolve_phase(target, rows)
    scope = f"phase {phase}" if phase else f"gameplan {gid}"

    # --- Coverage: open items + exit criteria addressed? ---
    coverage: list[str] = []
    for it in sb.unresolved_open_items(gdir, phase):
        coverage.append(f"open item {it['id']} unresolved: {it['text'][:70]}")
    crit_phases = [phase] if phase else [r.number for r in rows]
    for pn in crit_phases:
        for c in sb.unchecked_exit_criteria(gdir, pn):
            coverage.append(f"phase {pn} exit criterion unchecked: {c['text'][:70]}")
    if not phase:
        incomplete = [r.number for r in rows if r.status != "complete"]
        if incomplete:
            coverage.append(f"phase(s) not complete: {', '.join(incomplete)}")

    # --- Coherence: nothing contradicted, graph reconciled? ---
    coherence = list(sb._drift_warnings(paths, rows))
    pc = sb.pending_cascades(gdir / "_cascade-reports")
    if pc:
        coherence.append(f"{len(pc)} pending cascade report(s): {', '.join(pc)}")

    # --- Grounding: lessons cite their evidence? (D-017) ---
    grounding = _lessons_without_evidence(index_text)

    # --- CALM anti-bias axes (D1): the critique target is self-authored ---
    summary_sec = sections.get_section(index_text, "Per-Phase Completion Summaries") or ""
    self_enhancement = _self_enhancement_flags(
        gdir, phase, summary_sec, has_objective_gap=bool(coverage or coherence))
    authority = _authority_flags(index_text)

    dims = [
        {"name": "Coverage",
         "question": "Is every open item resolved and every exit criterion met?",
         "gaps": coverage},
        {"name": "Coherence",
         "question": "Does the work contradict nothing recorded, with the graph reconciled?",
         "gaps": coherence},
        {"name": "Grounding",
         "question": "Does each active lesson cite the evidence that produced it?",
         "gaps": grounding},
        {"name": "Self-enhancement",
         "question": ("This target is self-authored — a judge tends to over-rate its own "
                      "work (CALM). Is any resolved item closed by a hollow note, or any "
                      "completion claim outrunning a live gap? Scrutinize each PASS you are "
                      "tempted to give."),
         "gaps": self_enhancement},
        {"name": "Authority",
         "question": ("Does any lesson lean on a citation that does not resolve in-repo — a "
                      "paper, URL, or bare 'verified' — rather than provenance you can check "
                      "(commit, path, count)? A citation is a pointer, never an authority."),
         "gaps": authority},
    ]
    for d in dims:
        d["clean"] = not d["gaps"]
    gap_count = sum(len(d["gaps"]) for d in dims)
    return {
        "ok": True,
        "target": scope,
        "dimensions": dims,
        "gap_count": gap_count,
        "summary": (f"self-critique of {scope}: {gap_count} gap(s) across "
                    f"{len(dims)} dimensions"),
        "prompt": (
            "Reference-free self-critique. Coverage / Coherence / Grounding adapt "
            "STORM's rubric; Self-enhancement / Authority add CALM's anti-bias "
            "checklist (the target is your own work, so the bias is yours to catch). "
            "The engine surfaced the gaps it can detect deterministically per "
            "dimension; YOU grade each dimension and decide whether to close the "
            "gaps or accept them with reason. Advisory — it never blocks "
            "(INVARIANT-05); an empty dimension is a pass on that axis."
        ),
    }
