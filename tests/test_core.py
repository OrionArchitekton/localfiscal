"""Integration tests across extract → ledger → invoice → report (value-asserting)."""

from pathlib import Path

from localfiscal.extract import extract_receipt
from localfiscal.invoice import generate_invoice_pdf
from localfiscal.ledger import KIND_EXPENSE, KIND_INCOME, Ledger
from localfiscal.money import format_money, parse_money
from localfiscal.report import generate_report, report_data


def test_ledger_add_list_exact(tmp_path):
    led = Ledger(tmp_path / "l.db")
    t = led.add("2026-06-28", "Coffee Shop", parse_money("4.50", "USD"), "USD", "meals", KIND_EXPENSE)
    assert t.amount_minor == 450
    rows = led.list()
    assert len(rows) == 1 and rows[0].amount_minor == 450


def test_extract_no_amount_is_needs_review_not_fabricated():
    data = extract_receipt(Path("/nonexistent.jpg"))
    assert data["needs_review"] is True
    assert data["amount_minor"] is None  # v0.1 fabricated 4200 here — never again


def test_invoice_pdf_is_real(tmp_path):
    p = generate_invoice_pdf("Acme", parse_money("123.00", "USD"), "USD", "Work", tmp_path / "inv.pdf")
    assert p.exists()
    assert p.read_bytes()[:4] == b"%PDF"


def test_report_md_and_json_agree_and_net_is_signed(tmp_path):
    led = Ledger(tmp_path / "l.db")
    led.add("2026-06-01", "Client A", parse_money("0.10", "USD"), "USD", "income", KIND_INCOME)
    led.add("2026-06-01", "Shop", parse_money("0.20", "USD"), "USD", "supplies", KIND_EXPENSE)
    s = report_data(led, "now")["currencies"]["USD"]
    assert s["income"] == 10 and s["expense"] == 20 and s["net"] == -10  # exact, signed
    md = generate_report(led, "now", "md", out_dir=tmp_path).read_text()
    js = generate_report(led, "now", "json", out_dir=tmp_path).read_text()
    assert format_money(-10, "USD") in md  # "-$0.10"
    assert '"net_minor": -10' in js  # md and json never disagree
