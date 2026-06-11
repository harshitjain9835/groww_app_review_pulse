import sqlite3
import os
import logging
from typing import Optional
from .models import RunRecord, DeliveryRecord

logger = logging.getLogger(__name__)

class RunLedger:
    def __init__(self, db_path: str = "g:\\project 3\\data\\ledger.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    product TEXT NOT NULL,
                    iso_week TEXT NOT NULL,
                    status TEXT NOT NULL,
                    review_count INTEGER,
                    window_weeks INTEGER,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    error_message TEXT,
                    UNIQUE(product, iso_week, status)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    url TEXT,
                    idempotency_key TEXT,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                )
            ''')
            conn.commit()

    def record_run(self, run: RunRecord):
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('''
                    INSERT INTO runs (run_id, product, iso_week, status, review_count, window_weeks, started_at, completed_at, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (run.run_id, run.product, run.iso_week, run.status, run.review_count, run.window_weeks, run.started_at, run.completed_at, run.error_message))
                
                for d in run.deliveries:
                    conn.execute('''
                        INSERT INTO deliveries (run_id, channel, external_id, url, idempotency_key)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (run.run_id, d.channel, d.external_id, d.url, d.idempotency_key))
                conn.commit()
            except sqlite3.IntegrityError as e:
                logger.warning(f"Ledger Integrity Exception: A successful run for {run.product} {run.iso_week} might already exist. Details: {e}")

    def get_successful_run(self, product: str, iso_week: str) -> Optional[RunRecord]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM runs WHERE product = ? AND iso_week = ? AND status = 'completed'", (product, iso_week)).fetchone()
            if row:
                d_rows = conn.execute("SELECT * FROM deliveries WHERE run_id = ?", (row['run_id'],)).fetchall()
                deliveries = [DeliveryRecord(**dict(d)) for d in d_rows]
                run_dict = dict(row)
                run_dict['deliveries'] = deliveries
                return RunRecord(**run_dict)
        return None