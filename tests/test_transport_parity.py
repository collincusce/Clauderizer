"""Transport parity matrix (2.0 P4): CLI ops vs MCP, equal after normalizing.

Both transports dispatch the same REGISTRY, so parity SHOULD be structural —
this matrix proves it stays true op by op, with identical staged-state
preludes applied to twin repos by DIRECT fixture setup (never via the
transport under test). The comparison is `equal after JSON-normalizing BOTH
payloads` against the explicit allowlist below. What this in-process pair
covers: the CLI path is `ops.run_op` + the JSON round-trip `clauderize ops`
performs; the MCP path is the server's registered callable —
`mcp_server._deliver_aware(name, spec)` over the same REGISTRY — plus the
same JSON round-trip FastMCP's serialization performs. What it deliberately
does NOT cover: FastMCP's wire-level argument coercion and stdio framing,
which the live-handshake probe (mcp_probe / doctor) owns (L-64/L-66).

PINNED DIVERGENCE ALLOWLIST — each entry cites why it exists:
  * ``clauderizer_status`` — the P7 server-side bootstrap (INVARIANT-08's
    hook-less tier): the FIRST MCP tool result on a hook-less host carries a
    one-time status note; the CLI never attaches it. REQUIRED — a test below
    FAILS if this divergence disappears, because its disappearance would mean
    the bootstrap tier silently died.
  * ``cz_state`` — the INVARIANT-10 stamp is env-armed and change-triggered
    off in-memory per-process state, so cross-transport equality is
    unmeasurable per call; stripped before comparison.
  * tuple-vs-list — erased by the JSON normalization itself (both transports
    emit JSON on the wire, so this is normalization, not divergence).
  * absolute repo roots — each transport runs against its own twin repo, so
    result paths differ by root prefix only; roots are rewritten to <ROOT>
    before comparison (path anchoring, not divergence).
"""

from __future__ import annotations

import json
import os
import shutil
from contextlib import contextmanager
from pathlib import Path

import pytest

from clauderizer import mcp_server, ops, session
from clauderizer import mutations as M
from clauderizer import paths as P

GID = "2026-05-01-bootstrap"

#: The matrix: (op, args, prelude) — preludes run identically on both twins via
#: direct mutations/fixture calls, per the vetting condition.
def _prelude_cascade(paths, config):
    M.transition_status(paths, config, id="subsys.auth", to_status="completed")


def _prelude_criteria(paths, config):
    M.set_exit_criteria(paths, gameplan_id=GID, phase="1", criteria=["works end to end"])


def _prelude_open_item(paths, config):
    M.add_open_item(paths, gameplan_id=GID, text="a parity probe item")


def _prelude_finding(paths, config):
    M.add_finding(paths, title="parity probe", severity="low", impact="i",
                  today="2026-07-28")


MATRIX = [
    ("cz_status", {}, None),
    ("cz_gameplans", {}, None),
    ("cz_get", {"id": "D-001"}, None),
    ("cz_list_decisions", {}, None),
    ("cz_list_findings", {}, _prelude_finding),
    ("cz_corpus_health", {}, None),
    ("cz_curate", {}, None),
    ("cz_loop_step", {}, None),
    ("cz_add_lesson", {"text": "parity lesson", "gameplan_id": GID}, None),
    ("cz_add_output", {"phase": "1", "key": "parity_key", "value": "v"}, None),
    ("cz_check_exit_criterion", {"phase": "1", "criterion": "works", "gameplan_id": GID},
     _prelude_criteria),
    ("cz_resolve_open_item", {"id": "O-01", "resolution": "done", "gameplan_id": GID},
     _prelude_open_item),
    ("cz_resolve_cascade",
     {"verdicts": {"feat.login": "no change needed"}, "updates_applied": "none",
      "gameplan_id": GID},
     _prelude_cascade),
    ("cz_dismiss_proposal", {"proposal_id": "parity:000000000000"}, None),
    ("cz_mine_failures", {}, None),   # CLAUDERIZER_TRANSCRIPTS_DIR pinned below
]


@contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _twin(tmp_path: Path, name: str) -> Path:
    src = Path(__file__).parent / "fixtures" / "sample_repo"
    dest = tmp_path / name
    shutil.copytree(src, dest)
    return dest


def _normalize(payload: dict, root: Path) -> dict:
    """The shared normalization: JSON round-trip (what both wires do) + root
    anchoring + the allowlisted strips documented in the module docstring."""
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    raw = raw.replace(str(root), "<ROOT>")
    out = json.loads(raw)
    out.pop("cz_state", None)                      # INVARIANT-10: unmeasurable per call
    out.pop("clauderizer_status", None)            # P7 bootstrap: asserted separately
    return out


def _run_matrix_row(tmp_path, monkeypatch, name, args, prelude):
    tdir = tmp_path / "transcripts"
    tdir.mkdir(exist_ok=True)
    monkeypatch.setenv("CLAUDERIZER_TRANSCRIPTS_DIR", str(tdir))
    payloads = {}
    for side, transport in (("cli", None), ("mcp", None)):
        repo = _twin(tmp_path, f"{name.replace('_', '-')}-{side}")
        paths = P.resolve(repo)
        from clauderizer import config as cfg
        config = cfg.Config.load(paths.config_file)
        if prelude:
            prelude(paths, config)
        with _chdir(repo):
            session.reset()
            if side == "cli":
                got = ops.run_op(name, **args)
            else:
                spec = ops.REGISTRY[name]
                got = mcp_server._deliver_aware(name, spec)(**args)
        payloads[side] = _normalize(got, repo)
    return payloads


@pytest.mark.parametrize("name,args,prelude", MATRIX,
                         ids=[row[0] for row in MATRIX])
def test_cli_and_mcp_payloads_are_equal_after_normalization(
        tmp_path, monkeypatch, name, args, prelude):
    payloads = _run_matrix_row(tmp_path, monkeypatch, name, args, prelude)
    assert payloads["cli"] == payloads["mcp"], (
        f"{name}: transports diverged beyond the pinned allowlist — "
        f"an undocumented divergence is a contract break, document it or fix it")


def test_the_p7_bootstrap_divergence_is_required_not_merely_tolerated(
        tmp_path, monkeypatch):
    """The one divergence that MUST exist: on a hook-less host that has not
    seen status, the first MCP tool result carries clauderizer_status and the
    CLI result does not. If this test fails, the bootstrap tier died silently
    — which is exactly the blindness it exists to prevent (INVARIANT-08)."""
    for var in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SESSION",
                "CLAUDE_PROJECT_DIR"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("CURSOR_TRACE_ID", "parity-probe")   # a hook-less host
    repo = _twin(tmp_path, "bootstrap-probe")
    with _chdir(repo):
        session.reset()
        cli = ops.run_op("cz_gameplans")
        session.reset()
        mcp = mcp_server._deliver_aware("cz_gameplans", ops.REGISTRY["cz_gameplans"])()
    try:
        assert "clauderizer_status" not in cli
        assert "clauderizer_status" in mcp, (
            "the P7 server-side bootstrap no longer attaches status on a "
            "hook-less host — INVARIANT-08's last tier is dead")
        assert "[Clauderizer]" in mcp["clauderizer_status"]
    finally:
        session.reset()


def test_bootstrap_stands_down_on_hook_hosts_and_after_delivery(
        tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDECODE", "1")
    repo = _twin(tmp_path, "hookhost-probe")
    with _chdir(repo):
        session.reset()
        got = mcp_server._deliver_aware("cz_gameplans", ops.REGISTRY["cz_gameplans"])()
        assert "clauderizer_status" not in got   # the hook delivers; no double-inject
    session.reset()
