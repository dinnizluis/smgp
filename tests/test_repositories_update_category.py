from datetime import date
import os
import tempfile

from infrastructure.database import init_db
from infrastructure.repositories import TransactionRepository, CategoryRepository


def test_update_category_basic():
    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, 'test.db')
        init_db(db_path)
        txr = TransactionRepository(db_path)
        cat = CategoryRepository(db_path)
        # create a category
        food_id = cat.ensure(None, 'Food')
        # insert a transaction without category
        txr.insert(date=date.today().isoformat(), description='Lunch', amount=-12.5, account_type='checking', category_id=None)
        rows = txr.list_all(limit=10)
        assert len(rows) >= 1
        tx = rows[0]
        tx_id = tx['id']
        # update category
        ok = txr.update_category(tx_id, food_id)
        assert ok is True
        updated = txr.get_by_id(tx_id)
        assert updated['category_id'] == food_id
