import sqlite3

import os
DB_PATH = os.path.join(os.path.dirname(__file__), "weather.db")

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS areas (
  area_code TEXT PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS forecast_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  area_code TEXT NOT NULL,
  fetched_at TEXT NOT NULL,
  raw_json TEXT,
  FOREIGN KEY (area_code) REFERENCES areas(area_code)
);

CREATE TABLE IF NOT EXISTS forecast_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  date TEXT NOT NULL,
  weather_text TEXT NOT NULL,
  UNIQUE(run_id, date),
  FOREIGN KEY (run_id) REFERENCES forecast_runs(id)
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()