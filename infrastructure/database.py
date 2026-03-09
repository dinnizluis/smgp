import os
import sqlite3
from pathlib import Path
from typing import Iterator
from contextlib import contextmanager


DEFAULT_DB_PATH = os.path.join("data", "smgp.db")


_SCHEMA = [
    # categories table
    """
    CREATE TABLE IF NOT EXISTS categories (
        id TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        created_at DATETIME DEFAULT (CURRENT_TIMESTAMP)
    );
    """,

    # transactions table
    """
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        date DATE NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        account_type TEXT NOT NULL,
        category_id TEXT,
        created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
        FOREIGN KEY(category_id) REFERENCES categories(id)
    );
    """,

    # index to speed queries by date
    """
    CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
    """,
    # import batch metadata
    """
    CREATE TABLE IF NOT EXISTS import_batches (
        id TEXT PRIMARY KEY,
        source TEXT,
        file_type TEXT,
        rows_parsed INTEGER DEFAULT 0,
        inserted INTEGER DEFAULT 0,
        failed INTEGER DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT (CURRENT_TIMESTAMP)
    );
    """,
]


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if column not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        conn.commit()


def _ensure_data_dir(db_path: str) -> None:
    p = Path(db_path)
    parent = p.parent
    # if parent exists and is a file -> cannot create directory
    if parent.exists() and not parent.is_dir():
        raise OSError(f"Cannot create data directory, path exists and is not a directory: {parent}")
    # create if missing
    created = False
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
        created = True
    return created


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Cria o arquivo .db (se necessário) e aplica o esquema mínimo do MVP.

    - Garante que a pasta `data/` exista.
    - Habilita `foreign_keys`.
    - Cria as tabelas `categories` e `transactions`.
    """
    _ensure_data_dir(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.cursor()
        for stmt in _SCHEMA:
            cur.executescript(stmt)
        conn.commit()
        # ensure newer columns exist for migrations
        try:
            _ensure_column(conn, 'transactions', 'batch_id', 'TEXT')
            _ensure_column(conn, 'categories', 'created_from_batch', 'TEXT')
            _ensure_column(conn, 'import_batches', 'file_type', 'TEXT')
        except Exception:
            # best-effort: if migrations fail, continue (DB might be new)
            pass
    finally:
        conn.close()


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Retorna uma conexão SQLite pronta para uso.

    A função garante que a pasta exista e habilita `foreign_keys`.
    Caller é responsável por fechar a conexão.
    """
    _ensure_data_dir(db_path)
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def connection_context(db_path: str = DEFAULT_DB_PATH) -> Iterator[sqlite3.Connection]:
    """Context manager-like helper para usar em `with` (via yield).

    Exemplo:
        with connection_context('data/smgp.db') as conn:
            ...
    """
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


if __name__ == "__main__":
    # allow quick manual initialization
    print(f"Inicializando DB em: {DEFAULT_DB_PATH}")
    init_db(DEFAULT_DB_PATH)
    print("Pronto.")
