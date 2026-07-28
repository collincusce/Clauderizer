"""Interrupted-session detection: work landed, the closing writes never ran
(D-070 P1, intent-postmortem-with-backstop-landings).

Pins the fire-quiet geometry from the refuter verdicts — fire ONLY when the
phase is in_progress AND >=1 non-docs commit landed since the tracker anchor
AND every closing residue is absent; ANY closing artifact keeps it quiet.
Evidence-absent (no git, no anchor, zero work commits) means no claim (D-065).
One voice (L-55/L-65): the single describe() subsumes the memory-lag claim and
explains the clean_tree FAIL and do-phase STOP interactions — and a greppable
assertion proves no fourth phrasing exists under src/.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from clauderizer import config as cfg
from clauderizer import paths as P
from clauderizer.rituals import interrupted, memory_lag, preflight
from clauderizer.rituals import status_bundle as S

REPO_ROOT = Path(__file__).resolve().parents[1]
GAMEPLAN = "2026-05-01-bootstrap"


def _run(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=str(repo), capture_output=True,
                       encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 0, f"git {args}: {r.stderr}"
    return r.stdout.strip()


def _commit(repo: Path, message: str) -> None:
    _run(repo, "add", "-A")
    _run(repo, "commit", "-q", "--no-gpg-sign", "-m", message)


def _git_repo(repo: Path) -> Path:
    _run(repo, "init", "-q", "-b", "main")
    _run(repo, "config", "user.email", "test@example.invalid")
    _run(repo, "config", "user.name", "Test")
    _run(repo, "config", "commit.gpgsign", "false")
    _commit(repo, "scaffold")
    return repo


def _set_phase_1(repo: Path, status: str) -> None:
    gdir = repo / "docs" / "gameplans" / GAMEPLAN
    for name in ("CHAT-HANDOFF-INDEX.md", "PHASE-STATUS.md"):
        p = gdir / name
        if not p.exists():
            continue
        out = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("| 1 |"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                cells[2] = status
                line = "| " + " | ".join(cells) + " |"
            out.append(line)
        p.write_text("\n".join(out) + "\n", encoding="utf-8")


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


@pytest.fixture
def interrupted_repo(temp_repo: Path) -> Path:
    """in_progress phase 1 (the fixture's own state — the scaffold commit IS
    the tracker anchor), then a src/ work commit; none of phase 1's closing
    writes exist."""
    repo = _git_repo(temp_repo)
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "thing.py").write_text("x = 1\n", encoding="utf-8")
    _commit(repo, "feat: real work")
    return repo


def _target():
    return {"number": "1", "name": "phase one"}


def _detect(repo):
    paths, _ = _ctx(repo)
    return interrupted.detect(paths, GAMEPLAN, _target(), "in_progress")


# --- fire: all residues absent, work landed -----------------------------------

def test_fires_with_all_closing_residues_absent(interrupted_repo):
    rec = _detect(interrupted_repo)
    assert rec is not None
    assert rec["commits"] >= 1
    assert "cz_add_phase_summary" in rec["never_ran"]
    assert "cz_add_output" in rec["never_ran"]
    assert rec["scratch"] is False


def test_scratch_flag_true_iff_tree_dirty(interrupted_repo):
    (interrupted_repo / "scratch.tmp").write_text("wip", encoding="utf-8")
    rec = _detect(interrupted_repo)
    assert rec is not None and rec["scratch"] is True


# --- quiet: any closing artifact present --------------------------------------

def test_quiet_when_phase_summary_exists(interrupted_repo):
    idx = interrupted_repo / "docs" / "gameplans" / GAMEPLAN / "CHAT-HANDOFF-INDEX.md"
    idx.write_text(idx.read_text(encoding="utf-8")
                   + "\n## Per-Phase Completion Summaries\n\n### Phase 1\nDone-ish.\n",
                   encoding="utf-8")
    assert _detect(interrupted_repo) is None


def test_quiet_when_outputs_block_exists(interrupted_repo):
    st = interrupted_repo / "docs" / "gameplans" / GAMEPLAN / "PHASE-STATUS.md"
    st.write_text(st.read_text(encoding="utf-8")
                  + "\n### Phase 1 Outputs\n```\nK: v\n```\n", encoding="utf-8")
    assert _detect(interrupted_repo) is None


def test_quiet_when_closing_handoff_artifact_exists(interrupted_repo):
    """Phase 1 is the fixture's LAST phase, so its closing handoff artifact is
    the post-mortem; for a mid-gameplan phase it is the next phase's handoff
    (same residue slot in _closing_residues)."""
    gdir = interrupted_repo / "docs" / "gameplans" / GAMEPLAN
    (gdir / "POST-MORTEM.md").write_text("# Post-mortem\n", encoding="utf-8")
    assert _detect(interrupted_repo) is None


# --- quiet: evidence absent = no claim (D-065) --------------------------------

def test_quiet_with_zero_work_commits(temp_repo):
    repo = _git_repo(temp_repo)   # scaffold commit = anchor; nothing after
    assert _detect(repo) is None


def test_quiet_without_git_or_anchor(temp_repo):
    assert _detect(temp_repo) is None          # no git repo at all


def test_quiet_for_non_in_progress_states(interrupted_repo):
    paths, _ = _ctx(interrupted_repo)
    for state in ("ready", "not_started", "blocked", "deferred", "complete"):
        assert interrupted.detect(paths, GAMEPLAN, _target(), state) is None


# --- digest + preflight: one line, one voice ----------------------------------

def test_digest_byte_identical_without_and_one_line_with(interrupted_repo):
    paths, config = _ctx(interrupted_repo)
    config.active_gameplan = GAMEPLAN
    config.focus = GAMEPLAN
    bundle = S.compute(paths, config)
    assert bundle.get("interrupted") is not None
    digest = S.render_digest(bundle)
    line = "⚠ Interrupted session: " + interrupted.describe(bundle["interrupted"])
    assert line in digest
    stripped = dict(bundle)
    stripped.pop("interrupted")
    assert line not in S.render_digest(stripped)


def test_preflight_warns_never_fails_and_absent_when_quiet(interrupted_repo):
    paths, config = _ctx(interrupted_repo)
    config.active_gameplan = GAMEPLAN
    config.focus = GAMEPLAN
    config.preflight_checks = ["deps_spotcheck"]
    from clauderizer.profiles.detect import Profile
    profile = Profile(name="generic", commands={}, baseline_test_regex="")
    res = preflight.run(paths, config, profile, runner=lambda c, w: (0, "")).to_dict()
    gate = next(c for c in res["checks"] if c["name"] == "interrupted_session")
    assert gate["status"] == "warn"
    assert res["passed"] is True
    # quiet repo: the check row is absent entirely (INVARIANT-07)
    idx = paths.gameplan_dir(GAMEPLAN) / "CHAT-HANDOFF-INDEX.md"
    idx.write_text(idx.read_text(encoding="utf-8")
                   + "\n## Per-Phase Completion Summaries\n\n### Phase 1\nok\n",
                   encoding="utf-8")
    res2 = preflight.run(paths, config, profile, runner=lambda c, w: (0, "")).to_dict()
    assert all(c["name"] != "interrupted_session" for c in res2["checks"])


def test_one_voice_wording_subsumption_and_uniqueness(interrupted_repo):
    """The describe() must carry the memory-lag claim, the clean_tree FAIL and
    the do-phase STOP explanation — and its key phrase must exist EXACTLY once
    under src/ so no surface can fork the wording (L-55/L-65 greppable pin)."""
    rec = _detect(interrupted_repo)
    rec["scratch"] = True
    text = interrupted.describe(rec)
    assert "the memory is behind the repo" in text          # subsumes memory_lag
    assert "clean_tree" in text and "STOP" in text          # downstream frictions
    assert "a backstop is a signal" in text
    src = REPO_ROOT / "src"
    hits = [p for p in src.rglob("*.py")
            if "likely an interrupted session" in p.read_text(encoding="utf-8")]
    assert [p.name for p in hits] == ["interrupted.py"]


def test_disjoint_with_memory_lag_by_predicate(interrupted_repo):
    """The two detectors can never both fire for one phase: memory-lag needs an
    UNSTARTED state, this one needs in_progress."""
    paths, _ = _ctx(interrupted_repo)
    for state in ("in_progress", "ready", "not_started"):
        lag = memory_lag.detect(paths, GAMEPLAN, _target(), state)
        intr = interrupted.detect(paths, GAMEPLAN, _target(), state)
        assert not (lag and intr)


# --- the liveness gate: one voice per repo state ------------------------------

def _stamp(paths, **over):
    import json
    import socket
    from clauderizer import session_ledger
    rec = {"kind": "session", "gameplan": GAMEPLAN, "phase": "1",
           "pid": 4194000, "start": None, "host": socket.gethostname(),
           "agent": "claude-code", "transport": "mcp", "at": "2026-07-27"}
    rec.update(over)
    p = paths.clauderizer_dir / session_ledger.LEDGER
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def test_quiet_when_the_claimant_is_provably_alive(interrupted_repo):
    """A live claimant means ordinary mid-phase work — an active session's own
    digest must stay byte-identical while it works (INVARIANT-08)."""
    import os
    paths, _ = _ctx(interrupted_repo)
    _stamp(paths, pid=os.getppid())          # a live process that is not us
    assert _detect(interrupted_repo) is None


def test_quiet_for_the_viewing_session_itself(interrupted_repo):
    import os
    paths, _ = _ctx(interrupted_repo)
    _stamp(paths, pid=os.getpid(), transport="unknown")
    assert _detect(interrupted_repo) is None


def test_dead_claimant_defers_to_stranded_one_voice(interrupted_repo):
    """A provably dead claimant is stranded.py's finding — exactly one of the
    two detectors speaks for any repo state."""
    import subprocess
    import sys
    from clauderizer.rituals import stranded
    paths, _ = _ctx(interrupted_repo)
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    _stamp(paths, pid=child.pid)
    assert _detect(interrupted_repo) is None
    assert stranded.detect(paths, GAMEPLAN, _target(), "in_progress") is not None


def test_fires_when_the_ledger_cannot_grade(interrupted_repo):
    """cli-transport stamp (probe inconclusive): the git-evidence backstop is
    exactly for what the ledger cannot vouch for."""
    import subprocess
    import sys
    paths, _ = _ctx(interrupted_repo)
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    _stamp(paths, pid=child.pid, transport="cli")
    assert _detect(interrupted_repo) is not None


# --- refusal journal ----------------------------------------------------------

def test_refused_write_op_is_journaled_on_both_paths(temp_repo, monkeypatch):
    monkeypatch.chdir(temp_repo)
    from clauderizer import ops as O
    res = O.run_op("cz_transition_phase", phase_n="1", to_status="nonsense")
    assert res["ok"] is False
    paths = P.resolve(temp_repo)
    journal = paths.clauderizer_dir / "refusals.jsonl"
    assert journal.exists()
    import json
    lines = [json.loads(ln) for ln in journal.read_text(encoding="utf-8").splitlines()]
    assert lines[-1]["op"] == "cz_transition_phase"
    assert lines[-1]["kind"] == "refusal"
    # the MCP path (direct REGISTRY access) journals identically
    O.REGISTRY["cz_transition_phase"].fn(phase_n="1", to_status="nonsense")
    lines2 = journal.read_text(encoding="utf-8").splitlines()
    assert len(lines2) == len(lines) + 1


def test_successful_and_read_ops_never_journal(temp_repo, monkeypatch):
    monkeypatch.chdir(temp_repo)
    from clauderizer import ops as O
    O.run_op("cz_status")
    paths = P.resolve(temp_repo)
    assert not (paths.clauderizer_dir / "refusals.jsonl").exists()
