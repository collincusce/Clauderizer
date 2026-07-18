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
from .graph import abstract_index, index
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
    print("Host targets for `clauderize init` (multi-host default — D-046):\n")
    print(f"  {'host':<12} {'mode':<11} MCP config")
    print(f"  {'claude-code':<12} {'auto-write':<11} .mcp.json + .claude/settings.json hooks")
    for hid, em in hosttargets.HOST_EMITTERS.items():
        mode = "auto-write" if em.auto_write else "guide-only"
        print(f"  {hid:<12} {mode:<11} {em.config_path}")
    print("\n  Bare `init` wires ALL of the above (non-destructive, path-safe).")
    print("  `--host <name>` is an optional SCOPE filter (only touch that host).")
    print("  Guide-only hosts get a .clauderizer/<host>-mcp-setup.md instead of")
    print("  rewriting global/TOML config (D-031).")


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
            serve_wsl_here=getattr(args, "serve_wsl_here", False),
        )
    except (WiringRefused, hosts.SessionHostError, hosttargets.HostTargetError) as exc:
        print(f"✗ init refused: {exc}")
        return 1
    print(f"Clauderized {report.repo}")
    wired = report.hosts_wired or [report.host_target]
    print(f"  size={report.size}  host profile={report.host_profile}"
          f"  session host={report.session_host}")
    print(f"  hosts wired ({len(wired)}): {', '.join(wired)}")
    n_changed = len(report.changed)
    print(f"  {n_changed} file(s) written/updated, {len(report.actions) - n_changed} kept as-is")
    if args.verbose:
        for a in report.actions:
            print(f"    {a}")
    for w in report.warnings:
        print(f"  ! {w}")
    for a in report.advisories:
        print(f"  → {a}")
    if report.host_target_auto and len(wired) > 1:
        print("  · multi-host default: every supported agent is wired; pass "
              "`--host <name>` to touch only one host's files")
    print("\nNext: open any wired agent on this repo. AGENTS.md tells it to call "
          "cz_status first; Claude Code also gets a SessionStart digest.")
    print("If a host needs a human step (folder trust, TOML paste, amp approve), "
          "run `clauderize doctor` for the configure checklist.")
    print("Or run `clauderize status`.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    paths, config = _load()
    if config is None:
        print("Not a clauderized repo. Run `clauderize init`.")
        return 1
    # Self-heal every bespoke auto-write host's registration (the app wipes its config
    # on project switch, with no persistent source to merge from — D-055/D-056). An
    # explicit CLI run is write-permitted; silent + idempotent, and NOT done from the
    # read-only hook (INVARIANT-06). Detected-only + opt-out-aware, so a no-op off host.
    from . import bespoke_hosts
    for _host in bespoke_hosts.all_hosts().values():
        _host.self_heal()
    # An explicit CLI ask evaluates standing conditions (D3), same as cz_status;
    # only the read-only hook path stays probe-free.
    bundle = status_bundle.compute(paths, config, conditions=True)
    if args.json:
        print(json.dumps(bundle, indent=2))
    else:
        print(status_bundle.render_digest(bundle, tools=TOOL_NAMES))
    return 0


def cmd_gameplans(args: argparse.Namespace) -> int:
    """List the open gameplans (the portfolio); --all includes finished ones."""
    from . import ops

    try:
        res = ops.cz_gameplans(include_closed=args.all)
    except Exception as exc:  # not-a-repo and friends — report, don't traceback
        print(f"Error: {exc}")
        return 1
    if args.json:
        print(json.dumps(res, indent=2))
        return 0
    print(res["summary"])
    for c in res["gameplans"]:
        mark = "*" if c["is_focus"] else " "
        ph = c["phase"]
        ph_s = (f'phase {ph["number"]}/{c["total_phases"]} "{ph["name"]}"'
                if ph else c["lifecycle"])
        extra = ""
        if c["blockers"]:
            extra += f"  blocked:{len(c['blockers'])}"
        if c["pending_cascades"]:
            extra += f"  cascades:{c['pending_cascades']}"
        print(f" {mark} {c['id']}  [{c['kind']}]  {ph_s}{extra}")
    return 0


def cmd_focus(args: argparse.Namespace) -> int:
    """Switch focus to a gameplan; with no id, report current focus + portfolio."""
    from . import ops

    try:
        res = ops.cz_focus(gameplan_id=args.gameplan_id or "")
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    if args.json:
        print(json.dumps(res, indent=2))
        return 0
    if not res.get("ok"):
        print(res.get("error", "focus failed"))
        return 1
    print(res["summary"])
    if res.get("warning"):
        print(f"⚠ {res['warning']}")
    return 0


def cmd_reindex(args: argparse.Namespace) -> int:
    paths, config = _load()
    if config is None:
        print("Not a clauderized repo. Run `clauderize init`.")
        return 1
    graph = index.build(paths.docs)
    index.write_cache(graph, paths.index_file, paths.docs)
    aidx = abstract_index.build(paths)
    abstract_index.write_cache(aidx, paths.abstract_index_file)
    print(f"Reindexed {len(graph.entities)} entities -> {paths.index_file}")
    print(f"Reindexed {len(aidx['entries'])} corpus entries -> {paths.abstract_index_file}")
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


def cmd_upgrade(args: argparse.Namespace) -> int:
    """Modernize the corpus (D-042): the mechanical tier applies, the memory
    tier prints as proposals — never auto-applied."""
    paths, config = _load()
    if config is None:
        print("Not a clauderized repo. Run `clauderize init`.")
        return 1
    from . import modernize
    from . import proposals as _proposals

    res = (modernize.report(paths, config) if args.report
           else modernize.apply(paths, config))
    if args.json:
        print(json.dumps(res, indent=2))
        return 0
    # Terse by default (D-052): show the mechanical work in full, but summarize the
    # advisory proposals as a COUNT + a pointer instead of a wall of suggestions —
    # the next session's digest and the clauderizer-modernize skill triage them.
    pending = _proposals.filter_pending(res.get("proposals", []),
                                        _proposals.load_ledger(paths))
    mech = res.get("applied") or res.get("mechanical") or []
    verb = "applied" if res.get("applied") else "available"
    print(f"{len(mech)} mechanical update(s) {verb}; {len(pending)} advisory proposal(s) awaiting triage")
    for item in res.get("mechanical", []):
        print(f"  would apply: {item['action']} — {item['detail']}")
    for act in res.get("applied", []):
        print(f"  applied: {act}")
    if pending:
        print(f"  {len(pending)} proposal(s) await your triage — invoke the "
              f"clauderizer-modernize skill to handle / dismiss / defer them")
        print("  (your next session will remind you; `cz_modernize` or `--json` lists them in full)")
    return 0


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
    # Multi-host doctor (D-046/D-048): check every enabled host's readiness and
    # surface configure-on-demand steps — never hard-block (INVARIANT-05).
    # Claude launchability probes still run when claude-code is in the set.
    enabled = hosttargets.expand_enabled_hosts(getattr(config, "enabled_hosts", None))
    multi = len(enabled) > 1
    print(f"✓ enabled hosts ({len(enabled)}): {', '.join(enabled)}"
          + ("  [multi-host default]" if multi else ""))
    detected = __import__("clauderizer.session", fromlist=["detect_session_agent"]).detect_session_agent()
    if detected:
        print(f"✓ session agent detected this process: {detected}")
    else:
        print("? session agent: not detected (P7 bootstrap will fire if status undelivered)")

    wire_claude = hosttargets.CLAUDE_CODE in enabled
    hook_argv = None
    session_host = config.session_host

    if wire_claude or _mcp_registered(paths.mcp_json):
        mcp_ok = _mcp_registered(paths.mcp_json)
        check(".mcp.json registers clauderizer", mcp_ok,
              "missing — re-run `clauderize init`")
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
        if mcp_ok:
            # Multi-host portable .mcp.json is engine-native (uvx), not session_host-
            # composed. Verify it as native so windows-wsl session_host (which still
            # composes Claude hooks) does not false-fail a correct multi install.
            mcp_probe_host = session_host
            if wiring and hosttargets.is_path_safe(list(wiring)):
                mcp_probe_host = None  # portable → native launchability
                if session_host and str(session_host).startswith("windows-wsl"):
                    print("✓ MCP config is portable (multi-host); session_host "
                          f"{session_host} still composes Claude hooks")
            verdict("MCP server launchable for session host",
                    hosts.verify_wiring(wiring, mcp_probe_host))
            if _mcp_wiring_missing_extra(wiring):
                check("MCP server wiring includes the [mcp] extra", False,
                      "wired via `--from clauderizer` WITHOUT the [mcp] extra; re-run "
                      "`clauderize init` (1.0.3+) for `--from clauderizer[mcp]`")
            if wiring and not hosttargets.is_path_safe(list(wiring)):
                # Intentional for scoped Claude-only + windows-wsl dogfood — not
                # drift and not "unverifiable from this host" (exit 3). Info only.
                print("· MCP path-safety: .mcp.json is machine-specific (local Claude "
                      "dogfood); bare `clauderize init` writes portable multi-host")
                if not session_host and hosts.is_wsl_shim(list(wiring)):
                    unverified += 1
                    print("? session host of record — not recorded, but the wiring is "
                          "wsl.exe-shimmed (a Windows session host); re-run "
                          "`clauderize init` to record it")

    if wire_claude:
        settings = paths.root / ".claude" / "settings.json"
        check("SessionStart hook registered", _hook_registered(settings),
              "missing — re-run `clauderize init` (or `init --host claude-code`)")
        hook_argv = _hook_command(settings)
        if hook_argv:
            verdict("SessionStart hook launchable for session host",
                    hosts.verify_hook_wiring(hook_argv, session_host))

    check("AGENTS.md floor present", _has_marker(paths.agents_md, "clauderizer"))

    # Per-host readiness + configure-on-demand (D-048)
    for hid in enabled:
        if hid == hosttargets.CLAUDE_CODE:
            continue
        em = hosttargets.HOST_EMITTERS.get(hid)
        if em is None:
            warn(f"host {hid}", "unknown — not in HOST_EMITTERS")
            continue
        if em.auto_write:
            present = _host_mcp_registered(paths.root / em.config_path, em.servers_key)
            if present:
                print(f"✓ {hid}: MCP config present ({em.config_path})")
                # Default is presence (verify_wiring already launch-probes the session
                # host's wiring; a handshake per enabled host adds latency for little
                # gain — O-01/L-07). `--deep` opts into the capability check for every
                # auto-write host, reusing the shared mcp_probe primitive (D-056).
                if getattr(args, "deep", False):
                    import tempfile

                    from . import mcp_probe
                    entry = _host_registered_entry(paths.root / em.config_path, em.servers_key)
                    r = mcp_probe.handshake_probe(entry or {}, cwd=tempfile.gettempdir())
                    verdict(f"{hid} MCP initialize handshake",
                            hosts.Probe(r["status"], r["detail"]))
            else:
                warn(f"{hid} MCP",
                     f"{em.config_path} missing clauderizer — re-run `clauderize init` "
                     f"or `init --host {hid}`")
                for hint in hosttargets.configure_hints(hid):
                    print(f"    configure: {hint}")
        else:
            guide = paths.root / ".clauderizer" / f"{hid}-mcp-setup.md"
            if guide.is_file():
                print(f"✓ {hid}: guide-only setup present ({guide.name})")
            else:
                warn(f"{hid} guide",
                     f"missing {guide.name} — re-run `clauderize init`")
            for hint in hosttargets.configure_hints(hid):
                print(f"    configure: {hint}")
        if hid == "grok":
            hooks_path = paths.root / hosttargets.GROK_HOOKS_REL
            if hooks_path.is_file():
                print(f"✓ grok: governance hooks present ({hosttargets.GROK_HOOKS_REL})")
            else:
                warn("grok hooks",
                     f"{hosttargets.GROK_HOOKS_REL} missing — re-run `clauderize init`")
            print("  note: grok Hook→ctx=no — floor + P7 bootstrap; needs /hooks-trust")
        rel = hosttargets.NATIVE_INSTRUCTIONS.get(hid)
        if rel is not None:
            check(f"{hid} native floor present",
                  _has_marker(paths.root / rel, "clauderizer"),
                  f"missing {rel} — re-run `clauderize init --host {hid}`")

    # Bespoke auto-write hosts (kimi-desktop and any future one — D-056). Generic over
    # the BESPOKE_HOSTS registry: self-heal each (the app wipes its config on project
    # switch, O-01), then report registered / unregistrable / not installed, and verify
    # CAPABILITY (not presence, L-25) with a live MCP initialize handshake.
    import tempfile

    from . import bespoke_hosts, mcp_probe
    for host in bespoke_hosts.all_hosts().values():
        # Self-heal first so the report reflects the healed state (idempotent no-op when
        # current; detected-only + opt-out-aware; never raises).
        heal = host.self_heal()
        if heal["status"] == "wired" and heal.get("changed"):
            print(f"✓ {host.id}: re-applied MCP registration ({heal['path']})")
        cfg = host.detect_config()
        if cfg is None:
            print(f"· {host.id}: app not detected — nothing to wire")
            continue
        if heal["status"] == "unregistrable":
            warn(host.id, f"app detected but no launchable command to register — "
                          f"{'; '.join(heal['warnings'])}")
        elif _host_mcp_registered(cfg, host.servers_key):
            # Opt-in WSL-serving pin (D-057): report WHICH repo the desktop serves so the
            # single-repo tradeoff is never silent.
            pinned = host.pinned_repo(cfg)
            if pinned:
                print(f"✓ {host.id}: MCP registered, PINNED to serve {pinned} ({cfg})")
                warn(f"{host.id} pin", f"the desktop serves {pinned} for EVERY project "
                     "opened in the app (opt-in WSL override, D-057) — not the project you open. "
                     "Unpin via `clauderize uninstall`.")
            else:
                print(f"✓ {host.id}: MCP registered ({cfg})")
            # Spawn the composed command from a non-repo cwd (the way the app does) and
            # complete an MCP initialize handshake asserting serverInfo.name=='clauderizer'.
            # Fails loudly on MSYS-mangled / UNC / vanished commands; unverifiable (never
            # green) when the command targets a host this doctor can't reach.
            entry = _host_registered_entry(cfg, host.servers_key)
            r = mcp_probe.handshake_probe(entry or {}, cwd=tempfile.gettempdir())
            verdict(f"{host.id} MCP initialize handshake", hosts.Probe(r["status"], r["detail"]))
            # A bespoke host's server is a SEPARATE install (e.g. Windows pipx) from this
            # engine, so a version skew is advisory (not same-install drift): flag it so
            # the host doesn't silently serve a stale engine.
            served = r.get("server_version")
            if r["status"] == "ok" and served and served != __version__:
                warn(f"{host.id} MCP version",
                     f"the host serves clauderizer {served} but this engine is {__version__} "
                     f"— update that install (e.g. `pipx upgrade clauderizer`)")
        else:
            warn(host.id, f"app detected but clauderizer not in {cfg} — re-run `clauderize init`")
        # Detected but can't serve THIS repo (e.g. a WSL repo under a Windows desktop's
        # UNC-cwd spawn limit, D-054): the registered entry still serves other repos the
        # host opens; surface the host's own guidance for this one.
        if heal.get("unservable"):
            warn(host.id, heal["unservable"])

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
    # Abstract index (D3): detect a missing/schema-stale cache and advise reindex —
    # read-only (never builds it; the runtime self-heals). The upgrade nudge an
    # existing repo gets after moving to an engine that ships the abstract index.
    ai_status = abstract_index.cache_status(paths)
    check("abstract index fresh", ai_status is None, ai_status or "")
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
    # Corpus modernization stamp (D-042) — advisory: stale means newer engine
    # capabilities haven't been delivered to this corpus yet; never a failure.
    stamp = config.procedure_version or ""
    if stamp == PROCEDURE_VERSION:
        print(f"✓ corpus modernized to procedure v{PROCEDURE_VERSION}")
    else:
        warn("corpus modernization available",
             f"corpus procedure stamp is {stamp or 'missing'}; this engine "
             f"carries procedure v{PROCEDURE_VERSION} (the methodology "
             f"document's version line — separate from the engine's own "
             f"v{__version__}) — run `clauderize upgrade` to apply mechanical "
             "updates and review the advisory proposals")
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
              "resolved.")
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

    if getattr(args, "list_ops", False):
        for entry in ops.list_ops():
            tag = "write" if entry["writes"] else "read "
            needs = ("  needs: " + ", ".join(entry["required"])) if entry["required"] else ""
            print(f"[{tag}] {entry['op']}{needs}")
            if entry["summary"]:
                print(f"        {entry['summary']}")
        print('\nRun `clauderize ops --schema <op>` for one op\'s full args, then pass '
              '`[{"op": "<op>", "args": {...}}]` to `clauderize ops <file|->`.')
        return 0
    if getattr(args, "schema", None):
        sch = ops.op_schema(args.schema)
        if sch is None:
            print(json.dumps({"ok": False,
                              "error": f"unknown op {args.schema!r} — run 'clauderize ops --list'"}))
            return 1
        print(json.dumps(sch, indent=2))
        return 0
    if not args.file:
        print(json.dumps({"ok": False,
                          "error": "nothing to do — pass a JSON file or '-', or use --list / --schema <op>"}))
        return 2

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


def _host_registered_entry(path: Path, servers_key: str) -> dict | None:
    """The clauderizer server entry ({command, args}) from a per-host config, or
    None — so doctor can smoke-test the exact command that was registered."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    servers = data.get(servers_key)
    if isinstance(servers, dict) and isinstance(servers.get("clauderizer"), dict):
        return servers["clauderizer"]
    return None


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
                    help="launcher PREFIX the wiring uses to invoke the engine's "
                         "commands — e.g. 'uvx --from clauderizer' or 'pipx run "
                         "clauderizer' — not a path to a single binary "
                         "(default: auto-compose from the install)")
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
    pi.add_argument("--serve-wsl-here", action="store_true", dest="serve_wsl_here",
                    help="opt-in (kimi-desktop, D-057): pin the Windows desktop app to "
                         "serve THIS WSL-hosted repo (via --repo + a Windows-safe cwd). "
                         "The desktop then serves this one repo for every project opened; "
                         "no-op off the WSL-repo + Windows-desktop combo. Unpin via "
                         "`clauderize uninstall`.")
    pi.add_argument("-v", "--verbose", action="store_true")
    pi.set_defaults(func=cmd_init)

    ps = sub.add_parser("status", help="print current gameplan status")
    ps.add_argument("--json", action="store_true")
    ps.set_defaults(func=cmd_status)

    pg = sub.add_parser("gameplans", help="list open gameplans (the portfolio)")
    pg.add_argument("--all", action="store_true", help="include finished gameplans")
    pg.add_argument("--json", action="store_true")
    pg.set_defaults(func=cmd_gameplans)

    pf = sub.add_parser("focus", help="switch the focus gameplan (default target)")
    pf.add_argument("gameplan_id", nargs="?",
                    help="gameplan id to focus; omit to report current focus + portfolio")
    pf.add_argument("--json", action="store_true")
    pf.set_defaults(func=cmd_focus)

    pr = sub.add_parser("reindex", help="rebuild the graph cache from markdown")
    pr.set_defaults(func=cmd_reindex)

    pup = sub.add_parser(
        "upgrade",
        help="modernize this repo's corpus: apply the engine's mechanical updates "
             "(config stamp + migrations, missing gate-example files, the "
             "procedure-doc refresh) and print advisory proposals it never "
             "auto-applies")
    pup.add_argument("--report", action="store_true", help="report only — apply nothing")
    pup.add_argument("--json", action="store_true")
    pup.set_defaults(func=cmd_upgrade)

    pd = sub.add_parser("doctor", help="verify the install and report drift")
    pd.add_argument("--deep", action="store_true",
                    help="also spawn each auto-write host's registered MCP command and "
                         "complete an initialize handshake (capability, not just presence)")
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
    po.add_argument("file", nargs="?", help="JSON file of [{op, args}, ...], or '-' for stdin")
    po.add_argument("--list", action="store_true", dest="list_ops",
                    help="list every op (name, read/write, summary, required args), then exit")
    po.add_argument("--schema", metavar="OP", default=None,
                    help="print one op's required + optional args as JSON, then exit")
    po.set_defaults(func=cmd_ops)

    pu = sub.add_parser("uninstall",
                        help="reverse Clauderizer's wiring footprint (preserves docs/)")
    pu.add_argument("--host", default=None,
                    help="scope to one host's footprint (default: the full footprint)")
    pu.set_defaults(func=cmd_uninstall)
    return p


def main(argv: list[str] | None = None) -> int:
    from ._stdio import harden_stdio

    harden_stdio()  # cp1252 consoles must degrade glyphs, never crash (1.5.2)
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
