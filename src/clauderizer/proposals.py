"""Persistent triage for advisory modernize proposals (D-052).

`modernize.report()` re-derives its advisory proposals on every run and never
writes anything (D-042) — so a proposal can neither be dismissed nor tracked, and
once a corpus is version-current the digest stops surfacing them at all. This
layer adds the missing state, without breaking the two-tier contract:

- each proposal carries a STABLE, content-derived ``id`` (a materially-changed
  proposal — e.g. a newly-declared gate — hashes to a new id and re-surfaces);
- a per-user, gitignored ledger (``.clauderizer/proposals.local.toml``) records
  the user's verdict: **dismissed** (hide until it materially changes) or
  **deferred** (snoozed to a date). **handle** needs no record — doing the work
  resolves the underlying condition, so the detector stops emitting it.

Read/filter here is pure; the ledger writes are the blessed cz_* tools' job. The
engine only ever SURFACES the pending set — the agent decides (INVARIANT-05)."""

from __future__ import annotations

import datetime
import hashlib
import tomllib
from pathlib import Path

from .markdown import writer
from .paths import RepoPaths

LEDGER_NAME = "proposals.local.toml"


def ledger_path(paths: RepoPaths) -> Path:
    return paths.clauderizer_dir / LEDGER_NAME


def proposal_id(kind: str, *parts: object) -> str:
    """``<kind>:<12-hex>`` derived from ``kind`` + the identifying parts. The kind
    prefix keeps ids legible in the ledger; the hash makes a materially-changed
    proposal (different parts) a genuinely different id."""
    raw = "\x1f".join([kind, *(str(p) for p in parts)])
    return f"{kind}:{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]}"


def load_ledger(paths: RepoPaths) -> dict[str, dict[str, str]]:
    """``{"dismissed": {id: date}, "deferred": {id: until-date}}``. A missing or
    malformed ledger reads as empty (triage is best-effort, never fatal)."""
    p = ledger_path(paths)
    if not p.exists():
        return {"dismissed": {}, "deferred": {}}
    try:
        with p.open("rb") as fh:
            raw = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return {"dismissed": {}, "deferred": {}}
    return {
        "dismissed": {str(k): str(v) for k, v in dict(raw.get("dismissed", {})).items()},
        "deferred": {str(k): str(v) for k, v in dict(raw.get("deferred", {})).items()},
    }


def _dump_ledger(led: dict) -> str:
    lines = [
        "# Clauderizer proposal-triage ledger — per-user, gitignored (D-052).",
        "# 'dismissed' hides a proposal until it materially changes; 'deferred'",
        "# snoozes it to a date. Delete an entry to see that proposal again.",
        "",
    ]
    for table in ("dismissed", "deferred"):
        lines.append(f"[{table}]")
        for k in sorted(led.get(table, {})):
            lines.append(f'"{k}" = "{led[table][k]}"')   # ids are [a-z_]+:[0-9a-f]+ — quote-safe
        lines.append("")
    return "\n".join(lines) + "\n"


def _write_ledger(paths: RepoPaths, led: dict) -> None:
    p = ledger_path(paths)
    writer.refuse_if_symlink(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_dump_ledger(led), encoding="utf-8")


def _today() -> str:
    return datetime.date.today().isoformat()


def dismiss(paths: RepoPaths, pid: str) -> dict:
    led = load_ledger(paths)
    led["dismissed"][pid] = _today()
    led["deferred"].pop(pid, None)
    _write_ledger(paths, led)
    return {"ok": True, "id": pid, "verdict": "dismissed",
            "summary": f"dismissed proposal {pid} — it won't re-surface until it materially changes"}


def defer(paths: RepoPaths, pid: str, days: int = 7) -> dict:
    days = max(1, int(days))
    until = (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
    led = load_ledger(paths)
    led["deferred"][pid] = until
    led["dismissed"].pop(pid, None)
    _write_ledger(paths, led)
    return {"ok": True, "id": pid, "verdict": "deferred", "until": until,
            "summary": f"deferred proposal {pid} until {until}"}


def is_suppressed(led: dict, pid: str, today: str | None = None) -> bool:
    """True when ``pid`` is dismissed, or deferred to a date still in the future."""
    if pid in led.get("dismissed", {}):
        return True
    until = led.get("deferred", {}).get(pid)
    if not until:
        return False
    return (today or _today()) < until


def filter_pending(proposals: list[dict], led: dict, today: str | None = None) -> list[dict]:
    """Proposals the user has not dismissed or actively deferred."""
    return [p for p in proposals if not is_suppressed(led, str(p.get("id", "")), today)]
