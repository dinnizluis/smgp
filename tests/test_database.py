import os
import tempfile

from infrastructure.database import init_db, get_connection
from infrastructure.repositories import CategoryRepository, TransactionRepository


def test_init_and_repositories_work():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_smgp.db")

        # init DB
        init_db(db_path)
        assert os.path.exists(db_path)

        # basic tables exist
        conn = get_connection(db_path)
        try:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            names = [r[0] for r in cur.fetchall()]
            assert "categories" in names
            assert "transactions" in names
        finally:
            conn.close()

        # repositories
        cat_repo = CategoryRepository(db_path)
        tx_repo = TransactionRepository(db_path)

        cat_id = cat_repo.ensure(None, "Não categorizado")
        assert isinstance(cat_id, str) and len(cat_id) > 0

        inserted = tx_repo.insert(date="2026-03-07", description="coffee", amount=-3.5, account_type="checking", category_id=cat_id)
        assert inserted is True
        # duplicate should be ignored
        inserted2 = tx_repo.insert(date="2026-03-07", description="coffee", amount=-3.5, account_type="checking", category_id=cat_id)
        assert inserted2 is False

        assert tx_repo.count() == 1
