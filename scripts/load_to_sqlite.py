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
    excel_file = get_latest_excel_file()
    if not excel_file:
        print("No compiled Excel files found.")
        return

    print(f"Loading latest file to SQLite: {excel_file.name}")
    conn = sqlite3.connect(DB_PATH)

    try:
        print(f"Loading from: {excel_file.name}")
        
        # Detect file type
        file_type = detect_file_type(excel_file.name)
        if not file_type:
            print(f"   ⚠️  Unknown file type, cannot load")
            return
        
        config = file_type_mapping[file_type]
        table_name = config["table"]
        
        # Read the single sheet file
        df = pd.read_excel(excel_file)

        # Convert date column to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date

        print(f"Inserting {len(df)} rows into table '{table_name}'...")
        df.to_sql(table_name, conn, if_exists="append", index=False)

        conn.commit()
        print("✅ File successfully loaded into SQLite.")
        
    except Exception as e:
        print(f"Error during loading: {e}")
    finally:
        conn.close()

    if DELETE_AFTER_LOAD:
        os.remove(excel_file)
        print(f"Deleted: {excel_file.name}")
def load_to_supabase():
    excel_file = get_latest_excel_file()
    if not excel_file:
        print("No compiled Excel files found.")
        return

    print(f"Found latest compiled file to upload to Supabase: {excel_file.name}")
    try:
        conn = supabase_db.get_supabase_connection()
    except Exception as e:
        print(f"Supabase connection error: {e}")
        return

    successful_uploads = 0
    failed_uploads = 0
    
    try:
        print(f"\n📁 Loading: {excel_file.name}")
        
        # Detect file type
        file_type = detect_file_type(excel_file.name)
        if not file_type:
            print(f"   ⚠️  Unknown file type, cannot upload")
            failed_uploads += 1
            return
            
        config = file_type_mapping[file_type]
        table_name = config["table"]
        
        print(f"   📊 Detected type: {file_type} -> {table_name}")
        
        try:
            # Read the Excel file (single sheet)
            df = pd.read_excel(excel_file)
            
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
                return
                
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
                
                with conn.cursor() as cur:
                    # Use INSERT ... ON CONFLICT DO NOTHING to handle duplicates properly
                    # This respects the unique constraints we've set up for each table
                    insert_query = f"""
                        INSERT INTO {table_name} ({cols}) 
                        VALUES ({vals_placeholder})
                        ON CONFLICT DO NOTHING
                    """
                    
                    data = df_upload.values.tolist()
                    try:
                        cur.executemany(insert_query, data)
                        rows_inserted = cur.rowcount
                        
                        conn.commit()
                        print(f"   ✅ Processed {len(data)} rows, inserted {rows_inserted} new rows (duplicates automatically skipped)")
                        successful_uploads += 1
                        
                    except Exception as sql_error:
                        print(f"   🔍 SQL Error details:")
                        print(f"      Query: {insert_query}")
                        print(f"      Columns: {list(df_upload.columns)}")
                        print(f"      Sample data: {data[0] if data else 'No data'}")
                        conn.rollback()
                        raise sql_error
                        
        except Exception as e:
            print(f"   ❌ Error processing file: {e}")
            failed_uploads += 1
            conn.rollback()
        
        print(f"\n📊 Upload Summary:")
        print(f"   ✅ Successful: {successful_uploads}")
        print(f"   ❌ Failed: {failed_uploads}")
        print(f"   📁 File processed: {excel_file.name}")
        
    except Exception as e:
        print(f"Error during Supabase loading: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    ### load_to_sqlite()
    load_to_supabase()