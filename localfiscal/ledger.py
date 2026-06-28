"""Simple local sqlite ledger."""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import List, Optional

@dataclass
class Transaction:
    id: int
    date: str
    vendor: str
    amount: float
    category: str
    source: Optional[str] = None

class Ledger:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        con = sqlite3.connect(self.db_path)
        con.execute("""
            CREATE TABLE IF NOT EXISTS tx (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                vendor TEXT,
                amount REAL,
                category TEXT,
                source TEXT
            )
        """)
        con.commit()
        con.close()

    def add(self, date: str, vendor: str, amount: float, category: str, source: Optional[str] = None) -> Transaction:
        con = sqlite3.connect(self.db_path)
        cur = con.execute(
            "INSERT INTO tx (date, vendor, amount, category, source) VALUES (?,?,?,?,?)",
            (date, vendor, amount, category, source)
        )
        con.commit()
        tx_id = cur.lastrowid
        con.close()
        return Transaction(id=tx_id, date=date, vendor=vendor, amount=amount, category=category, source=source)

    def list(self, limit: int = 50) -> List[Transaction]:
        con = sqlite3.connect(self.db_path)
        rows = con.execute("SELECT id,date,vendor,amount,category,source FROM tx ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        con.close()
        return [Transaction(*r) for r in rows]

    def get(self, tx_id: int) -> Optional[Transaction]:
        con = sqlite3.connect(self.db_path)
        row = con.execute("SELECT * FROM tx WHERE id=?", (tx_id,)).fetchone()
        con.close()
        if row:
            return Transaction(*row)
        return None
