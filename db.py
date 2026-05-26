import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")


class JobDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_jobs (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                remote_id  TEXT UNIQUE,
                title      TEXT,
                company    TEXT,
                tags       TEXT,
                url        TEXT,
                saved_at   TEXT
            )
        """)
        self.conn.commit()

    def save_job(self, job: dict):
        self.conn.execute(
            """
            INSERT OR IGNORE INTO saved_jobs
                (remote_id, title, company, tags, url, saved_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                job["id"],
                job["title"],
                job["company"],
                job["tags"],
                job["url"],
                datetime.now().isoformat(),
            ),
        )
        self.conn.commit()

    def list_jobs(self):
        return self.conn.execute(
            "SELECT * FROM saved_jobs ORDER BY saved_at DESC"
        ).fetchall()

    def delete_job(self, remote_id: str):
        self.conn.execute(
            "DELETE FROM saved_jobs WHERE remote_id = ?", (remote_id,)
        )
        self.conn.commit()
