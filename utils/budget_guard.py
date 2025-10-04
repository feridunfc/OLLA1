from __future__ import annotations
import os, sqlite3, threading
from dataclasses import dataclass
from datetime import datetime

DB_PATH = os.getenv("BUDGET_DB", "budget.db")
MONTHLY_LIMIT = float(os.getenv("MONTHLY_BUDGET", "100.0"))

@dataclass
class BudgetRecord:
    task_id: str
    usd: float
    status: str  # reserved | committed | released
    ts: str

class BudgetGuard:
    """Persistent budget guard using sqlite; reserve/commit/release."""
    def __init__(self, db_path: str = DB_PATH, monthly_limit: float = MONTHLY_LIMIT):
        self.db_path = db_path
        self.monthly_limit = monthly_limit
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("""CREATE TABLE IF NOT EXISTS budget(
            task_id TEXT PRIMARY KEY, usd REAL, status TEXT, ts TEXT)""")
        self._conn.commit()

    def _used_this_month(self) -> float:
        cur = self._conn.execute(
          "SELECT COALESCE(SUM(usd),0) FROM budget WHERE status='committed' AND substr(ts,1,7)=?",
          (datetime.utcnow().strftime("%Y-%m"),)
        )
        val = cur.fetchone()[0]
        return float(val or 0.0)

    def reserve(self, task_id: str, est_usd: float) -> bool:
        with self._lock:
            if self._used_this_month() + est_usd > self.monthly_limit:
                return False
            self._conn.execute(
              "INSERT OR REPLACE INTO budget(task_id,usd,status,ts) VALUES(?,?,'reserved',?)",
              (task_id, float(est_usd), datetime.utcnow().isoformat())
            )
            self._conn.commit()
            return True

    def commit(self, task_id: str, actual_usd: float) -> None:
        with self._lock:
            self._conn.execute(
              "UPDATE budget SET status='committed', usd=?, ts=? WHERE task_id=?",
              (float(actual_usd), datetime.utcnow().isoformat(), task_id)
            )
            self._conn.commit()

    def release(self, task_id: str) -> None:
        with self._lock:
            self._conn.execute(
              "UPDATE budget SET status='released', ts=? WHERE task_id=?",
              (datetime.utcnow().isoformat(), task_id)
            )
            self._conn.commit()

    def usage_this_month(self) -> float:
        return self._used_this_month()
