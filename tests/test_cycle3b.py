"""Cycle-3 regressions: date CSV-injection, $LOCALFISCAL_DB consistency, full-ledger reports."""

import csv
import io

from typer.testing import CliRunner

from localfiscal.cli import app
from localfiscal.exporters import transactions_to_csv
from localfiscal.ledger import KIND_EXPENSE, Ledger
from localfiscal.report import report_data

runner = CliRunner()


def test_csv_neutralizes_date_field(tmp_path):
    led = Ledger(tmp_path / "l.db")
    led.add("=cmd|'/c calc'", "V", 500, "USD", "x", KIND_EXPENSE)  # malicious 'date'
    body = transactions_to_csv(led.list())
    for row in list(csv.reader(io.StringIO(body)))[1:]:
        assert not row[1] or row[1][0] not in "=+-@\t\r"  # date column neutralized


def test_cli_respects_localfiscal_db_env(tmp_path, monkeypatch):
    db = tmp_path / "custom.db"
    monkeypatch.setenv("LOCALFISCAL_DB", str(db))
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["add", "2026-06-01", "V", "5.00"]).exit_code == 0
    assert db.exists()  # CLI honored the env-configured DB (same as the web UI)
    assert not (tmp_path / "data" / "ledger.db").exists()


def test_reports_cover_the_whole_ledger(tmp_path):
    led = Ledger(tmp_path / "l.db")
    for i in range(60):  # more than the default list() cap of 50
        led.add("2026-06-01", f"V{i}", 100, "USD", "x", KIND_EXPENSE)
    assert len(led.list(limit=None)) == 60  # None = no cap
    assert len(led.list(limit=50)) == 50  # explicit cap still works
    assert report_data(led, "now")["count"] == 60  # report is not silently truncated
