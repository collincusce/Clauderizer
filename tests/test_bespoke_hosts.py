"""The bespoke auto-write host framework (D-056). Proves the shared lifecycle
(detect → compose → merge → self-heal → remove) is genuinely GENERIC: a second,
test-only host with a different servers-key runs the whole lifecycle with zero
kimi-desktop code. Every write is against a temp tree (L-29)."""

import json

from clauderizer import bespoke_hosts as bh
from clauderizer import kimidesktop as kd


def test_registry_contains_kimi_desktop():
    assert bh.BESPOKE_HOSTS.get("kimi-desktop") is kd._HOST
    assert isinstance(kd._HOST, bh.BespokeHost)


def test_generic_merge_is_nondestructive_and_idempotent(tmp_path):
    cfg = tmp_path / "servers.json"
    cfg.write_text(json.dumps({"servers": {"other": {"command": "x"}}}), encoding="utf-8")
    entry = {"command": "clauderizer-mcp", "args": []}
    _, first = bh.merge_entry(cfg, entry, servers_key="servers")
    _, second = bh.merge_entry(cfg, entry, servers_key="servers")
    assert first is True and second is False                     # idempotent
    servers = json.loads(cfg.read_text(encoding="utf-8"))["servers"]
    assert servers["other"] == {"command": "x"}                 # preserved
    assert servers["clauderizer"] == entry
    assert bh.remove_entry(cfg, servers_key="servers") is True
    assert "clauderizer" not in json.loads(cfg.read_text(encoding="utf-8"))["servers"]


class _FakeHost(bh.BespokeHost):
    """A minimal second bespoke host — a different servers_key, its own config path,
    NO Windows/daimon specifics — to prove the base lifecycle is host-agnostic."""

    id = "fake-host"
    opt_out_env = "CLAUDERIZER_NO_FAKE"
    servers_key = "servers"

    def __init__(self, cfg):
        self._cfg = cfg

    def candidate_configs(self, **kw):
        return [self._cfg]

    def compose_entry(self, cfg, **kw):
        return ({"command": "fake-mcp", "args": ["--serve"]}, [])

    def setup_guide(self):
        return "fake host setup guide"


def test_second_host_runs_the_full_lifecycle_generically(tmp_path):
    cfg = tmp_path / "app" / "cfg" / "servers.json"
    cfg.parent.mkdir(parents=True)                              # detected-only: dir exists
    host = _FakeHost(cfg)
    env = dict(home=tmp_path, platform="linux", environ={}, in_wsl=False)

    assert host.detect_config(**env) == cfg
    r = host.wire(**env)
    assert r["status"] == "wired" and r["changed"] is True
    assert json.loads(cfg.read_text(encoding="utf-8"))["servers"]["clauderizer"] == \
        {"command": "fake-mcp", "args": ["--serve"]}
    assert host.wire(**env)["changed"] is False                # idempotent no-op

    cfg.write_text('{"servers": {}}', encoding="utf-8")          # app wipes it
    assert host.self_heal(**env)["changed"] is True             # self-heal re-applies

    assert host.remove_registration(cfg) is True
    assert "clauderizer" not in json.loads(cfg.read_text(encoding="utf-8"))["servers"]


def test_second_host_respects_its_own_opt_out(tmp_path):
    cfg = tmp_path / "app" / "cfg" / "servers.json"
    cfg.parent.mkdir(parents=True)
    host = _FakeHost(cfg)
    assert host.detect_config(home=tmp_path, platform="linux",
                              environ={"CLAUDERIZER_NO_FAKE": "1"}, in_wsl=False) is None
    assert host.wire(home=tmp_path, platform="linux",
                     environ={"CLAUDERIZER_NO_FAKE": "1"}, in_wsl=False)["status"] == "not_detected"


def test_second_host_unregistrable_when_compose_returns_none(tmp_path):
    cfg = tmp_path / "app" / "cfg" / "servers.json"
    cfg.parent.mkdir(parents=True)

    class _NoCmdHost(_FakeHost):
        def compose_entry(self, cfg, **kw):
            return (None, ["no launchable command here"])

    host = _NoCmdHost(cfg)
    r = host.wire(home=tmp_path, platform="linux", environ={}, in_wsl=False)
    assert r["status"] == "unregistrable" and r["entry"] is None
    assert r["warnings"] == ["no launchable command here"]
    assert not cfg.exists()                                     # nothing written — no dead entry


def test_second_host_surfaces_unservable_reason(tmp_path):
    cfg = tmp_path / "app" / "cfg" / "servers.json"
    cfg.parent.mkdir(parents=True)

    class _UnservableHost(_FakeHost):
        def unservable_reason(self, cfg, *, in_wsl, users_dir):
            return "this repo can't be served here"

    r = _UnservableHost(cfg).wire(home=tmp_path, platform="linux", environ={}, in_wsl=False)
    assert r["status"] == "wired" and r["unservable"] == "this repo can't be served here"
