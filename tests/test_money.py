"""S1 — money is represented and parsed exactly (integer minor-units + currency)."""

from decimal import Decimal

import pytest

from localfiscal.money import (
    format_money,
    from_decimal,
    minor_units,
    parse_money,
    to_decimal,
)


def test_parse_us_format():
    assert parse_money("$1,234.56", "USD") == 123456
    assert parse_money("1234.56", "USD") == 123456
    assert parse_money("0.10", "USD") == 10
    assert parse_money("0.20", "USD") == 20


def test_parse_eu_format():
    # EU grouping: dot=thousands, comma=decimal
    assert parse_money("1.234,56", "EUR") == 123456
    assert parse_money("€1.234,56", "EUR") == 123456


def test_parse_thousands_without_decimal():
    assert parse_money("1,234", "USD") == 123400  # $1,234.00
    assert parse_money("12,345", "USD") == 1234500


def test_parse_negative():
    assert parse_money("-42.00", "USD") == -4200


def test_parse_rejects_garbage():
    with pytest.raises(ValueError):
        parse_money("no digits here", "USD")
    with pytest.raises(ValueError):
        parse_money("", "USD")


def test_format_us():
    assert format_money(123456, "USD") == "$1,234.56"
    assert format_money(10, "USD") == "$0.10"
    assert format_money(-4200, "USD") == "-$42.00"


def test_format_eu():
    # EU rendering: dot=thousands, comma=decimal, euro sign
    assert format_money(123456, "EUR") == "€1.234,56"


def test_jpy_zero_decimals():
    assert minor_units("JPY") == 0
    assert parse_money("1,234", "JPY") == 1234
    assert format_money(1234, "JPY") == "¥1,234"


def test_float_lossy_sum_is_exact():
    # 0.10 + 0.20 must be exactly 0.30 in minor units (the float trap)
    a = parse_money("0.10", "USD")
    b = parse_money("0.20", "USD")
    assert a + b == 30
    assert format_money(a + b, "USD") == "$0.30"


def test_decimal_roundtrip():
    assert to_decimal(123456, "USD") == Decimal("1234.56")
    assert from_decimal(Decimal("1234.56"), "USD") == 123456
    # quantization: more precision than the currency allows rounds half-up
    assert from_decimal(Decimal("1.005"), "USD") == 101
