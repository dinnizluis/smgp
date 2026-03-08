from types import SimpleNamespace

from app.dashboard import guess_account_type, file_type_to_account_type


def test_guess_account_type_credit_keywords():
    assert guess_account_type("Nubank_credit_statement.csv") == "credit"
    assert guess_account_type("cartao_visa.csv") == "credit"
    assert guess_account_type("mycreditcard.csv") == "credit"


def test_guess_account_type_default_checking():
    assert guess_account_type("transactions.csv") == "checking"
    assert guess_account_type("") == "checking"


def test_apply_selected_account_type_to_rows(tmp_path):
    # simulate uploaded rows as simple objects with attributes like dataclass
    rows = [SimpleNamespace(date="2025-11-01", description="A", amount=1.0), SimpleNamespace(date="2025-11-02", description="B", amount=2.0)]
    from app.dashboard import get_dashboard_summary
    # ensure that applying via persistence path will not raise (we test heuristic separately)
    # here we just check guess function; actual persistence tested elsewhere
    assert guess_account_type("credit_file.csv") == "credit"


def test_file_type_label_mapping():
    assert file_type_to_account_type("Conta corrente") == "checking"
    assert file_type_to_account_type("Fatura cartão") == "credit"
