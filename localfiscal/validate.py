"""Boundary validation for money amounts (integer minor units).

Moving money to integer minor units already makes ``nan``/``inf`` unrepresentable.
This guard rejects the remaining bad inputs — non-int, negative-where-disallowed,
and implausibly large magnitudes — at the CLI/web boundary, fail-closed.
"""

from __future__ import annotations

import re

# 1e13 major units (e.g. ten trillion dollars) in minor units — anything larger is a typo/attack.
_MAX_MINOR = 10 ** 15
_ISO_CURRENCY = re.compile(r"[A-Z]{3}")


class InvalidAmount(ValueError):
    """Raised when an amount fails boundary validation."""


class InvalidCurrency(ValueError):
    """Raised when a currency code is not a 3-letter ISO-4217 code."""


def validate_currency(currency: str) -> str:
    """Return the upper-cased 3-letter ISO-4217 code, or raise.

    Rejecting anything but ``[A-Z]{3}`` both keeps the ledger sane and removes a
    CSV/OFX injection vector (a crafted currency cannot become a formula cell).
    """
    code = (currency or "").strip().upper()
    if not _ISO_CURRENCY.fullmatch(code):
        raise InvalidCurrency(f"currency must be a 3-letter ISO-4217 code, got {currency!r}")
    return code


def validate_minor(minor: int, currency: str = "USD", *, allow_negative: bool = False) -> int:
    if isinstance(minor, bool) or not isinstance(minor, int):
        raise InvalidAmount("amount must be integer minor units")
    if not allow_negative and minor < 0:
        raise InvalidAmount("amount must not be negative (use --income to record income)")
    if abs(minor) > _MAX_MINOR:
        raise InvalidAmount("amount is implausibly large")
    return minor
