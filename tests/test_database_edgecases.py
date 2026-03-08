import os
import tempfile
import pathlib
import pytest

from infrastructure.database import init_db


def test_init_db_raises_when_parent_is_file(tmp_path):
    # create a file where the parent directory should be
    parent = tmp_path / "parentfile"
    parent.write_text("i am a file, not a dir")
    db_path = parent / "db.sqlite"
    # calling init_db should raise because parent exists and is not a directory
    with pytest.raises(OSError):
        init_db(str(db_path))
