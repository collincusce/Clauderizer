"""``clauderize init`` — drop Clauderizer into a repo.

Every step is idempotent: re-running ``init`` fills gaps and refreshes
engine-owned files, but never clobbers user content. The second run on an
unchanged repo produces zero diffs (a tested invariant).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .. import assets, hosts, hosttargets
from ..config import Config, merge_missing
from ..graph import abstract_index, index
from ..markdown import sections, writer
from ..paths import RepoPaths, resolve
from ..profiles import detect

# Zero-install fallback when nothing is on PATH. uvx resolves the package on
# demand. Overridable with --run-cmd "pipx run clauderizer". The -q matters:
# on a cold cache uv prints resolution progress to stderr, which the hook
# wrapper reroutes into stdout (L-07) — straight into session context, and in
# front of the --version identity line the probes parse (stranger-readiness
# Phase 0, cache-clean walk).
DEFAULT_RUN = ["uvx", "-q", "--from", "clauderizer"]


class WiringRefused(RuntimeError):
    """A composed wiring command failed its spawn test; nothing was written.

    The H-04 regression guard: init must never write a command the session
    host cannot launch (e.g. a multi-word --run-cmd that composes an invalid
    subcommand like ``clauderize clauderizer-mcp``).
    """


def _under_uv_cache(p: Path) -> bool:
    """Is this path inside uv's cache — i.e. a uvx ephemeral tool environment?

    ``uvx --from clauderizer clauderize init`` runs from an env under uv's
    CACHE. Wiring those console-script paths into ``.mcp.json`` / the hook
    wrapper produces wiring that dies on ``uv cache clean`` — doctor drift
    plus engine-unreachable breadcrumbs until a re-init (found live in the
    stranger-readiness Phase 0 walk). Such paths must never be wired; the
    durable zero-install ``uvx --from clauderizer`` form is.
    """
    try:
        rp = p.resolve()
    except OSError:
        rp = p
    if "archive-v0" in rp.parts:  # uvx ephemeral envs live here on every OS
        return True
    candidates: list[Path] = []
    env_cache = os.environ.get("UV_CACHE_DIR")
    if env_cache:
        candidates.append(Path(env_cache))
    if sys.platform == "win32":
        lad = os.environ.get("LOCALAPPDATA")
        if lad:
            candidates.append(Path(lad) / "uv" / "cache")
    else:
        try:
            candidates.append(Path.home() / ".cache" / "uv")
        except RuntimeError:
            pass
    for c in candidates:
        try:
            if rp.is_relative_to(c.resolve()):
                return True
        except (OSError, ValueError):
            continue
    return False


def _resolve_invocation(run_cmd: list[str] | None) -> tuple[list[str], list[str]]:
    """Resolve how this machine should launch the MCP server and the hook.

    Returns ``(mcp_argv, hook_argv)`` as full command lists. When the user passes
    an explicit ``--run-cmd`` prefix, the entry-point name is appended to it.
    Otherwise we prefer the installed console scripts (venv/pipx — the common
    Windows→WSL / venv path that ``uvx``-only wiring used to break), falling back
    to ``uvx --from clauderizer`` only when nothing is on PATH.
    """
    if run_cmd:
        return [*run_cmd, "clauderizer-mcp"], [*run_cmd, "clauderizer-hook"]
    # Prefer the console scripts that sit next to the *running* interpreter — the
    # most reliable hit for a venv/pipx install, even when that bin dir isn't on
    # PATH (the Windows→WSL / unactivated-venv case shutil.which misses). On
    # win32 the scripts carry .exe (and live in Scripts/, which IS the
    # interpreter's dir for a venv). NEVER wire a uvx ephemeral env (it dies on
    # `uv cache clean`); fall back to PATH lookup, then the durable uvx form.
    bindir = Path(sys.executable).parent

    def _script(name: str) -> Path | None:
        for candidate in (bindir / f"{name}.exe", bindir / name):
            if candidate.exists():
                return candidate
        return None

    if not _under_uv_cache(bindir):
        mcp = _script("clauderizer-mcp")
        hook = _script("clauderizer-hook")
        if mcp and hook:
            return [str(mcp)], [str(hook)]
    which_mcp = shutil.which("clauderizer-mcp")
    which_hook = shutil.which("clauderizer-hook")
    if (which_mcp and which_hook
            and not _under_uv_cache(Path(which_mcp))):
        # (uvx prepends its ephemeral bin to PATH, so which() finds the same
        # dying paths the bindir check just refused — filter those too)
        return [which_mcp], [which_hook]
    # Absolutize uvx when present: hooks and shimmed commands run in non-login
    # shells whose PATH may not include ~/.local/bin (observed live on WSL).
    uvx = shutil.which(DEFAULT_RUN[0]) or DEFAULT_RUN[0]
    run = [uvx, *DEFAULT_RUN[1:]]
    # The MCP server needs the optional `mcp` extra; the hook and CLI do not. The
    # zero-install uvx path must request `clauderizer[mcp]` for the SERVER command
    # only — `--from clauderizer` never installs the extra, so the wired server
    # printed the missing-package notice and exited without serving (H-14, found
    # live across the pet/standard/saas stranger-readiness dogfood). The hook
    # command stays extra-free so its cold resolve downloads nothing it can't use.
    mcp_run = [*run[:-1], f"{run[-1]}[mcp]"]
    return [*mcp_run, "clauderizer-mcp"], [*run, "clauderizer-hook"]


@dataclass
class InitReport:
    repo: str
    host_profile: str = ""
    size: str = ""
    session_host: str = ""
    host_target: str = ""
    host_target_auto: bool = False  # defaulted to multi (*) with no --host flag
    hosts_wired: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    # Nudges that aren't problems — e.g. the onboarding advisory (D-044): the
    # repo has real docs and the scaffolded Clauderizer docs are still
    # placeholders, so the natural next step is seeding.
    advisories: list[str] = field(default_factory=list)

    def note(self, action: str, path: Path | str, changed: bool) -> None:
        verb = "wrote" if changed else "kept"
        self.actions.append(f"{verb} {path}")
        if changed:
            self.changed.append(str(path))


# A "docs"/"audit" workflow accumulates deliverables across phases, so a dirty
# tree and a missing host test runner are normal — these checks become advisory
# (still shown, never fatal) instead of crying wolf on every resume.
WORKFLOW_ADVISORY = {
    "code": [],
    "docs": ["clean_tree", "branch_base", "branch_creation"],
    "audit": ["clean_tree", "branch_base", "branch_creation", "tests"],
}


def init(
    root: Path,
    *,
    size: str = "standard",
    profile: str = "auto",
    gameplan: str | None = None,
    run_cmd: list[str] | None = None,
    workflow: str = "code",
    session_host: str | None = None,
    host_target: str | None = None,
    spawn_test: bool = True,
    serve_wsl_here: bool = False,
) -> InitReport:
    root = root.resolve()
    paths = resolve(root)
    report = InitReport(repo=str(root))

    # 0. session host of record (D3): explicit flag > what config already
    # records > adoption of the host the existing wiring serves > native.
    existing_config = Config.load(paths.config_file) if paths.config_file.exists() else None
    resolved_host = (
        session_host
        or (existing_config.session_host if existing_config else None)
        or hosts.detect(hosts.read_wiring(paths.mcp_json))
    )
    hosts.parse(resolved_host)  # invalid values fail loudly before anything composes
    report.session_host = resolved_host

    # 0a. Host wiring set (D-046 multi-host default): --host is a SCOPE FILTER,
    # not exclusive identity. Bare init expands enabled_hosts (default ["*"] =
    # every project-level host). Session preference (host_target) stays for
    # doctor primary / display — runtime routing uses session.detect (D-047).
    prior_enabled = (
        list(existing_config.enabled_hosts)
        if existing_config is not None else ["*"]
    )
    try:
        wired = hosttargets.hosts_to_wire(
            host_flag=host_target, enabled_hosts=prior_enabled)
    except hosttargets.HostTargetError:
        raise
    report.hosts_wired = list(wired)
    # Session preference: scoped --host wins; else keep prior; else claude-code.
    if host_target is not None and str(host_target).strip():
        resolved_target = hosttargets.parse_host_target(host_target)
    else:
        resolved_target = hosttargets.parse_host_target(
            (existing_config.host_target if existing_config else None)
            or hosttargets.detect_host_target(root)
            or hosttargets.CLAUDE_CODE
        )
    report.host_target = resolved_target
    # First bare init only: presentation hint that multi-host is the default
    # (not a wiring warning — report.warnings stays for spawn probes).
    report.host_target_auto = host_target is None and existing_config is None

    engine_mcp, engine_hook = _resolve_invocation(run_cmd)
    mcp_cmd = hosts.compose(engine_mcp, resolved_host)
    hook_cmd = hosts.compose(engine_hook, resolved_host)

    # 0b. spawn-test every composed command BEFORE any write (H-04 guard):
    # wiring that cannot answer --version must never reach .mcp.json or the
    # hook registration. "Unverifiable" (no interop path to the session host)
    # proceeds with a loud warning naming the command to certify from there.
    if spawn_test:
        for label, argv in (("MCP server", mcp_cmd), ("SessionStart hook", hook_cmd)):
            probe = hosts.spawn_probe(argv)
            if probe.status == "fail":
                raise WiringRefused(
                    f"the composed {label} command failed its spawn test — "
                    f"nothing was written.\n"
                    f"  command: {' '.join(argv)}\n"
                    f"  probe:   {probe.detail}\n"
                    f"  Drop --run-cmd to let init resolve the installed console "
                    f"scripts, or pass\n"
                    f"  --session-host windows-wsl:<distro> for a WSL engine driven "
                    f"from Windows."
                )
            if probe.status == "unverifiable":
                report.warnings.append(f"{label} wiring unverifiable: {probe.detail}")

    # 1–2. detect host language
    if profile == "auto":
        prof, _alts = detect.detect(root)
    else:
        prof = detect.load(profile)
    report.host_profile = prof.name

    # 3. size -> default config
    defaults = Config.for_size(size, host_profile=prof.name)
    defaults.preflight_advisory = list(WORKFLOW_ADVISORY.get(workflow, []))
    report.size = size

    # 4. config.toml (merge missing on re-run); record the session host of
    # record so every later init/doctor composes and verifies for it.
    config = merge_missing(existing_config, defaults) if existing_config else defaults
    config.session_host = resolved_host
    config.host_target = resolved_target
    # Persist multi default unless this run was a scoped --host install.
    if host_target is not None and str(host_target).strip():
        # Scope filter for this run: if config was multi, keep multi enabled so
        # a later bare init re-expands; only record singleton when the prior
        # config was already a singleton or first-time scoped install.
        if existing_config is None or hosttargets.ALL_HOSTS not in (
            existing_config.enabled_hosts or []
        ):
            config.enabled_hosts = [resolved_target]
        else:
            config.enabled_hosts = ["*"]
    else:
        config.enabled_hosts = ["*"]
    # Init is an upgrade moment (D-042): stamp the corpus with this engine's
    # procedure version so status can tell a current corpus from a stale one.
    from .. import PROCEDURE_VERSION as _PROC_V

    config.procedure_version = _PROC_V
    changed = writer.create_if_absent(paths.config_file, config.to_toml()) or _rewrite_if_diff(
        paths.config_file, config.to_toml()
    )
    report.note("config", paths.config_file, changed)

    # 5. profile.lock.toml — write once, then PRESERVE. It's the project's editable
    # per-project command override (read back by detect.load_for_repo); regenerating
    # it on every run would clobber those edits. Delete it to re-derive from a profile.
    changed = writer.create_if_absent(paths.profile_lock, prof.to_lock_toml())
    report.note("profile.lock", paths.profile_lock, changed)

    # 6. scaffold docs (enabled modules only; never clobber)
    paths.procedure_file.parent.mkdir(parents=True, exist_ok=True)
    changed = writer.create_if_absent(paths.procedure_file, assets.procedure_text())
    report.note("procedure", paths.procedure_file, changed)
    for module in config.modules:
        tmpl = assets.doc_template(module)
        if tmpl is None:
            continue
        path = paths.doc(module)
        changed = writer.create_if_absent(path, tmpl)
        report.note(f"doc:{module}", path, changed)

    # 6b. onboarding advisory (D-044): this repo already has documentation and
    # the Clauderizer docs are still scaffold placeholders — say so once, with
    # the next step. Detection is read-only; the engine never seeds anything.
    from .. import onboard as _onboard

    _unseeded = _onboard.unseeded_docs(paths)
    if _unseeded:
        _cands = _onboard.spec_candidates(paths)
        if _cands:
            report.advisories.append(
                f"this repo has {len(_cands)} existing doc(s) that look like specs "
                f"(e.g. {_cands[0]['path']}) while {len(_unseeded)} scaffolded "
                f"Clauderizer doc(s) are still placeholders — have your agent run "
                f"cz_onboard (or the clauderizer-onboard skill) to seed memory from them")

    # 7. optional first gameplan
    if gameplan:
        from .. import mutations

        r = mutations.create_gameplan(paths, gameplan)
        config.active_gameplan = r["gameplan_id"]
        _rewrite_if_diff(paths.config_file, config.to_toml())
        report.note("gameplan", r["dir"], bool(r["files_changed"]))

    # 8. CLAUDE.md stanza (marker block; preserves the rest — content found
    # INSIDE the markers that is plainly not the stanza gets moved out below
    # the block, never deleted; surface that loudly when it happens).
    stanza = assets.template_text("claude_stanza.md")
    for label, target in (("CLAUDE.md", paths.claude_md),
                          ("AGENTS.md", paths.agents_md)):
        # 8b: AGENTS.md gets the SAME host-agnostic marker block, so kimi
        # (KIMI_AGENTS_MD) and any other AGENTS.md-aware harness get Clauderizer
        # too (D2). One source stanza for both files: they cannot drift (L-16).
        had_banner = (target.exists() and
                      sections.RECOVERY_BANNER in target.read_text(encoding="utf-8"))
        changed = writer.upsert_marker_block(target, "clauderizer", stanza)
        report.note(label, target, changed)
        if (changed and not had_banner and target.exists()
                and sections.RECOVERY_BANNER in target.read_text(encoding="utf-8")):
            print(f"  ! {label}: found project content inside the managed block — "
                  f"moved it below the block (review and relocate or delete)")

    # 9. install skills (engine-owned: refresh)
    for skill_dir in assets.skill_dirs():
        dest_dir = root / ".claude" / "skills" / skill_dir.name
        for src in skill_dir.iterdir():
            if src.is_file():
                changed = _rewrite_if_diff(dest_dir / src.name, src.read_text(encoding="utf-8"))
                report.note(f"skill:{skill_dir.name}", dest_dir / src.name, changed)

    # 10–11b. Multi-host wiring (D-046). Wire every host in `wired` (default: all).
    # Claude Code keeps SessionStart hooks + kimi-setup (INVARIANT-07). Other hosts
    # get emit_host_wiring. When multi-host includes non-claude auto-write emitters,
    # .mcp.json is finished with the PORTABLE command so the repo is committable
    # across machines (D-031); pure claude-code-only still prefers local mcp_cmd.
    wire_claude = hosttargets.CLAUDE_CODE in wired
    wire_others = [h for h in wired if h != hosttargets.CLAUDE_CODE]
    multi = len(wired) > 1 or hosttargets.ALL_HOSTS in (config.enabled_hosts or [])

    if wire_claude:
        # 11. SessionStart hook wrapper + registration (D4).
        wrapper_name = hosts.wrapper_filename(resolved_host)
        wrapper_path = root / ".clauderizer" / wrapper_name
        changed = _rewrite_if_diff(
            wrapper_path,
            hosts.render_hook_wrapper(engine_hook, root=root,
                                      windows=wrapper_name.endswith(".cmd")),
            exact_newlines=True,
        )
        if changed and not wrapper_name.endswith(".cmd"):
            try:
                wrapper_path.chmod(wrapper_path.stat().st_mode | 0o755)
            except OSError:
                pass
        report.note("hook wrapper", wrapper_path, changed)
        registered_hook = hosts.hook_wrapper_invocation(root, resolved_host)
        if spawn_test:
            probe = hosts.hook_digest_probe(registered_hook, cwd=hosts.non_repo_cwd())
            if probe.status == "fail":
                raise WiringRefused(
                    f"the SessionStart wrapper failed its spawn test — hook registration "
                    f"left unchanged.\n"
                    f"  command: {' '.join(registered_hook)}  (from a non-repo cwd)\n"
                    f"  probe:   {probe.detail}\n"
                    f"  The wrapper was written to {wrapper_path} for inspection; the "
                    f"engine command\n"
                    f"  itself probed OK in the pre-write gate, so suspect the wrapper "
                    f"shell (/bin/sh, cmd, wsl.exe) or the repo anchor."
                )
            if probe.status == "unverifiable":
                report.warnings.append(f"SessionStart wrapper unverifiable: {probe.detail}")
        changed = _register_hook(root / ".claude" / "settings.json", registered_hook)
        report.note("hook", root / ".claude" / "settings.json", changed)

        # The Kimi Code CLI guide (.clauderizer/kimi-setup.md) is emitted by the
        # per-host wiring (emit_host_wiring('kimi')) whenever the kimi host is
        # wired — the multi-host default wires it, so it is no longer a claude-leg
        # special case (D-049; single-sourced in hosttargets.kimi_setup_guide).

        # .mcp.json: local (possibly machine-specific) only when Claude-only.
        # Multi-host repos get the portable command below after other emitters.
        if not multi:
            changed = _register_mcp(paths.mcp_json, mcp_cmd)
            report.note(".mcp.json", paths.mcp_json, changed)
            if not hosttargets.is_path_safe(mcp_cmd):
                gi = _ensure_gitignore(root / ".gitignore", paths.mcp_json.name)
                report.note(".gitignore (.mcp.json — local wiring, not committable)",
                            root / ".gitignore", gi)

    for hid in wire_others:
        for res in hosttargets.emit_host_wiring(hid, root):
            report.note(f"{res.label}:{hid}", res.path, res.changed)

    # Bespoke auto-write hosts (kimi-desktop and any future one — D-053/D-056): the
    # hosts whose config is a per-user runtime home clauderizer auto-writes. Generic
    # over the BESPOKE_HOSTS registry. Detected-only — a silent no-op when the app is
    # not installed; on a detected-but-unwritable/unregistrable config, or one that
    # can't serve THIS repo (unservable), it drops the host's setup guide so a
    # spawn-broken agent can READ its way out (file tools still work — D-054).
    from .. import bespoke_hosts

    # Opt-in WSL-serving pin (D-057): --serve-wsl-here pins the kimi-desktop daimon to
    # serve THIS WSL repo (--repo <UNC> + a Windows-safe cwd), recorded in a durable
    # sidecar so self-heal re-applies it after the app wipes its mcp.json (C-01). Written
    # BEFORE the wire loop so the host composes the pin. A no-op (with a note) off the
    # WSL-repo + Windows-desktop combo.
    if serve_wsl_here:
        from .. import kimidesktop, winhost
        desk_cfg = kimidesktop.detect_config()
        distro = os.environ.get("WSL_DISTRO_NAME", "")
        if (desk_cfg is not None and distro
                and kimidesktop._is_windows_side(desk_cfg, kimidesktop.WSL_USERS_DIR)
                and not str(root).startswith("/mnt/")):
            unc = winhost.wsl_repo_to_unc(root, distro)
            sidecar = kimidesktop.write_serve_pin(desk_cfg, unc)
            report.note("kimi-desktop serve-pin", sidecar, True)
            report.warnings.append(
                f"kimi-desktop: PINNED to serve this repo ({unc}). The desktop will serve "
                "THIS repo for every project you open in the app (opt-in override, D-057) — "
                "restart the app / open a new session to pick it up. To unpin: run "
                "`clauderize uninstall` or delete the clauderizer-serve.json sidecar.")
        else:
            report.warnings.append(
                "kimi-desktop: --serve-wsl-here had no effect — it applies only to a "
                "WSL-hosted repo opened in the Windows desktop app (nothing to pin here).")

    for host in bespoke_hosts.all_hosts().values():
        desk = host.wire()
        guide = root / ".clauderizer" / f"{host.id}-mcp-setup.md"
        if desk["status"] == "wired":
            report.note(f"{host.id} MCP", desk["path"], desk.get("changed", True))
            for w in desk["warnings"]:
                report.warnings.append(f"{host.id}: {w}")
            if desk.get("unservable"):
                report.note(f"{host.id} guide",
                            guide, _rewrite_if_diff(guide, host.setup_guide()))
                report.warnings.append(f"{host.id}: {desk['unservable']}")
        elif desk["status"] in ("failed", "unregistrable"):
            report.note(f"{host.id} guide",
                        guide, _rewrite_if_diff(guide, host.setup_guide()))
            for w in desk["warnings"]:
                report.warnings.append(f"{host.id}: {w}")

    # Multi-host (or any non-claude that shares .mcp.json): ensure portable .mcp.json.
    if multi or (not wire_claude and any(
        hosttargets.HOST_EMITTERS.get(h)
        and hosttargets.HOST_EMITTERS[h].auto_write
        and hosttargets.HOST_EMITTERS[h].config_path == ".mcp.json"
        for h in wire_others
    )):
        # Prefer portable so dual Claude+Grok/Cursor machines share one committable file.
        port = hosttargets.PORTABLE_COMMAND
        # Use [mcp] extra form for the server when possible — match engine_mcp shape
        # if it is already portable; otherwise stick to PORTABLE_COMMAND.
        changed = _register_mcp(paths.mcp_json, list(port))
        report.note(".mcp.json (portable multi-host)", paths.mcp_json, changed)

    # 12. gitignore the disposable caches; build the graph + abstract indexes
    gi = root / ".gitignore"
    changed = _ensure_gitignore(gi, ".clauderizer/index.json")
    changed = _ensure_gitignore(gi, ".clauderizer/abstract_index.json") or changed
    # per-user proposal-triage ledger — personal "seen it" state, not team memory (D-052)
    changed = _ensure_gitignore(gi, ".clauderizer/proposals.local.toml") or changed
    # Local-only journals: machine-local operational history (telemetry) and the
    # PII-linted dream journal (D-058) — never committable in a target repo.
    changed = _ensure_gitignore(gi, ".clauderizer/telemetry.jsonl") or changed
    changed = _ensure_gitignore(gi, ".clauderizer/dreams.jsonl") or changed
    changed = _ensure_gitignore(gi, ".clauderizer/dreams.schedule.toml") or changed
    report.note(".gitignore", gi, changed)
    graph = index.build(paths.docs)
    index.write_cache(graph, paths.index_file, paths.docs)
    abstract_index.write_cache(abstract_index.build(paths), paths.abstract_index_file)

    return report


# --- helpers ------------------------------------------------------------------


def _rewrite_if_diff(path: Path, content: str, *, exact_newlines: bool = False) -> bool:
    """Write ``content`` if the file differs; report whether anything changed.

    ``exact_newlines`` writes/compares BYTES: executable wrapper scripts carry
    their newline convention as part of their contract (hook.sh must stay \\n
    even when written from a win32 host — the distro's sh chokes on \\r; the
    cmd template's \\r\\n must not become \\r\\r\\n via text-mode translation,
    which also broke init idempotency on win32 by making the read-back never
    equal the render).
    """
    writer.refuse_if_symlink(path)
    if exact_newlines:
        data = content.encode("utf-8")
        if path.exists() and path.read_bytes() == data:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return True
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _register_mcp(mcp_json: Path, mcp_cmd: list[str]) -> bool:
    data = {}
    if mcp_json.exists():
        try:
            data = json.loads(mcp_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    servers = data.setdefault("mcpServers", {})
    entry = {"command": mcp_cmd[0], "args": list(mcp_cmd[1:])}
    if servers.get("clauderizer") == entry:
        return False
    servers["clauderizer"] = entry
    writer.refuse_if_symlink(mcp_json)
    mcp_json.parent.mkdir(parents=True, exist_ok=True)
    mcp_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


# The Claude Code hook events the wrapper is registered under (D-025/D1). The
# SAME wrapper command serves both: SessionStart is the cold-start digest (and
# re-fires with source=compact, so it also covers post-compaction re-injection);
# UserPromptSubmit runs the analyze gate per prompt. PreCompact/PostCompact are
# intentionally absent — Claude Code does not inject their stdout into context
# (D1), so registering them would be dead wiring. The engine's dispatcher
# implements every event regardless of which a host fires.
HOOK_EVENTS = ("SessionStart", "UserPromptSubmit")


def _register_hook(settings_json: Path, hook_argv: list[str],
                   events: tuple[str, ...] = HOOK_EVENTS) -> bool:
    data = {}
    if settings_json.exists():
        try:
            data = json.loads(settings_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    hook_cmd = " ".join(hook_argv)
    hooks = data.setdefault("hooks", {})

    for event in events:
        # Drop ANY existing clauderizer hook entry — direct entry-point wiring or
        # the D4 wrapper (hosts.is_hook_command is the shared matcher) — not just
        # an exact-string match. This makes re-running init with a changed
        # invocation (e.g. uvx -> venv path -> wrapper) REPLACE the hook instead
        # of appending a duplicate. Non-clauderizer hooks under this event are
        # preserved untouched.
        cleaned: list[dict] = []
        for group in hooks.get(event, []):
            kept = [h for h in group.get("hooks", [])
                    if not hosts.is_hook_command(h.get("command", ""))]
            if kept:
                cleaned.append({**group, "hooks": kept})
            elif not group.get("hooks"):
                cleaned.append(group)  # preserve unrelated empty groups verbatim
        cleaned.append({"hooks": [{"type": "command", "command": hook_cmd}]})
        hooks[event] = cleaned

    new_text = json.dumps(data, indent=2) + "\n"
    if settings_json.exists() and settings_json.read_text(encoding="utf-8") == new_text:
        return False
    writer.refuse_if_symlink(settings_json)
    settings_json.parent.mkdir(parents=True, exist_ok=True)
    settings_json.write_text(new_text, encoding="utf-8")
    return True


def _ensure_gitignore(gitignore: Path, line: str) -> bool:
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if line in existing.splitlines():
        return False
    new = existing.rstrip("\n") + ("\n" if existing else "") + line + "\n"
    writer.refuse_if_symlink(gitignore)
    gitignore.write_text(new, encoding="utf-8")
    return True
