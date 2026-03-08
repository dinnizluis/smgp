import os
import tempfile
import sqlite3

from infrastructure.repositories import bootstrap, CategoryRepository, TransactionRepository


def test_repositories_insert_and_deduplicate():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        bootstrap(db_path)

        cat_repo = CategoryRepository(db_path)
        tx_repo = TransactionRepository(db_path)

        # ensure default category exists
        default_id = cat_repo.ensure(None, "Não categorizado")
        assert isinstance(default_id, str)

        # insert one transaction
        ok = tx_repo.insert(date="2025-10-01", description="Foo", amount=10.0, account_type="checking", category_id=default_id)
        assert ok is True
        assert tx_repo.count() == 1

        # duplicate insertion should be ignored
        ok2 = tx_repo.insert(date="2025-10-01", description="Foo", amount=10.0, account_type="checking", category_id=default_id)
        assert ok2 is False
        assert tx_repo.count() == 1

        # insert different transaction
        ok3 = tx_repo.insert(date="2025-10-02", description="Bar", amount=5.5, account_type="checking", category_id=default_id)
        assert ok3 is True
        assert tx_repo.count() == 2

        # inserting with invalid category should raise IntegrityError
        try:
            tx_repo.insert(date="2025-10-03", description="Baz", amount=1.0, account_type="checking", category_id="nope")
        except sqlite3.IntegrityError:
            raised = True
        else:
            raised = False
        assert raised is True
