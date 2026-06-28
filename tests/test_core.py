import tempfile
from pathlib import Path
from localfiscal.ledger import Ledger
from localfiscal.extract import extract_receipt
from localfiscal.invoice import generate_invoice_pdf
from localfiscal.report import generate_report

def test_ledger_add_list():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "l.db"
        l = Ledger(db)
        t = l.add("2026-06-28", "Coffee Shop", 4.5, "meals")
        assert t.id > 0
        assert len(l.list()) >= 1

def test_extract_fallback():
    # uses fallback heuristic when no vision
    data = extract_receipt(Path("/nonexistent.jpg"))
    assert "amount" in data and "vendor" in data

def test_invoice_and_report():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "l.db"
        l = Ledger(db)
        l.add("2026-06-01", "Client A", 500, "income")
        p = generate_invoice_pdf("Acme", 123.0, "Work", Path(td)/"inv.pdf")
        assert p.exists()
        r = generate_report(l, "now", "md")
        assert r.exists() and "Total" in r.read_text()
