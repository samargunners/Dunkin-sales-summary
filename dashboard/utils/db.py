from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # goes from /dashboard/utils → /dunkin-sales-summary
DB_PATH = BASE_DIR / "db" / "sales.db"

def get_connection():
    return sqlite3.connect(DB_PATH)