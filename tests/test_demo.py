import csv
from pathlib import Path

import pytest
from pypdf import PdfReader
from typer.testing import CliRunner

from localfiscal.cli import app
from localfiscal.ledger import Ledger
from localfiscal.report import report_data


def test_demo_creates_sample_books_without_touching_real_ledger(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    real = tmp_path / "private.db"
    monkeypatch.setenv("LOCALFISCAL_DB", str(real))
    result = CliRunner().invoke(app, ["demo", "--out", "sample"])
    assert result.exit_code == 0, result.output
    folder = Path("sample")
    ledger = Ledger(folder / "ledger.db")
    summary = report_data(ledger, "sample")
    assert summary["count"] == 3
    assert summary["currencies"]["USD"]["net"] == 119550
    assert (folder / "receipt.txt").read_text().endswith("TOTAL $42.00\n")
    assert "$1,195.50" in (folder / "report-sample.md").read_text()
    with (folder / "transactions.csv").open() as stream:
        assert len(list(csv.DictReader(stream))) == 3
    assert "$1,250.00" in PdfReader(folder / "invoice.pdf").pages[0].extract_text()
    assert not real.exists()


@pytest.mark.parametrize("kind", ["folder", "file", "symlink"])
def test_demo_refuses_existing_path(tmp_path, kind):
    target = tmp_path / "sample"
    if kind == "folder":
        target.mkdir()
    elif kind == "file":
        target.write_text("private")
    else:
        real = tmp_path / "real"
        real.mkdir()
        target.symlink_to(real, target_is_directory=True)
    result = CliRunner().invoke(app, ["demo", "--out", str(target)])
    assert result.exit_code == 2
    assert "already exists" in result.output
    assert not (target / "ledger.db").exists()
