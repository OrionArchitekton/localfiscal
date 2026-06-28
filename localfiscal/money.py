"""Exact money as integer minor-units + ISO-4217 currency.

No float ever touches a money value. A *minor unit* is the smallest indivisible
unit of a currency (cents for USD/EUR/GBP, whole yen for JPY). Amounts are stored
and summed as Python ``int`` (exact, no rounding drift) and only converted to
``Decimal`` for display or interop.
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

# minor-unit decimal places per currency (ISO-4217 subset we render correctly)
_MINOR_UNITS = {"USD": 2, "EUR": 2, "GBP": 2, "CAD": 2, "AUD": 2, "JPY": 0}
_SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "$", "AUD": "$", "JPY": "¥"}
# (grouping-separator, decimal-separator) per currency; default is US style
_GROUPING = {"EUR": (".", ","), "USD": (",", "."), "GBP": (",", "."), "JPY": (",", ".")}

DEFAULT_CURRENCY = "USD"


def minor_units(currency: str = DEFAULT_CURRENCY) -> int:
    """Number of decimal places this currency's minor unit carries."""
    return _MINOR_UNITS.get(currency.upper(), 2)


def symbol(currency: str = DEFAULT_CURRENCY) -> str:
    return _SYMBOLS.get(currency.upper(), "")


def is_supported(currency: str) -> bool:
    return currency.upper() in _MINOR_UNITS


def parse_money(text: str, currency: str = DEFAULT_CURRENCY) -> int:
    """Parse a human-written money string into integer minor units.

    Locale-aware: handles US (``$1,234.56``) and EU (``1.234,56``) grouping.
    Rule: when both ``.`` and ``,`` appear, the rightmost is the decimal point;
    with a single separator it is the decimal point only when the trailing group
    is no longer than the currency's minor-unit count, otherwise it is thousands
    grouping. Raises ``ValueError`` when no numeric amount is present.
    """
    if text is None:
        raise ValueError("no amount: None")
    digits_places = minor_units(currency)
    raw = str(text).strip()
    negative = raw.startswith("-") or (raw.startswith("(") and raw.endswith(")"))
    # keep only digits and separators
    s = re.sub(r"[^0-9.,]", "", raw)
    if not re.search(r"\d", s):
        raise ValueError(f"no numeric amount in {text!r}")

    has_dot = "." in s
    has_comma = "," in s
    if has_dot and has_comma:
        dec_sep = "." if s.rfind(".") > s.rfind(",") else ","
        thou_sep = "," if dec_sep == "." else "."
        s = s.replace(thou_sep, "")
        int_part, _, frac = s.partition(dec_sep)
    elif has_dot or has_comma:
        sep = "." if has_dot else ","
        trailing = s.rsplit(sep, 1)[1]
        if s.count(sep) == 1 and digits_places > 0 and 0 < len(trailing) <= digits_places:
            int_part, _, frac = s.partition(sep)
        else:  # multiple separators or a 3+ digit group → thousands grouping
            int_part, frac = s.replace(sep, ""), ""
    else:
        int_part, frac = s, ""

    int_part = int_part or "0"
    if digits_places:
        frac = (frac + "0" * digits_places)[:digits_places]
        value = int(int_part) * (10 ** digits_places) + int(frac)
    else:
        value = int(int_part)
    return -value if negative else value


def format_money(minor: int, currency: str = DEFAULT_CURRENCY) -> str:
    """Render integer minor units as a localized money string with symbol."""
    places = minor_units(currency)
    group_sep, dec_sep = _GROUPING.get(currency.upper(), (",", "."))
    sym = symbol(currency)
    negative = minor < 0
    minor = abs(int(minor))
    if places:
        whole, frac = divmod(minor, 10 ** places)
        body = f"{whole:,}".replace(",", group_sep) + dec_sep + f"{frac:0{places}d}"
    else:
        body = f"{minor:,}".replace(",", group_sep)
    out = f"{sym}{body}"
    return f"-{out}" if negative else out


def to_decimal(minor: int, currency: str = DEFAULT_CURRENCY) -> Decimal:
    """Exact Decimal value of these minor units (for interop/display only)."""
    places = minor_units(currency)
    return (Decimal(int(minor)) / (Decimal(10) ** places)).quantize(
        Decimal(1).scaleb(-places) if places else Decimal(1)
    )


def from_decimal(value: Decimal, currency: str = DEFAULT_CURRENCY) -> int:
    """Quantize a Decimal to the currency's minor unit (half-up) and return int minor units."""
    places = minor_units(currency)
    q = Decimal(value).quantize(Decimal(1).scaleb(-places) if places else Decimal(1), rounding=ROUND_HALF_UP)
    return int(q.scaleb(places))
