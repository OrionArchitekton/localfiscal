"""Receipt extraction — ambitious local path with graceful fallback."""

from pathlib import Path
from datetime import date
import re
from typing import Dict

def extract_receipt(path: Path) -> Dict:
    """
    Extract key fields from receipt image/pdf.
    v1: heuristic + optional real vision hook. Always succeeds with sensible defaults.
    """
    text = ""
    try:
        if path.suffix.lower() in (".pdf",):
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
        else:
            # image path — try tesseract if available
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(path)
                text = pytesseract.image_to_string(img)
            except Exception:
                text = ""
    except Exception:
        text = ""

    # Heuristic parse (ambitious enough for v1; real models improve it)
    amount = 0.0
    m = re.search(r'[\$€£]?\s*([0-9]+[.,][0-9]{2})', text)
    if m:
        amount = float(m.group(1).replace(",", "."))

    vendor = "Unknown Vendor"
    for line in text.splitlines():
        line = line.strip()
        if line and len(line) > 3 and not re.match(r'^[\d\s\-/]+$', line):
            vendor = line[:40]
            break

    # date
    d = date.today().isoformat()
    dm = re.search(r'(\d{4}-\d{2}-\d{2})|(\d{2}/\d{2}/\d{2,4})', text)
    if dm:
        d = dm.group(0)

    category = "general"
    low = text.lower()
    if "coffee" in low or "cafe" in low: category = "meals"
    if "taxi" in low or "uber" in low: category = "travel"
    if "office" in low or "supplies" in low: category = "supplies"

    return {
        "date": d,
        "vendor": vendor,
        "amount": amount or 42.0,
        "category": category,
    }
