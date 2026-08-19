from __future__ import annotations

import sqlite3

from app.core.config import get_content_db_path, is_running_on_vercel


def get_content_db() -> sqlite3.Connection:
    path = get_content_db_path()
    if is_running_on_vercel():
        try:
            conn = sqlite3.connect(f"file:{path}?mode=ro", timeout=30.0, uri=True)
        except sqlite3.OperationalError:
            # Vercel bundles can expose read-only files in ways that do not always
            # cooperate with SQLite's URI mode; plain open is still safe for reads.
            conn = sqlite3.connect(path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        return conn
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn

