"""Failure-miner (idea #3, borrowed from Headroom's `headroom learn`).

Scans Claude Code session transcripts (JSONL) for failure->fix patterns and
PROPOSES draft corrections/lessons for the agent to confirm. Read-only,
deterministic, stdlib-only. It is INVOKED (never auto-fires) and PROPOSES
(never writes) — the agent routes accepted proposals through cz_add_correction /
cz_add_lesson (D-015/INVARIANT-05; append-only INVARIANT-03 preserved).

Three detectors, tuned for precision over recall (a noisy proposer would flood
the curated store the memory gauge fights):
  A. tool error -> same-tool success within a small window (a fix);
  B. pytest "N failed" -> later "passed" with no failures (a special tool-fix);
  C. an explicit short user correction ("no, ...", "that's wrong", "instead ...").
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# Error signatures in tool_result CONTENT — is_error is NOT reliably set for
# shell failures (the Bash/PowerShell tools return stderr as content with no
# flag), so content matching is required for recall. Kept specific for precision.
_ERR_SIGNS = re.compile(
    r"(command not found|Exit code [1-9]|Traceback \(most recent call|"
    r"\bfatal:|No such file or directory|: error:|\bSyntaxError\b|"
    r"\bModuleNotFoundError\b|\bAssertionError\b|\bImportError\b|"
    r"\bNameError\b|\b[1-9]\d* failed\b|permission denied)",
    re.IGNORECASE,
)
# [1-9]\d* (not \d+) so a clean "0 failed" summary is NOT read as a failure —
# precision over recall (a passing run must never look like a fix to apply).
_TEST_FAILED = re.compile(r"\b([1-9]\d*) failed\b", re.IGNORECASE)
_TEST_PASSED = re.compile(r"\b(\d+) passed\b", re.IGNORECASE)

# Strong, anchored user-correction cues — precision over recall. Anchored at the
# message start so "no" buried in prose ("there's no rush") does not trip it.
_CORRECTION = re.compile(
    r"^(no[,. ]|nope\b|that'?s wrong|that'?s not (right|correct|what)|"
    r"do(n'?t| not)\b|stop\b|revert\b|undo\b|incorrect\b|wrong\b|"
    r"actually,? ?(no|you|it|that|the)|instead of\b|not what i|"
    r"you should(n'?t| not)? have|why did you|that was (a )?mistake)",
    re.IGNORECASE,
)

# Tools where an error followed by a same-tool success is a meaningful fix.
# Search/read tools are excluded: a no-match grep or a missing-file read is a
# benign "error", not a corrected mistake.
_RETRY_TOOLS = {"Bash", "PowerShell", "Edit", "Write", "NotebookEdit"}

# Tool-protocol hiccups: real "errors" that are agent<->harness usage friction,
# not durable project lessons. Excluded to keep proposals worth a human glance
# (precision tuning, Phase 3 — the curated store must not fill with these).
_NOISE = re.compile(
    r"(has not been read yet|String to replace not found|"
    r"String not found in file|File has already been read|"
    r"content has changed since it was last read|"
    r"old_string|cannot apply edit|Blocked:.{0,40}followed by)",
    re.IGNORECASE,
)


def _iter_records(path: Path):
    # utf-8-sig strips a leading BOM so the first record is not lost; errors=
    # "replace" keeps arbitrary non-UTF-8 bytes in captured tool output from
    # aborting the decode (real transcripts carry raw shell stdout, and the
    # decode happens here during iteration — outside the json.loads try below).
    # Only dict records are yielded: a valid-JSON-but-non-object line (42, "x",
    # [1,2]) is skipped, not crashed — full schema-drift tolerance (O-03).
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except (ValueError, TypeError):
                continue  # tolerate partial/garbled lines (schema drift, O-03)
            if isinstance(obj, dict):
                yield obj


def _content(rec: dict):
    msg = rec.get("message") if isinstance(rec.get("message"), dict) else None
    return (msg or {}).get("content", rec.get("content"))


def _blocks(rec: dict) -> list[dict]:
    c = _content(rec)
    return [b for b in c if isinstance(b, dict)] if isinstance(c, list) else []


def _user_text(rec: dict) -> str | None:
    """The human text of a user turn, or None for tool-result-bearing turns."""
    if rec.get("type") != "user":
        return None
    c = _content(rec)
    return c if isinstance(c, str) else None


def _result_text(block: dict) -> str:
    c = block.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        # Structured content blocks: only string `text` fields contribute. A
        # non-str text (e.g. {"text": 123}) is skipped, not str-joined (which
        # would raise) — shape tolerance past JSON validity (O-03).
        return " ".join(b["text"] for b in c
                        if isinstance(b, dict) and isinstance(b.get("text"), str))
    return ""


def _is_error_result(block: dict) -> bool:
    if block.get("is_error"):
        return True
    return bool(_ERR_SIGNS.search(_result_text(block)))


def mine(path, *, window: int = 8, max_user_len: int = 600) -> list[dict]:
    """Return a list of proposal dicts mined from the transcript at ``path``.

    Each proposal: ``{kind, evidence, draft}`` where ``draft`` is suggested
    cz_add_correction arguments for the agent to confirm and complete.
    """
    path = Path(path)
    tool_uses: list[tuple[int, str, str]] = []   # (seq, id, name)
    results: dict[str, dict] = {}                # id -> {is_error, text}
    corrections: list[str] = []
    seq = 0
    for rec in _iter_records(path):
        ut = _user_text(rec)
        if ut is not None:
            head = ut.strip()
            if 0 < len(head) <= max_user_len and _CORRECTION.match(head):
                corrections.append(head)
        for b in _blocks(rec):
            bt = b.get("type")
            if bt == "tool_use":
                seq += 1
                tool_uses.append((seq, b.get("id"), b.get("name")))
            elif bt == "tool_result":
                rid = b.get("tool_use_id")
                # Must be a str: it is used as a dict key, so a malformed
                # list/dict id would raise "unhashable type" — skip it (O-03).
                if isinstance(rid, str):
                    results[rid] = {"is_error": _is_error_result(b),
                                    "text": _result_text(b)}

    proposals: list[dict] = []
    seen: set[tuple] = set()

    # Detectors A + B: errored tool -> same-tool success within `window`.
    for idx, (s, tid, name) in enumerate(tool_uses):
        if name not in _RETRY_TOOLS:
            continue
        res = results.get(tid)
        if not res or not res["is_error"]:
            continue
        if _NOISE.search(res["text"]):
            continue  # tool-protocol hiccup, not a project lesson
        for (s2, tid2, name2) in tool_uses[idx + 1: idx + 1 + window]:
            if name2 != name:
                continue
            res2 = results.get(tid2)
            if res2 and not res2["is_error"]:
                err = res["text"].strip()
                key = (name, err[:80])
                if key in seen:
                    break
                seen.add(key)
                is_test = bool(_TEST_FAILED.search(err))
                kind = "test-fix" if is_test else "tool-fix"
                proposals.append({
                    "kind": kind,
                    "tool": name,
                    "evidence": f"{name} errored then a later {name} call succeeded",
                    "error_excerpt": _excerpt(err),
                    "draft": {
                        "gameplan_said": "(n/a — execution-time error, not a plan divergence)",
                        "actually": f"A {name} call failed ({_excerpt(err, 120)}) and was "
                                    f"corrected by a later successful {name} call.",
                        "why": "(confirm the root cause)",
                        "lesson": "(optional: the durable takeaway, if any)",
                    },
                })
                break

    # Detector C: explicit short user correction.
    for q in corrections:
        key = ("user", q[:80])
        if key in seen:
            continue
        seen.add(key)
        proposals.append({
            "kind": "user-correction",
            "evidence": "user message opened with a correction cue",
            "error_excerpt": _excerpt(q),
            "draft": {
                "gameplan_said": "(what the agent did/assumed)",
                "actually": _excerpt(q, 200),
                "why": "(confirm why the original was wrong)",
                "lesson": "(optional: the durable takeaway)",
            },
        })

    return proposals


def _excerpt(text: str, n: int = 160) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"


def mine_dir(transcripts_dir, **kw) -> dict:
    """Mine every ``*.jsonl`` under a directory; return ``{file: [proposals]}``."""
    d = Path(transcripts_dir)
    out: dict[str, list[dict]] = {}
    for p in sorted(d.glob("*.jsonl")):
        try:
            out[p.name] = mine(p, **kw)
        except Exception:  # noqa: BLE001
            # Best-effort isolation: one pathological transcript must never abort
            # the whole batch. Known shapes are handled at the source (above); this
            # is the net for any unforeseen drift (O-03 — degrade, don't crash).
            continue
    return out
