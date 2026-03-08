from datetime import date, timedelta
from typing import Optional, Dict, List
import re
import json
import unicodedata
from pathlib import Path

from infrastructure.repositories import TransactionRepository


# Helpers for category inference
DEFAULT_RULES_PATH = Path("data/category_rules.json")


def _normalize_text(s: str) -> str:
    if not s:
        return ""
    # lowercase, strip, remove accents
    s = s.lower().strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s


def load_category_rules(path: Optional[str] = None) -> List[Dict]:
    """Load category rules from JSON file. Returns list of rule dicts.

    Each rule is expected to contain: pattern (string), category (string), type ('keyword'|'regex'), priority (int)
    """
    p = Path(path) if path else DEFAULT_RULES_PATH

    # If the main file doesn't exist, try the example/template next to it
    if not p.exists():
        alt = p.with_name(p.name + ".example")
        if alt.exists():
            p = alt
        else:
            return []

    def try_load_text(text: str) -> List[Dict]:
        try:
            data = json.loads(text)
            return data if isinstance(data, list) else []
        except Exception:
            # Try to strip common Markdown fences (```json ... ```)
            stripped = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", text)
            stripped = re.sub(r"\n```\s*$", "", stripped)
            try:
                data = json.loads(stripped)
                return data if isinstance(data, list) else []
            except Exception:
                return []

    try:
        with p.open("r", encoding="utf-8") as f:
            # Prefer json.load but keep a text fallback to sanitize accidental fences
            try:
                data = json.load(f)
                return data if isinstance(data, list) else []
            except Exception:
                f.seek(0)
                text = f.read()
                return try_load_text(text)
    except Exception:
        return []


def infer_category_for_transaction(tx, rules: Optional[List[Dict]] = None) -> Optional[str]:
    """Infer a category name for a Transaction-like object using provided rules.

    Rules are applied in descending priority order. For 'keyword' rules the normalized
    keyword must be a substring of the normalized description. For 'regex' rules the
    pattern is matched against the normalized description.
    """
    if rules is None:
        rules = load_category_rules()

    if not rules:
        return None

    desc = getattr(tx, "description", "")
    norm = _normalize_text(desc)

    # sort by priority descending (higher priority first)
    sorted_rules = sorted(rules, key=lambda r: int(r.get("priority", 0)), reverse=True)
    for r in sorted_rules:
        rtype = r.get("type", "keyword")
        pat = r.get("pattern", "")
        if not pat:
            continue
        if rtype == "regex":
            try:
                if re.search(pat, norm):
                    return r.get("category")
            except re.error:
                # skip invalid regex
                continue
        else:
            # keyword match
            if pat in norm:
                return r.get("category")

    return None



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


def get_period_total(start_date: str, end_date: str, db_path: Optional[str] = None) -> float:
    repo = TransactionRepository(db_path) if db_path else TransactionRepository()
    return repo.sum_between(start_date, end_date)


def get_period_category_totals(start_date: str, end_date: str, db_path: Optional[str] = None) -> List[Dict]:
    repo = TransactionRepository(db_path) if db_path else TransactionRepository()
    return repo.sum_by_category_between(start_date, end_date)


def get_sorted_period_category_totals(
    start_date: str,
    end_date: str,
    db_path: Optional[str] = None,
    exclude_zero: bool = True,
    top_n: Optional[int] = 8,
) -> List[Dict]:
    """Return period category totals sorted descending by `total`.

    - `exclude_zero`: if True, remove categories with total == 0.
    - `top_n`: limit results to top N categories (default 8 for MVP). Use None for no limit.
    """
    repo = TransactionRepository(db_path) if db_path else TransactionRepository()
    rows = repo.sum_by_category_between(start_date, end_date)
    if exclude_zero:
        rows = [r for r in rows if float(r.get("total", 0)) != 0]
    rows_sorted = sorted(rows, key=lambda r: float(r.get("total", 0)), reverse=True)
    if top_n is not None:
        try:
            n = int(top_n)
            rows_sorted = rows_sorted[:n]
        except Exception:
            pass
    return rows_sorted


def compute_period_preset(preset: str, today: Optional[date] = None) -> (str, str):
    """Return (start_iso, end_iso) for a named preset.

    Presets: current_week, last_4_weeks, last_month, last_quarter, last_6_months, last_year
    """
    if today is None:
        today = date.today()

    if preset == "current_week":
        return _week_start_end_for(today)

    if preset == "last_4_weeks":
        # last 28 days ending today
        start = today - timedelta(days=27)
        end = today
        return start.isoformat(), end.isoformat()

    if preset == "last_month":
        # previous calendar month
        first = today.replace(day=1)
        last_month_end = first - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return last_month_start.isoformat(), last_month_end.isoformat()

    if preset == "last_quarter":
        # previous 3-month calendar period
        m = (today.month - 1) // 3 * 3 + 1
        quarter_start = date(today.year, m, 1)
        prev_q_end = quarter_start - timedelta(days=1)
        prev_q_start_month = ((prev_q_end.month - 1) // 3) * 3 + 1
        prev_q_start = date(prev_q_end.year, prev_q_start_month, 1)
        return prev_q_start.isoformat(), prev_q_end.isoformat()

    if preset == "last_6_months":
        start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        # go back 5 more months
        month = start.month
        year = start.year
        for _ in range(5):
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
        start = start.replace(year=year, month=month, day=1)
        end = today
        return start.isoformat(), end.isoformat()

    if preset == "last_year":
        start = date(today.year - 1, 1, 1)
        end = date(today.year - 1, 12, 31)
        return start.isoformat(), end.isoformat()

    raise ValueError("Unknown preset")
