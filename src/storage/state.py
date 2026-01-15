from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


class StateStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_listings (
                listing_id TEXT PRIMARY KEY,
                first_seen TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                listing_id TEXT,
                sent_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def has_seen(self, listing_id: str) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT 1 FROM seen_listings WHERE listing_id = ? LIMIT 1",
            (listing_id,),
        )
        return cur.fetchone() is not None

    def mark_seen(self, listing_id: str, first_seen: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO seen_listings (listing_id, first_seen) VALUES (?, ?)",
            (listing_id, first_seen),
        )
        self.conn.commit()

    def record_alert(self, listing_id: str, sent_at: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO alerts (listing_id, sent_at) VALUES (?, ?)",
            (listing_id, sent_at),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
