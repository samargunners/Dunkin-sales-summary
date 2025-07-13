import sqlite3
import pandas as pd
from pathlib import Path
import os
from datetime import datetime

# --- CONFIGURATION ---
DB_PATH = Path("db/sales.db")
COMPILED_DIR = Path("data/compiled")
DELETE_AFTER_LOAD = False  # Set to True to delete file after successful load

# Expected column schema for validation (subset check)
expected_columns = {
    "sales_summary": [
        "Store", "PC_Number", "Date", "Gross_Sales", "Net_Sales",
        "DD_Adjusted_No_Markup", "PA_Sales_Tax", "DD_Discount", "Guest_Count",
        "Avg_Check", "Gift_Card_Sales", "Void_Amount", "Refund", "Void_Qty", "Cash_IN"
    ],
    "sales_by_order_type": [
        "Store", "PC_Number", "Date", "Order_Type", "Net_Sales",
        "Percent_Sales", "Guests", "Percent_Guest", "Avg_Check"
    ],
    "sales_by_daypart": [
        "Store", "PC_Number", "Date", "Daypart", "Net_Sales",
        "Percent_Sales", "Check_Count", "Avg_Check"
    ],
    "sales_by_subcategory": [
        "Store", "PC_Number", "Date", "Subcategory", "Qty_Sold",
        "Net_Sales", "Percent_Sales"
    ],
    "labor_metrics": [
        "Store", "PC_Number", "Date", "Labor_Position", "Reg_Hours",
        "OT_Hours", "Total_Hours", "Reg_Pay", "OT_Pay", "Total_Pay", "Percent_Labor"
    ],
    "tender_type_metrics": [
        "Store", "PC_Number", "Date", "Tender_Type", "Detail_Amount"
    ]
}

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

    sheet_to_table = expected_columns.keys()

    try:
        for sheet_name in sheet_to_table:
            table_name = sheet_name
            df = pd.read_excel(excel_path, sheet_name=sheet_name)

            # Optional: Convert 'Date' column to datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            # Schema validation
            expected = set(expected_columns[table_name])
            actual = set(df.columns)
            if not expected.issubset(actual):
                missing = expected - actual
                raise ValueError(f"Missing columns in '{sheet_name}': {missing}")

            print(f"➡️ Inserting '{sheet_name}' into table '{table_name}'...")
            df.to_sql(table_name, conn, if_exists="append", index=False)

        conn.commit()
        print("✅ All sheets successfully loaded into SQLite.")
    except Exception as e:
        print(f"❌ Error during loading: {e}")
    finally:
        conn.close()

    if DELETE_AFTER_LOAD:
        os.remove(excel_path)
        print(f"🗑️ Deleted: {excel_path.name}")

if __name__ == "__main__":
    load_to_sqlite()