"""S9 — currency is first-class: rendered with its symbol, never silently summed."""

from localfiscal.ledger import KIND_EXPENSE, Ledger
from localfiscal.money import parse_money
from localfiscal.report import generate_report, report_data


def test_mixed_currency_is_segregated_not_summed(tmp_path):
    led = Ledger(tmp_path / "l.db")
    led.add("2026-06-01", "US Shop", parse_money("10.00", "USD"), "USD", "supplies", KIND_EXPENSE)
    led.add("2026-06-01", "EU Shop", parse_money("10,00", "EUR"), "EUR", "supplies", KIND_EXPENSE)
    data = report_data(led, "now")
    assert set(data["currencies"]) == {"USD", "EUR"}  # two separate buckets, not one false total
    assert data["currencies"]["USD"]["expense"] == 1000
    assert data["currencies"]["EUR"]["expense"] == 1000


def test_report_md_shows_each_currency_symbol(tmp_path):
    led = Ledger(tmp_path / "l.db")
    led.add("2026-06-01", "US Shop", parse_money("12.34", "USD"), "USD", "supplies", KIND_EXPENSE)
    led.add("2026-06-01", "EU Shop", parse_money("56,78", "EUR"), "EUR", "supplies", KIND_EXPENSE)
    md = generate_report(led, "now", "md", out_dir=tmp_path).read_text()
    assert "## USD" in md and "## EUR" in md
    assert "$12.34" in md  # USD symbol + US grouping
    assert "€56,78" in md  # EUR symbol + EU grouping
