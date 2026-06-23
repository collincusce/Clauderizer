"""``clauderize`` — the human/agent command line.

Subcommands:
    init           drop Clauderizer into the current repo (idempotent)
    status         print the current gameplan digest
    reindex        rebuild the disposable graph cache from markdown
    doctor         verify the install and report drift
    release-check  preflight the four version registries + push ordering (O3)
    mcp            launch the MCP server (stdio)
    ops            execute a JSON batch of cz_* operations (the no-MCP fallback)
    uninstall      reverse the wiring footprint (preserves docs/ memory)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from . import PROCEDURE_VERSION, __version__, hosts, hosttargets
from .config import Config, ConfigError
from .graph import index
from .paths import find_repo_root, resolve
from .rituals import status_bundle
from .scaffold.init import WiringRefused, _resolve_invocation, init as run_init
from .tools_list import TOOL_NAMES


def _load(root: Path | None = None):
    paths = resolve(find_repo_root(root or Path.cwd()))
    if not paths.config_file.exists():
        return paths, None
    return paths, Config.load(paths.config_file)


def _print_host_list() -> None:
    """Discoverability for `clauderize init --list-hosts`: the host ids `--host`
    accepts, each with where its MCP registration lands and whether it's
    auto-written or guide-only."""
    from . import hosttargets
    print("Host targets for `clauderize init --host <name>`:\n")
    print(f"  {'host':<12} {'mode':<11} MCP config")
    print(f"  {'claude-code':<12} {'auto-write':<11} .mcp.json + .claude/settings.json hooks (default)")
    for hid, em in hosttargets.HOST_EMITTERS.items():
        mode = "auto-write" if em.auto_write else "guide-only"
        print(f"  {hid:<12} {mode:<11} {em.config_path}")
    print("\n  Omit --host to default to claude-code. Other hosts also get the "
          "AGENTS.md floor;\n  guide-only hosts get a .clauderizer/<host>-mcp-setup.md guide.")


def cmd_init(args: argparse.Namespace) -> int:
    if getattr(args, "list_hosts", False):
        _print_host_list()
        return 0
    run_cmd = args.run_cmd.split() if args.run_cmd else None
    try:
        report = run_init(
            Path(args.path).resolve(),
            size=args.size,
            profile=args.profile,
            gameplan=args.gameplan,
            run_cmd=run_cmd,
            workflow=args.workflow,
            session_host=args.session_host,
            host_target=args.host,
            spawn_test=not args.no_spawn_test,
        )
    except (WiringRefused, hosts.SessionHostError, hosttargets.HostTargetError) as exc:
        print(f"✗ init refused: {exc}")
        return 1
    print(f"Clauderized {report.repo}")
    print(f"  size={report.size}  host profile={report.host_profile}"
          f"  host target={report.host_target}  session host={report.session_host}")
    n_changed = len(report.changed)
    print(f"  {n_changed} file(s) written/updated, {len(report.actions) - n_changed} kept as-is")
    if args.verbose:
        for a in report.actions:
            print(f"    {a}")
    for w in report.warnings:
        print(f"  ! {w}")
    if report.host_target_auto:
        print(f"  · host target defaulted to claude-code; pass `--host <name>` to target "
              f"another agent tool ({', '.join(hosttargets.HOST_EMITTERS)})")
    if report.host_target == hosttargets.CLAUDE_CODE:
        print("\nNext: open a Claude Code session here — the SessionStart hook will show status.")
        print("Or run `clauderize status`.")
    else:
        print(f"\nNext: open {report.host_target} on this repo — it loads the emitted MCP "
              f"config and the AGENTS.md floor tells the agent to call cz_status first.")
        print("See the .clauderizer/*-setup.md guide(s) for any manual hook wiring, "
              "or run `clauderize status`.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    paths, config = _load()
    if config is None:
        print("Not a clauderized repo. Run `clauderize init`.")
        return 1
    bundle = status_bundle.compute(paths, config)
    if args.json:
        print(json.dumps(bundle, indent=2))
    else:
        print(status_bundle.render_digest(bundle, tools=TOOL_NAMES))
    return 0


def cmd_reindex(args: argparse.Namespace) -> int:
    paths, config = _load()
    if config is None:
        print("Not a clauderized repo. Run `clauderize init`.")
        return 1
    graph = index.build(paths.docs)
    index.write_cache(graph, paths.index_file, paths.docs)
    print(f"Reindexed {len(graph.entities)} entities -> {paths.index_file}")
    return 0


def _mcp_wiring_missing_extra(wiring: list[str] | None) -> bool:
    """True if the MCP server is wired via uvx/pipx `--from clauderizer` WITHOUT the
    [mcp] extra (H-15). Such a command launches but cannot import the mcp SDK, so it
    refuses to serve — yet a --version/presence probe never notices (the silent
    failure the stranger-readiness dogfood surfaced). Only the `--from` form is
    judged; a direct console-script path can't be assessed statically."""
    if not wiring or "--from" not in wiring:
        return False
    i = wiring.index("--from")
    spec = wiring[i + 1] if i + 1 < len(wiring) else ""
    runs_mcp = any(tok.endswith("clauderizer-mcp") for tok in wiring)
    return runs_mcp and spec.startswith("clauderizer") and "[mcp]" not in spec


def cmd_doctor(args: argparse.Namespace) -> int:
    paths, config = _load()
    if config is None:
        print("✗ Not a clauderized repo (no .clauderizer/config.toml). Run `clauderize init`.")
        return 1
    ok = True
    unverified = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal ok
        mark = "✓" if condition else "✗"
        print(f"{mark} {label}" + (f" — {detail}" if detail and not condition else ""))
        if not condition:
            ok = False

    def verdict(label: str, probe: hosts.Probe) -> None:
        # Three-state launchability (D3): pass shows its evidence, fail flips
        # drift, and "unverifiable from this host" is an honest middle that is
        # never rendered as green.
        nonlocal ok, unverified
        if probe.status == "ok":
            print(f"✓ {label} — {probe.detail}")
        elif probe.status == "unverifiable":
            unverified += 1
            print(f"? {label} — unverifiable from this host: {probe.detail}")
        else:
            ok = False
            print(f"✗ {label} — {probe.detail}")

    def warn(label: str, detail: str) -> None:
        # Advisory middle state outside launchability: shown, counted toward
        # exit 3, never green and never drift.
        nonlocal unverified
        unverified += 1
        print(f"? {label} — {detail}")

    check("config.toml present", paths.config_file.exists())
    check("procedure shipped", paths.procedure_file.exists())
    check("CLAUDE.md stanza", _has_marker(paths.claude_md, "clauderizer"))
    # The MCP + SessionStart-hook wiring is host_target-specific: init writes the
    # Claude Code files (.mcp.json + .claude/settings.json) ONLY for claude-code,
    # so checking them for a cursor/continue/… repo would false-fail a healthy
    # install (O-09). Branch on the recorded host_target; full per-host
    # launchability probing is Phase 13.
    host_target = config.host_target
    if host_target == hosttargets.CLAUDE_CODE:
        mcp_ok = _mcp_registered(paths.mcp_json)
        # Stripped-host_target guard: if the Claude Code wiring is absent but a
        # per-host config still registers clauderizer, host_target was likely
        # stripped — an older pre-host_target engine, or a config hand-edit,
        # rewrote config.toml without [host] target, so it defaulted back to
        # claude-code. Bare `init` would then write Claude Code wiring (the WRONG
        # repair); name the right one. (Observed live in P9 cross-version testing.)
        if not mcp_ok:
            stray = next((h for h, em in hosttargets.HOST_EMITTERS.items()
                          if em.auto_write
                          and _host_mcp_registered(paths.root / em.config_path, em.servers_key)),
                         None)
            if stray:
                warn("host target",
                     f"Claude Code wiring is absent but {stray}'s config registers "
                     f"clauderizer — host_target was likely stripped by an older engine "
                     f"or a config hand-edit. Re-run `clauderize init --host {stray}` "
                     f"(NOT bare `init`, which would wire Claude Code)")
        check(".mcp.json registers clauderizer", mcp_ok)
        # Session host of record (D3): launchability is only meaningful relative to
        # the host that spawns sessions, so surface — and validate — the record.
        session_host = config.session_host
        wiring = hosts.read_wiring(paths.mcp_json)
        if session_host:
            try:
                hosts.parse(session_host)
                print(f"✓ session host of record: {session_host}")
            except hosts.SessionHostError as exc:
                ok = False
                print(f"✗ session host of record — {exc}")
        elif hosts.is_wsl_shim(wiring):
            unverified += 1
            print("? session host of record — not recorded, but the wiring is wsl.exe-shimmed "
                  "(a Windows session host); re-run `clauderize init` to record it")
        else:
            print("✓ session host of record: native (default — not recorded)")
        # Fidelity: registration present is not enough — the command must be
        # launchable BY THE SESSION HOST OF RECORD, or doctor must say it cannot tell.
        verdict("MCP server launchable for session host",
                hosts.verify_wiring(wiring, session_host))
        # H-15: the launchability verdict above probes presence/identity (--version),
        # which the MCP entry answers WITHOUT importing the mcp SDK — so it stayed
        # green even when the wired command lacked the [mcp] extra and could never
        # serve. Statically catch that exact misconfiguration on the uvx path.
        if _mcp_wiring_missing_extra(wiring):
            check("MCP server wiring includes the [mcp] extra", False,
                  "wired via `--from clauderizer` WITHOUT the [mcp] extra, so the server "
                  "cannot import the mcp SDK and refuses to serve; re-run `clauderize init` "
                  "(1.0.3+) to rewire it as `--from clauderizer[mcp]`")
        settings = paths.root / ".claude" / "settings.json"
        check("SessionStart hook registered", _hook_registered(settings))
        hook_argv = _hook_command(settings)
        # D-010: the hook is executed as a STRING through the harness's executor
        # shell from an arbitrary cwd — the verdict must traverse that leg (Git
        # Bash + non-repo cwd) or say honestly that it cannot. The direct argv
        # probe alone stayed green through the entire H-08 outage.
        verdict("SessionStart hook launchable for session host",
                hosts.verify_hook_wiring(hook_argv, session_host))
    else:
        # Non-claude host: verify ITS config (init does not write .mcp.json /
        # .claude hooks for these). Presence + floor only here; launchability is
        # P13 (O-09). hook_argv left None so the wrapper block below self-skips.
        hook_argv = None
        em = hosttargets.HOST_EMITTERS.get(host_target)
        if em is None:
            check(f"host target '{host_target}' known", False, "unknown host")
        elif em.auto_write:
            check(f"{host_target} MCP config registers clauderizer",
                  _host_mcp_registered(paths.root / em.config_path, em.servers_key),
                  f"{em.config_path} missing or lacks the clauderizer entry — "
                  f"re-run `clauderize init --host {host_target}`")
        else:
            print(f"✓ host target '{host_target}': guide-only — register MCP by hand "
                  f"(see .clauderizer/{host_target}-mcp-setup.md)")
        # the floor reaches the agent via AGENTS.md, or a native rules file for
        # the hosts that do not read AGENTS.md (Continue, Gemini)
        rel = hosttargets.NATIVE_INSTRUCTIONS.get(host_target)
        if rel is not None:
            check(f"{host_target} native floor present",
                  _has_marker(paths.root / rel, "clauderizer"))
        else:
            check("AGENTS.md floor present", _has_marker(paths.agents_md, "clauderizer"))
    # D4 breadcrumb wrapper: when the registered command is the wrapper, its
    # file must exist and its baked engine command should match what a fresh
    # init would compose (staleness = the engine moved since the last init).
    wrapper_token = next(
        (t for t in (hook_argv or [])
         if ".clauderizer/hook." in t or ".clauderizer\\hook." in t),
        None,
    )
    if wrapper_token:
        wrapper_path = Path(wrapper_token)
        if not wrapper_path.is_file():
            # windows-wsl registrations carry the DISTRO-side spelling
            # (/home/… — or /C:/… for a win32-resident repo), which this host
            # may not be able to stat; the wrapper itself lives in this repo.
            tail = wrapper_token.replace("\\", "/").rsplit("/.clauderizer/", 1)
            if len(tail) == 2:
                candidate = paths.root / ".clauderizer" / tail[1]
                if candidate.is_file():
                    wrapper_path = candidate
        check("hook wrapper present", wrapper_path.is_file(),
              f"{wrapper_token} missing — re-run `clauderize init`")
        if wrapper_path.is_file():
            # Bytes, not read_text: universal-newline normalization would strip
            # the cmd template's \r\n and make a healthy win32 wrapper never
            # compare equal to its own render (a permanent false "stale" nudge).
            wrapper_text = wrapper_path.read_bytes().decode("utf-8", errors="replace")
            baked = hosts.wrapper_engine_argv(wrapper_text)
            current = _resolve_invocation(None)[1]
            expected = hosts.render_hook_wrapper(
                current, root=paths.root,
                windows=wrapper_path.name.endswith(".cmd"))
            if baked is None:
                check("hook wrapper freshness", False,
                      "no engine-hook line found — re-run `clauderize init`")
            elif wrapper_text == expected:
                check("hook wrapper freshness", True)
            elif baked == current:
                # Right engine, old template — e.g. missing the H-09 repo
                # anchor. The hook still launches, so this is a nudge, not drift.
                warn("hook wrapper freshness",
                     "wrapper template predates this engine (missing the repo "
                     "anchor or later template fixes) — re-run `clauderize init`")
            else:
                warn("hook wrapper freshness",
                     f"wrapper invokes `{' '.join(baked)}` but a fresh init would "
                     f"compose `{' '.join(current)}` — re-run `clauderize init` if "
                     f"the engine moved (expected with a custom --run-cmd)")
    elif hook_argv:
        warn("hook wrapper",
             "not installed (direct engine wiring) — re-run `clauderize init` to add "
             "the cold-start breadcrumb wrapper (D4)")
    check("index cache present", paths.index_file.exists())
    # A lock that doesn't parse is silently ignored by load_for_repo — surface it.
    lock_err = _lock_parse_error(paths.profile_lock)
    check("profile.lock.toml parses", lock_err is None, lock_err or "")
    # Engine identity (D9): the code that runs must be the code you see.
    meta_v = _metadata_version()
    check("engine metadata matches source version",
          meta_v is None or meta_v == __version__,
          f"dist-info reports {meta_v}, running source is {__version__} — "
          f"stale install metadata; reinstall (pip install -e . for a checkout)")
    repo_v = _engine_repo_version(paths.root)
    if repo_v is not None:
        check("running engine matches this repo's engine source",
              repo_v == __version__,
              f"repo pyproject declares {repo_v}, running engine is {__version__} — "
              f"the wiring executes a different build than this repo's code "
              f"(stale uvx/pipx cache?)")
    # procedure version drift (MAJOR)
    drift = _procedure_drift(paths.procedure_file)
    check("procedure version compatible", drift is None, drift or "")
    if config.active_gameplan:
        gp = paths.gameplan_dir(config.active_gameplan) / "GAMEPLAN.md"
        check(f"active gameplan {config.active_gameplan} on disk", gp.exists())
    if not ok:
        print("\nDrift detected — re-run `clauderize init` to repair.")
        return 2
    if unverified:
        # Exit 3: nothing failed, but ≥1 check could not be verified from this
        # host — "OK" would be a false green for the session host of record.
        print(f"\nOK — {unverified} check(s) unverifiable from this host; run "
              f"`clauderize doctor` from the session host of record to certify.")
        return 3
    print("\nOK")
    return 0


def cmd_release_check(args: argparse.Namespace) -> int:
    """O3/D-011: refuse to stage a release on a skewed registry or unpushed tree."""
    from .release_check import run

    code, checks = run(Path.cwd())
    marks = {"ok": "✓", "fail": "✗", "unverifiable": "?", "skip": "-"}
    for c in checks:
        print(f"{marks[c.status]} {c.label}" + (f" — {c.detail}" if c.detail else ""))
    if code == 0:
        print("\nOK — stage the release: tag the pushed commit, push the tag, cut "
              "the GitHub Release (publishing fires on the Release, not the tag).")
    elif code == 2:
        print("\nRED — do not tag and do not cut a Release until every ✗ is "
              "resolved (L-08).")
    else:
        print("\nOK with unverifiable check(s) — verify each ? manually before "
              "staging; an unswept registry is how versions get double-claimed.")
    return code


def cmd_mcp(args: argparse.Namespace) -> int:
    from .mcp_server import main as mcp_main

    return mcp_main()


def cmd_uninstall(args: argparse.Namespace) -> int:
    """Reverse Clauderizer's wiring footprint, preserving the durable ``docs/``
    memory and every unrelated entry (P8). ``--host <name>`` scopes to one host's
    per-host footprint; with no host the FULL footprint is removed (the
    Claude Code .mcp.json key + .claude hooks, every per-host MCP registration,
    the CLAUDE.md/AGENTS.md marker stanzas, skills, and the .clauderizer/ dir)."""
    from .paths import find_repo_root
    from .scaffold.uninstall import uninstall

    if args.host is not None:
        try:
            hosttargets.parse_host_target(args.host)
        except hosttargets.HostTargetError as exc:
            print(f"✗ {exc}")
            return 2
    repo = find_repo_root(Path.cwd())
    report = uninstall(repo, host=args.host)
    scope = f"host '{args.host}'" if args.host else "full footprint"
    if report.removed:
        print(f"Uninstalled Clauderizer ({scope}) from {repo}:")
        for item in report.removed:
            print(f"  - removed {item}")
    else:
        print(f"Nothing to remove ({scope}) — no Clauderizer footprint found in {repo}.")
    for k in report.kept:
        print(f"  · kept {k}")
    return 0


def cmd_ops(args: argparse.Namespace) -> int:
    """Execute ``[{op, args}, ...]`` against the shared ops registry (L-05).

    Every tracked write reachable without an MCP client: op names and arg
    shapes are exactly the cz_* tool names and schemas. Args live in a JSON
    file (or stdin with ``-``) by design — no shell-quoting hazards. Exit 0
    when every op succeeded, 1 when any failed, 2 when the batch itself is
    unreadable.
    """
    from . import ops

    if args.file == "-":
        # PS 5.1 pipes can prepend a BOM to otherwise-valid JSON; tolerate it.
        raw = sys.stdin.read().lstrip(chr(0xFEFF))
    else:
        path = Path(args.file)
        if not path.exists():
            print(json.dumps({"ok": False, "error": f"no such file: {args.file}"}))
            return 2
        raw = path.read_text(encoding="utf-8-sig")
    try:
        batch = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"invalid JSON: {e}"}))
        return 2
    if isinstance(batch, dict):
        batch = [batch]  # single-op convenience
    if not isinstance(batch, list):
        print(json.dumps({"ok": False, "error": 'expected a JSON array of {"op", "args"}'}))
        return 2
    results, all_ok = ops.run_batch(batch)
    print(json.dumps({"ok": all_ok, "results": results}, indent=2))
    return 0 if all_ok else 1


# --- doctor helpers -----------------------------------------------------------


def _has_marker(path: Path, name: str) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return f"<!-- {name}:start -->" in text


def _mcp_registered(mcp_json: Path) -> bool:
    if not mcp_json.exists():
        return False
    try:
        data = json.loads(mcp_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return "clauderizer" in data.get("mcpServers", {})


def _host_mcp_registered(path: Path, servers_key: str) -> bool:
    """A per-host config (``.cursor/mcp.json`` etc.) registers clauderizer under
    its own servers key — doctor's presence check for a non-claude host_target."""
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    servers = data.get(servers_key)
    return isinstance(servers, dict) and "clauderizer" in servers


def _hook_registered(settings: Path) -> bool:
    if not settings.exists():
        return False
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    for group in data.get("hooks", {}).get("SessionStart", []):
        for h in group.get("hooks", []):
            if hosts.is_hook_command(h.get("command", "")):
                return True
    return False


def _hook_command(settings: Path) -> list[str] | None:
    if not settings.exists():
        return None
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    for group in data.get("hooks", {}).get("SessionStart", []):
        for h in group.get("hooks", []):
            cmd = h.get("command", "")
            if hosts.is_hook_command(cmd):
                return cmd.split()
    return None


def _metadata_version() -> str | None:
    """Version the installed dist-info claims — ``None`` when not installed.

    An editable install's metadata freezes at install time; observed live on
    this repo as pip reporting 0.3.0 while the source ran 0.5.0 (H-01/H-03
    session). A mismatch means version-reporting surfaces lie.
    """
    try:
        from importlib.metadata import version

        return version("clauderizer")
    except Exception:
        return None


def _engine_repo_version(root: Path) -> str | None:
    """The repo's own engine version, when the repo IS the clauderizer source.

    Returns ``None`` for ordinary clauderized repos. For the dogfooding case it
    lets doctor catch "the hook/MCP wiring runs an older build than the code
    you're editing" — a stale uvx/pipx cache, the exact skew a green
    launchability check can't see.
    """
    pp = root / "pyproject.toml"
    if not pp.exists():
        return None
    import tomllib

    try:
        data = tomllib.loads(pp.read_text(encoding="utf-8"))
    except Exception:
        return None
    project = data.get("project") or {}
    if project.get("name") != "clauderizer":
        return None
    v = project.get("version")
    return str(v) if v else None


def _lock_parse_error(lock_path: Path) -> str | None:
    """Return a description of why the profile lock can't parse, else None."""
    if not lock_path.exists():
        return None  # no lock is fine — packaged defaults apply
    import tomllib

    try:
        with lock_path.open("rb") as fh:
            tomllib.load(fh)
    except tomllib.TOMLDecodeError as e:
        return f"invalid TOML ({e}) — overrides are being ignored; fix or delete it"
    except OSError as e:
        return str(e)
    return None


def _procedure_drift(procedure_file: Path) -> str | None:
    if not procedure_file.exists():
        return "procedure file missing"
    m = re.search(r"Procedure version\**:?\s*([0-9]+)\.([0-9]+)\.([0-9]+)",
                  procedure_file.read_text(encoding="utf-8"))
    if not m:
        return None
    host_major = int(m.group(1))
    engine_major = int(PROCEDURE_VERSION.split(".")[0])
    if host_major != engine_major:
        return f"host procedure v{m.group(0)} vs engine v{PROCEDURE_VERSION} (MAJOR mismatch)"
    return None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="clauderize", description="Drop-in working memory for AI agents.")
    p.add_argument("--version", action="version", version=f"clauderizer {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    pi = sub.add_parser("init", help="drop Clauderizer into this repo")
    pi.add_argument("path", nargs="?", default=".", help="repo path (default: cwd)")
    pi.add_argument("--size", choices=["pet", "standard", "saas"], default="standard")
    pi.add_argument("--profile", default="auto", help="host language profile (default: auto-detect)")
    pi.add_argument("--gameplan", default=None, help="also create a first gameplan with this name")
    pi.add_argument("--run-cmd", default=None,
                    help="how the repo invokes the engine (default: 'uvx --from clauderizer')")
    pi.add_argument("--workflow", choices=["code", "docs", "audit"], default="code",
                    help="docs/audit make clean_tree (and test) checks advisory, not fatal")
    pi.add_argument("--session-host", default=None, dest="session_host",
                    help="which host spawns Claude Code sessions: 'native' (default; "
                         "auto-detected from existing wiring) or 'windows-wsl:<distro>' "
                         "for a WSL-installed engine driven from Windows")
    pi.add_argument("--host", default=None, dest="host",
                    help="which agent tool drives this repo (default: claude-code; "
                         "auto-detected when omitted). Other hosts get their own MCP "
                         "config + AGENTS.md floor + setup guide: "
                         + ", ".join(hosttargets.HOST_EMITTERS))
    pi.add_argument("--list-hosts", action="store_true", dest="list_hosts",
                    help="list the valid --host values (and where each writes) and exit")
    pi.add_argument("--no-spawn-test", action="store_true",
                    help="skip the pre-write launch probes (escape hatch for sandboxes "
                         "that cannot spawn; the probes are the mis-wiring guard)")
    pi.add_argument("-v", "--verbose", action="store_true")
    pi.set_defaults(func=cmd_init)

    ps = sub.add_parser("status", help="print current gameplan status")
    ps.add_argument("--json", action="store_true")
    ps.set_defaults(func=cmd_status)

    pr = sub.add_parser("reindex", help="rebuild the graph cache from markdown")
    pr.set_defaults(func=cmd_reindex)

    pd = sub.add_parser("doctor", help="verify the install and report drift")
    pd.set_defaults(func=cmd_doctor)

    prc = sub.add_parser(
        "release-check",
        help="preflight a release: push ordering + the four version registries "
             "(source, remote tags, Releases, PyPI) — exit 0 ok / 2 red / 3 unverifiable",
    )
    prc.set_defaults(func=cmd_release_check)

    pm = sub.add_parser("mcp", help="launch the MCP server (stdio)")
    pm.set_defaults(func=cmd_mcp)

    po = sub.add_parser("ops", help="execute a JSON batch of cz_* operations (no-MCP fallback)")
    po.add_argument("file", help="JSON file of [{op, args}, ...], or '-' for stdin")
    po.set_defaults(func=cmd_ops)

    pu = sub.add_parser("uninstall",
                        help="reverse Clauderizer's wiring footprint (preserves docs/)")
    pu.add_argument("--host", default=None,
                    help="scope to one host's footprint (default: the full footprint)")
    pu.set_defaults(func=cmd_uninstall)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    try:
        return args.func(args)
    except ConfigError as exc:
        # A corrupt .clauderizer/config.toml must not crash any command with a raw
        # traceback — the diagnostic tools especially should report it (P11).
        print(f"✗ {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
