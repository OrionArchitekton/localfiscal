"""Regression tests from the v0.2 adversarial pass — confidently-wrong amounts + export injection."""

import csv
import io

from localfiscal.exporters import transactions_to_csv, transactions_to_ofx
from localfiscal.extract import find_amount
from localfiscal.ledger import KIND_EXPENSE, Ledger
from localfiscal.money import parse_money


def test_total_savings_marketing_line_not_picked():
    # "TOTAL SAVINGS" contains "total" but is not the amount due
    assert find_amount("TOTAL SAVINGS $999.00\nTOTAL DUE $12.34", "USD") == 1234


def test_strong_total_preferred_over_subtotal_and_tax():
    assert find_amount("Subtotal $10.00\nTax $2.34\nGrand Total $12.34", "USD") == 1234


def test_date_is_not_parsed_as_an_amount():
    # a bare date / integer must NOT become a fabricated amount — needs-review instead
    assert find_amount("Date: 2026-06-28\nThank you for shopping", "USD") is None


def test_bare_quantity_is_not_parsed_as_an_amount():
    assert find_amount("Qty 12 items\nGuests 4", "USD") is None


def test_real_total_with_symbol_still_parses():
    assert find_amount("Coffee 4.50\nTOTAL $4.50", "USD") == 450


def test_csv_neutralizes_formula_injection(tmp_path):
    led = Ledger(tmp_path / "l.db")
    led.add("2026-06-01", "=2+2+cmd|'/c calc'!A1", parse_money("4.50", "USD"), "USD", "meals", KIND_EXPENSE)
    led.add("2026-06-02", "@SUM(A1:A9)", parse_money("1.00", "USD"), "USD", "x", KIND_EXPENSE)
    body = transactions_to_csv(led.list())
    cells = [row[2] for row in list(csv.reader(io.StringIO(body)))[1:]]
    for cell in cells:
        assert cell[0] not in "=+-@\t\r"  # no cell starts with a spreadsheet-formula trigger


def test_ofx_escapes_sgml_special_characters(tmp_path):
    led = Ledger(tmp_path / "l.db")
    led.add("2026-06-01", "A & B <Corp>", parse_money("4.50", "USD"), "USD", "meals", KIND_EXPENSE)
    ofx = transactions_to_ofx(led.list())
    assert "&amp;" in ofx and "&lt;Corp&gt;" in ofx
    assert "<Corp>" not in ofx  # the angle-bracketed text is escaped, not a live tag
