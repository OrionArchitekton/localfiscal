"""Minimal FastAPI web UI for localfiscal (local-first, loopback by default)."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from . import __version__
from .extract import extract_receipt
from .invoice import generate_invoice_pdf
from .ledger import KIND_EXPENSE, Ledger
from .money import DEFAULT_CURRENCY, format_money, parse_money
from .report import generate_report
from .validate import InvalidAmount, validate_minor

app = FastAPI(title="localfiscal")

UPLOAD_DIR = Path(tempfile.gettempdir()) / "localfiscal-uploads"


def _db_path() -> Path:
    return Path(os.environ.get("LOCALFISCAL_DB", "data/ledger.db"))


def _ledger() -> Ledger:
    """Lazy ledger — no database is created at import time."""
    return Ledger(_db_path())


def default_host() -> str:
    """Bind loopback unless the operator explicitly opts into exposure."""
    return os.environ.get("LOCALFISCAL_HOST", "127.0.0.1")


def safe_upload_path(upload_dir: Path, filename: str) -> Path:
    """Resolve an uploaded filename to a path that cannot escape ``upload_dir``.

    Strips all directory components (POSIX and Windows separators), rejects
    ``.``/``..``, and verifies the resolved path stays inside the sandbox.
    """
    upload_dir = Path(upload_dir)
    name = os.path.basename((filename or "").replace("\\", "/"))
    name = os.path.basename(name)  # belt-and-suspenders after separator swap
    if not name or name in (".", ".."):
        name = "upload"
    candidate = upload_dir / name
    if not candidate.resolve().is_relative_to(upload_dir.resolve()):
        candidate = upload_dir / "upload"
    return candidate


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
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = safe_upload_path(UPLOAD_DIR, file.filename or "").name
    fd, tmp = tempfile.mkstemp(dir=UPLOAD_DIR, suffix=Path(safe_name).suffix)
    try:
        with os.fdopen(fd, "wb") as out:
            shutil.copyfileobj(file.file, out)
        data = extract_receipt(Path(tmp))
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    if not data["needs_review"]:
        try:
            validate_minor(data["amount_minor"], data["currency"])
        except (ValueError, InvalidAmount):
            data["needs_review"] = True  # implausible parsed amount → don't persist it
    if data["needs_review"]:
        return {"status": "needs_review", "reason": "could not parse a plausible amount", "fields": data}
    tx = _ledger().add(
        date=data["date"], vendor=data["vendor"], amount_minor=data["amount_minor"],
        currency=data["currency"], category=data["category"], kind=KIND_EXPENSE,
        source=safe_name,
    )
    return {"status": "ingested", "tx": tx.__dict__, "display": format_money(tx.amount_minor, tx.currency)}


@app.post("/invoice")
def make_invoice(
    client: str = Form(...), amount: str = Form(...), currency: str = Form(DEFAULT_CURRENCY)
):
    try:
        minor = validate_minor(parse_money(amount, currency), currency)
    except (ValueError, InvalidAmount) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    pdf = generate_invoice_pdf(
        client, minor, currency.upper(), "Professional services", Path("data/invoice.pdf")
    )
    return FileResponse(pdf, filename="invoice.pdf")


@app.get("/report")
def rpt():
    p = generate_report(_ledger(), "current", "md")
    return FileResponse(p, filename="report.md")


@app.get("/health")
def health():
    return {"ok": True, "version": __version__, "db_exists": _db_path().exists()}


def run() -> None:  # pragma: no cover - console-script entrypoint (starts a server)
    import uvicorn

    uvicorn.run(
        app,
        host=default_host(),
        port=int(os.environ.get("LOCALFISCAL_PORT", "8080")),
    )


if __name__ == "__main__":  # pragma: no cover
    run()
