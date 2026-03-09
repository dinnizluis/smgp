import uuid
from typing import Optional, List, Dict

from .database import get_connection, init_db, DEFAULT_DB_PATH
from typing import Any


class CategoryRepository:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
    def ensure(self, id: Optional[str], name: str, created_from_batch: Optional[str] = None) -> str:
        """Ensure a category exists. Returns category id.

        If the category did not exist and is created now, `created_from_batch`
        will be recorded (if provided).
        """
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            # check existing
            cur.execute("SELECT id FROM categories WHERE name = ?", (name,))
            row = cur.fetchone()
            if row:
                return row[0]

            # create new with optional created_from_batch
            if id is None:
                id = uuid.uuid4().hex
            cur.execute(
                "INSERT INTO categories (id, name, created_from_batch) VALUES (?, ?, ?)",
                (id, name, created_from_batch),
            )
            conn.commit()
            return id
        finally:
            conn.close()

    def list_all(self) -> List[Dict]:
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name, created_at, created_from_batch FROM categories ORDER BY name")
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def delete_by_name(self, name: str) -> bool:
        """Delete a category by name. Reassigns transactions to NULL for that category.

        Returns True if a category was deleted, False otherwise.
        """
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM categories WHERE name = ?", (name,))
            row = cur.fetchone()
            if not row:
                return False
            cid = row[0]
            # set transactions to uncategorized
            cur.execute("UPDATE transactions SET category_id = NULL WHERE category_id = ?", (cid,))
            # delete category
            cur.execute("DELETE FROM categories WHERE id = ?", (cid,))
            conn.commit()
            return True
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

    def is_duplicate(self, date: str, amount: float, description: str) -> bool:
        """Public wrapper for duplicate check (useful for tests)."""
        return self._is_duplicate(date, amount, description)

    def insert(self, *, id: Optional[str] = None, date: str, description: str, amount: float, account_type: str, category_id: Optional[str] = None, batch_id: Optional[str] = None) -> bool:
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
                INSERT INTO transactions (id, date, description, amount, account_type, category_id, batch_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (id, date, description, amount, account_type, category_id, batch_id),
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
            q = "SELECT id, date, description, amount, account_type, category_id, batch_id, created_at FROM transactions ORDER BY date DESC"
            if limit:
                q += " LIMIT %d" % int(limit)
            cur.execute(q)
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_by_id(self, id: str) -> Optional[Dict]:
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, date, description, amount, account_type, category_id, batch_id, created_at FROM transactions WHERE id = ?", (id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def update_category(self, id: str, category_id: Optional[str]) -> bool:
        """Update the category_id of a transaction. Returns True if a row was updated."""
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute("UPDATE transactions SET category_id = ? WHERE id = ?", (category_id, id))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def delete_all(self) -> None:
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM transactions")
            conn.commit()
        finally:
            conn.close()

    def sum_between(self, start_date: str, end_date: str) -> float:
        """Return sum(amount) for transactions between start_date and end_date (inclusive)."""
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE date BETWEEN ? AND ?",
                (start_date, end_date),
            )
            val = cur.fetchone()[0]
            return float(val) if val is not None else 0.0
        finally:
            conn.close()

    def sum_by_category_between(self, start_date: str, end_date: str) -> List[Dict]:
        """Return list of dicts with category name and sum for transactions in range.

        Result rows: {"category": name, "total": float}
        """
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    COALESCE(c.name, 'Não categorizado') AS category,
                    COALESCE(SUM(t.amount), 0) AS total
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY total DESC
                """,
                (start_date, end_date),
            )
            rows = cur.fetchall()
            return [{"category": r[0], "total": float(r[1])} for r in rows]
        finally:
            conn.close()


def bootstrap(db_path: str = DEFAULT_DB_PATH) -> None:
    """Convenience function to initialize DB and ensure default categories."""
    init_db(db_path)
    cat_repo = CategoryRepository(db_path)
    cat_repo.ensure(None, "Não categorizado")


class ImportBatchRepository:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path

    def create_batch(self, id: str, source: Optional[str] = None, notes: Optional[str] = None, file_type: Optional[str] = None) -> None:
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO import_batches (id, source, file_type, notes) VALUES (?, ?, ?, ?)",
                (id, source, file_type, notes),
            )
            conn.commit()
        finally:
            conn.close()

    def update_counts(self, id: str, rows_parsed: int = None, inserted: int = None, failed: int = None) -> None:
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            updates = []
            params: list[Any] = []
            if rows_parsed is not None:
                updates.append("rows_parsed = ?")
                params.append(rows_parsed)
            if inserted is not None:
                updates.append("inserted = ?")
                params.append(inserted)
            if failed is not None:
                updates.append("failed = ?")
                params.append(failed)
            if not updates:
                return
            params.append(id)
            q = "UPDATE import_batches SET " + ", ".join(updates) + " WHERE id = ?"
            cur.execute(q, tuple(params))
            conn.commit()
        finally:
            conn.close()

    def get_batch(self, id: str) -> Optional[Dict]:
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, source, file_type, rows_parsed, inserted, failed, notes, created_at FROM import_batches WHERE id = ?", (id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
