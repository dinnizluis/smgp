import uuid

from infrastructure.database import init_db
from infrastructure.repositories import ImportBatchRepository


def test_create_and_update_batch(tmp_path):
    db_path = str(tmp_path / "b.db")
    # initialize schema
    init_db(db_path)

    repo = ImportBatchRepository(db_path)
    bid = uuid.uuid4().hex
    repo.create_batch(bid, source="unit-test", notes="initial")

    b = repo.get_batch(bid)
    assert b is not None
    assert b["source"] == "unit-test"
    assert b["rows_parsed"] == 0

    repo.update_counts(bid, rows_parsed=10, inserted=8, failed=2)
    b2 = repo.get_batch(bid)
    assert b2["rows_parsed"] == 10
    assert b2["inserted"] == 8
    assert b2["failed"] == 2
