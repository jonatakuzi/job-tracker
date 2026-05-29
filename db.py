"""
db.py - SQLite storage layer for job-tracker.

All saved jobs live in a single 'jobs' table. The database file
(jobs.db) is created automatically on first run in the same directory.

Schema:
    id          TEXT PRIMARY KEY  - RemoteOK job ID
    title       TEXT              - Job title / position name
    company     TEXT              - Company name
    tags        TEXT              - Comma-separated skill tags from the listing
    url         TEXT              - Direct link to the job posting
    date        TEXT              - ISO date string from RemoteOK
    saved_at    TEXT              - Local timestamp when you saved it
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS jobs (
    id       TEXT PRIMARY KEY,
    title    TEXT NOT NULL,
    company  TEXT,
    tags     TEXT,
    url      TEXT,
    date     TEXT,
    saved_at TEXT
)
"""


class JobDB:
    """Thin wrapper around sqlite3 for storing and retrieving saved jobs."""

    def __init__(self, path: str = DB_PATH):
        """
        Open (or create) the database file and ensure the jobs table exists.
        SQLite creates the .db file automatically if it is not there yet,
        which means no setup step is needed before the first run.
        """
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(CREATE_TABLE)
        self.conn.commit()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def save_job(self, job: dict) -> bool:
        """
        Insert a job into the database.
        Returns True if the job was saved, False if the ID was already present.
        The PRIMARY KEY constraint on 'id' prevents duplicates automatically.
        """
        try:
            self.conn.execute(
                "INSERT INTO jobs (id, title, company, tags, url, date, saved_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(job["id"]),
                    job.get("position", ""),
                    job.get("company", ""),
                    ", ".join(job.get("tags", [])),
                    job.get("url", ""),
                    job.get("date", ""),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_job(self, job_id: str) -> bool:
        """
        Delete a saved job by its RemoteOK ID.
        Returns True if a row was deleted, False if the ID was not found.
        """
        cur = self.conn.execute("DELETE FROM jobs WHERE id = ?", (str(job_id),))
        self.conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def list_jobs(self) -> list[dict]:
        """
        Return all saved jobs as a list of dicts, sorted newest-first
        by the time they were saved (not by the job's original post date).
        """
        rows = self.conn.execute(
            "SELECT * FROM jobs ORDER BY saved_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_job(self, job_id: str) -> dict | None:
        """Return a single saved job by its RemoteOK ID, or None if not found."""
        row = self.conn.execute(
            "SELECT * FROM jobs WHERE id = ?", (str(job_id),)
        ).fetchone()
        return dict(row) if row else None

    def get_stats(self) -> dict:
        """
        Summarize everything in the saved jobs database.

        Returns:
            total         - Number of bookmarked jobs
            top_companies - Top 5 companies by how many listings you saved
            top_tags      - Top 10 skill tags across all saved listings
            oldest_save   - Timestamp of the first job you ever saved
            newest_save   - Timestamp of the most recent save

        Useful for spotting which skills appear most in roles you are
        interested in, which can guide what to study or emphasize on a resume.
        """
        jobs = self.list_jobs()
        if not jobs:
            return {"total": 0, "top_companies": [], "top_tags": [],
                    "oldest_save": None, "newest_save": None}

        company_counts: dict[str, int] = {}
        for j in jobs:
            c = (j.get("company") or "Unknown").strip() or "Unknown"
            company_counts[c] = company_counts.get(c, 0) + 1

        tag_counts: dict[str, int] = {}
        for j in jobs:
            for tag in [t.strip() for t in (j.get("tags") or "").split(",") if t.strip()]:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            "total": len(jobs),
            "top_companies": sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "oldest_save": jobs[-1]["saved_at"],
            "newest_save": jobs[0]["saved_at"],
        }

    # ------------------------------------------------------------------

    def close(self):
        """Close the database connection when the program exits."""
        self.conn.close()
