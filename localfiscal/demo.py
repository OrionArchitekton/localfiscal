"""Fictional sample books, built with the same modules as real books."""

import shutil
from pathlib import Path

from .exporters import export_transactions
from .extract import extract_receipt
from .invoice import generate_invoice_pdf
from .ledger import KIND_INCOME, Ledger
from .report import generate_report


def create_demo(folder: Path) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    try:
        receipt = folder / "receipt.txt"
        receipt.write_text("Sample Stationery\n2026-01-02\nTOTAL $42.00\n", encoding="utf-8")
        parsed = extract_receipt(receipt)
        if parsed["needs_review"] or parsed["amount_minor"] != 4200:
            raise ValueError("The sample receipt could not be read correctly; no demo books were kept.")
        ledger = Ledger(folder / "ledger.db")
        ledger.add("2026-01-01", "Example Client", 125000, category="services", kind=KIND_INCOME)
        ledger.add("2026-01-02", "Sample Stationery", parsed["amount_minor"], category="supplies",
                   source="receipt.txt")
        ledger.add("2026-01-03", "Example Cafe", 1250, category="meals")
        generate_invoice_pdf(
            "Example Client", 125000, description="Sample services", out=folder / "invoice.pdf"
        )
        generate_report(ledger, "sample", out_dir=folder)
        export_transactions(ledger.list(limit=None), "csv", folder / "transactions.csv")
    except BaseException:
        shutil.rmtree(folder)
        raise
    return folder
