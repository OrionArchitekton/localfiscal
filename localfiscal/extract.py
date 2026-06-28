"""Receipt extraction — heuristic parser with an optional local vision hook.

Never fabricates an amount. When no amount can be parsed the result is flagged
``needs_review`` (``amount_minor`` is ``None``) so the caller can decide, rather
than writing an invented value to the ledger.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Dict, Optional

from .money import DEFAULT_CURRENCY, parse_money

# currency hints found in receipt text → ISO code
_CURRENCY_HINTS = [
    ("€", "EUR"), ("EUR", "EUR"),
    ("£", "GBP"), ("GBP", "GBP"),
    ("¥", "JPY"), ("JPY", "JPY"),
    ("$", "USD"), ("USD", "USD"),
]
# a money-like token: optional symbol then grouped digits with a decimal part
_AMOUNT_RE = re.compile(r"[\$€£¥]?\s*\d[\d.,]*\d|\d")
# lines whose label marks the grand total (preferred over subtotal/tax)
_TOTAL_LABELS = re.compile(r"\b(grand\s*total|total\s*due|balance\s*due|amount\s*due|total)\b", re.I)
_NON_TOTAL = re.compile(r"\b(sub\s*total|subtotal|tax|vat|tip|change|cash|card)\b", re.I)


def _read_text(path: Path) -> str:
    try:
        if path.suffix.lower() == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        try:
            import pytesseract
            from PIL import Image

            return pytesseract.image_to_string(Image.open(path))
        except Exception:
            return ""
    except Exception:
        return ""


def detect_currency(text: str) -> str:
    for token, code in _CURRENCY_HINTS:
        if token in text:
            return code
    return DEFAULT_CURRENCY


def find_amount(text: str, currency: str = DEFAULT_CURRENCY) -> Optional[int]:
    """Return the receipt's amount in minor units, or ``None`` if none is parseable.

    Prefers a line labelled as the grand TOTAL over subtotal/tax lines; never
    invents a value. (v0.1 returned a fabricated ``$42.00`` here.)
    """
    total_candidates: list[int] = []
    other_candidates: list[int] = []
    for line in text.splitlines():
        if _NON_TOTAL.search(line) and not _TOTAL_LABELS.search(line):
            continue
        for tok in _AMOUNT_RE.findall(line):
            try:
                val = parse_money(tok, currency)
            except ValueError:
                continue
            if _TOTAL_LABELS.search(line):
                total_candidates.append(val)
            else:
                other_candidates.append(val)
    if total_candidates:
        return max(total_candidates)
    if other_candidates:
        return max(other_candidates)
    return None


def _guess_vendor(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line and len(line) > 3 and not re.match(r"^[\d\s\-/]+$", line):
            return line[:40]
    return "Unknown Vendor"


def _guess_category(text: str) -> str:
    low = text.lower()
    rules = [
        (("coffee", "cafe", "restaurant", "meal"), "meals"),
        (("taxi", "uber", "lyft", "flight", "hotel"), "travel"),
        (("office", "supplies", "staples"), "supplies"),
    ]
    for keywords, cat in rules:
        if any(k in low for k in keywords):
            return cat
    return "general"


def _guess_date(text: str) -> str:
    dm = re.search(r"(\d{4}-\d{2}-\d{2})|(\d{2}/\d{2}/\d{2,4})", text)
    return dm.group(0) if dm else date.today().isoformat()


def extract_receipt(
    path: Path,
    use_vision: bool = False,
    ollama_url: Optional[str] = None,
) -> Dict:
    """Extract fields from a receipt. Returns a dict that always includes
    ``amount_minor`` (int minor units or ``None``), ``currency`` and ``needs_review``.
    """
    text = _read_text(Path(path))
    if use_vision:
        from .vision import vision_extract_text

        vtext = vision_extract_text(Path(path), ollama_url)
        if vtext:
            text = vtext + "\n" + text

    currency = detect_currency(text)
    amount_minor = find_amount(text, currency)
    return {
        "date": _guess_date(text),
        "vendor": _guess_vendor(text),
        "amount_minor": amount_minor,
        "currency": currency,
        "category": _guess_category(text),
        "needs_review": amount_minor is None,
    }
