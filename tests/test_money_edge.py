"""FIX-B — sign placement and zero-decimal currency edge cases (silent-corruption paths)."""

import pytest

from localfiscal.money import parse_money


def test_dollar_then_minus_is_negative_not_positive():
    # "$-5.00" must not silently become +500
    assert parse_money("$-5.00", "USD") == -500
    assert parse_money("-$5.00", "USD") == -500


def test_misplaced_internal_minus_is_rejected():
    with pytest.raises(ValueError):
        parse_money("5-00", "USD")
    with pytest.raises(ValueError):
        parse_money("--5", "USD")


def test_jpy_rejects_fractional_input():
    # zero-decimal currency: "123.45" is not 12345 yen — it is invalid
    with pytest.raises(ValueError):
        parse_money("123.45", "JPY")
    with pytest.raises(ValueError):
        parse_money("100.5", "JPY")


def test_jpy_accepts_thousands_grouped():
    assert parse_money("1,234", "JPY") == 1234
    assert parse_money("1,234,567", "JPY") == 1234567
    assert parse_money("1234", "JPY") == 1234


def test_usd_unaffected_by_jpy_rule():
    assert parse_money("123.45", "USD") == 12345
    assert parse_money("1,234.56", "USD") == 123456
