#!/usr/bin/env python
"""localfiscal CLI — ambitious local receipt + invoice + ledger for solopreneurs."""

import typer
from pathlib import Path
from .ledger import Ledger, Transaction
from .extract import extract_receipt
from .invoice import generate_invoice_pdf
from .report import generate_report

app = typer.Typer(help="localfiscal — local-first finance that actually works")

ledger_path = Path("data/ledger.db")
ledger = Ledger(ledger_path)

@app.command()
def ingest(path: Path = typer.Argument(..., exists=True, help="Receipt image or PDF")):
    """Ingest a receipt (local vision or fallback)."""
    data = extract_receipt(path)
    tx = ledger.add(
        date=data["date"],
        vendor=data["vendor"],
        amount=data["amount"],
        category=data.get("category", "uncategorized"),
        source=str(path),
    )
    typer.echo(f"INGESTED: {tx.id} | {tx.date} | {tx.vendor} | {tx.amount} | {tx.category}")

@app.command()
def add(date: str, vendor: str, amount: float, category: str = typer.Option("general", "--category")):
    """Manual add transaction."""
    tx = ledger.add(date=date, vendor=vendor, amount=amount, category=category)
    typer.echo(f"ADDED: {tx.id}")

@app.command("list-tx")
def list_tx(limit: int = typer.Option(20, "--limit")):
    """List recent transactions."""
    for t in ledger.list(limit=limit):
        typer.echo(f"{t.id} | {t.date} | {t.vendor} | {t.amount:.2f} | {t.category}")

@app.command()
def invoice(client: str, amount: float, description: str = "Services", out: Path = Path("invoice.pdf")):
    """Generate a simple invoice PDF."""
    pdf_path = generate_invoice_pdf(client, amount, description, out)
    typer.echo(f"INVOICE: {pdf_path}")

@app.command()
def report(period: str = typer.Option("current", "--period"), fmt: str = typer.Option("md", "--fmt")):
    """Generate P&L style report."""
    out = generate_report(ledger, period, fmt)
    typer.echo(f"REPORT: {out}")

@app.command()
def health():
    """Quick health + db check."""
    typer.echo("localfiscal v0.1.0 OK")
    typer.echo(f"db: {ledger_path} exists={ledger_path.exists()}")

if __name__ == "__main__":
    app()
