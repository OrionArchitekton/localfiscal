"""FIX-D — ingest validates the extracted amount before persisting (no poisoned ledger)."""

from typer.testing import CliRunner

from localfiscal.cli import app

runner = CliRunner()


def test_ingest_rejects_absurd_extracted_amount(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    receipt = tmp_path / "huge.txt"
    receipt.write_text("Mega Store\nTOTAL $99999999999999999.99\n")
    res = runner.invoke(app, ["ingest", str(receipt)])
    assert res.exit_code == 3
    assert "review" in res.output.lower()
    # the implausible value must not have been written to the ledger
    assert runner.invoke(app, ["list-tx"]).output.strip() == ""


def test_ingest_accepts_plausible_amount(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    receipt = tmp_path / "ok.txt"
    receipt.write_text("Corner Store\nTOTAL $12.34\n")
    res = runner.invoke(app, ["ingest", str(receipt)])
    assert res.exit_code == 0 and "$12.34" in res.output
