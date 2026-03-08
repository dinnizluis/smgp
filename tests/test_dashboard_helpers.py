from app.dashboard import file_type_to_account_type, guess_account_type


def test_file_type_to_account_type():
    assert file_type_to_account_type("Fatura cartão") == "credit"
    assert file_type_to_account_type("Conta corrente") == "checking"


def test_guess_account_type():
    assert guess_account_type("Nubank") == "credit"
    assert guess_account_type("") == "checking"
    assert guess_account_type("My Checking") == "checking"
