from datetime import date, timedelta

from infrastructure.database import init_db
from infrastructure.repositories import TransactionRepository, CategoryRepository
from app.dashboard import get_dashboard_summary


def _iso(d: date) -> str:
    return d.isoformat()


def test_dashboard_summary_returns_expected_values(tmp_path):
    db_path = str(tmp_path / "dash.db")
    init_db(db_path)

    txr = TransactionRepository(db_path)
    cat = CategoryRepository(db_path)
    food = cat.ensure(None, "Food")

    today = date.today()
    monday = today - timedelta(days=today.weekday())

    txr.insert(date=_iso(monday), description="Meal", amount=10.0, account_type="checking", category_id=food)
    txr.insert(date=_iso(monday + timedelta(days=1)), description="Snack", amount=5.0, account_type="checking", category_id=food)

    summary = get_dashboard_summary(db_path)
    assert summary["current"] == 15.0
    assert isinstance(summary["categories"], list)
    food_row = next((c for c in summary["categories"] if c["category"] == "Food"), None)
    assert food_row is not None and food_row["total"] == 15.0
