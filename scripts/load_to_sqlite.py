# Update the load_to_sqlite.py script to delete compiled files after loading
script_path = "/mnt/data/dunkin_sales_dashboard/scripts/load_to_sqlite.py"

script_content = '''import sqlite3
import pandas as pd
from pathlib import Path
import os

DB_PATH = Path("db/sales.db")
COMPILED_DIR = Path("data/compiled")

def load_to_sqlite():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    def load_table(csv_name, table_name):
        path = COMPILED_DIR / csv_name
        if path.exists():
            print(f"Inserting data into {table_name}...")
            df = pd.read_csv(path)
            df.to_sql(table_name, conn, if_exists="append", index=False)
            os.remove(path)  # delete after loading
            print(f"✔️ {csv_name} loaded and deleted.")
        else:
            print(f"File not found: {csv_name}")

    load_table("sales_summary.csv", "sales_summary")
    load_table("sales_by_order_type.csv", "sales_by_order_type")
    load_table("sales_by_daypart.csv", "sales_by_daypart")
    load_table("sales_by_subcategory.csv", "sales_by_subcategory")
    load_table("labor_metrics.csv", "labor_metrics")

    conn.commit()
    conn.close()
    print("✅ All data loaded into SQLite and CSVs deleted.")

if __name__ == "__main__":
    load_to_sqlite()
'''

with open(script_path, "w") as f:
    f.write(script_content)

script_path
