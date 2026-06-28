"""S3 — money inputs validated at the boundary (CLI + unit)."""

import pytest
from typer.testing import CliRunner

from localfiscal.cli import app
from localfiscal.validate import InvalidAmount, validate_minor

runner = CliRunner()


def test_rejects_negative_by_default():
    with pytest.raises(InvalidAmount):
        validate_minor(-1, "USD")


def test_allows_negative_when_flagged():
    assert validate_minor(-1, "USD", allow_negative=True) == -1


def test_rejects_absurd_magnitude():
    with pytest.raises(InvalidAmount):
        validate_minor(10 ** 18, "USD")


def test_rejects_non_int_and_bool():
    with pytest.raises(InvalidAmount):
        validate_minor(1.5, "USD")  # type: ignore[arg-type]
    with pytest.raises(InvalidAmount):
        validate_minor(True, "USD")


def test_accepts_normal():
    assert validate_minor(123456, "USD") == 123456


def test_cli_add_rejects_unparseable_amount(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = runner.invoke(app, ["add", "2026-06-28", "Vendor", "not-money"])
    assert r.exit_code != 0


def test_cli_add_rejects_negative(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = runner.invoke(app, ["add", "2026-06-28", "Vendor", "-5.00"])
    assert r.exit_code != 0


def test_cli_add_parses_grouped_amount(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = runner.invoke(app, ["add", "2026-06-28", "Vendor", "$1,234.56"])
    assert r.exit_code == 0
    assert "$1,234.56" in r.output  # formatted, exact — not truncated, not raw minor units
