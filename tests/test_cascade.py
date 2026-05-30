from datetime import datetime, timezone

from clauderizer.graph import cascade, index

FIXED = datetime(2026, 5, 2, 12, 0, 0, tzinfo=timezone.utc)


def test_render_report_lists_direct_and_transitive(sample_repo):
    g = index.build(sample_repo / "docs")
    report = cascade.render_report(
        g, "subsys.calc-engine", "version 1.1.0 -> 2.0.0 (MAJOR)", now=FIXED
    )
    assert "# Cascade Report: subsys.calc-engine" in report
    assert "subsys.auth" in report
    assert "feat.legacy" in report
    # transitive section should mention feat.login (depends on auth)
    assert "feat.login" in report
    assert "Generated: 2026-05-02T12:00:00Z" in report


def test_run_writes_report_file(temp_repo):
    g = index.build(temp_repo / "docs")
    reports_dir = temp_repo / "docs" / "gameplans" / "2026-05-01-bootstrap" / "_cascade-reports"
    result = cascade.run(
        g, "subsys.auth", "status active -> completed", reports_dir, now=FIXED
    )
    assert result["written"] is True
    out = reports_dir / "2026-05-02-subsys.auth.md"
    assert out.exists()
    assert "feat.login" in out.read_text(encoding="utf-8")
    assert result["direct"] == ["feat.login"]


def test_dry_run_does_not_write(temp_repo):
    g = index.build(temp_repo / "docs")
    reports_dir = temp_repo / "docs" / "gameplans" / "2026-05-01-bootstrap" / "_cascade-reports"
    before = set(reports_dir.glob("*.md"))
    result = cascade.run(g, "subsys.auth", "x", reports_dir, dry_run=True, now=FIXED)
    assert result["written"] is False
    assert set(reports_dir.glob("*.md")) == before
