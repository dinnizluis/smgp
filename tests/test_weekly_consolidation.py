from datetime import date, timedelta

from infrastructure.database import init_db
from infrastructure.repositories import TransactionRepository, CategoryRepository
from application.use_cases import get_current_week_total, get_previous_week_total, get_week_comparison, get_category_totals_current_week


def _iso(d: date) -> str:
    return d.isoformat()


def test_week_totals_and_comparison(tmp_path):
    db_path = str(tmp_path / "w.db")
    init_db(db_path)

    txr = TransactionRepository(db_path)
    cat = CategoryRepository(db_path)
    default_cat = cat.ensure(None, "Não categorizado")

    today = date.today()
    # current week: use Monday of this week
    monday = today - timedelta(days=today.weekday())
    # previous week monday
    prev_monday = monday - timedelta(days=7)

    # insert transactions
    txr.insert(date=_iso(monday), description="A", amount=10.0, account_type="checking", category_id=default_cat)
    txr.insert(date=_iso(monday + timedelta(days=1)), description="B", amount=20.0, account_type="checking", category_id=default_cat)
    txr.insert(date=_iso(prev_monday), description="C", amount=5.0, account_type="checking", category_id=default_cat)

    current = get_current_week_total(db_path)
    previous = get_previous_week_total(db_path)
    assert current == 30.0
    assert previous == 5.0

    comp = get_week_comparison(db_path)
    assert comp["current"] == 30.0
    assert comp["previous"] == 5.0
    assert isinstance(comp["pct_change"], float)


def test_category_totals_current_week(tmp_path):
    db_path = str(tmp_path / "w2.db")
    init_db(db_path)
    txr = TransactionRepository(db_path)
    cat = CategoryRepository(db_path)

    food_id = cat.ensure(None, "Food")
    misc_id = cat.ensure(None, "Misc")

    today = date.today()
    monday = today - timedelta(days=today.weekday())

    txr.insert(date=_iso(monday), description="Lunch", amount=12.5, account_type="checking", category_id=food_id)
    txr.insert(date=_iso(monday + timedelta(days=2)), description="Snack", amount=2.5, account_type="checking", category_id=food_id)
    txr.insert(date=_iso(monday + timedelta(days=1)), description="Pen", amount=1.0, account_type="checking", category_id=misc_id)

    cats = get_category_totals_current_week(db_path)
    # find food total
    food = next((c for c in cats if c["category"] == "Food"), None)
    misc = next((c for c in cats if c["category"] == "Misc"), None)
    assert food is not None and food["total"] == 15.0
    assert misc is not None and misc["total"] == 1.0
