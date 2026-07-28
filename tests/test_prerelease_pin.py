"""Pre-release engines pin their portable wiring (the 2.0.0a1 alpha caveat).

An unpinned ``uvx --from clauderizer[mcp]`` resolve only ever sees the latest
STABLE release, so a pre-release engine emitting the bare spec silently hands
the repo to a different (older) serving engine — the H-30 serving-vs-tree
split, reproduced at init time. portable_from_spec ==-pins on pre-releases and
stays bare on stable, and every portable composition site goes through it.
"""

import json

import clauderizer
from clauderizer import hosttargets as HT
from clauderizer import portable_from_spec
from clauderizer.scaffold.init import init


def test_spec_pins_on_prerelease_and_not_on_stable(monkeypatch):
    monkeypatch.setattr(clauderizer, "__version__", "2.0.0a1")
    assert portable_from_spec("mcp") == "clauderizer[mcp]==2.0.0a1"
    assert portable_from_spec() == "clauderizer==2.0.0a1"
    monkeypatch.setattr(clauderizer, "__version__", "3.1.0rc2")
    assert portable_from_spec() == "clauderizer==3.1.0rc2"
    monkeypatch.setattr(clauderizer, "__version__", "1.4.0.dev3")
    assert portable_from_spec() == "clauderizer==1.4.0.dev3"
    monkeypatch.setattr(clauderizer, "__version__", "2.0.0")
    assert portable_from_spec("mcp") == "clauderizer[mcp]"
    monkeypatch.setattr(clauderizer, "__version__", "2.0.1.post1")
    assert portable_from_spec() == "clauderizer"          # post-releases are releases


def test_portable_constants_match_the_running_version():
    """Version-agnostic: on a pre-release tree the constants must carry the ==
    pin; on a stable tree they must not — so this survives 2.0.0 finals."""
    spec = HT.PORTABLE_COMMAND[HT.PORTABLE_COMMAND.index("--from") + 1]
    if clauderizer.is_prerelease():
        assert spec == f"clauderizer[mcp]=={clauderizer.__version__}"
        assert f"clauderizer=={clauderizer.__version__}" in HT.PORTABLE_HOOK_COMMAND
    else:
        assert spec == "clauderizer[mcp]"
        assert "==" not in HT.PORTABLE_HOOK_COMMAND
    assert HT.is_path_safe(HT.PORTABLE_COMMAND)           # pin stays committable


def test_init_emits_the_pinned_portable_command(empty_python_repo):
    """The default multi-host init finishes .mcp.json with the PORTABLE command
    (D-031); on a pre-release engine that command must be ==-pinned or the
    wired server is a different engine."""
    init(empty_python_repo, size="pet", spawn_test=False)
    data = json.loads((empty_python_repo / ".mcp.json").read_text(encoding="utf-8"))
    argv = [data["mcpServers"]["clauderizer"]["command"],
            *data["mcpServers"]["clauderizer"].get("args", [])]
    joined = " ".join(argv)
    if "--from" in argv:                                   # portable form in play
        spec = argv[argv.index("--from") + 1]
        if clauderizer.is_prerelease():
            assert spec.endswith(f"=={clauderizer.__version__}"), joined
        else:
            assert "==" not in spec, joined
    else:
        # Local console-script wiring (this venv) — the committable emitters
        # still pin: covered by the constants test above.
        assert argv[0].endswith("clauderizer-mcp") or "clauderizer" in joined
