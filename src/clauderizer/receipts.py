"""Seen-vs-open engagement receipts (D-073) — per-machine, disposable, advisory.

The digest's open-findings/open-items lines re-bill every unresolved id every
session with no engagement axis: a register nobody has read is indistinguishable
from one read and deliberately left open. Receipts add that axis as pure
labeling — the D-069 engagement detector, never a filter (D-068 drop-nothing;
both buckets always render every id).

Receipts land ONLY on genuine engagement — cz_get success and the
cz_resolve_finding / cz_resolve_open_item / cz_check_exit_criterion writes —
never from handoff/phase-context assembly (an id whose body rode in a bundle the
agent may never have attended must not read as seen). The append rides the ops
REGISTRY seam (the refusal-journal precedent), so library read functions,
fixtures and embedders stay byte-free (C-02).

Constitution (D-073's five bounds):
  * lock-free O_APPEND single-line sorted-keys JSONL — no write lock (L-03);
  * best-effort at every call site — a failed append never breaks the read or
    the resolve it rides on;
  * ``load_seen`` is torn-line-tolerant (the telemetry ``read_events``
    convention) and a missing/garbled sidecar reads as no receipts;
  * per-machine and gitignored (D-067): losing the file loses engagement labels,
    never canonical memory — machine B inherits nothing from machine A, the same
    personal-not-team framing D-052 gave dismissals;
  * reader attribution (``session.detect_session_agent``) is receipt METADATA
    for the D-064 matrix and forensics — the digest split is ANY-reader.

Open-item receipts are gameplan-qualified (``<gameplan_id>:O-NN``) because O-NN
numbers restart per gameplan; corpus ids (D-/INVARIANT-/H-/L-) are global and
recorded bare. cz_check_exit_criterion engagement is recorded under the
synthetic ``criteria:<gameplan_id>:<phase>`` key — collision-free with register
ids by construction, so the digest split ignores it and the matrix can still
count the engagement.
"""

from __future__ import annotations

import json
from datetime import date as _date

from .paths import RepoPaths

RECEIPTS_NAME = "seen.local.jsonl"


def _today(today: str | None) -> str:
    return today or _date.today().isoformat()


def record_seen(paths: RepoPaths, ids, *, via: str, reader: str | None = None,
                today: str | None = None) -> dict | None:
    """Append one receipt line for ``ids`` not already receipted on this machine.

    Idempotent per id (any reader): an id already carrying a receipt is skipped,
    which bounds the sidecar to O(engaged ids) in steady state; the via/reader of
    the FIRST engagement is what the line retains. Returns the appended record,
    or None when every id was already receipted (nothing written). Callers wrap
    this best-effort — it may raise on an unwritable sidecar."""
    from .markdown import writer

    want = [str(i).strip() for i in (ids or []) if str(i).strip()]
    if not want:
        return None
    seen = load_seen(paths)
    fresh = [i for i in want if i not in seen]
    if not fresh:
        return None
    if reader is None:
        from .session import detect_session_agent
        reader = detect_session_agent() or "unknown"
    rec = {"kind": "seen", "date": _today(today), "via": via,
           "reader": reader, "ids": fresh}
    p = paths.seen_file
    writer.refuse_if_symlink(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    # One compact sorted-keys line per call; "a" opens O_APPEND, and the single
    # write keeps concurrent same-machine writers line-atomic in practice — the
    # tolerant reader makes the worst interleaving a skipped line, never lost
    # canonical state (receipts are labels).
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    return rec


def load_seen(paths: RepoPaths) -> dict[str, dict]:
    """``{id: {first_seen, last_seen, readers, via}}`` merged from the sidecar.

    Missing file, torn lines and non-receipt garbage all read as no receipts —
    the sidecar is disposable state and its reader degrades, never crashes."""
    p = paths.seen_file
    if not p.exists():
        return {}
    out: dict[str, dict] = {}
    try:
        with open(p, encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except (ValueError, TypeError):
                    continue
                if not isinstance(obj, dict) or obj.get("kind") != "seen":
                    continue
                ids = obj.get("ids")
                if not isinstance(ids, list):
                    continue
                date = str(obj.get("date") or "")
                reader = str(obj.get("reader") or "unknown")
                via = str(obj.get("via") or "")
                for i in ids:
                    i = str(i).strip()
                    if not i:
                        continue
                    rec = out.setdefault(i, {"first_seen": date, "last_seen": date,
                                             "readers": [], "via": via})
                    rec["last_seen"] = date or rec["last_seen"]
                    if reader not in rec["readers"]:
                        rec["readers"].append(reader)
    except OSError:
        return {}
    return out


def split_seen(ids, seen: dict[str, dict], *, prefix: str = "") -> tuple[list, list]:
    """Partition ``ids`` into ``(never_engaged, engaged_but_open)`` — any-reader.

    Order-preserving and exhaustive: every id lands in exactly one bucket
    (the D-068 drop-nothing assertion is checkable on the output). ``prefix``
    qualifies the lookup key (open items receipt as ``<gid>:O-NN``) while the
    returned buckets keep the bare display ids."""
    never, engaged = [], []
    for i in ids:
        (engaged if f"{prefix}{i}" in seen else never).append(i)
    return never, engaged
