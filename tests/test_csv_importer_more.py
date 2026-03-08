import io
import pytest

import pandas as pd

from importers.csv_importer import (
    _normalize_amount,
    _normalize_date,
    _normalize_description,
    parse_csv,
    InvalidCSVError,
)


def test_normalize_amount_variants():
    assert _normalize_amount(123.45) == 123.45
    assert _normalize_amount("1234.56") == 1234.56
    assert _normalize_amount("1.234,56") == 1234.56
    assert _normalize_amount("R$ 1.234,56") == 1234.56
    assert _normalize_amount("$1,234.56") == 1234.56


def test_normalize_amount_invalid():
    with pytest.raises(ValueError):
        _normalize_amount(None)
    with pytest.raises(ValueError):
        _normalize_amount("not-a-number")


def test_normalize_date_and_description():
    assert _normalize_date("2025-11-01") == "2025-11-01"
    # pandas can parse many formats; assert matches pandas' own parser
    assert _normalize_date("01/11/2025") == pd.to_datetime("01/11/2025").date().isoformat()

    with pytest.raises(ValueError):
        _normalize_date("not-a-date")

    assert _normalize_description("  hello ") == "hello"
    with pytest.raises(ValueError):
        _normalize_description("")


def test_parse_csv_missing_columns_raises():
    # missing amount column
    csv = "date,description\n2025-11-01,foo"
    with pytest.raises(InvalidCSVError):
        parse_csv(io.StringIO(csv))


def test_parse_csv_reads_bytes_with_quoted_amount():
    b = b'date,description,amount\n2025-11-01,Loja,"R$ 1.234,56"\n'
    rows = parse_csv(b)
    assert len(rows) == 1
    assert rows[0].amount == 1234.56
