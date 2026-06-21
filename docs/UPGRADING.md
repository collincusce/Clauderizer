# Upgrading & Uninstalling

> Companion to the README's install section. Every command below is
> copy-paste runnable from a repo root; the maintainers execute these blocks
> verbatim as live walks (transcripts in the gameplan outputs registry).

## Upgrading the engine

Clauderizer separates the **engine** (the installed package) from the
**wiring** (the files `init` writes into your repo). Upgrading is always the
same two moves:

```bash
# 1. update the engine — pick your install mode:
pipx upgrade clauderizer          # pipx installs
uv tool upgrade clauderizer       # uv tool installs
# zero-install uvx users skip this step: uvx --from clauderizer resolves
# the newest release on demand (add --refresh if it answers from cache)

# 2. refresh the wiring (idempotent; engine-owned files only):
uvx --from clauderizer clauderize init
uvx --from clauderizer clauderize doctor    # expect exit 0
```

`init` never clobbers your content: `docs/`, CLAUDE.md text outside the
marker block, and `.clauderizer/profile.lock.toml` edits survive every
re-run. Only engine-owned files — the hook wrapper, the skills, the stanza
between the markers — are refreshed.

### What doctor tells you after an engine update

- `? hook wrapper freshness — wrapper template predates this engine …`
  (exit 3): the old wrapper still works; re-run `clauderize init` to pick up
  template fixes.
- `? hook wrapper freshness — wrapper invokes … but a fresh init would
  compose …` (exit 3): the engine moved (new venv path, changed install
  mode). Re-run `clauderize init`.
- any `✗` (exit 2): drift — wiring points at something that no longer
  launches; doctor's message names the broken leg. Re-run `clauderize init`.

### Upgrading from 0.9.0 or earlier (zero-install users)

0.9.0's `init`, when run via `uvx`, wired the **ephemeral uv-cache path**;
`uv cache clean` then breaks the MCP registration and the SessionStart
digest (doctor reports drift; sessions see an
`[Clauderizer] engine unreachable` breadcrumb). Releases after 0.9.0 wire
the durable `uvx -q --from clauderizer` form instead. The cure is the
standard two moves above, run once on the newer engine.

## Uninstalling

Clauderizer's value lives in `docs/` — and that is **your project's
memory, not the tool's**. Uninstalling removes the machinery and keeps the
memory.

**Recommended: `clauderize uninstall`.** With no flag it reverses the **full
footprint** in one step — the `clauderizer` MCP key from `.mcp.json` and every
per-host config, the clauderizer hooks + wrapper from `.claude/settings.json`,
the `CLAUDE.md`/`AGENTS.md` marker stanzas and native-instructions floors, the
`clauderizer-*` skills, and the `.clauderizer/` directory — each removal
key/marker-scoped so other servers, foreign hooks, and your own content survive.
`--host <name>` scopes it to one host. Your `docs/` memory is never touched:

```bash
uvx --from clauderizer clauderize uninstall              # full footprint, every host
uvx --from clauderizer clauderize uninstall --host cursor   # or just one host
```

Then drop the package itself (the memory in `docs/` stays):

```bash
pipx uninstall clauderizer    # or: uv tool uninstall clauderizer (zero-install uvx users skip this)
```

### Manual fallback (Claude Code wiring only)

If you cannot run the engine, the blocks below remove the **Claude Code**
wiring by hand (`.mcp.json`, the `.claude/settings.json` hooks, the
CLAUDE.md/AGENTS.md stanzas). For any other host, remove its `clauderizer`
MCP entry from that host's config file (see the per-host paths in
[TRUST.md](TRUST.md)). From the repo root:

```bash
# 1. the MCP registration (preserves any other servers in the file)
python3 - <<'EOF'
import json, pathlib
p = pathlib.Path(".mcp.json")
d = json.loads(p.read_text(encoding="utf-8"))
d.get("mcpServers", {}).pop("clauderizer", None)
p.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
EOF

# 2. the hook entries — SessionStart AND UserPromptSubmit (preserves unrelated hooks)
python3 - <<'EOF'
import json, pathlib
p = pathlib.Path(".claude/settings.json")
d = json.loads(p.read_text(encoding="utf-8"))
for event in ("SessionStart", "UserPromptSubmit"):
    groups = d.get("hooks", {}).get(event, [])
    for g in groups:
        g["hooks"] = [h for h in g.get("hooks", [])
                      if "clauderizer-hook" not in h.get("command", "")
                      and ".clauderizer/hook." not in h.get("command", "")
                      and ".clauderizer\\hook." not in h.get("command", "")]
    kept = [g for g in groups if g.get("hooks")]
    if kept:
        d["hooks"][event] = kept
    elif "hooks" in d:
        d["hooks"].pop(event, None)
p.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
EOF

# 3. the engine's working directory (config, wrapper, disposable cache)
rm -rf .clauderizer

# 4. the CLAUDE.md and AGENTS.md stanzas (keeps everything outside the markers)
python3 - <<'EOF'
import pathlib, re
for name in ("CLAUDE.md", "AGENTS.md"):
    p = pathlib.Path(name)
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"<!-- clauderizer:start -->.*?<!-- clauderizer:end -->\n?", "", t, flags=re.S)
    p.write_text(t, encoding="utf-8")
EOF

# 5. the skills
rm -rf .claude/skills/clauderizer-*

# KEEP: docs/ — gameplans, decisions, lessons, findings are project history
```

Then remove the package itself if you installed it
(`pipx uninstall clauderizer` / `uv tool uninstall clauderizer`;
zero-install uvx users have nothing to remove).

Verify the end state:

```bash
uvx --from clauderizer clauderize doctor    # "Not a clauderized repo" — exit 1
```

A Claude Code session in the repo now starts with no digest and no errors.
