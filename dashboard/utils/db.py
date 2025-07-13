import sqlite3
from pathlib import Path

# Debugging
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "db" / "sales.db"
print(f"Resolved DB path: {DB_PATH}")
print(f"Exists: {DB_PATH.exists()}")

def get_connection():
    return sqlite3.connect(DB_PATH)