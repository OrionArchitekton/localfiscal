"""Minimal FastAPI web UI for localfiscal (ambitious but lean)."""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
import shutil
from .ledger import Ledger
from .extract import extract_receipt
from .invoice import generate_invoice_pdf
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
    tx = LEDGER.add(date=data["date"], vendor=data["vendor"], amount=data["amount"], category=data["category"], source=file.filename)
    return {"status": "ingested", "tx": tx.__dict__}

@app.post("/invoice")
def make_invoice(client: str = Form(...), amount: float = Form(...)):
    pdf = generate_invoice_pdf(client, amount, "Professional services", Path("data/invoice.pdf"))
    return FileResponse(pdf, filename="invoice.pdf")

@app.get("/report")
def rpt():
    p = generate_report(LEDGER, "current", "md")
    return FileResponse(p, filename="report.md")

@app.get("/health")
def health():
    return {"ok": True, "version": "0.1.0", "db_exists": DB.exists()}
