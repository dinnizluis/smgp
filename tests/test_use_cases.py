import os
from datetime import date, timedelta
import tempfile

from infrastructure.database import init_db
from infrastructure.repositories import TransactionRepository, CategoryRepository
from application.use_cases import (
    _normalize_text,
    load_category_rules,
    infer_category_for_transaction,
    get_period_total,
    get_period_category_totals,
    get_sorted_period_category_totals,
    compute_period_preset,
)
from domain.models import Transaction


def test_normalize_text():
    assert _normalize_text('Áçúnto Teste') == 'acunto teste'
    assert _normalize_text('') == ''


def test_load_rules_missing(tmp_path):
    p = tmp_path / 'nope.json'
    assert load_category_rules(str(p)) == []


def test_infer_with_invalid_regex(tmp_path):
    rules = [
        {"pattern": "(unclosed", "category": "X", "type": "regex", "priority": 100},
        {"pattern": "valid", "category": "Y", "type": "keyword", "priority": 50},
    ]
    tx = Transaction(id=None, date='2026-01-01', description='valid merchant', amount=10.0)
    # invalid regex must be skipped and keyword match should return Y
    assert infer_category_for_transaction(tx, rules) == 'Y'


def test_period_aggregation_and_categories():
    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, 'test.db')
        init_db(db_path)
        txr = TransactionRepository(db_path)
        cat = CategoryRepository(db_path)
        food = cat.ensure(None, 'Food')

        today = date.today()
        s = today - timedelta(days=2)
        e = today
        # insert transactions within period
        txr.insert(date=s.isoformat(), description='Meal1', amount=10.0, account_type='checking', category_id=food)
        txr.insert(date=e.isoformat(), description='Meal2', amount=5.0, account_type='checking', category_id=food)
        # insert outside period
        txr.insert(date=(s - timedelta(days=10)).isoformat(), description='Old', amount=100.0, account_type='checking', category_id=food)

        total = get_period_total(s.isoformat(), e.isoformat(), db_path)
        assert total == 15.0
        cats = get_period_category_totals(s.isoformat(), e.isoformat(), db_path)
        assert isinstance(cats, list)
        row = next((c for c in cats if c['category'] == 'Food'), None)
        assert row is not None and row['total'] == 15.0


def test_compute_presets():
    t = date(2026, 3, 10)
    s, e = compute_period_preset('current_week', today=t)
    assert s <= e
    s, e = compute_period_preset('last_4_weeks', today=t)
    assert (date.fromisoformat(e) - date.fromisoformat(s)).days == 27
    s, e = compute_period_preset('last_month', today=t)
    assert date.fromisoformat(s).month != t.month
    s, e = compute_period_preset('last_year', today=t)
    assert date.fromisoformat(s).year == 2025


def test_get_sorted_period_category_totals_order_and_exclude_zero():
    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, 'test.db')
        init_db(db_path)
        txr = TransactionRepository(db_path)
        cat = CategoryRepository(db_path)
        a = cat.ensure(None, 'A')
        b = cat.ensure(None, 'B')
        c = cat.ensure(None, 'C')

        today = date.today()
        s = today - timedelta(days=2)
        e = today
        # A => 10, B => 0 (5 + -5), C => 2
        txr.insert(date=s.isoformat(), description='A1', amount=10.0, account_type='checking', category_id=a)
        txr.insert(date=s.isoformat(), description='B1', amount=5.0, account_type='checking', category_id=b)
        txr.insert(date=e.isoformat(), description='B2', amount=-5.0, account_type='checking', category_id=b)
        txr.insert(date=e.isoformat(), description='C1', amount=2.0, account_type='checking', category_id=c)

        rows = get_sorted_period_category_totals(s.isoformat(), e.isoformat(), db_path=db_path, exclude_zero=True, top_n=None)
        assert all(float(r['total']) != 0 for r in rows)
        # must be sorted descending by total: A (10) then C (2)
        assert rows[0]['category'] == 'A'
        assert float(rows[0]['total']) == 10.0
        assert rows[1]['category'] == 'C'
        assert float(rows[1]['total']) == 2.0


def test_get_sorted_period_category_totals_top_n():
    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, 'test.db')
        init_db(db_path)
        txr = TransactionRepository(db_path)
        cat = CategoryRepository(db_path)
        x = cat.ensure(None, 'X')
        y = cat.ensure(None, 'Y')
        z = cat.ensure(None, 'Z')

        today = date.today()
        s = today - timedelta(days=2)
        e = today
        txr.insert(date=s.isoformat(), description='X1', amount=100.0, account_type='checking', category_id=x)
        txr.insert(date=s.isoformat(), description='Y1', amount=50.0, account_type='checking', category_id=y)
        txr.insert(date=e.isoformat(), description='Z1', amount=25.0, account_type='checking', category_id=z)

        rows = get_sorted_period_category_totals(s.isoformat(), e.isoformat(), db_path=db_path, top_n=2)
        assert len(rows) == 2
        assert rows[0]['category'] == 'X'
        assert rows[1]['category'] == 'Y'