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
from .validate import validate_currency

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
            self._migrate(con)
            con.commit()
        finally:
            con.close()

    def _migrate(self, con: sqlite3.Connection) -> None:
        """Upgrade a v0.1 ledger (amount REAL, no currency/kind) in place, idempotently.

        v0.1 stored a single float ``amount`` and no ``currency``/``kind``. On such a
        database ``CREATE TABLE IF NOT EXISTS`` no-ops, so we add the new columns and
        backfill ``amount_minor`` from the old float amount (×100, rounded). A fresh
        v0.2 database already has ``amount_minor`` and is left untouched.
        """
        cols = {row[1] for row in con.execute("PRAGMA table_info(tx)").fetchall()}
        if "amount_minor" in cols:
            return  # already v0.2 schema
        con.execute("ALTER TABLE tx ADD COLUMN amount_minor INTEGER")
        if "currency" not in cols:
            con.execute("ALTER TABLE tx ADD COLUMN currency TEXT NOT NULL DEFAULT 'USD'")
        if "kind" not in cols:
            con.execute("ALTER TABLE tx ADD COLUMN kind TEXT NOT NULL DEFAULT 'expense'")
        if "amount" in cols:
            # old float dollars → integer cents (best-effort, half-up via ROUND)
            con.execute(
                "UPDATE tx SET amount_minor = CAST(ROUND(amount * 100) AS INTEGER)"
                " WHERE amount_minor IS NULL"
            )
        con.execute("UPDATE tx SET amount_minor = 0 WHERE amount_minor IS NULL")

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
        currency = validate_currency(currency)
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

    def list(self, limit: int | None = 50) -> builtins.list[Transaction]:
        """Recent transactions (newest first). ``limit=None`` returns the whole ledger
        (used by reports and exports so no rows are silently dropped)."""
        sql = "SELECT id,date,vendor,amount_minor,currency,category,kind,source FROM tx ORDER BY id DESC"
        params: tuple = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)
        con = self._connect()
        try:
            rows = con.execute(sql, params).fetchall()
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
