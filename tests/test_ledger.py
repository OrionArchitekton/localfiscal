"""S1 — ledger stores money exactly (integer minor-units + currency), no float."""

from pathlib import Path

from localfiscal.ledger import Ledger, Transaction
from localfiscal.money import parse_money


def test_exact_money_roundtrip(tmp_path):
    led = Ledger(tmp_path / "l.db")
    t = led.add(
        date="2026-06-28",
        vendor="Coffee Shop",
        amount_minor=parse_money("4.50", "USD"),
        currency="USD",
        category="meals",
        kind="expense",
    )
    assert t.amount_minor == 450
    assert t.currency == "USD"
    got = led.list()[0]
    assert got.amount_minor == 450
    assert got.currency == "USD"
    assert isinstance(got.amount_minor, int)


def test_sum_is_exact_no_float_drift(tmp_path):
    led = Ledger(tmp_path / "l.db")
    led.add(date="2026-06-28", vendor="A", amount_minor=10, currency="USD", category="x")
    led.add(date="2026-06-28", vendor="B", amount_minor=20, currency="USD", category="x")
    total = sum(t.amount_minor for t in led.list())
    assert total == 30  # exact; floats would give 0.30000000000000004


def test_transaction_has_no_float_amount_field():
    # the float `amount` field is gone; only integer minor units remain
    fields = Transaction.__dataclass_fields__
    assert "amount_minor" in fields
    assert "amount" not in fields
    assert fields["amount_minor"].type in ("int", int)
