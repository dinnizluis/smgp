import io
import pytest

from importers.csv_importer import parse_csv, InvalidCSVError


def test_parse_bytes_and_formats():
    csv = """date,description,amount
2026-03-01,Padaria Sion,12,34
2026-03-02,Negativo,(1.234,56)
"""
    # fix locales: use dot for thousands and comma decimal intentionally malformed as two columns
    b = csv.encode("utf-8")
    with pytest.raises(InvalidCSVError):
        # malformed CSV should raise
        parse_csv(io.BytesIO(b))


def test_parse_amount_variants():
    csv = """date,description,amount
2026-03-01,Padaria Sion,"12,34"
2026-03-02,Negativo,"(1.234,56)"
2026-03-03,DotDecimal,"1234.56"
"""
    rows = parse_csv(io.StringIO(csv))
    assert len(rows) == 3
    assert rows[0].amount == 12.34
    assert rows[1].amount == -1234.56
    assert rows[2].amount == 1234.56


def test_missing_columns_error():
    csv = """valor,titulo
1,foo
"""
    with pytest.raises(InvalidCSVError):
        parse_csv(io.StringIO(csv))
