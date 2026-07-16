# kimi-code-truth-up-k3-mcp-autowrite — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-16

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Confirm current Kimi Code CLI contract | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Flip kimi MCP to auto-write .kimi-code/mcp.json | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Reconcile kimi setup guides and fix stale .kimi paths | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Docs sweep, cascade, and release | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
kimi-code-cli-contract: Kimi Code CLI (github.com/MoonshotAI/kimi-code, TypeScript/npm) is the SUCCESSOR to the older Kimi CLI (kimi-cli, pip/Python, .kimi/). It serves Kimi K2.6/K3. Config: project .kimi-code/ + user ~/.kimi-code/ ($KIMI_CODE_HOME). MCP: project .kimi-code/mcp.json, key=mcpServers, entry={command,args} (also url/transport/env/cwd/enabled) — AUTO-WRITABLE (Cursor-identical), project overrides user by name. Hooks: [[hooks]] array in config.toml, 13 events incl SessionStart/UserPromptSubmit/PreCompact/PostCompact; stdout injected to context iff exit 0 (exit 2 = stderr correction) — TOML, guide-only. Skills: loaded from .kimi-code/skills/, .agents/skills/, ~/.agents/skills/, built-in — NOT .claude/skills (Clauderizer skills do NOT come free here). AGENTS.md: repo ships AGENTS.md+CLAUDE.md; likely read but unconfirmed for kimi-code.
premise-correction: D-049's premise ("kimi is one host that renamed .kimi->.kimi-code") is WRONG. There are TWO distinct products: legacy Kimi CLI (.kimi/, existing `kimi` host, correct as-is) and successor Kimi Code CLI (.kimi-code/, serves K3). The existing `kimi` host is NOT stale — it correctly targets the legacy product. Supporting K3 out-of-the-box = adding Kimi Code CLI as a host, not renaming kimi. Two extra gaps vs D-049: (1) skills are not free on kimi-code (different skills dirs), (2) AGENTS.md floor read-status unconfirmed. Needs a decision correction + plan amendment.
```

### Phase 1 Outputs

```
kimi-emitter-autowrite: hosttargets.HOST_EMITTERS['kimi'] now = HostEmitter('kimi', '.kimi-code/mcp.json', 'mcpServers', True). emit_mcp('kimi') writes .kimi-code/mcp.json non-destructively; remove_mcp removes only clauderizer; detect_host_target auto-detects it; wiring_contract_sweep + path_safety_audit cover it (table-derived). Tests added: test_kimi_code_auto_writes_project_mcp_json, _emit_is_non_destructive, _uninstall_removes_only_clauderizer, test_detect_host_target_finds_kimi_code. Dropped kimi from test_guide_only_hosts_write_nothing. Suite 793->797 passed, 5 skipped.
```

### Phase 2 Outputs

```
kimi-guide-single-sourced: Single-sourced the kimi guide in hosttargets.kimi_setup_guide() (portable KIMI_HOOK_COMMAND, KIMI_HOOK_EVENTS = SessionStart/UserPromptSubmit/PreCompact/PostCompact). emit_host_wiring('kimi') now emits .clauderizer/kimi-setup.md (label 'hook-guide') alongside the auto-written mcp. Removed dead init.py _render_kimi_setup + _KIMI_HOOK_EVENTS (claude-leg special case); guide now rides the per-host wiring, produced by the multi-host default. Fixed configure_hints['kimi'] and paths.kimi_setup docstring to .kimi-code. Guide §3 targets ~/.kimi-code/config.toml; §4 documents skills exposure (.agents/skills / .kimi-code/skills, not .claude/skills). Only stale .kimi ref left in src is the deliberate 'legacy Kimi CLI used ~/.kimi/' mention.
```

## Corrections Log

### C-01 — Phase 0

**Phase**: 0
**What gameplan said**: D-049 framed the work as a truth-up of ONE host: the existing `kimi` host renamed its config dir .kimi -> .kimi-code and its MCP graduated to auto-write.
**What was actually correct**: There are two distinct products: legacy Kimi CLI (kimi-cli, pip, ~/.kimi/) and its successor Kimi Code CLI (kimi-code, npm, .kimi-code/) which is what serves Kimi K3. The existing `kimi` host correctly matched the LEGACY product; it was not stale. Per user decision, we REPOINT the `kimi` host id to the successor Kimi Code CLI (.kimi-code) and treat legacy Kimi CLI as EOL. Two facts D-049 missed: (1) Kimi Code CLI does NOT read .claude/skills (it reads .kimi-code/skills, .agents/skills), so per user decision the setup guide DOCUMENTS how to expose Clauderizer skills there rather than auto-emitting; (2) AGENTS.md read-status on kimi-code is likely (repo ships AGENTS.md) but unconfirmed.
**Why**: Phase 0's contract verification against current Kimi Code CLI docs (moonshotai.github.io/kimi-code, www.kimi.com/code, github.com/MoonshotAI/kimi-code) revealed the predecessor/successor split. Net effect on the plan is small — repointing the `kimi` host to .kimi-code with auto-write MCP is exactly Phases 1-3 as written — but the rationale and the skills/AGENTS.md notes are corrected.
**Lesson**: When a host's config paths look 'stale', confirm whether the host is one product that moved or two products (predecessor/successor) before renaming — Moonshot's kimi-cli (~/.kimi) and kimi-code (.kimi-code) are distinct tools, and the 'stale' path was correct for the legacy one.
