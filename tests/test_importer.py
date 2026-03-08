import io
import pytest

from importers.csv_importer import parse_csv, InvalidCSVError
from domain.models import Transaction


def test_parse_valid_sample_file():
    rows = parse_csv("data/Nubank_2025-11-07.csv")
    assert isinstance(rows, list)
    assert len(rows) == 109
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
