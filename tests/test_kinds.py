"""Phase 2 of concurrent-multi-axis-gameplans: kinds as real profiles.

The kind layer (kinds/*.toml + overlay), kind-aware create_gameplan, and the
DISPLAY-ONLY lexicon — proving a campaign reads in its own vocabulary in
digests/handoffs while the on-disk headings stay canonical so every parser works.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from clauderizer import config as cfg
from clauderizer import kinds
from clauderizer import ops
from clauderizer import paths as P
from clauderizer.rituals import handoff, status_bundle as S


@contextmanager
def _chdir(path: Path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _pc(repo: Path):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


# --- the kind layer ------------------------------------------------------------


def test_packaged_kinds_present():
    all_kinds = kinds.load_all()
    assert {"driven", "loop", "campaign"} <= set(all_kinds)
    assert kinds.is_known("campaign") and not kinds.is_known("nope")


def test_driven_is_identity_lexicon():
    d = kinds.resolve("driven")
    assert d.label("phase") == "phase" and d.label("output") == "output"
    assert d.first_phase == "Bootstrap"


def test_campaign_lexicon_and_template():
    c = kinds.resolve("campaign")
    assert c.label("phase") == "stage" and c.label("output") == "asset"
    assert c.first_phase == "Concept"
    assert "virality" in c.preflight_checks  # generic gate names (wired in Phase 3)


def test_unknown_kind_resolves_to_identity():
    k = kinds.resolve("totally-made-up")
    assert k.name == "totally-made-up"
    assert k.label("phase") == "phase"  # never crashes; passes terms through


def test_overlay_adds_and_overrides(tmp_path):
    overlay = tmp_path / "kinds"
    overlay.mkdir()
    (overlay / "research.toml").write_text(
        'name = "research"\n[lexicon]\nphase = "log entry"\n', encoding="utf-8")
    (overlay / "driven.toml").write_text(
        'name = "driven"\n[template]\nfirst_phase = "Kickoff"\n', encoding="utf-8")
    loaded = kinds.load_all(overlay)
    assert loaded["research"].label("phase") == "log entry"   # custom kind added
    assert loaded["driven"].first_phase == "Kickoff"          # packaged kind overridden


# --- kind-aware create_gameplan -----------------------------------------------


def test_create_gameplan_templates_first_phase_from_kind(temp_repo):
    with _chdir(temp_repo):
        res = ops.cz_create_gameplan("spring promo", kind="campaign")
        assert res["ok"] and res["kind"] == "campaign"
        gid = res["gameplan_id"]
    gp = (temp_repo / "docs" / "gameplans" / gid / "GAMEPLAN.md").read_text(encoding="utf-8")
    assert "> Kind: campaign" in gp
    assert "Phase 0: Concept" in gp  # templated from the kind, heading still canonical


def test_create_gameplan_rejects_unknown_kind(temp_repo):
    with _chdir(temp_repo):
        res = ops.cz_create_gameplan("whatever", kind="bogus")
        assert not res["ok"] and "unknown kind" in res["error"]
        assert "campaign" in res["error"]  # lists the known ones


# --- display-only lexicon: campaign reads in its vocabulary, parsers unaffected -


def test_campaign_digest_uses_lexicon_but_ondisk_stays_canonical(temp_repo):
    paths, _ = _pc(temp_repo)
    with _chdir(temp_repo):
        gid = ops.cz_create_gameplan("spring promo", kind="campaign")["gameplan_id"]
    paths, config = _pc(temp_repo)  # reload: focus is now the campaign
    bundle = S.compute(paths, config)
    assert bundle["kind"] == "campaign"
    assert "stage" in bundle["summary"] and "phase" not in bundle["summary"]
    digest = S.render_digest(bundle)
    assert "stage" in digest

    # on-disk headings + the phase parser are untouched (display-only, D3)
    gp = (paths.gameplan_dir(gid) / "GAMEPLAN.md").read_text(encoding="utf-8")
    assert "## Phase Breakdown" in gp and "### Phase 0" in gp
    assert len(S._phase_rows(paths.gameplan_dir(gid))) == 1  # parser still finds it


def test_campaign_handoff_uses_lexicon(temp_repo):
    paths, _ = _pc(temp_repo)
    with _chdir(temp_repo):
        gid = ops.cz_create_gameplan("spring promo", kind="campaign")["gameplan_id"]
    paths, config = _pc(temp_repo)
    md = handoff.assemble(paths, config, gid, "0", write=False)["handoff_md"]
    assert "# Stage 0 Handoff" in md and "## What This Stage Does" in md
    assert "# Phase 0 Handoff" not in md


def test_driven_handoff_unchanged(temp_repo):
    paths, config = _pc(temp_repo)
    md = handoff.assemble(paths, config, "2026-05-01-bootstrap", "1", write=False)["handoff_md"]
    assert "# Phase 1 Handoff" in md and "## What This Phase Does" in md  # identity
