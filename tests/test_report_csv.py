"""FIX-C/E — report CSV carries income/expense/net (md/json parity) and is injection-safe."""

import csv
import io

from localfiscal.exporters import report_to_csv
from localfiscal.ledger import KIND_EXPENSE, KIND_INCOME, Ledger
from localfiscal.money import parse_money
from localfiscal.report import report_data


def _ledger(tmp_path):
    led = Ledger(tmp_path / "l.db")
    led.add("2026-06-01", "Client", parse_money("100.00", "USD"), "USD", "income", KIND_INCOME)
    led.add("2026-06-02", "Shop", parse_money("30.00", "USD"), "USD", "supplies", KIND_EXPENSE)
    return led


def test_report_csv_includes_income_expense_net(tmp_path):
    data = report_data(_ledger(tmp_path), "now")
    body = report_to_csv(data)
    flat = body.lower()
    assert "income" in flat and "expense" in flat and "net" in flat
    s = data["currencies"]["USD"]
    assert s["income"] == 10000 and s["expense"] == 3000 and s["net"] == 7000
    # the exact minor values appear (parity with md/json which carry them)
    assert "10000" in body and "3000" in body and "7000" in body


def test_report_csv_neutralizes_formula_injection(tmp_path):
    led = Ledger(tmp_path / "l.db")
    led.add("2026-06-01", "V", parse_money("5.00", "USD"), "USD", '=HYPERLINK("http://evil")', KIND_EXPENSE)
    body = report_to_csv(report_data(led, "now"))
    rows = list(csv.reader(io.StringIO(body)))[1:]  # skip header
    # text cells (label, display) must not trigger a spreadsheet formula; the numeric
    # `minor` column may legitimately hold a negative integer (it is data, not text)
    for row in rows:
        for cell in (row[2], row[4]):
            assert not cell or cell[0] not in "=+-@\t\r"
