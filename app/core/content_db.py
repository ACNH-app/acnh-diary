from __future__ import annotations

import sqlite3

from app.core.config import get_content_db_path


def get_content_db() -> sqlite3.Connection:
    conn = sqlite3.connect(get_content_db_path(), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn

