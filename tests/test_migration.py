"""FIX-A — opening a v0.1 database migrates it in place (no data loss, no crash)."""

import sqlite3

from localfiscal.ledger import Ledger


def _make_v01_db(path):
    """Recreate the exact v0.1 schema (amount REAL, no currency/kind/amount_minor)."""
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE tx (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, vendor TEXT,"
        " amount REAL, category TEXT, source TEXT)"
    )
    con.execute(
        "INSERT INTO tx (date, vendor, amount, category, source) VALUES (?,?,?,?,?)",
        ("2026-05-01", "Old Vendor", 19.99, "meals", "old.jpg"),
    )
    con.execute(
        "INSERT INTO tx (date, vendor, amount, category, source) VALUES (?,?,?,?,?)",
        ("2026-05-02", "Coffee", 4.50, "meals", None),
    )
    con.commit()
    con.close()


def test_opening_v01_db_migrates_and_preserves_rows(tmp_path):
    db = tmp_path / "v01.db"
    _make_v01_db(db)

    led = Ledger(db)  # must migrate, not raise
    rows = sorted(led.list(), key=lambda t: t.id)
    assert len(rows) == 2
    assert rows[0].amount_minor == 1999  # 19.99 -> 1999 cents (backfilled, exact)
    assert rows[1].amount_minor == 450
    assert all(r.currency == "USD" for r in rows)  # default backfill
    assert all(r.kind == "expense" for r in rows)
    assert rows[0].vendor == "Old Vendor" and rows[0].category == "meals"


def test_new_adds_work_after_migration(tmp_path):
    db = tmp_path / "v01.db"
    _make_v01_db(db)
    led = Ledger(db)
    t = led.add("2026-06-01", "New Co", 12345, "EUR", "supplies")
    assert t.amount_minor == 12345 and t.currency == "EUR"
    assert len(led.list()) == 3


def test_migration_is_idempotent(tmp_path):
    db = tmp_path / "v01.db"
    _make_v01_db(db)
    Ledger(db)  # migrate once
    led2 = Ledger(db)  # opening again must not double-migrate or fail
    assert len(led2.list()) == 2
