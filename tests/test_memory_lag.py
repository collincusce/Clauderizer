"""Memory-lag detection: does anything notice when the tracker stops describing
the repo? (H-22, gameplan 2026-07-25 Phase 0)

The motivating failure is real and is in this repo's own history: 1.14.0
implemented, tested and pushed phases 5 and 6 across eight commits while the
phase table still read "not started". Every other discipline has a detector;
this one had none. ``test_historical_1_14_0_drift_would_have_fired`` is the
honest test — it runs the detector against that exact history and asserts it
would have caught the failure that motivated building it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from clauderizer import config as cfg
from clauderizer import paths as P
from clauderizer.rituals import _tables, memory_lag
from clauderizer.rituals import status_bundle as S

REPO_ROOT = Path(__file__).resolve().parents[1]

# The 1.14.0 drift window, measured from this repo (source of truth, L-33):
#   54290e2  close(P4) — the last tracker write; phases 5 and 6 read NOT STARTED
#   eac1c9a  fix(P5, core) — src/ + tests/, landed with the tracker still stale
DRIFT_COMMIT = "eac1c9a"
DRIFT_GAMEPLAN = "2026-07-24-evidence-traversal-1-14-0"


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


GAMEPLAN = "2026-05-01-bootstrap"


def _set_phase_1(repo: Path, status: str) -> None:
    """Rewrite phase 1's status cell in BOTH tracker files the parser accepts."""
    gdir = repo / "docs" / "gameplans" / GAMEPLAN
    for name in ("CHAT-HANDOFF-INDEX.md", "PHASE-STATUS.md"):
        f = gdir / name
        if not f.exists():
            continue
        out = []
        for line in f.read_text(encoding="utf-8").splitlines():
            cells = line.split("|")
            if line.strip().startswith("|") and len(cells) > 3 and cells[1].strip() == "1":
                cells[3] = f" {status} "
                line = "|".join(cells)
            out.append(line)
        f.write_text("\n".join(out) + "\n", encoding="utf-8")


def _lagging_repo(temp_repo: Path) -> Path:
    """A repo whose tracker says phase 1 has not begun, with code landed after."""
    _git_repo(temp_repo)
    _set_phase_1(temp_repo, "⬜ NOT STARTED")
    _commit(temp_repo, "tracker: phase 1 not started")   # <- the anchor
    (temp_repo / "src").mkdir(exist_ok=True)
    (temp_repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    _commit(temp_repo, "feat: implement phase 1 without telling the tracker")
    return temp_repo


def _bundle(repo: Path) -> dict:
    paths = P.resolve(repo)
    return S.compute(paths, cfg.Config.load(paths.config_file))


# --- the detector -------------------------------------------------------------

def test_lag_detected_when_tracker_reads_unstarted_but_code_landed(temp_repo):
    bundle = _bundle(_lagging_repo(temp_repo))
    lag = bundle.get("memory_lag")
    assert lag, "tracker said phase 1 had not begun while a src/ commit landed"
    assert lag["phase"] == "1"
    assert lag["commits"] == 1
    assert lag["state"] == "not_started"


def test_digest_names_the_phase_and_the_commit_count(temp_repo):
    digest = S.render_digest(_bundle(_lagging_repo(temp_repo)))
    assert "⚠ Memory lag:" in digest
    assert 'phase 1 "Wire it up"' in digest
    assert "1 non-docs commit landed" in digest
    assert "cz_transition_phase" in digest


def test_silent_once_the_tracker_records_the_work(temp_repo):
    """The same repo, with the tracker written AFTER the code — no signal."""
    repo = _lagging_repo(temp_repo)
    _set_phase_1(repo, "🟡 IN PROGRESS")
    _commit(repo, "tracker: phase 1 in progress")
    assert _bundle(repo).get("memory_lag") is None


def test_silent_for_an_in_progress_phase(temp_repo):
    """The scope gate, asserted rather than assumed: an in_progress phase is
    SUPPOSED to accumulate commits, so the detector must not cry wolf there."""
    repo = _git_repo(temp_repo)          # fixture ships phase 1 IN PROGRESS
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    _commit(repo, "feat: ordinary in-phase work")
    assert _bundle(repo).get("memory_lag") is None


def test_docs_only_commits_are_not_work(temp_repo):
    """A commit touching only the paths Clauderizer owns is bookkeeping, not
    work the tracker should have known about."""
    _git_repo(temp_repo)
    _set_phase_1(temp_repo, "⬜ NOT STARTED")
    _commit(temp_repo, "tracker: phase 1 not started")
    (temp_repo / "docs" / "NOTES.md").write_text("# notes\n", encoding="utf-8")
    _commit(temp_repo, "docs: a note")
    assert _bundle(temp_repo).get("memory_lag") is None


def test_no_git_is_no_claim(temp_repo):
    """Without git there is no evidence, so there is no assertion (D-065)."""
    _set_phase_1(temp_repo, "⬜ NOT STARTED")
    assert _bundle(temp_repo).get("memory_lag") is None


# --- INVARIANT-08: zero bytes when there is no lag ----------------------------

def test_digest_byte_identical_when_there_is_no_lag(temp_repo):
    """A live git history must not change a single byte of the digest while
    memory is current — the detector is conditionally emitted, not merely quiet
    (INVARIANT-08 keeps injected status focused and minimal)."""
    repo = _git_repo(temp_repo)
    # D-070 P1: "ordinary in-phase work" means a LIVE session holds the phase —
    # stamp this process as the claimant, exactly as transition_phase now does.
    # Without a live claimant this repo shape is honestly an interrupted
    # session and the digest SHOULD say so (test_interrupted_session.py).
    from clauderizer import session_ledger
    session_ledger.stamp(P.resolve(repo), GAMEPLAN, "1", today="2026-07-27")
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    _commit(repo, "feat: ordinary in-phase work")
    with_git = S.render_digest(_bundle(repo), tools=["cz_status"])

    subprocess.run(["rm", "-rf", str(repo / ".git")], check=True)
    without_git = S.render_digest(_bundle(repo), tools=["cz_status"])

    assert with_git == without_git
    assert "Memory lag" not in with_git


# --- pre-flight surfaces the same signal, advisory only -----------------------

def _preflight(repo: Path):
    from clauderizer.profiles.detect import detect
    from clauderizer.rituals import preflight

    paths = P.resolve(repo)
    config = cfg.Config.load(paths.config_file)
    profile, _ = detect(repo)
    return preflight.run(paths, config, profile, runner=lambda cmd, cwd: (0, ""))


def test_preflight_warns_on_memory_lag_and_never_fails(temp_repo):
    result = _preflight(_lagging_repo(temp_repo))
    lag = [c for c in result.checks if c.name == "memory_lag"]
    assert lag, "pre-flight must surface the same signal the digest does"
    assert lag[0].status == "warn"
    assert "phase 1" in lag[0].detail
    assert result.passed, "advisory only — it must never fail the ritual (INVARIANT-05)"
    assert "WARNINGS" in result._summary()


def test_preflight_check_list_unchanged_when_memory_is_current(temp_repo):
    """No lag, no check — the report is byte-identical to before this feature."""
    repo = _git_repo(temp_repo)
    assert not [c for c in _preflight(repo).checks if c.name == "memory_lag"]


def test_digest_and_preflight_word_the_finding_identically(temp_repo):
    """One claim, one sentence, two surfaces — the seam a test has to pin (L-55)."""
    repo = _lagging_repo(temp_repo)
    claim = memory_lag.describe(_bundle(repo)["memory_lag"])
    assert claim in S.render_digest(_bundle(repo))
    assert claim in [c for c in _preflight(repo).checks if c.name == "memory_lag"][0].detail


# --- the honest test: this repo's own history ---------------------------------

@pytest.fixture
def history_checkout(tmp_path: Path) -> Path:
    """An ISOLATED local clone of this repo checked out at the drift commit.

    A clone, not a worktree: nothing in the real repo's .git is written, so the
    isolation is structural rather than promised (L-29). Skips rather than fails
    when the history is unreachable — a shallow CI clone has no eac1c9a.
    """
    probe = subprocess.run(["git", "cat-file", "-e", f"{DRIFT_COMMIT}^{{commit}}"],
                           cwd=str(REPO_ROOT), capture_output=True)
    if probe.returncode != 0:
        pytest.skip(f"{DRIFT_COMMIT} unreachable (shallow clone) — history check skipped")
    dest = tmp_path / "history"
    _run(REPO_ROOT, "clone", "--quiet", "--local", "--no-checkout", str(REPO_ROOT), str(dest))
    _run(dest, "checkout", "--quiet", "--detach", DRIFT_COMMIT)
    return dest


def test_historical_1_14_0_drift_would_have_fired(history_checkout):
    """Criterion 7. At eac1c9a the 1.14.0 tracker read phases 5 and 6 NOT
    STARTED while implementation commits landed. The phase state is PARSED from
    the tracker as it stood at that commit — nothing here is hand-fed — so this
    exercises the whole chain against the failure that motivated it.
    """
    paths = P.resolve(history_checkout)
    gdir = paths.gameplan_dir(DRIFT_GAMEPLAN)
    rows = _tables.parse_phase_table_full((gdir / "PHASE-STATUS.md").read_text(encoding="utf-8"))
    target = next(r for r in rows if r.status != "complete")

    assert target.number == "5" and target.status == "not_started", (
        "source-of-truth guard: the tracker at this commit must read phase 5 unstarted")

    lag = memory_lag.detect(
        paths, DRIFT_GAMEPLAN,
        {"number": target.number, "name": target.name}, target.status)

    assert lag is not None, "the detector must fire on the failure that motivated it"
    assert lag["phase"] == "5"
    assert lag["commits"] >= 1
    assert lag["anchor"]
    assert "phase 5" in memory_lag.describe(lag)
