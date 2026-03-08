from infrastructure.database import init_db
from infrastructure.repositories import TransactionRepository, CategoryRepository


def test_persisted_account_type_respects_selection(tmp_path):
    db_path = str(tmp_path / "persist.db")
    init_db(db_path)

    txr = TransactionRepository(db_path)
    cat = CategoryRepository(db_path)
    default_cat = cat.ensure(None, "Não categorizado")

    # simulate rows parsed with default checking
    rows = [
        type("T", (), {"date": "2025-11-01", "description": "A", "amount": 10.0, "account_type": "checking"})(),
        type("T", (), {"date": "2025-11-02", "description": "B", "amount": 20.0, "account_type": "checking"})(),
    ]

    # user selected file type 'Fatura cartão' -> account_type 'credit'
    selected_account_type = "credit"

    # persist applying override as UI does
    for t in rows:
        t.account_type = selected_account_type
        txr.insert(date=t.date, description=t.description, amount=t.amount, account_type=t.account_type, category_id=default_cat)

    stored = txr.list_all()
    assert all(r["account_type"] == "credit" for r in stored)
