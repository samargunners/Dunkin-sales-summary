import sqlite3
import pandas as pd
from pathlib import Path
import os

# --- CONFIGURATION ---
DB_PATH = Path("db/sales.db")
COMPILED_DIR = Path("data/compiled")

def get_latest_excel_file():
    excel_files = sorted(COMPILED_DIR.glob("compiled_outputs_*.xlsx"), reverse=True)
    return excel_files[0] if excel_files else None

def load_to_sqlite():
    excel_path = get_latest_excel_file()
    if not excel_path:
        print("⚠️ No compiled Excel file found.")
        return

    print(f"📄 Loading from: {excel_path.name}")
    conn = sqlite3.connect(DB_PATH)

    # Mapping sheet names to target table names
    sheet_to_table = {
        "sales_summary": "sales_summary",
        "sales_by_order_type": "sales_by_order_type",
        "sales_by_daypart": "sales_by_daypart",
        "sales_by_subcategory": "sales_by_subcategory",
        "labor_metrics": "labor_metrics",
        "tender_type_metrics": "tender_type_metrics"
    }

    for sheet_name, table_name in sheet_to_table.items():
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            print(f"➡️ Inserting '{sheet_name}' into table '{table_name}'...")
            df.to_sql(table_name, conn, if_exists="append", index=False)
        except Exception as e:
            print(f"❌ Error loading sheet '{sheet_name}': {e}")

    conn.commit()
    conn.close()
    
    #os.remove(excel_path)
    print(f"✅ Loaded all sheets into SQLite and deleted {excel_path.name}")

if __name__ == "__main__":
    load_to_sqlite()
