"""Boundary validation for money amounts (integer minor units).

Moving money to integer minor units already makes ``nan``/``inf`` unrepresentable.
This guard rejects the remaining bad inputs — non-int, negative-where-disallowed,
and implausibly large magnitudes — at the CLI/web boundary, fail-closed.
"""

from __future__ import annotations

# 1e13 major units (e.g. ten trillion dollars) in minor units — anything larger is a typo/attack.
_MAX_MINOR = 10 ** 15


class InvalidAmount(ValueError):
    """Raised when an amount fails boundary validation."""


def validate_minor(minor: int, currency: str = "USD", *, allow_negative: bool = False) -> int:
    if isinstance(minor, bool) or not isinstance(minor, int):
        raise InvalidAmount("amount must be integer minor units")
    if not allow_negative and minor < 0:
        raise InvalidAmount("amount must not be negative (use --income to record income)")
    if abs(minor) > _MAX_MINOR:
        raise InvalidAmount("amount is implausibly large")
    return minor
