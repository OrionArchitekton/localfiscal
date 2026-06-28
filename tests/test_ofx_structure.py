"""FIX-F — OFX export is structurally valid (parsed, not just substring-checked)."""

import re
from decimal import Decimal

import pytest

from localfiscal.exporters import transactions_to_ofx
from localfiscal.ledger import KIND_EXPENSE, KIND_INCOME, Ledger
from localfiscal.money import parse_money


def test_ofx_structure_validates(tmp_path):
    led = Ledger(tmp_path / "l.db")
    led.add("2026-06-01", "Client", parse_money("1,234.56", "USD"), "USD", "income", KIND_INCOME)
    led.add("2026-06-02", "Coffee", parse_money("4.50", "USD"), "USD", "meals", KIND_EXPENSE)
    ofx = transactions_to_ofx(led.list())

    header, _, body = ofx.partition("\n\n")
    hdr_lines = [ln for ln in header.splitlines() if ln.strip()]
    assert hdr_lines and all(":" in ln for ln in hdr_lines)
    assert any(ln.startswith("OFXHEADER:") for ln in hdr_lines)

    # container (aggregate) tags must be balanced
    for tag in ("OFX", "SIGNONMSGSRSV1", "BANKMSGSRSV1", "STMTTRNRS", "STMTRS", "BANKTRANLIST"):
        opens, closes = body.count(f"<{tag}>"), body.count(f"</{tag}>")
        assert opens == closes >= 1, f"unbalanced <{tag}>: {opens} open / {closes} close"

    # every transaction carries the required leaf fields, a parseable amount and an 8-digit date
    blocks = re.findall(r"<STMTTRN>(.*?)</STMTTRN>", body, re.S)
    assert len(blocks) == 2
    for blk in blocks:
        for leaf in ("<TRNTYPE>", "<DTPOSTED>", "<TRNAMT>", "<FITID>", "<NAME>"):
            assert leaf in blk
        amount = re.search(r"<TRNAMT>(-?\d+\.\d+)", blk).group(1)
        Decimal(amount)  # raises if malformed
        assert len(re.search(r"<DTPOSTED>(\d{8})", blk).group(1)) == 8


def test_ofx_credit_and_debit_signs(tmp_path):
    led = Ledger(tmp_path / "l.db")
    led.add("2026-06-01", "Client", parse_money("100.00", "USD"), "USD", "income", KIND_INCOME)
    led.add("2026-06-02", "Shop", parse_money("30.00", "USD"), "USD", "x", KIND_EXPENSE)
    ofx = transactions_to_ofx(led.list())
    assert "<TRNTYPE>CREDIT" in ofx and "<TRNAMT>100.00" in ofx  # income positive
    assert "<TRNTYPE>DEBIT" in ofx and "<TRNAMT>-30.00" in ofx  # expense negative


def test_ofx_is_accepted_by_a_real_ofx_parser(tmp_path):
    OfxParser = pytest.importorskip("ofxparse").OfxParser
    led = Ledger(tmp_path / "l.db")
    led.add("2026-06-01", "Client", parse_money("1,234.56", "USD"), "USD", "income", KIND_INCOME)
    led.add("2026-06-02", "Coffee", parse_money("4.50", "USD"), "USD", "meals", KIND_EXPENSE)
    path = tmp_path / "x.ofx"
    path.write_text(transactions_to_ofx(led.list()))
    with open(path, "rb") as fh:
        ofx = OfxParser.parse(fh)
    txns = {t.payee: t for t in ofx.account.statement.transactions}
    assert len(txns) == 2
    assert txns["Client"].type == "credit" and str(txns["Client"].amount) == "1234.56"
    assert txns["Coffee"].type == "debit" and str(txns["Coffee"].amount) == "-4.50"
