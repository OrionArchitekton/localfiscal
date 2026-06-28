"""Local sqlite ledger — money stored as exact integer minor units.

Amounts are integer minor units (see ``localfiscal.money``); never floats. Each
row carries its ISO-4217 ``currency`` and a ``kind`` (``income``/``expense``) so
reports can compute a real signed net.
"""

from __future__ import annotations

import builtins
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .money import DEFAULT_CURRENCY

KIND_INCOME = "income"
KIND_EXPENSE = "expense"
_VALID_KINDS = (KIND_INCOME, KIND_EXPENSE)


@dataclass
class Transaction:
    id: int
    date: str
    vendor: str
    amount_minor: int
    currency: str
    category: str
    kind: str = KIND_EXPENSE
    source: str | None = None

    def signed_minor(self) -> int:
        """Income is positive, expense negative — the value that sums to a net."""
        return self.amount_minor if self.kind == KIND_INCOME else -abs(self.amount_minor)


class Ledger:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        con = self._connect()
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS tx (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    vendor TEXT NOT NULL,
                    amount_minor INTEGER NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'USD',
                    category TEXT NOT NULL DEFAULT 'general',
                    kind TEXT NOT NULL DEFAULT 'expense',
                    source TEXT
                )
                """
            )
            con.commit()
        finally:
            con.close()

    def add(
        self,
        date: str,
        vendor: str,
        amount_minor: int,
        currency: str = DEFAULT_CURRENCY,
        category: str = "general",
        kind: str = KIND_EXPENSE,
        source: str | None = None,
    ) -> Transaction:
        if not isinstance(amount_minor, int) or isinstance(amount_minor, bool):
            raise TypeError("amount_minor must be an int (minor units)")
        if kind not in _VALID_KINDS:
            raise ValueError(f"kind must be one of {_VALID_KINDS}, got {kind!r}")
        currency = currency.upper()
        con = self._connect()
        try:
            cur = con.execute(
                "INSERT INTO tx (date, vendor, amount_minor, currency, category, kind, source)"
                " VALUES (?,?,?,?,?,?,?)",
                (date, vendor, amount_minor, currency, category, kind, source),
            )
            con.commit()
            tx_id = cur.lastrowid
        finally:
            con.close()
        assert tx_id is not None  # AUTOINCREMENT row id is set after a committed INSERT
        return Transaction(
            id=tx_id,
            date=date,
            vendor=vendor,
            amount_minor=amount_minor,
            currency=currency,
            category=category,
            kind=kind,
            source=source,
        )

    def list(self, limit: int = 50) -> builtins.list[Transaction]:
        con = self._connect()
        try:
            rows = con.execute(
                "SELECT id,date,vendor,amount_minor,currency,category,kind,source"
                " FROM tx ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        finally:
            con.close()
        return [Transaction(*r) for r in rows]

    def get(self, tx_id: int) -> Transaction | None:
        con = self._connect()
        try:
            row = con.execute(
                "SELECT id,date,vendor,amount_minor,currency,category,kind,source FROM tx WHERE id=?",
                (tx_id,),
            ).fetchone()
        finally:
            con.close()
        return Transaction(*row) if row else None
