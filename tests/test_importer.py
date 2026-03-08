import io
import pytest

from importers.csv_importer import parse_csv, InvalidCSVError
from domain.models import Transaction


def test_parse_valid_sample_file():
    sample_csv = """date,title,amount
2025-10-29,99app *99app,17.80
2025-10-26,Ifd*Madero Industria e,56.19
2025-10-25,Uber* Trip,17.93
"""
    rows = parse_csv(io.StringIO(sample_csv))
    assert isinstance(rows, list)
    assert len(rows) == 3
    assert isinstance(rows[0], Transaction)
    assert rows[0].description == "99app *99app"


def test_missing_columns_raises():
    csv = "date,description\n2025-01-01,foo"
    with pytest.raises(InvalidCSVError):
        parse_csv(io.StringIO(csv))


def test_bad_row_raises():
    # missing description
    csv = "date,description,amount\n2025-01-01,,10"
    with pytest.raises(InvalidCSVError):
        parse_csv(io.StringIO(csv))
