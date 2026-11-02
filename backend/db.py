import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager
from backend.config import DB_PATH, BASE_DIR

def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    migration_file = BASE_DIR / "migrations" / "001_init.sql"
    with open(migration_file, "r", encoding="utf-8") as f:
        sql_script = f.read()

    with get_db() as conn:
        conn.executescript(sql_script)

    seed_sources()

def seed_sources():
    agencies_file = BASE_DIR / "agencies.json"
    if not agencies_file.exists():
        return

    with open(agencies_file, "r", encoding="utf-8") as f:
        sources_data = json.load(f)

    with get_db() as conn:
        for s in sources_data:
            conn.execute(
                """
                INSERT INTO sources (
                    source_key, agency, operator_type, base_url, timezone,
                    refresh_seconds, enabled, label
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_key) DO UPDATE SET
                    agency=excluded.agency,
                    operator_type=excluded.operator_type,
                    base_url=excluded.base_url,
                    timezone=excluded.timezone,
                    refresh_seconds=excluded.refresh_seconds,
                    label=excluded.label
                """,
                (
                    s["source_key"],
                    s["agency"],
                    s["operator_type"],
                    s["base_url"],
                    s.get("timezone", "Asia/Kolkata"),
                    s.get("refresh_seconds", 300),
                    s.get("enabled", 1),
                    s["label"]
                )
            )

