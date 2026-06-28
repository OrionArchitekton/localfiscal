"""Minimal FastAPI web UI for localfiscal (local-first)."""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from . import __version__
from .extract import extract_receipt
from .invoice import generate_invoice_pdf
from .ledger import KIND_EXPENSE, Ledger
from .money import DEFAULT_CURRENCY, format_money
from .report import generate_report

app = FastAPI(title="localfiscal")
DB = Path("data/ledger.db")
LEDGER = Ledger(DB)

HTML = """
<!doctype html><html><body style="font-family:sans-serif;max-width:720px;margin:2rem auto">
<h1>localfiscal — private local finance</h1>
<p>Upload receipt → extract → ledger. Generate invoices and reports. Everything local.</p>
<form action="/ingest" method="post" enctype="multipart/form-data">
  <input type="file" name="file" required/>
  <button type="submit">Ingest receipt</button>
</form>
<h2>Quick actions</h2>
<form action="/invoice" method="post">
  Client: <input name="client" value="Acme Co"/> Amount: <input name="amount" value="1200"/>
  <button>Generate invoice PDF</button>
</form>
<p><a href="/report">Report (md)</a> | <a href="/health">health</a></p>
</body></html>
"""


@app.get("/", response_class=HTMLResponse)
def root():
    return HTML


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    p = Path("/tmp") / file.filename
    with p.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    data = extract_receipt(p)
    if data["needs_review"]:
        return {"status": "needs_review", "reason": "could not parse amount", "fields": data}
    tx = LEDGER.add(
        date=data["date"], vendor=data["vendor"], amount_minor=data["amount_minor"],
        currency=data["currency"], category=data["category"], kind=KIND_EXPENSE,
        source=file.filename,
    )
    return {"status": "ingested", "tx": tx.__dict__, "display": format_money(tx.amount_minor, tx.currency)}


@app.post("/invoice")
def make_invoice(client: str = Form(...), amount: str = Form(...), currency: str = Form(DEFAULT_CURRENCY)):
    from .money import parse_money
    from .validate import validate_minor

    minor = validate_minor(parse_money(amount, currency), currency)
    pdf = generate_invoice_pdf(client, minor, currency, "Professional services", Path("data/invoice.pdf"))
    return FileResponse(pdf, filename="invoice.pdf")


@app.get("/report")
def rpt():
    p = generate_report(LEDGER, "current", "md")
    return FileResponse(p, filename="report.md")


@app.get("/health")
def health():
    return {"ok": True, "version": __version__, "db_exists": DB.exists()}
