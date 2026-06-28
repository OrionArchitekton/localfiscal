#!/usr/bin/env python
"""localfiscal CLI — local-first receipt + invoice + ledger for solopreneurs."""

from __future__ import annotations

import os
from pathlib import Path

import typer

from . import __version__
from .exporters import export_transactions
from .extract import extract_receipt
from .invoice import generate_invoice_pdf
from .ledger import KIND_EXPENSE, KIND_INCOME, Ledger
from .money import DEFAULT_CURRENCY, format_money, parse_money
from .validate import InvalidAmount, validate_currency, validate_minor

app = typer.Typer(help="localfiscal — local-first finance that actually works")

def _db_path() -> Path:
    """Ledger path — honors $LOCALFISCAL_DB so the CLI and web UI share one ledger."""
    return Path(os.environ.get("LOCALFISCAL_DB", "data/ledger.db"))


def _ledger() -> Ledger:
    return Ledger(_db_path())


def _parse_amount_or_exit(amount: str, currency: str) -> int:
    try:
        validate_currency(currency)
        minor = parse_money(amount, currency)
        return validate_minor(minor, currency)
    except (ValueError, InvalidAmount) as exc:
        typer.echo(f"ERROR: {exc}", err=True)
        raise typer.Exit(2) from None


@app.command()
def ingest(
    path: Path = typer.Argument(..., exists=True, help="Receipt image or PDF"),
    vision: bool = typer.Option(False, "--vision", help="Use a local Ollama vision model if configured"),
    ollama_url: str | None = typer.Option(None, "--ollama-url", help="Ollama base URL (else $OLLAMA_URL)"),
):
    """Ingest a receipt. If no amount can be parsed, flag for review (never invent one)."""
    if vision:
        from .vision import resolve_endpoint

        if resolve_endpoint(ollama_url) is None:
            typer.echo(
                "NOTE: --vision requested but no Ollama endpoint is configured "
                "(--ollama-url or $OLLAMA_URL); using the heuristic parser."
            )
    data = extract_receipt(path, use_vision=vision, ollama_url=ollama_url)
    review = data["needs_review"]
    if not review:
        try:
            validate_minor(data["amount_minor"], data["currency"])
        except (ValueError, InvalidAmount):
            review = True  # parsed an implausible amount → don't persist it
    if review:
        typer.echo(
            "NEEDS REVIEW: could not parse a plausible amount from this receipt. "
            "Add it manually:  localfiscal add <date> <vendor> <amount> --category <cat>"
        )
        raise typer.Exit(3)
    tx = _ledger().add(
        date=data["date"],
        vendor=data["vendor"],
        amount_minor=data["amount_minor"],
        currency=data["currency"],
        category=data["category"],
        kind=KIND_EXPENSE,
        source=str(path),
    )
    typer.echo(
        f"INGESTED: {tx.id} | {tx.date} | {tx.vendor} | "
        f"{format_money(tx.amount_minor, tx.currency)} | {tx.category}"
    )


@app.command()
def add(
    date: str,
    vendor: str,
    amount: str = typer.Argument(..., help="Amount, e.g. 12.50 or '$1,234.56'"),
    currency: str = typer.Option(DEFAULT_CURRENCY, "--currency"),
    category: str = typer.Option("general", "--category"),
    income: bool = typer.Option(False, "--income", help="Record as income (default: expense)"),
):
    """Manually add a transaction (amount parsed exactly to minor units)."""
    minor = _parse_amount_or_exit(amount, currency)
    kind = KIND_INCOME if income else KIND_EXPENSE
    tx = _ledger().add(
        date=date, vendor=vendor, amount_minor=minor, currency=currency.upper(),
        category=category, kind=kind,
    )
    typer.echo(f"ADDED: {tx.id} | {format_money(tx.amount_minor, tx.currency)} | {tx.kind}")


@app.command("list-tx")
def list_tx(limit: int = typer.Option(20, "--limit")):
    """List recent transactions."""
    for t in _ledger().list(limit=limit):
        typer.echo(
            f"{t.id} | {t.date} | {t.vendor} | "
            f"{format_money(t.amount_minor, t.currency)} | {t.category} | {t.kind}"
        )


@app.command()
def invoice(
    client: str,
    amount: str = typer.Argument(..., help="Invoice amount, e.g. 1200 or '$1,200.00'"),
    currency: str = typer.Option(DEFAULT_CURRENCY, "--currency"),
    description: str = typer.Option("Professional services", "--description"),
    out: Path = typer.Option(Path("invoice.pdf"), "--out"),
):
    """Generate a simple invoice PDF."""
    minor = _parse_amount_or_exit(amount, currency)
    pdf_path = generate_invoice_pdf(client, minor, currency.upper(), description, out)
    typer.echo(f"INVOICE: {pdf_path}")


@app.command()
def report(
    period: str = typer.Option("current", "--period"),
    fmt: str = typer.Option("md", "--fmt", help="md | json | csv"),
):
    """Generate a category + net (income/expense) report."""
    from .report import generate_report

    out = generate_report(_ledger(), period, fmt)
    typer.echo(f"REPORT: {out}")


@app.command()
def export(
    fmt: str = typer.Option("csv", "--fmt", help="csv | ofx"),
    out: Path | None = typer.Option(None, "--out"),
):
    """Export the full ledger for accountants (CSV or OFX/QFX)."""
    dest = export_transactions(_ledger().list(limit=None), fmt, out)
    typer.echo(f"EXPORT: {dest}")


@app.command()
def health():
    """Quick health + db check."""
    db = _db_path()
    typer.echo(f"localfiscal v{__version__} OK")
    typer.echo(f"db: {db} exists={db.exists()}")


if __name__ == "__main__":
    app()
