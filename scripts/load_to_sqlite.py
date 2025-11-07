from pathlib import Path
from datetime import datetime
import pandas as pd
import sqlite3
import os

def safe_print(msg, end='\n'):
    """Print with Unicode error handling for Windows console"""
    try:
        print(msg, end=end)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'), end=end)

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
    elif "Sales_summary" in filename_str or "Sales Mix Detail" in filename_str:  # From Sales Mix Detail
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
        safe_print("No compiled Excel files found.")
        return

    safe_print(f"Loading latest file to SQLite: {excel_file.name}")
    conn = sqlite3.connect(DB_PATH)

    try:
        safe_print(f"Loading from: {excel_file.name}")
        
        # Detect file type
        file_type = detect_file_type(excel_file.name)
        if not file_type:
            safe_print(f"   ⚠️  Unknown file type, cannot load")
            return
        
        config = file_type_mapping[file_type]
        table_name = config["table"]
        
        # Read the single sheet file
        df = pd.read_excel(excel_file)

        # Convert date column to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date

        safe_print(f"Inserting {len(df)} rows into table '{table_name}'...")
        df.to_sql(table_name, conn, if_exists="append", index=False)

        conn.commit()
        safe_print("✅ File successfully loaded into SQLite.")
        
    except Exception as e:
        safe_print(f"Error during loading: {e}")
    finally:
        conn.close()

    if DELETE_AFTER_LOAD:
        os.remove(excel_file)
        safe_print(f"Deleted: {excel_file.name}")
def load_to_supabase():
    excel_files = get_all_excel_files()
    if not excel_files:
        safe_print("No compiled Excel files found.")
        return

    safe_print(f"Found {len(excel_files)} compiled files to upload to Supabase:")
    for i, file in enumerate(excel_files, 1):
        safe_print(f"  {i}. {file.name}")
    
    try:
        conn = supabase_db.get_supabase_connection()
    except Exception as e:
        safe_print(f"Supabase connection error: {e}")
        return

    successful_uploads = 0
    failed_uploads = 0
    
    for excel_file in excel_files:
        try:
            safe_print(f"\n[FILE] Loading: {excel_file.name}")
            
            # Detect file type
            file_type = detect_file_type(excel_file.name)
            if not file_type:
                safe_print(f"   [WARNING] Unknown file type, cannot upload")
                failed_uploads += 1
                continue
                
            config = file_type_mapping[file_type]
            table_name = config["table"]
            
            safe_print(f"   [INFO] Detected type: {file_type} -> {table_name}")
            
            # Read the Excel file (single sheet)
            df = pd.read_excel(excel_file)
            
            safe_print(f"   [DATA] Read {len(df)} rows, {len(df.columns)} columns")
            
            # Convert date column to proper format
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], format='%m/%d/%y', errors='coerce').dt.date
            
            # Validate columns (flexible validation)
            expected_cols = set(config["columns"])
            actual_cols = set(df.columns)
            
            # Use columns that exist in both expected and actual
            valid_cols = list(expected_cols & actual_cols)
            if not valid_cols:
                safe_print(f"   [ERROR] No matching columns found")
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
            
            safe_print(f"   [UPLOAD] Uploading {len(df_upload)} rows to {table_name}")
            
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
                
                # Process in smaller batches to avoid timeouts
                batch_size = 50
                total_inserted = 0
                
                for i in range(0, len(data), batch_size):
                    batch = data[i:i+batch_size]
                    batch_num = i // batch_size + 1
                    total_batches = (len(data) + batch_size - 1) // batch_size
                    
                    safe_print(f"      Batch {batch_num}/{total_batches} ({len(batch)} rows)...", end='')
                    
                    try:
                        cur.executemany(insert_query, batch)
                        batch_inserted = cur.rowcount
                        total_inserted += batch_inserted
                        safe_print(f" SUCCESS {batch_inserted} inserted")
                        
                        conn.commit()
                        
                    except Exception as sql_error:
                        safe_print(f" ERROR")
                        safe_print(f"   [DEBUG] SQL Error details:")
                        safe_print(f"      Query: {insert_query}")
                        safe_print(f"      Columns: {list(df_upload.columns)}")
                        safe_print(f"      Sample data: {batch[0] if batch else 'No data'}")
                        conn.rollback()
                        raise sql_error
                
                safe_print(f"   [SUCCESS] Processed {len(data)} rows, inserted {total_inserted} new rows (duplicates automatically skipped)")
                successful_uploads += 1
                    
        except Exception as e:
            safe_print(f"   [ERROR] Error processing file: {e}")
            failed_uploads += 1
            try:
                conn.rollback()
            except:
                pass
    
    safe_print(f"\n[SUMMARY] Upload Summary:")
    safe_print(f"   [SUCCESS] Successful: {successful_uploads}")
    safe_print(f"   [FAILED] Failed: {failed_uploads}")
    safe_print(f"   [TOTAL] Total files processed: {len(excel_files)}")
        
    try:
        conn.close()
    except:
        pass  # Connection might already be closed

if __name__ == "__main__":
    ### load_to_sqlite()
    load_to_supabase()