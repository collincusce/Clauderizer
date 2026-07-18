"""MCP initialize-handshake verification primitive (mcp_probe, D-056) — extracted from
the kimi-desktop wiring (D-055) so any host's registered MCP command can be
capability-checked (L-25). `run` is injected so no test spawns a real process."""

import json

from clauderizer import mcp_probe as mp


def _run_serverinfo(name="clauderizer", version="1.10.0", eol=b"\r\n"):
    """A fake `run` for handshake_probe: replies with an MCP initialize result."""
    def run(argv, cwd, stdin, timeout):
        resp = {"jsonrpc": "2.0", "id": 1, "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": name, "version": version}}}
        return 0, json.dumps(resp).encode() + eol, b""
    return run


def test_handshake_ok_asserts_serverinfo():
    r = mp.handshake_probe({"command": "clauderizer-mcp", "args": []},
                           platform="linux", run=_run_serverinfo())
    assert r["status"] == "ok"
    assert r["server_name"] == "clauderizer" and r["server_version"] == "1.10.0"


def test_handshake_wrong_server_name_fails():
    r = mp.handshake_probe({"command": "x"}, platform="linux",
                           run=_run_serverinfo(name="somethingelse"))
    assert r["status"] == "fail" and "somethingelse" in r["detail"]


def test_handshake_no_serverinfo_fails_with_tail():
    def run(argv, cwd, stdin, timeout):
        return 0, b"not json at all\n", b"traceback: boom"
    r = mp.handshake_probe({"command": "x"}, platform="linux", run=run)
    assert r["status"] == "fail" and "no serverInfo" in r["detail"] and "boom" in r["detail"]


def test_handshake_spawn_not_found_fails():
    def run(argv, cwd, stdin, timeout):
        raise FileNotFoundError()
    r = mp.handshake_probe({"command": "gone.exe"}, platform="win32", run=run)
    assert r["status"] == "fail" and "cannot spawn" in r["detail"]


def test_handshake_timeout_fails():
    import subprocess
    def run(argv, cwd, stdin, timeout):
        raise subprocess.TimeoutExpired(cmd="x", timeout=timeout)
    r = mp.handshake_probe({"command": "x"}, platform="linux", timeout=2, run=run)
    assert r["status"] == "fail" and "timed out" in r["detail"]


def test_handshake_no_command_fails():
    r = mp.handshake_probe({}, platform="linux")
    assert r["status"] == "fail" and "no command" in r["detail"]


def test_spawn_target_translates_windows_exe_for_wsl():
    # The /mnt path is POSIX by definition, so it renders forward-slashed on any host
    # (incl. a Windows CI runner) — the default mnt_root is a PurePosixPath.
    argv, unreach = mp.spawn_target(
        {"command": r"C:\Users\rafaj\pipx\venvs\clauderizer\Scripts\clauderizer-mcp.exe",
         "args": []}, platform="linux")
    assert unreach is None
    assert argv == ["/mnt/c/Users/rafaj/pipx/venvs/clauderizer/Scripts/clauderizer-mcp.exe"]


def test_spawn_target_native_command_unchanged():
    argv, unreach = mp.spawn_target({"command": "/usr/bin/uvx", "args": ["--from", "x"]},
                                    platform="linux")
    assert unreach is None and argv == ["/usr/bin/uvx", "--from", "x"]


def test_handshake_unverifiable_for_wsl_exe_without_interop(monkeypatch):
    # wsl.exe-shimmed command seen from a host with no Windows interop → unverifiable,
    # never a false pass or a false fail (L-25).
    monkeypatch.setattr(mp.shutil, "which", lambda n: None)
    r = mp.handshake_probe({"command": "wsl.exe", "args": ["-d", "Ubuntu", "x"]},
                           platform="linux")
    assert r["status"] == "unverifiable" and "verify from the session host" in r["detail"]
