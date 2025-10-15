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

# File type mapping based on filename patterns and expected columns
file_type_mapping = {
    "Labor Hours": {
        "table": "labor_metrics", 
        "columns": ["store", "pc_number", "date", "labor_position", "Reg Hours", 
                   "OT Hours", "Total Hours", "Reg Pay", "OT Pay", "Total Pay", "% Labor"],
        "column_mapping": {
            "Reg Hours": "reg_hours",
            "OT Hours": "ot_hours", 
            "Total Hours": "total_hours",
            "Reg Pay": "reg_pay",
            "OT Pay": "ot_pay",
            "Total Pay": "total_pay",
            "% Labor": "percent_labor"
        }
    },
    "Sales by Daypart": {
        "table": "sales_by_daypart",
        "columns": ["store", "pc_number", "date", "daypart", "net_sales", 
                   "percent_sales", "check_count", "avg_check"]
    },
    "Sales by Subcategory": {
        "table": "sales_by_subcategory", 
        "columns": ["store", "pc_number", "date", "subcategory", "qty_sold", 
                   "net_sales", "percent_sales"]
    },
    "Tender Type": {
        "table": "tender_type_metrics",
        "columns": ["store", "pc_number", "date", "tender_type", "detail_amount"]
    },
    "Sales_summary": {  # Note: This is from Sales Mix Detail files
        "table": "sales_summary",
        "columns": ["store", "pc_number", "date", "gross_sales", "net_sales", 
                   "dd_adjusted_no_markup", "pa_sales_tax", "dd_discount", 
                   "guest_count", "avg_check", "gift_card_sales", "void_amount", 
                   "refund", "void_qty", "paid_in", "paid_out", "cash_in"]
    },
    "Menu Mix Metrics": {
        "table": "sales_by_order_type",
        "columns": ["store", "pc_number", "date", "order_type", "net_sales", 
                   "percent_sales", "guests", "percent_guest", "avg_check"]
    }
}

def detect_file_type(filename):
    """Detect file type based on filename pattern"""
    filename_str = str(filename)
    
    if "Labor Hours" in filename_str:
        return "Labor Hours"
    elif "Sales by Daypart" in filename_str:
        return "Sales by Daypart"
    elif "Sales by Subcategory" in filename_str:
        return "Sales by Subcategory"
    elif "Tender Type" in filename_str:
        return "Tender Type"
    elif "Sales_summary" in filename_str:  # From Sales Mix Detail
        return "Sales_summary"
    elif "Menu Mix Metrics" in filename_str:
        return "Menu Mix Metrics"
    else:
        return None

def get_latest_excel_file():
    excel_files = sorted(COMPILED_DIR.glob("*_copy.xlsx"), reverse=True)
    return excel_files[0] if excel_files else None

def get_all_excel_files():
    excel_files = sorted(COMPILED_DIR.glob("*_copy.xlsx"), reverse=True)
    return excel_files

def load_to_sqlite():
    excel_files = get_all_excel_files()
    if not excel_files:
        print("No compiled Excel files found.")
        return

    print(f"Loading {len(excel_files)} files to SQLite...")
    conn = sqlite3.connect(DB_PATH)

    try:
        for excel_path in excel_files:
            print(f"Loading from: {excel_path.name}")
            
            # Detect file type
            file_type = detect_file_type(excel_path.name)
            if not file_type:
                print(f"   ⚠️  Unknown file type, skipping...")
                continue
            
            config = file_type_mapping[file_type]
            table_name = config["table"]
            
            # Read the single sheet file
            df = pd.read_excel(excel_path)

            # Convert date column to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date

            print(f"Inserting {len(df)} rows into table '{table_name}'...")
            df.to_sql(table_name, conn, if_exists="append", index=False)

        conn.commit()
        print("✅ All files successfully loaded into SQLite.")
        
    except Exception as e:
        print(f"Error during loading: {e}")
    finally:
        conn.close()

    if DELETE_AFTER_LOAD:
        for excel_path in excel_files:
            os.remove(excel_path)
            print(f"Deleted: {excel_path.name}")
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

    successful_uploads = 0
    failed_uploads = 0
    
    try:
        for file_idx, excel_path in enumerate(excel_files, 1):
            print(f"\n📁 [{file_idx}/{len(excel_files)}] Loading: {excel_path.name}")
            
            # Detect file type
            file_type = detect_file_type(excel_path.name)
            if not file_type:
                print(f"   ⚠️  Unknown file type, skipping...")
                failed_uploads += 1
                continue
            
            config = file_type_mapping[file_type]
            table_name = config["table"]
            
            print(f"   📊 Detected type: {file_type} -> {table_name}")
            
            try:
                # Read the Excel file (single sheet)
                df = pd.read_excel(excel_path)
                
                print(f"   📈 Read {len(df)} rows, {len(df.columns)} columns")
                
                # Convert date column to proper format
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'], format='%m/%d/%y', errors='coerce').dt.date
                
                # Validate columns (flexible validation)
                expected_cols = set(config["columns"])
                actual_cols = set(df.columns)
                
                # Use columns that exist in both expected and actual
                valid_cols = list(expected_cols & actual_cols)
                if not valid_cols:
                    print(f"   ❌ No matching columns found")
                    failed_uploads += 1
                    continue
                
                df_upload = df[valid_cols].copy()
                
                # Apply column mapping if specified (for labor file)
                if 'column_mapping' in config:
                    column_mapping = config['column_mapping']
                    df_upload = df_upload.rename(columns=column_mapping)
                
                # Convert pc_number to string to avoid integer overflow issues
                if 'pc_number' in df_upload.columns:
                    df_upload['pc_number'] = df_upload['pc_number'].astype(str)
                
                # Handle NaN values properly based on data type
                for col in df_upload.columns:
                    if df_upload[col].dtype in ['float64', 'int64']:
                        # For numeric columns, fill NaN with 0
                        df_upload[col] = df_upload[col].fillna(0)
                    else:
                        # For text columns, fill NaN with empty string
                        df_upload[col] = df_upload[col].fillna('')
                
                # Remove rows where essential columns (store, pc_number, date) are missing
                essential_cols = ['store', 'pc_number', 'date']
                for col in essential_cols:
                    if col in df_upload.columns:
                        df_upload = df_upload[
                            (df_upload[col].notna()) & 
                            (df_upload[col] != '') & 
                            (df_upload[col] != '0')
                        ]
                
                print(f"   � Uploading {len(df_upload)} rows to {table_name}")
                
                # Build insert query with conflict handling
                cols = ','.join(df_upload.columns)
                vals_placeholder = ','.join(['%s'] * len(df_upload.columns))
                
                # Check if data for this date already exists in the table
                check_query = f"SELECT COUNT(*) FROM {table_name} WHERE date = %s"
                cur.execute(check_query, (df_upload['date'].iloc[0],))
                existing_count = cur.fetchone()[0]
                
                if existing_count > 0:
                    print(f"   ⚠️  Data for this date already exists ({existing_count} rows), skipping to prevent duplicates")
                    continue
                
                # Use simple INSERT since we've checked for existing data
                insert_query = f"""
                    INSERT INTO {table_name} ({cols}) 
                    VALUES ({vals_placeholder})
                """
                
                data = df_upload.values.tolist()
                with conn.cursor() as cur:
                    try:
                        cur.executemany(insert_query, data)
                        rows_inserted = cur.rowcount
                    except Exception as sql_error:
                        print(f"   🔍 SQL Error details:")
                        print(f"      Query: {insert_query}")
                        print(f"      Columns: {list(df_upload.columns)}")
                        print(f"      Sample data: {data[0] if data else 'No data'}")
                        raise sql_error
                
                conn.commit()
                print(f"   ✅ Successfully inserted {rows_inserted} rows (duplicates skipped)")
                successful_uploads += 1
                
            except Exception as e:
                print(f"   ❌ Error processing file: {e}")
                failed_uploads += 1
                conn.rollback()
        
        print(f"\n📊 Upload Summary:")
        print(f"   ✅ Successful: {successful_uploads}")
        print(f"   ❌ Failed: {failed_uploads}")
        print(f"   📁 Total processed: {len(excel_files)}")
        
    except Exception as e:
        print(f"Error during Supabase loading: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    ### load_to_sqlite()
    load_to_supabase()