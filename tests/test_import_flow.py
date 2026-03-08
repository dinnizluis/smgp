import os
import tempfile

from importers.csv_importer import parse_csv
from infrastructure.repositories import bootstrap, TransactionRepository


def test_import_flow_unique_count():
    # parse sample file
    rows = parse_csv("data/Nubank_2025-11-07.csv")
    # compute unique key set used by deduplication: date, amount, description
    uniques = {(t.date, t.amount, t.description) for t in rows}

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "flow.db")
        bootstrap(db_path)
        tx_repo = TransactionRepository(db_path)
        inserted = 0
        for t in rows:
            if tx_repo.insert(date=t.date, description=t.description, amount=t.amount, account_type=t.account_type or "checking"):
                inserted += 1

        assert inserted == len(uniques)
        assert tx_repo.count() == len(uniques)
