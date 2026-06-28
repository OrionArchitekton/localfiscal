"""S2 — receipt amounts parsed correctly (locale, TOTAL preference) or needs-review."""

from pathlib import Path

from localfiscal.extract import detect_currency, extract_receipt, find_amount


def test_picks_total_over_subtotal_and_tax():
    text = "Subtotal 1,200.00\nTax 34.56\nTOTAL $1,234.56\n"
    assert find_amount(text, "USD") == 123456


def test_thousands_separator_not_truncated():
    # v0.1 truncated $1,234.56 -> $1.23
    assert find_amount("TOTAL: $1,234.56", "USD") == 123456


def test_eu_format_total():
    assert find_amount("TOTAL 1.234,56", "EUR") == 123456


def test_no_amount_returns_none_not_fabricated():
    assert find_amount("just some words, no prices", "USD") is None


def test_detect_currency():
    assert detect_currency("Total €5,00") == "EUR"
    assert detect_currency("Total $5.00") == "USD"
    assert detect_currency("£9.99") == "GBP"


def test_extract_missing_file_is_needs_review():
    data = extract_receipt(Path("/does/not/exist.jpg"))
    assert data["needs_review"] is True and data["amount_minor"] is None
