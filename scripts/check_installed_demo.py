"""Exercise the exact source archive advertised to buyers, without using the checkout package."""

import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
match = re.search(
    r"pipx install (https://github\.com/OrionArchitekton/localfiscal/archive/[a-f0-9]{40}\.zip)", readme
)
if match is None:
    raise SystemExit("README needs an immutable localfiscal archive URL")

with tempfile.TemporaryDirectory(prefix="installed-localfiscal-") as temporary:
    books = Path(temporary) / "sample"
    subprocess.run(
        [sys.executable, "-m", "pipx", "run", "--spec", match[1],
         "localfiscal", "demo", "--out", str(books)],
        check=True,
    )
    connection = sqlite3.connect(books / "ledger.db")
    try:
        rows = connection.execute("SELECT kind, amount_minor FROM tx").fetchall()
    finally:
        connection.close()
    income = sum(amount for kind, amount in rows if kind == "income")
    expense = sum(amount for kind, amount in rows if kind == "expense")
    assert (income, expense, income - expense, len(rows)) == (125000, 5450, 119550, 3)
    csv_bytes = (books / "transactions.csv").read_bytes()
    assert b"\r\r\n" not in csv_bytes and len(csv_bytes.splitlines()) == 4
    print("Pinned archive verified: income 125000, expense 5450, net 119550 minor units")
