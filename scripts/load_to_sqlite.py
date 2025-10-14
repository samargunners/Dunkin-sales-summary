from pathlib import Path
from datetime import datetime
import pandas as pd
import sqlite3
import os

BASE_DIR = Path(__file__).resolve().parents[1]
import sys
sys.path.append(str(BASE_DIR))
from dashboard.utils import supabase_db
DB_PATH = BASE_DIR / "db" / "sales.db"
COMPILED_DIR = BASE_DIR / "data" / "compiled"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # ✅ Ensure db/ exists
DELETE_AFTER_LOAD = False  # Set to True to delete file after successful load

# Expected column schema for validation (subset check)
expected_columns = {
    "sales_summary": [
        "Store", "PC_Number", "Date", "Gross_Sales", "Net_Sales",
        "DD_Adjusted_No_Markup", "PA_Sales_Tax", "DD_Discount", "Guest_Count",
        "Avg_Check", "Gift_Card_Sales", "Void_Amount", "Refund", "Void_Qty", 
        "Paid_IN", "Paid_OUT", "Cash_IN"
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

def get_all_excel_files():
    excel_files = sorted(COMPILED_DIR.glob("compiled_outputs_*.xlsx"), reverse=True)
    return excel_files

### def load_to_sqlite():
    excel_path = get_latest_excel_file()
    if not excel_path:
        print("No compiled Excel file found.")
        return

    print(f"Loading from: {excel_path.name}")
    conn = sqlite3.connect(DB_PATH)

    sheet_to_table = expected_columns.keys()

    try:
        for sheet_name in sheet_to_table:
            table_name = sheet_name
            df = pd.read_excel(excel_path, sheet_name=sheet_name)

            # Optional: Convert 'Date' column to datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date

            # Schema validation
            expected = set(expected_columns[table_name])
            actual = set(df.columns)
            if not expected.issubset(actual):
                missing = expected - actual
                raise ValueError(f"Missing columns in '{sheet_name}': {missing}")

            print(f"Inserting '{sheet_name}' into table '{table_name}'...")
            df.to_sql(table_name, conn, if_exists="append", index=False)

        conn.commit()
        print(" All sheets successfully loaded into SQLite.")
    except Exception as e:
        print(f"Error during loading: {e}")
    finally:
        conn.close()

    if DELETE_AFTER_LOAD:
        os.remove(excel_path)
        print(f"Deleted: {excel_path.name}")
###
def load_to_supabase():
    excel_files = get_all_excel_files()
    if not excel_files:
        print("No compiled Excel files found.")
        return

    print(f"Found {len(excel_files)} compiled files to upload to Supabase")
    try:
        conn = supabase_db.get_supabase_connection()
    except Exception as e:
        print(f"Supabase connection error: {e}")
        return

    sheet_to_table = expected_columns.keys()
    
    try:
        for file_idx, excel_path in enumerate(excel_files, 1):
            print(f"\n📁 [{file_idx}/{len(excel_files)}] Loading: {excel_path.name}")

            for sheet_name in sheet_to_table:
                table_name = sheet_name
                
                try:
                    df = pd.read_excel(excel_path, sheet_name=sheet_name)
                except Exception as e:
                    print(f"   ⚠️  Sheet '{sheet_name}' not found in {excel_path.name}, skipping...")
                    continue

                # Optional: Convert 'Date' column to datetime
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date

                # Schema validation
                expected = set(expected_columns[table_name])
                actual = set(df.columns)
                if not expected.issubset(actual):
                    missing = expected - actual
                    print(f"   ⚠️  Missing columns in '{sheet_name}': {missing}")
                    continue

                print(f"   📊 Upserting '{sheet_name}' -> {len(df)} rows")
                
                # Build upsert query to handle duplicates
                cols = ','.join(df.columns)
                vals_placeholder = ','.join(['%s'] * len(df.columns))
                
                # Use ON CONFLICT DO UPDATE to handle duplicates
                update_cols = [col for col in df.columns if col.lower() != 'id']
                update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_cols])
                
                upsert_query = f"""
                    INSERT INTO {table_name} ({cols}) 
                    VALUES ({vals_placeholder})
                    ON CONFLICT (id) DO UPDATE SET {update_clause}
                """
                
                data = df.values.tolist()
                with conn.cursor() as cur:
                    cur.executemany(upsert_query, data)
            
            print(f"   ✅ Completed file: {excel_path.name}")
            
        conn.commit()
        print(f"\n🎉 All {len(excel_files)} files successfully loaded into Supabase!")
        
    except Exception as e:
        print(f"Error during Supabase loading: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    ### load_to_sqlite()
    load_to_supabase()