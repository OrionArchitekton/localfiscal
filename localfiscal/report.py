"""Reports."""

from pathlib import Path
from .ledger import Ledger
import json

def generate_report(ledger: Ledger, period: str, fmt: str = "md") -> Path:
    txs = ledger.list(limit=1000)
    total = sum(t.amount for t in txs)
    by_cat = {}
    for t in txs:
        by_cat[t.category] = by_cat.get(t.category, 0.0) + t.amount

    out = Path("data") / f"report-{period}.{fmt}"
    out.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "md":
        lines = [f"# localfiscal Report {period}\n", f"**Total:** ${total:.2f}\n"]
        for c, a in sorted(by_cat.items()):
            lines.append(f"- {c}: ${a:.2f}")
        out.write_text("\n".join(lines))
    else:
        out.write_text(json.dumps({"period": period, "total": total, "by_category": by_cat}, indent=2))
    return out
