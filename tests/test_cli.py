"""CLI seam — exercises the six commands end-to-end (value-asserting)."""

from pathlib import Path

from typer.testing import CliRunner

from localfiscal.cli import app

runner = CliRunner()


def test_health(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = runner.invoke(app, ["health"])
    assert r.exit_code == 0
    assert "localfiscal v0.2.0" in r.output


def test_add_list_invoice_report_export_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["add", "2026-06-01", "Client A", "$1,234.56", "--income"]).exit_code == 0
    assert runner.invoke(app, ["add", "2026-06-02", "Coffee", "4.50", "--category", "meals"]).exit_code == 0

    listed = runner.invoke(app, ["list-tx"])
    assert listed.exit_code == 0
    assert "$1,234.56" in listed.output and "$4.50" in listed.output

    inv = runner.invoke(app, ["invoice", "Acme", "1200", "--out", "inv.pdf"])
    assert inv.exit_code == 0 and Path("inv.pdf").exists()

    for fmt in ("md", "json", "csv"):
        assert runner.invoke(app, ["report", "--fmt", fmt]).exit_code == 0
    for fmt in ("csv", "ofx"):
        assert runner.invoke(app, ["export", "--fmt", fmt]).exit_code == 0


def test_ingest_needs_review_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    receipt = tmp_path / "note.txt"
    receipt.write_text("just a note, no prices here")
    r = runner.invoke(app, ["ingest", str(receipt)])
    assert r.exit_code == 3
    assert "NEEDS REVIEW" in r.output
    assert runner.invoke(app, ["list-tx"]).output.strip() == ""  # nothing was added


def test_ingest_parses_total_amount(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    receipt = tmp_path / "receipt.txt"
    receipt.write_text("Big Store\nSubtotal 10.00\nTOTAL $12.34\n")
    r = runner.invoke(app, ["ingest", str(receipt)])
    assert r.exit_code == 0
    assert "$12.34" in r.output  # picked TOTAL, exact
