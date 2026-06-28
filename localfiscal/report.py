"""Reports — exact integer money; md / json / csv stay consistent by construction.

Every format is derived from the same integer minor-unit totals, so the markdown
and JSON (and CSV) reports can never disagree (the v0.1 float bug). Income/expense
sign convention gives a real net; mixed-currency ledgers are reported per currency,
never silently summed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .ledger import KIND_INCOME, Ledger, Transaction
from .money import DEFAULT_CURRENCY, format_money


def _summarize(txs: List[Transaction], currency: str) -> Dict:
    """Per-currency summary: signed net plus income/expense and per-category expense."""
    rows = [t for t in txs if t.currency == currency]
    income = sum(t.amount_minor for t in rows if t.kind == KIND_INCOME)
    expense = sum(abs(t.amount_minor) for t in rows if t.kind != KIND_INCOME)
    net = income - expense
    by_cat: Dict[str, int] = {}
    for t in rows:
        signed = t.signed_minor()
        by_cat[t.category] = by_cat.get(t.category, 0) + signed
    return {"income": income, "expense": expense, "net": net, "by_category": by_cat}


def report_data(ledger: Ledger, period: str) -> Dict:
    """Structured, exact report payload (the single source every format renders)."""
    txs = ledger.list(limit=1_000_000)
    currencies = sorted({t.currency for t in txs}) or [DEFAULT_CURRENCY]
    return {
        "period": period,
        "currencies": {c: _summarize(txs, c) for c in currencies},
        "count": len(txs),
    }


def _render_md(data: Dict) -> str:
    lines = [f"# localfiscal Report {data['period']}", ""]
    for cur, s in data["currencies"].items():
        lines.append(f"## {cur}")
        lines.append(f"- **Income:** {format_money(s['income'], cur)}")
        lines.append(f"- **Expenses:** {format_money(s['expense'], cur)}")
        lines.append(f"- **Net:** {format_money(s['net'], cur)}")
        lines.append("")
        lines.append("### By category (net)")
        for c, a in sorted(s["by_category"].items()):
            lines.append(f"- {c}: {format_money(a, cur)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_json(data: Dict) -> str:
    out = {"period": data["period"], "count": data["count"], "currencies": {}}
    for cur, s in data["currencies"].items():
        out["currencies"][cur] = {
            "income_minor": s["income"],
            "expense_minor": s["expense"],
            "net_minor": s["net"],
            "income": format_money(s["income"], cur),
            "expense": format_money(s["expense"], cur),
            "net": format_money(s["net"], cur),
            "by_category": {
                c: {"minor": a, "display": format_money(a, cur)}
                for c, a in sorted(s["by_category"].items())
            },
        }
    return json.dumps(out, indent=2)


def render(data: Dict, fmt: str) -> str:
    if fmt == "md":
        return _render_md(data)
    if fmt == "json":
        return _render_json(data)
    if fmt == "csv":
        from .exporters import report_to_csv

        return report_to_csv(data)
    if fmt == "ofx":
        raise ValueError("ofx is a transaction export, use `export --fmt ofx`, not `report`")
    raise ValueError(f"unknown report format: {fmt!r}")


def generate_report(
    ledger: Ledger, period: str, fmt: str = "md", out_dir: Optional[Path] = None
) -> Path:
    data = report_data(ledger, period)
    body = render(data, fmt)
    out = Path(out_dir or "data") / f"report-{period}.{fmt}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    return out
