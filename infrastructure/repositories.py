import uuid
from typing import Optional, List, Dict

from .database import get_connection, init_db, DEFAULT_DB_PATH


class CategoryRepository:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path

    def ensure(self, id: Optional[str], name: str) -> str:
        """Ensure a category exists. Returns category id."""
        if id is None:
            id = uuid.uuid4().hex
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO categories (id, name) VALUES (?, ?)",
                (id, name),
            )
            conn.commit()
            # fetch id in case another row exists with same name
            cur.execute("SELECT id FROM categories WHERE name = ?", (name,))
            row = cur.fetchone()
            return row[0]
        finally:
            conn.close()

    def list_all(self) -> List[Dict]:
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name, created_at FROM categories ORDER BY name")
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


class TransactionRepository:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path

    def _is_duplicate(self, date: str, amount: float, description: str) -> bool:
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM transactions WHERE date = ? AND amount = ? AND description = ? LIMIT 1",
                (date, amount, description),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()

    def insert(self, *, id: Optional[str] = None, date: str, description: str, amount: float, account_type: str, category_id: Optional[str] = None) -> bool:
        """Insert a transaction.

        Returns True if inserted, False if detected as duplicate and not inserted.
        """
        if id is None:
            id = uuid.uuid4().hex

        if self._is_duplicate(date, amount, description):
            return False

        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO transactions (id, date, description, amount, account_type, category_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (id, date, description, amount, account_type, category_id),
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def count(self) -> int:
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM transactions")
            return cur.fetchone()[0]
        finally:
            conn.close()

    def list_all(self, limit: Optional[int] = None) -> List[Dict]:
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            q = "SELECT id, date, description, amount, account_type, category_id, created_at FROM transactions ORDER BY date DESC"
            if limit:
                q += " LIMIT %d" % int(limit)
            cur.execute(q)
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


def bootstrap(db_path: str = DEFAULT_DB_PATH) -> None:
    """Convenience function to initialize DB and ensure default categories."""
    init_db(db_path)
    cat_repo = CategoryRepository(db_path)
    cat_repo.ensure(None, "Não categorizado")
