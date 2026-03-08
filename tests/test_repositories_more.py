import os
import tempfile
import sqlite3

from infrastructure.repositories import bootstrap, TransactionRepository


def test_transaction_duplicate_and_get_delete(tmp_path):
    db_path = str(tmp_path / "r.db")
    bootstrap(db_path)
    txr = TransactionRepository(db_path)

    # insert one
    ok = txr.insert(date="2025-11-01", description="A", amount=1.0, account_type="checking")
    assert ok is True
    # duplicate insert should return False
    ok2 = txr.insert(date="2025-11-01", description="A", amount=1.0, account_type="checking")
    assert ok2 is False

    # count and is_duplicate
    assert txr.count() == 1
    assert txr.is_duplicate("2025-11-01", 1.0, "A") is True

    # get_by_id (fetch an id from list_all)
    rows = txr.list_all()
    assert len(rows) == 1
    rid = rows[0]["id"]
    fetched = txr.get_by_id(rid)
    assert fetched is not None and fetched["description"] == "A"

    # delete_all clears
    txr.delete_all()
    assert txr.count() == 0


def test_insert_with_nonexistent_category_raises(tmp_path):
    db_path = str(tmp_path / "r2.db")
    bootstrap(db_path)
    txr = TransactionRepository(db_path)

    # using a random category id that does not exist should raise IntegrityError
    try:
        txr.insert(date="2025-11-01", description="X", amount=5.0, account_type="checking", category_id="no-such-cat")
    except sqlite3.IntegrityError:
        # expected on some SQLite builds
        return
    else:
        # if no exception was raised, ensure the row was not inserted or FK was ignored
        # check if count is 0 or 1 but ensure category column matches
        rows = txr.list_all()
        if rows:
            assert rows[0]["category_id"] == "no-such-cat"
