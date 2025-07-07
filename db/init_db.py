import sqlite3
from pathlib import Path

# Define path to SQLite DB (Windows-friendly, relative to project)
db_path = Path("db/sales.db")
db_path.parent.mkdir(parents=True, exist_ok=True)

# Connect and create tables
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create sales_summary table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sales_summary (
    store_id TEXT,
    date TEXT,
    gross_sales REAL,
    net_sales REAL,
    tax REAL,
    guest_count INTEGER,
    avg_check REAL,
    gift_card_sales REAL,
    refunds REAL,
    void_amount REAL,
    cash_in REAL,
    deposits REAL,
    cash_over_short REAL
)
""")

# Create sales_by_order_type table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sales_by_order_type (
    store_id TEXT,
    date TEXT,
    order_type TEXT,
    net_sales REAL,
    guests INTEGER,
    avg_check REAL
)
""")

# Create sales_by_daypart table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sales_by_daypart (
    store_id TEXT,
    date TEXT,
    daypart TEXT,
    net_sales REAL,
    check_count INTEGER,
    avg_check REAL
)
""")

# Create sales_by_subcategory table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sales_by_subcategory (
    store_id TEXT,
    date TEXT,
    subcategory TEXT,
    qty_sold INTEGER,
    net_sales REAL,
    percent_sales REAL
)
""")

# Create labor_metrics table
cursor.execute("""
CREATE TABLE IF NOT EXISTS labor_metrics (
    store_id TEXT,
    date TEXT,
    position TEXT,
    reg_hours REAL,
    ot_hours REAL,
    total_hours REAL,
    reg_pay REAL,
    ot_pay REAL,
    total_pay REAL,
    percent_labor REAL
)
""")

# Commit and close
conn.commit()
conn.close()
