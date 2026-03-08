import os
import io
import tempfile

from importers.csv_importer import parse_csv
from infrastructure.repositories import bootstrap, TransactionRepository


def test_import_flow_unique_count():
    # Use an embedded sample CSV for tests (avoid relying on user's private data file)
    sample_csv = """date,title,amount
2025-10-29,99app *99app,17.80
2025-10-26,Ifd*Madero Industria e,56.19
2025-10-25,Uber* Trip,17.93
2025-10-25,Uber* Trip,17.93
"""

    rows = parse_csv(io.StringIO(sample_csv))
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
