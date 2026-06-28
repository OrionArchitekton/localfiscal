"""S6/S7 — real CSV (RFC-4180, round-trips) and OFX/QFX (valid SGML) exports."""

import csv
import io

from localfiscal.exporters import (
    export_transactions,
    transactions_to_csv,
    transactions_to_ofx,
)
from localfiscal.ledger import KIND_EXPENSE, KIND_INCOME, Ledger
from localfiscal.money import parse_money


def _ledger(tmp_path):
    led = Ledger(tmp_path / "l.db")
    led.add("2026-06-01", "Client A", parse_money("1,234.56", "USD"), "USD", "income", KIND_INCOME)
    led.add("2026-06-02", "Coffee", parse_money("4.50", "USD"), "USD", "meals", KIND_EXPENSE)
    return led


def test_csv_round_trips_through_csv_reader(tmp_path):
    body = transactions_to_csv(_ledger(tmp_path).list())
    rows = list(csv.DictReader(io.StringIO(body)))
    assert len(rows) == 2
    by_vendor = {r["vendor"]: r for r in rows}
    assert int(by_vendor["Client A"]["amount_minor"]) == 123456
    assert by_vendor["Client A"]["amount"] == "1234.56"  # exact decimal, not float noise


def test_csv_is_real_csv_not_json(tmp_path):
    body = transactions_to_csv(_ledger(tmp_path).list())
    assert not body.lstrip().startswith("{")  # v0.1 wrote JSON into a .csv
    assert body.splitlines()[0].startswith("id,date,vendor,amount_minor")


def test_ofx_is_well_formed_sgml(tmp_path):
    body = transactions_to_ofx(_ledger(tmp_path).list())
    assert body.startswith("OFXHEADER:100")
    assert "DATA:OFXSGML" in body
    assert "<OFX>" in body and "</OFX>" in body
    assert body.count("<STMTTRN>") == 2
    assert "<TRNAMT>1234.56" in body  # income → credit, positive
    assert "<TRNAMT>-4.50" in body  # expense → debit, negative


def test_export_writes_both_formats(tmp_path):
    led = _ledger(tmp_path)
    csv_path = export_transactions(led.list(), "csv", tmp_path / "out.csv")
    assert csv_path.exists() and csv_path.read_text().startswith("id,date")
    ofx_path = export_transactions(led.list(), "ofx", tmp_path / "out.ofx")
    assert ofx_path.exists() and ofx_path.read_text().startswith("OFXHEADER")
