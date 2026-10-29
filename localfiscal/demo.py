"""Fictional sample books, built with the same modules as real books."""

import ctypes
import errno
import os
import sys
import tempfile
from pathlib import Path

from .exporters import export_transactions
from .extract import extract_receipt
from .invoice import generate_invoice_pdf
from .ledger import KIND_INCOME, Ledger
from .report import generate_report, report_data


def _publish_new_directory(staged: Path, destination: Path) -> None:
    """Atomically publish without replacing a file, directory or symlink."""
    if sys.platform == "win32":
        # Windows rename refuses every existing destination (unlike POSIX rename).
        os.rename(staged, destination)
        return
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(-100, os.fsencode(staged), -100, os.fsencode(destination), 1)  # RENAME_NOREPLACE
    elif sys.platform == "darwin" and hasattr(libc, "renamex_np"):
        rename = libc.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(os.fsencode(staged), os.fsencode(destination), 4)  # RENAME_EXCL
    else:
        raise OSError(errno.ENOTSUP, "Atomic no-overwrite publication is unavailable")
    if result:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(destination))


def create_demo(folder: Path) -> tuple[Path, dict]:
    folder = Path(folder).absolute()
    if os.path.lexists(folder):
        raise FileExistsError(errno.EEXIST, "Output path already exists", str(folder))
    folder.parent.mkdir(parents=True, exist_ok=True)
    # Sibling staging keeps publication on the same filesystem. Never generate
    # through the destination path, and never recursively remove that path.
    with tempfile.TemporaryDirectory(prefix=".localfiscal-demo-", dir=folder.parent) as temporary:
        staged = Path(temporary) / "books"
        staged.mkdir()
        receipt = staged / "receipt.txt"
        receipt.write_text("Sample Stationery\n2026-01-02\nTOTAL $42.00\n", encoding="utf-8")
        parsed = extract_receipt(receipt)
        if parsed["needs_review"] or parsed["amount_minor"] != 4200:
            raise ValueError("The sample receipt could not be read correctly; no demo books were kept.")
        ledger = Ledger(staged / "ledger.db")
        ledger.add("2026-01-01", "Example Client", 125000, category="services", kind=KIND_INCOME)
        ledger.add("2026-01-02", "Sample Stationery", parsed["amount_minor"], category="supplies",
                   source="receipt.txt")
        ledger.add("2026-01-03", "Example Cafe", 1250, category="meals")
        generate_invoice_pdf(
            "Example Client", 125000, description="Sample services", out=staged / "invoice.pdf"
        )
        generate_report(ledger, "sample", out_dir=staged)
        export_transactions(ledger.list(limit=None), "csv", staged / "transactions.csv")
        totals = report_data(ledger, "sample")["currencies"]["USD"]
        _publish_new_directory(staged, folder)
    return folder, totals
