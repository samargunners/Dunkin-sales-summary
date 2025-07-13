# dashboard/utils/db.py

import sqlite3
from pathlib import Path

# Always resolve relative to the project root, not the current working directory
BASE_DIR = Path(__file__).resolve().parent.parent  # <- goes up to dunkin-sales-summary/
DB_PATH = BASE_DIR / "db" / "sales.db"

def get_connection():
    return sqlite3.connect(DB_PATH)
