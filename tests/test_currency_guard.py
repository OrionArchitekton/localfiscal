"""C3 — currency is validated at the source (kills currency CSV/OFX injection) + vision UX."""

import pytest
from typer.testing import CliRunner

from localfiscal.cli import app
from localfiscal.ledger import KIND_EXPENSE, Ledger
from localfiscal.validate import InvalidCurrency, validate_currency

runner = CliRunner()


def test_validate_currency_rejects_non_iso_and_normalizes():
    assert validate_currency("usd") == "USD"
    for bad in ("=CMD", "US", "USDD", "$$$", "=2+2"):
        with pytest.raises(InvalidCurrency):
            validate_currency(bad)


def test_ledger_add_rejects_crafted_currency(tmp_path):
    led = Ledger(tmp_path / "l.db")
    with pytest.raises(ValueError):
        led.add("2026-06-01", "V", 500, "=2+2", "x", KIND_EXPENSE)  # injection-style currency


def test_cli_add_rejects_crafted_currency(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = runner.invoke(app, ["add", "2026-06-01", "V", "5.00", "--currency", "=CMD"])
    assert r.exit_code != 0
    assert runner.invoke(app, ["list-tx"]).output.strip() == ""  # nothing persisted


def test_cli_ingest_vision_without_endpoint_warns_and_falls_back(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    receipt = tmp_path / "r.txt"
    receipt.write_text("Corner Shop\nTOTAL $5.00\n")
    r = runner.invoke(app, ["ingest", str(receipt), "--vision"])
    assert "no Ollama endpoint" in r.output  # the spec's "clear message"
    assert r.exit_code == 0 and "$5.00" in r.output  # heuristic fallback still works
