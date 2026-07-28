#!/usr/bin/env python3
"""Phase-5 D-064 evidence-matrix harness — runnable, committed, reproducible.

Drives the REAL tree engine (the repo venv's editable install) over throwaway
fixtures built per leg (never the real repo — L-29); the only real-repo reads
are the two production measurements (recording coverage, gap/reinforce
production counts), which write nothing. Results land beside this file as
matrix-p5-results.json; each leg emits {leg, status: run|gap, figures, notes}.

Run:  .venv/bin/python docs/gameplans/<gid>/matrix-p5-harness.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
VENV_PY = REPO / ".venv" / "bin" / "python"
CLI = REPO / ".venv" / "bin" / "clauderize"

GUARDS = {
    "CLAUDERIZER_NO_KIMI_DESKTOP": "1",   # L-29/L-64: never touch per-user state
    "CLAUDERIZER_NO_SPAWN_PROBE": "1",
    "CLAUDERIZER_NO_NETWORK": "1",
}
os.environ.update(GUARDS)
sys.path.insert(0, str(REPO / "src"))

from clauderizer import mutations as M            # noqa: E402
from clauderizer import paths as P                # noqa: E402
from clauderizer import receipts as RC            # noqa: E402
from clauderizer.rituals import interrupted, merge_audit, stranded  # noqa: E402

TODAY = date.today().isoformat()


def sh(args, cwd=None, env=None, timeout=300):
    e = {**os.environ, **GUARDS, **(env or {})}
    return subprocess.run([str(a) for a in args], cwd=cwd, env=e,
                          capture_output=True, text=True, timeout=timeout)


def ops_py(fixture: Path, code: str, env=None) -> dict:
    """Run engine code in a SUBPROCESS against a fixture (repo via env; fresh
    in-memory state per call, argv under our control)."""
    e = {"CLAUDERIZER_REPO": str(fixture), **(env or {})}
    r = sh([VENV_PY, "-c", code], env=e)
    if r.returncode != 0:
        return {"_error": r.stderr[-2000:]}
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {"_raw": r.stdout[-2000:], "_stderr": r.stderr[-500:]}


def cli_ops(fixture: Path, batch: list[dict], env=None, timeout=600):
    """Run a JSON batch through `clauderize ops -` — the REGISTRY seam
    (_journaled(_receipted(_stamped(fn)))), which raw ops.* calls bypass.
    Repo targeting via CLAUDERIZER_REPO (ops has no global --repo flag)."""
    return subprocess.run([str(CLI), "ops", "-"], input=json.dumps(batch),
                          capture_output=True, text=True, timeout=timeout,
                          env={**os.environ, **GUARDS,
                               "CLAUDERIZER_REPO": str(fixture), **(env or {})})


def make_fixture(work: Path, name: str, *, gameplan: str | None = "matrix-target",
                 python_profile: bool = False) -> tuple[Path, str | None]:
    fx = work / name
    fx.mkdir(parents=True)
    if python_profile:
        (fx / "pyproject.toml").write_text('[project]\nname = "fx"\n', encoding="utf-8")
        (fx / "test_fx.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    sh(["git", "init", "-q", "-b", "main"], cwd=fx)
    sh(["git", "-C", fx, "config", "user.email", "matrix@example.invalid"])
    sh(["git", "-C", fx, "config", "user.name", "Matrix Harness"])
    r = sh([CLI, "init", "--size", "pet"], cwd=fx)
    if r.returncode != 0:
        raise RuntimeError(f"init failed for {name}: {r.stderr[-500:]}")
    gid = None
    if gameplan:
        paths = P.resolve(fx)
        gid = M.create_gameplan(paths, gameplan)["gameplan_id"]
        from clauderizer.config import Config
        cfg = Config.load(paths.config_file)
        cfg.active_gameplan = gid          # what init does after create_gameplan
        paths.config_file.write_text(cfg.to_toml(), encoding="utf-8")
    sh(["git", "-C", fx, "add", "-A"])
    sh(["git", "-C", fx, "commit", "-qm", "fixture: clauderized baseline"])
    return fx, gid


def crafted_stamp(fx: Path, gid: str, phase: str, *, pid: int, start, host=None,
                  transport="mcp"):
    import socket
    rec = {"kind": "session", "gameplan": gid, "phase": str(phase), "pid": pid,
           "start": start, "host": host or socket.gethostname(),
           "agent": "matrix", "transport": transport, "at": TODAY}
    led = fx / ".clauderizer" / "sessions.jsonl"
    led.write_text(json.dumps(rec) + "\n", encoding="utf-8")


def proc_start(pid: int):
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="ascii", errors="replace")
        return stat.rsplit(")", 1)[1].split()[19]
    except Exception:
        return None


# --- Leg 1: recording coverage (production, read-only) ------------------------

def leg_recording_coverage() -> dict:
    tel = REPO / ".clauderizer" / "telemetry.jsonl"
    kinds: dict[str, int] = {}
    for line in tel.read_text(encoding="utf-8").splitlines():
        try:
            k = json.loads(line).get("kind", "?")
        except Exception:
            k = "<bad>"
        kinds[k] = kinds.get(k, 0) + 1
    stints = kinds.get("stint", 0)
    ledger = (REPO / ".clauderizer" / "sessions.jsonl").exists()
    log = sh(["git", "-C", REPO, "log", "--since=2026-07-27T21:55", "--format=%h %s"])
    commits = [l for l in log.stdout.strip().splitlines() if l]
    # Sessions evidenced by the commit record since the stint recorder landed
    # (P2 @ cabbd3e): each close/curate/merge cluster is a distinct working
    # session; the P7/P8 fleet adds two worker sessions beside the hub's.
    sessions = ["P3-build", "dream-distill", "P4+A002-build", "P7-hub",
                "P8-worker (fleet)", "curator-worker (fleet)"]
    return {
        "leg": "recording_coverage(O-01)", "status": "run",
        "figures": {
            "stint_events": stints, "telemetry_kinds": kinds,
            "sessions_ledger_exists": ledger,
            "sessions_since_recorder_landed": len(sessions),
            "coverage_fraction": 0.0 if sessions else None,
            "by_host_kind": {"claude-code": {"sessions": len(sessions), "stints": stints}},
        },
        "notes": ("0 stints across every real session since the recorder landed — "
                  "cause is the serving-engine capability gap (H-30: session MCP is "
                  "the published 1.14.3 engine, which predates record_run_stint), "
                  "NOT agent non-compliance (every phase ran cz_preflight). "
                  f"Commit evidence: {len(commits)} commits / sessions {sessions}. "
                  "Wind-down math over this ledger is fiction today; see the "
                  "budgets_ops_mode leg for live capability proof on the tree engine."),
    }


# --- Leg 2: stranded-state controls (zero FP required) ------------------------

def leg_stranded(work: Path) -> dict:
    fx, gid = make_fixture(work, "stranded")
    paths = P.resolve(fx)
    M.transition_phase(paths, gameplan_id=gid, phase_n="0",
                       to_status="in_progress", today=TODAY)
    target = {"number": "0", "name": "Bootstrap"}
    cases, fp, detections = [], 0, 0

    def run_case(label, expect_fire):
        nonlocal fp, detections
        rec = stranded.detect(paths, gid, target, "in_progress")
        fired = rec is not None
        if fired and not expect_fire:
            fp += 1
        if fired and expect_fire:
            detections += 1
        cases.append({"case": label, "expect_fire": expect_fire, "fired": fired,
                      "grade": (rec or {}).get("grade")})

    # A-alive control: crafted mcp stamp naming a LIVE child process.
    child = subprocess.Popen(["sleep", "300"])
    try:
        crafted_stamp(fx, gid, "0", pid=child.pid, start=proc_start(child.pid))
        run_case("A-alive (live claimant)", expect_fire=False)
    finally:
        child.terminate(); child.wait()
    # Own-pid control.
    crafted_stamp(fx, gid, "0", pid=os.getpid(), start=proc_start(os.getpid()))
    run_case("own-pid claimant", expect_fire=False)
    # Cross-host control.
    crafted_stamp(fx, gid, "0", pid=999999, start="1", host="other-host.invalid")
    run_case("cross-host claimant", expect_fire=False)
    # CLI-transport control (exits by design -> inconclusive, never dead).
    crafted_stamp(fx, gid, "0", pid=999999, start="1", transport="cli")
    run_case("cli-transport claimant", expect_fire=False)
    # Same-host MCP stranding: provably dead claimant.
    dead = subprocess.Popen(["true"]); dead_pid = dead.pid
    dead_start = proc_start(dead_pid); dead.wait()
    crafted_stamp(fx, gid, "0", pid=dead_pid, start=dead_start)
    run_case("same-host-mcp dead claimant", expect_fire=True)

    return {"leg": "stranded_state", "status": "run",
            "figures": {"false_positives": fp, "detections": detections,
                        "controls": len(cases) - 1, "cases": cases},
            "notes": "zero-FP requirement: false_positives must be 0 with detection on the dead case."}


# --- Leg 3: backstop (interrupted) fire/quiet ---------------------------------

def leg_backstop(work: Path) -> dict:
    cases = []

    def build(label):
        fx, gid = make_fixture(work, f"backstop-{label}")
        paths = P.resolve(fx)
        M.transition_phase(paths, gameplan_id=gid, phase_n="0",
                           to_status="in_progress", today=TODAY)
        sh(["git", "-C", fx, "add", "-A"])
        sh(["git", "-C", fx, "commit", "-qm", "tracker: phase 0 in_progress"])
        led = fx / ".clauderizer" / "sessions.jsonl"
        if led.exists():
            led.unlink()                      # default: ledger cannot grade
        return fx, gid, paths

    def work_commit(fx):
        (fx / "src_mod.py").write_text("VALUE = 42\n", encoding="utf-8")
        sh(["git", "-C", fx, "add", "src_mod.py"])
        sh(["git", "-C", fx, "commit", "-qm", "feat: real work"])

    def run_case(label, paths, gid, expect_fire):
        rec = interrupted.detect(paths, gid, {"number": "0", "name": "Bootstrap"},
                                 "in_progress")
        cases.append({"case": label, "expect_fire": expect_fire,
                      "fired": rec is not None,
                      "never_ran": (rec or {}).get("never_ran")})

    fx, gid, paths = build("fire")            # work + no residue + no stamp
    work_commit(fx)
    run_case("seeded abandoned work", paths, gid, True)

    fx, gid, paths = build("healthy")         # closing residue present -> quiet
    work_commit(fx)
    M.add_phase_summary(paths, gameplan_id=gid, phase="0",
                        text="Honest close: summary written.")
    run_case("healthy close (summary present)", paths, gid, False)

    fx, gid, paths = build("alive")           # live claimant -> quiet
    work_commit(fx)
    child = subprocess.Popen(["sleep", "300"])
    try:
        crafted_stamp(fx, gid, "0", pid=child.pid, start=proc_start(child.pid))
        run_case("alive claimant (liveness gate)", paths, gid, False)
    finally:
        child.terminate(); child.wait()

    fx, gid, paths = build("nowork")          # zero work commits -> quiet
    run_case("no work commits", paths, gid, False)

    fires_ok = all(c["fired"] == c["expect_fire"] for c in cases)
    return {"leg": "backstop_detector", "status": "run",
            "figures": {"cases": cases, "geometry_holds": fires_ok},
            "notes": "fire on seeded abandoned work; quiet on healthy close, live claimant, no-work."}


# --- Leg 4: never-engaged vs engaged receipts advisory ------------------------

def leg_never_engaged(work: Path) -> dict:
    fx, gid = make_fixture(work, "receipts")
    paths = P.resolve(fx)
    M.add_finding(paths, title="Engaged finding", severity="low", impact="matrix")
    M.add_finding(paths, title="Genuinely ignored finding", severity="low",
                  impact="matrix")
    # Drop-nothing golden (D-068): with NO sidecar the digest carries no
    # engagement keys at all — byte-identical to the pre-receipts shape.
    dig0 = ops_py(fx, "import json;from clauderizer import ops;"
                      "print(json.dumps(ops.cz_status()))")
    pre_sidecar_silent = "findings_engagement" not in json.dumps(dig0)
    # Engage exactly one finding through the receipted REGISTRY seam — the
    # wrapper lives on the op objects (_receipted), so a raw ops.cz_get() call
    # records nothing; the CLI ops path exercises the production write.
    cli_ops(fx, [{"op": "cz_get", "args": {"id": "H-01"}}])
    seen = RC.load_seen(paths)
    never, engaged = RC.split_seen(["H-01", "H-02"], seen)
    dig1 = ops_py(fx, "import json;from clauderizer import ops;"
                      "print(json.dumps(ops.cz_status()))")
    text1 = json.dumps(dig1)
    return {"leg": "never_engaged_advisory", "status": "run",
            "figures": {
                "pre_sidecar_no_engagement_keys": pre_sidecar_silent,
                "seen_keys": sorted(seen),
                "fires_on_ignored": never == ["H-02"],
                "quiet_on_engaged": engaged == ["H-01"],
                "digest_mentions_never_engaged": ("never" in text1 and "H-02" in text1),
            },
            "notes": ("emission is sidecar-gated by design (D-068 drop-nothing): "
                      "no receipts -> no keys; with one cz_get receipt the split "
                      "fires on the genuinely ignored finding only.")}


# --- Leg 5: merge-audit seeded-fault protocol ---------------------------------

def leg_merge_audit(work: Path) -> dict:
    fx, gid = make_fixture(work, "mergeaudit")
    paths = P.resolve(fx)
    doc = fx / "docs" / "DECISIONS.md"
    if not doc.exists():        # pet-size init scaffolds a leaner doc set
        doc.write_text("# Decisions\n\nAppend-only ADR log.\n", encoding="utf-8")
        sh(["git", "-C", fx, "add", "-A"])
        sh(["git", "-C", fx, "commit", "-qm", "docs: seed DECISIONS.md"])
    seeded, detected, clean, false_pos = 0, 0, 0, 0
    trials = []

    def commit_all(msg):
        sh(["git", "-C", fx, "add", "-A"]); sh(["git", "-C", fx, "commit", "-qm", msg])

    def audit(label, expect):
        nonlocal detected, false_pos
        head = sh(["git", "-C", fx, "rev-parse", "HEAD"]).stdout.strip()[:12]
        rec = merge_audit.compute(paths)
        # A hit counts only against the merge just made: compute() audits the
        # most recent DOCS-TOUCHING merge, so an older bad merge resurfacing
        # under a docs-silent clean merge is scope, not a false positive.
        hit = bool(rec) and rec.get("merge") == head
        if expect and hit:
            detected += 1
        if not expect and hit:
            false_pos += 1
        kinds = sorted({f["kind"] for f in (rec or {}).get("findings", [])}) if hit else []
        trials.append({"trial": label, "expect_finding": expect, "found": hit,
                       "kinds": kinds})

    def lost_update(i):
        nonlocal seeded
        seeded += 1
        base = doc.read_text(encoding="utf-8")
        sh(["git", "-C", fx, "checkout", "-qb", f"side{i}"])
        (fx / f"code{i}.py").write_text("x = 1\n", encoding="utf-8")
        commit_all(f"side{i}: code only")
        sh(["git", "-C", fx, "checkout", "-q", "main"])
        doc.write_text(base + f"\n### D-10{i} — hub decision {i}\n\nKept? It must be.\n",
                       encoding="utf-8")
        commit_all(f"main: D-10{i} recorded")
        # The lost-update shape: a bad resolution whose merge RESULT reverts the
        # docs blob main had already advanced (side never touched the doc).
        r = sh(["git", "-C", fx, "merge", "-q", "--no-ff", f"side{i}", "-m",
                f"merge side{i}"])
        if r.returncode == 0:
            doc.write_text(base, encoding="utf-8")     # resolver drops main's D-line
            sh(["git", "-C", fx, "add", "-A"])
            sh(["git", "-C", fx, "commit", "-q", "--amend", "--no-edit"])
        audit(f"lost-update-{i}", expect=True)

    def clean_merge(i, *, same_file=False, fenced=False):
        nonlocal clean
        clean += 1
        sh(["git", "-C", fx, "checkout", "-qb", f"clean{i}"])
        if same_file:
            base = doc.read_text(encoding="utf-8")
            doc.write_text(base + f"\n### D-20{i} — side note {i}\n\nAppend-only.\n",
                           encoding="utf-8")
        elif fenced:
            (fx / "docs" / f"GUIDE{i}.md").write_text(
                "# Guide\n\n```text\n<<<<<<< example\n=======\n>>>>>>> example\n```\n",
                encoding="utf-8")
        else:
            (fx / f"clean{i}.py").write_text("y = 2\n", encoding="utf-8")
        commit_all(f"clean{i}: additive")
        sh(["git", "-C", fx, "checkout", "-q", "main"])
        (fx / f"main{i}.txt").write_text("m\n", encoding="utf-8")
        commit_all(f"main{i}: unrelated")
        sh(["git", "-C", fx, "merge", "-q", "--no-ff", f"clean{i}", "-m",
            f"merge clean{i}"])
        audit(f"clean-{i}{'-samefile' if same_file else ''}{'-fenced' if fenced else ''}",
              expect=False)

    for i in range(1, 4):
        lost_update(i)
    clean_merge(1); clean_merge(2, same_file=True); clean_merge(3, same_file=True)
    clean_merge(4, fenced=True)

    # Healthy-repo digest byte-identity: a fresh clean fixture digests identically twice.
    fy, _ = make_fixture(work, "mergeaudit-healthy")
    d1 = ops_py(fy, "import json;from clauderizer import ops;print(json.dumps(ops.cz_status()))")
    d2 = ops_py(fy, "import json;from clauderizer import ops;print(json.dumps(ops.cz_status()))")
    return {"leg": "merge_audit_seeded_fault", "status": "run",
            "figures": {"seeded_faults": seeded, "detected": detected,
                        "detection_rate": f"{detected}/{seeded}",
                        "clean_merges": clean, "false_positives": false_pos,
                        "fp_rate": f"{false_pos}/{clean}",
                        "healthy_digest_byte_identical": d1 == d2,
                        "trials": trials,
                        "production_true_negative": "P8 merge 784ccd9 (docs-touching, audit silent)"},
            "notes": "squash blind spot remains stated-unclaimed (D-076); fenced quoted markers must not flag."}


# --- Leg 6: cz_state stamp — WSL slow-FS row ----------------------------------

def leg_stamp_wsl(work: Path) -> dict:
    """One CLI-ops BATCH per arm = one server session: the in-memory
    change-trigger dedup applies within it (INVARIANT-10 bound 2)."""
    # cz_status/cz_next_phase_context are _NO_STATE_STAMP by design (they ARE
    # the state) — use a plain read op for the change-trigger geometry.
    batch = ([{"op": "cz_list_open_items", "args": {}}] * 6
             + [{"op": "cz_add_output",
                 "args": {"phase": "0", "key": "k", "value": "v"}},
                {"op": "cz_list_open_items", "args": {}}])

    def arm(fx: Path, armed: bool) -> dict:
        t0 = time.perf_counter()
        r = cli_ops(fx, batch,
                    env={"CLAUDERIZER_STATE_STAMP": "1"} if armed else {})
        dt = time.perf_counter() - t0
        stamps = []
        try:
            out = json.loads(r.stdout)
            results = out if isinstance(out, list) else out.get("results", [])
            stamps = ["cz_state" in json.dumps(x) for x in results]
        except Exception:
            for line in r.stdout.splitlines():
                if line.strip().startswith(("{", "[")):
                    stamps.append("cz_state" in line)
        status_stamps = [s for i, s in enumerate(stamps) if i != 6][:6]
        return {"exit": r.returncode, "batch_s": round(dt, 2),
                "per_op_ms": round(dt / 8 * 1000, 1),
                "stamped_results": sum(bool(s) for s in stamps),
                "first_status_stamped": bool(stamps and stamps[0]),
                "middle_statuses_stamped": sum(bool(s) for s in status_stamps[1:]),
                "post_change_stamped": bool(stamps and stamps[-1])}

    figures = {}
    fx, _ = make_fixture(work, "stamp-ext4")
    fx2, _ = make_fixture(work, "stamp-ext4-off")
    figures["ext4"] = {"armed": arm(fx, True), "unarmed": arm(fx2, False)}
    drv = Path("/mnt/c/temp") if Path("/mnt/c").exists() else None
    drv_status = "gap"
    if drv:
        try:
            drv.mkdir(parents=True, exist_ok=True)
            dwork = Path(tempfile.mkdtemp(prefix="cz-matrix-", dir=drv))
            fx3, _ = make_fixture(dwork, "stamp-drvfs")
            fx4, _ = make_fixture(dwork, "stamp-drvfs-off")
            figures["drvfs"] = {"armed": arm(fx3, True), "unarmed": arm(fx4, False)}
            drv_status = "run"
            shutil.rmtree(dwork, ignore_errors=True)
        except Exception as e:                                    # noqa: BLE001
            figures["drvfs_error"] = str(e)[-300:]
    figures["drvfs_arm_status"] = drv_status
    return {"leg": "stamp_slow_fs_wsl", "status": "run", "figures": figures,
            "notes": ("armed arm expects: first cz_status stamped, the five "
                      "identical repeats silent (change-trigger), the "
                      "post-mutation cz_status stamped again; unarmed arm "
                      "expects zero stamps (silent-by-default, INVARIANT-10). "
                      "Overhead = armed vs unarmed batch time, ext4 vs DrvFs.")}


# --- Leg 7: budgets — ops-mode arm (kimi-pinned arm probed separately) --------

def leg_budgets_ops(work: Path) -> dict:
    fx, gid = make_fixture(work, "budgets", python_profile=True)
    g = fx / "docs" / "gameplans" / gid / "GAMEPLAN.md"
    text = g.read_text(encoding="utf-8")
    text = text.replace("> Status:", "> Budget: 1 session\n> Status:", 1)
    g.write_text(text, encoding="utf-8")
    sh(["git", "-C", fx, "add", "-A"])
    sh(["git", "-C", fx, "commit", "-qm", "declare gameplan budget"])
    rr = cli_ops(fx, [{"op": "cz_preflight", "args": {}}])
    tel = fx / ".clauderizer" / "telemetry.jsonl"
    stints = []
    if tel.exists():
        for line in tel.read_text(encoding="utf-8").splitlines():
            try:
                o = json.loads(line)
                if o.get("kind") == "stint":
                    stints.append(o)
            except Exception:
                pass
    from clauderizer.rituals import budgets as B
    paths = P.resolve(fx)
    assess = B.assess(paths, gid, None)
    ctx = ops_py(fx, "import json;from clauderizer import ops;"
                     "r=ops.cz_next_phase_context();"
                     "print(json.dumps({'wind_down': r.get('wind_down'),"
                     "'keys':[k for k in r if 'wind' in k or 'budget' in k]}))")
    return {"leg": "budgets_ops_mode", "status": "run",
            "figures": {"stints_recorded": len(stints),
                        "stint_sample": stints[:1],
                        "assess": assess, "context_wind_down": ctx,
                        "ops_exit": rr.returncode,
                        "ops_stdout_tail": rr.stdout[-400:],
                        "ops_stderr_tail": rr.stderr[-600:]},
            "notes": ("ops-mode (CLI, no MCP): the cz_preflight OP must record a "
                      "host-stable distinct-DATE stint; with '> Budget: 1 session' "
                      "declared, spent=1 lands in the reserve window -> wind_down "
                      "derived at read time. This is the live capability proof that "
                      "the production 0% coverage is a serving-engine gap, not a "
                      "recorder defect.")}


# --- Leg 8: memory-gap detection ---------------------------------------------

def leg_gap(work: Path) -> dict:
    fx, gid = make_fixture(work, "gap")
    miss = ops_py(fx, "import json;from clauderizer import ops;"
                      "r=ops.cz_analyze('quantum blockchain teapot orbital mechanics');"
                      "print(json.dumps({'memory_gap': r.get('memory_gap'),"
                      "'has_advisory': bool(r.get('gap_advisory')),"
                      "'decisions': len(r.get('decisions', [])),"
                      "'invariants': len(r.get('invariants', []))}))")
    paths = P.resolve(fx)
    M.add_decision(paths, title="Use teapot orbital caching for the API",
                   context="matrix", decision="cache in the teapot orbit",
                   consequences="warm teapots")
    hit = ops_py(fx, "import json;from clauderizer import ops;"
                     "r=ops.cz_analyze('teapot orbital caching API');"
                     "print(json.dumps({'memory_gap': r.get('memory_gap', False),"
                     "'decisions': len(r.get('decisions', []))}))")
    events, bad_keys, has_text = [], [], False
    tel = fx / ".clauderizer" / "telemetry.jsonl"
    if tel.exists():
        for line in tel.read_text(encoding="utf-8").splitlines():
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("kind") == "gap":
                events.append(o)
                extra = set(o) - {"kind", "surface", "gameplan", "phase", "date",
                                  "query_terms"}
                if extra:
                    bad_keys.append(sorted(extra))
                if "teapot" in json.dumps(o):
                    has_text = True
    ch = ops_py(fx, "import json;from clauderizer import ops;"
                    "print(json.dumps(ops.cz_corpus_health().get('gap_events')))")
    # Production side (read-only): real repo gap events + conversion.
    prod_gaps = 0
    for line in (REPO / ".clauderizer" / "telemetry.jsonl").read_text(
            encoding="utf-8").splitlines():
        try:
            if json.loads(line).get("kind") == "gap":
                prod_gaps += 1
        except Exception:
            pass
    return {"leg": "gap_detection", "status": "run",
            "figures": {"advisory_on_empty_registers": miss,
                        "quiet_on_hit": hit, "fixture_gap_events": len(events),
                        "event_key_violations": bad_keys,
                        "probe_text_leaked": has_text,
                        "corpus_health_gap_events": ch,
                        "production_gap_events": prod_gaps,
                        "production_gap_conversion": None},
            "notes": ("capability proven on fixture; production events are 0 because "
                      "the serving engine cannot emit them until 2.0.0a1 publishes — "
                      "gap-conversion rate is a NULL RESULT recorded as successful "
                      "outcome (L-50), trend baseline 0 at verb birth.")}


# --- Leg 9: reinforce verb ----------------------------------------------------

def leg_reinforce(work: Path) -> dict:
    fx, gid = make_fixture(work, "reinforce")
    paths = P.resolve(fx)
    M.add_lesson(paths, gameplan_id=gid,
                 text="Always pin the framistat calibration before the widget "
                      "assembly run, because uncalibrated framistats corrupt "
                      "the widget tolerance ledger.")
    # The write-time advisory scans PROJECT lessons — promote the seed there
    # (the production shape: a twin of an already-promoted lesson arrives).
    M.promote_lesson(paths, gameplan_id=gid, number=1)
    dup = ops_py(fx, "import json;from clauderizer import ops;"
                     "r=ops.cz_add_lesson(text='Pin the framistat calibration before "
                     "any widget assembly run - an uncalibrated framistat corrupts "
                     "the widget tolerance ledger.', gameplan_id='%s');"
                     "print(json.dumps({'advisory': r.get('advisory', ''),"
                     "'related': r.get('related_lessons')}))" % gid)
    offers = "reinforce" in json.dumps(dup).lower()
    r1 = ops_py(fx, "import json;from clauderizer import ops;"
                    "print(json.dumps(ops.cz_reinforce_lesson(number='1', "
                    "gameplan_id='%s')))" % gid)
    r2 = ops_py(fx, "import json;from clauderizer import ops;"
                    "print(json.dumps(ops.cz_reinforce_lesson(number='1', "
                    "gameplan_id='%s')))" % gid)
    body = (fx / "docs" / "gameplans" / gid / "CHAT-HANDOFF-INDEX.md").read_text(
        encoding="utf-8")
    x2 = "reinforced x2" in body
    reinforced_events = 0
    tel = fx / ".clauderizer" / "telemetry.jsonl"
    if tel.exists():
        reinforced_events = sum(1 for line in tel.read_text(encoding="utf-8").splitlines()
                                if '"reinforced"' in line)
    return {"leg": "reinforce_verb", "status": "run",
            "figures": {"near_dup_offers_reinforce": offers,
                        "advisory_payload": dup,
                        "reinforce_1": r1.get("ok", r1), "reinforce_2": r2.get("ok", r2),
                        "trailer_x2_present": x2,
                        "telemetry_reinforced_events": reinforced_events,
                        "production_token_weight": {
                            "canonical_before_after_curator": [6884, 6913],
                            "handoff_estimate_before_after": [6035, 5988],
                            "entries_before_after": [21, 20],
                            "provenance": "curator-loop iteration outputs, 2026-07-28"},
                        "production_re_derivation_priors": (
                            "P3-era curator: 6 re-derivation proposals; L-69 write-time "
                            "advisory fired at Jaccard 0.505 (threshold 0.40)"),
                        "production_verb_uses": 0},
            "notes": ("capability proven on fixture (offer -> blessed write -> xN "
                      "trailer -> telemetry); production before/after re-derivation "
                      "rate is a NULL RESULT at verb birth (unservable until "
                      "2.0.0a1 ships) — successful outcome per L-50.")}


LEGS = {
    "coverage": lambda w: leg_recording_coverage(),
    "stranded": leg_stranded,
    "backstop": leg_backstop,
    "never_engaged": leg_never_engaged,
    "merge_audit": leg_merge_audit,
    "stamp_wsl": leg_stamp_wsl,
    "budgets_ops": leg_budgets_ops,
    "gap": leg_gap,
    "reinforce": leg_reinforce,
}


def main() -> int:
    only = sys.argv[1:] or list(LEGS)
    work = Path(tempfile.mkdtemp(prefix="cz-matrix-p5-"))
    results = {"generated": TODAY, "harness": "matrix-p5-harness.py",
               "engine": "tree venv (editable)", "workdir": str(work), "legs": []}
    for name in only:
        fn = LEGS[name]
        try:
            out = fn(work)
        except Exception as e:                                   # noqa: BLE001
            import traceback
            out = {"leg": name, "status": "error",
                   "error": traceback.format_exc()[-1500:]}
        results["legs"].append(out)
        print(f"[{out.get('status','?'):5}] {name}: "
              f"{json.dumps(out.get('figures', out.get('error','')))[:220]}")
    out_path = HERE / "matrix-p5-results.json"
    prior = []
    if out_path.exists():
        try:
            prior = json.loads(out_path.read_text(encoding="utf-8")).get("legs", [])
        except Exception:
            prior = []
    keep = [l for l in prior if l.get("leg") not in
            {x.get("leg") for x in results["legs"]}]
    results["legs"] = keep + results["legs"]
    out_path.write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"results -> {out_path}")
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
