import builtins
from importlib import reload
import io

import app.dashboard as dashboard


class DummyStreamlit:
    def __init__(self):
        self.last = {}

    def title(self, *a, **k):
        return None

    def write(self, *a, **k):
        return None

    def file_uploader(self, *a, **k):
        return None

    def selectbox(self, *a, **k):
        # during summary, choose a preset other than Custom
        return "current_week"

    def date_input(self, *a, **k):
        # not expected to be called in this flow
        return None

    def metric(self, *a, **k):
        return None

    def subheader(self, *a, **k):
        return None

    def dataframe(self, *a, **k):
        return None

    def checkbox(self, *a, **k):
        return True

    def error(self, *a, **k):
        return None

    def success(self, *a, **k):
        return None

    def markdown(self, *a, **k):
        return None


def test_main_no_upload(monkeypatch):
    dummy = DummyStreamlit()
    monkeypatch.setattr(dashboard, 'st', dummy)
    # reload to ensure module-level title call uses monkeypatched st
    reload(dashboard)
    # call main which should run summary branch without raising
    dashboard.main()


def test_main_with_upload_and_persist(monkeypatch):
    # prepare a small CSV
    csv = """date,description,amount
2026-03-03,Ifd*Madero Industria e,36.59
2026-03-04,Uber* Trip,17.93
"""

    class Uploaded(io.StringIO):
        def __init__(self, s):
            super().__init__(s)
            self.name = 'sample.csv'

    # dummy repos to avoid touching real DB
    class DummyCatRepo:
        def ensure(self, id, name):
            return 'default-cat'

    class DummyTxRepo:
        def __init__(self, db_path=None):
            self.inserted = []

        def insert(self, *, id=None, date=None, description=None, amount=None, account_type=None, category_id=None):
            self.inserted.append((date, description, amount, category_id))
            return True

        def is_duplicate(self, date, amount, description):
            return False

    class DummyBatchRepo:
        def create_batch(self, id, source=None, notes=None):
            return None

        def update_counts(self, id, rows_parsed=None, inserted=None, failed=None):
            return None

    # stateful st to return different selectbox values
    class StatefulST(DummyStreamlit):
        def file_uploader(self, *a, **k):
            return Uploaded(csv)

        def selectbox(self, label, options, index=0):
            if 'Tipo de arquivo' in label:
                return 'Conta corrente'
            return 'current_week'

        def button(self, label):
            # simulate user clicking persist
            if label == 'Persistir transações':
                return True
            return False

    st_dummy = StatefulST()
    monkeypatch.setattr(dashboard, 'st', st_dummy)
    monkeypatch.setattr(dashboard, 'CategoryRepository', DummyCatRepo)
    monkeypatch.setattr(dashboard, 'TransactionRepository', DummyTxRepo)
    monkeypatch.setattr(dashboard, 'ImportBatchRepository', DummyBatchRepo)
    monkeypatch.setattr(dashboard, 'bootstrap', lambda: None)

    # reload module to pick up monkeypatched st for module-level calls
    reload(dashboard)
    dashboard.main()
