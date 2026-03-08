from datetime import date, timedelta
from typing import Optional, Dict, List

from infrastructure.repositories import TransactionRepository


def _week_start_end_for(d: date) -> (str, str):
    """Return ISO date strings for start (Monday) and end (Sunday) of week containing d."""
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return start.isoformat(), end.isoformat()


def get_current_week_total(db_path: Optional[str] = None) -> float:
    repo = TransactionRepository(db_path) if db_path else TransactionRepository()
    today = date.today()
    s, e = _week_start_end_for(today)
    return repo.sum_between(s, e)


def get_previous_week_total(db_path: Optional[str] = None) -> float:
    repo = TransactionRepository(db_path) if db_path else TransactionRepository()
    today = date.today()
    start = today - timedelta(days=today.weekday()) - timedelta(days=7)
    end = start + timedelta(days=6)
    return repo.sum_between(start.isoformat(), end.isoformat())


def get_week_comparison(db_path: Optional[str] = None) -> Dict:
    current = get_current_week_total(db_path)
    previous = get_previous_week_total(db_path)
    if previous == 0:
        pct = None
    else:
        pct = round((current - previous) / abs(previous) * 100, 2)
    return {"current": current, "previous": previous, "pct_change": pct}


def get_category_totals_current_week(db_path: Optional[str] = None) -> List[Dict]:
    repo = TransactionRepository(db_path) if db_path else TransactionRepository()
    today = date.today()
    s, e = _week_start_end_for(today)
    return repo.sum_by_category_between(s, e)
