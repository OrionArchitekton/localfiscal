"""Real exports accountants actually use: RFC-4180 CSV and OFX/QFX (SGML).

Both derive from exact integer minor units. CSV round-trips through ``csv.reader``;
OFX emits a valid OFX 1.0.2 SGML statement (one ``<STMTTRN>`` per transaction,
grouped into one statement per currency).
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from .ledger import KIND_INCOME, Transaction
from .money import format_money, to_decimal

CSV_FIELDS = [
    "id", "date", "vendor", "amount_minor", "amount", "currency", "category", "kind", "source",
]

# leading chars a spreadsheet treats as a formula (CSV/formula injection)
_FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value: object) -> str:
    """Neutralize spreadsheet formula injection in a free-text field."""
    s = "" if value is None else str(value)
    if s and s[0] in _FORMULA_TRIGGERS:
        return "'" + s
    return s


def _sgml_escape(value: object) -> str:
    """Escape SGML-special characters so a field value cannot break OFX structure."""
    s = "" if value is None else str(value)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def transactions_to_csv(txs: list[Transaction]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_FIELDS)
    for t in txs:
        writer.writerow([
            t.id, t.date, _csv_safe(t.vendor), t.amount_minor,
            str(to_decimal(t.amount_minor, t.currency)), t.currency,
            _csv_safe(t.category), t.kind, _csv_safe(t.source or ""),
        ])
    return buf.getvalue()


def report_to_csv(data: dict) -> str:
    """Report CSV from the structured payload — carries income/expense/net (md/json
    parity) plus per-category nets, with every text cell injection-neutralized."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["currency", "section", "label", "minor", "display"])
    for cur, s in data["currencies"].items():
        for label in ("income", "expense", "net"):
            writer.writerow([cur, "summary", label, s[label], _csv_safe(format_money(s[label], cur))])
        for category, minor in sorted(s["by_category"].items()):
            writer.writerow(
                [cur, "category", _csv_safe(category), minor, _csv_safe(format_money(minor, cur))]
            )
    return buf.getvalue()


def _ofx_date(date_str: str) -> str:
    """Normalize an ISO/loose date to OFX YYYYMMDD (best-effort, digits only)."""
    digits = "".join(ch for ch in date_str if ch.isdigit())
    return (digits + "00000000")[:8] if digits else "00000000"


def _ofx_amount(t: Transaction) -> str:
    """Signed decimal string for OFX TRNAMT (income credit +, expense debit -)."""
    return str(to_decimal(t.signed_minor(), t.currency))


_OFX_HEADER = (
    "OFXHEADER:100\n"
    "DATA:OFXSGML\n"
    "VERSION:102\n"
    "SECURITY:NONE\n"
    "ENCODING:USASCII\n"
    "CHARSET:1252\n"
    "COMPRESSION:NONE\n"
    "OLDFILEUID:NONE\n"
    "NEWFILEUID:NONE\n\n"
)


def transactions_to_ofx(txs: list[Transaction]) -> str:
    by_cur: dict[str, list[Transaction]] = {}
    for t in txs:
        by_cur.setdefault(t.currency, []).append(t)

    parts = [_OFX_HEADER, "<OFX>\n"]
    parts.append(
        "<SIGNONMSGSRSV1><SONRS><STATUS><CODE>0<SEVERITY>INFO</STATUS>"
        "<DTSERVER>00000000<LANGUAGE>ENG</SONRS></SIGNONMSGSRSV1>\n"
    )
    parts.append("<BANKMSGSRSV1>\n")
    for idx, (cur, rows) in enumerate(sorted(by_cur.items()), start=1):
        dates = [_ofx_date(t.date) for t in rows] or ["00000000"]
        parts.append(
            f"<STMTTRNRS><TRNUID>{idx}<STATUS><CODE>0<SEVERITY>INFO</STATUS>\n"
            f"<STMTRS><CURDEF>{cur}"
            "<BANKACCTFROM><BANKID>localfiscal<ACCTID>ledger<ACCTTYPE>CHECKING</BANKACCTFROM>\n"
            f"<BANKTRANLIST><DTSTART>{min(dates)}<DTEND>{max(dates)}\n"
        )
        for t in rows:
            trntype = "CREDIT" if t.kind == KIND_INCOME else "DEBIT"
            name = _sgml_escape((t.vendor or "")[:32])
            memo = _sgml_escape((t.category or "")[:32])
            parts.append(
                f"<STMTTRN><TRNTYPE>{trntype}<DTPOSTED>{_ofx_date(t.date)}"
                f"<TRNAMT>{_ofx_amount(t)}<FITID>{t.id}<NAME>{name}<MEMO>{memo}</STMTTRN>\n"
            )
        net = sum(t.signed_minor() for t in rows)
        parts.append(
            "</BANKTRANLIST>"
            f"<LEDGERBAL><BALAMT>{to_decimal(net, cur)}<DTASOF>{max(dates)}</LEDGERBAL>\n"
            "</STMTRS></STMTTRNRS>\n"
        )
    parts.append("</BANKMSGSRSV1>\n</OFX>\n")
    return "".join(parts)


def export_transactions(
    txs: list[Transaction], fmt: str = "csv", out: Path | None = None
) -> Path:
    fmt = fmt.lower()
    if fmt == "csv":
        body, ext = transactions_to_csv(txs), "csv"
    elif fmt in ("ofx", "qfx"):
        body, ext = transactions_to_ofx(txs), fmt
    else:
        raise ValueError(f"unknown export format: {fmt!r} (use csv or ofx)")
    dest = Path(out) if out else Path("data") / f"export.{ext}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")
    return dest
