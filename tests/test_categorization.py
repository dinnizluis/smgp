import pytest

from domain.models import Transaction
from application.use_cases import infer_category_for_transaction, load_category_rules


@pytest.mark.parametrize(
    "desc,expected",
    [
        ("Ifd*Madero Industria e", "Alimentação"),
        ("Uber* Trip", "Transporte"),
        ("SALARIO DE MARC3", "Renda"),
        ("SUPERMERCADO PÃO DE AÇÚCAR", "Supermercado"),
        ("Compra no Mercado Livre", "Compras"),
        ("Unknown merchant XYZ", None),
    ],
)
def test_infer_category_simple(desc, expected):
    tx = Transaction(id=None, date="2025-10-10", description=desc, amount=10.0)
    rules = load_category_rules()
    cat = infer_category_for_transaction(tx, rules)
    assert cat == expected
