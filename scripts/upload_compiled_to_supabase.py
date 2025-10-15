#!/usr/bin/env python3
"""
Upload all compiled Excel files from data/compiled/ to Supabase
Updated to work with the new file structure and column schemas.
"""

from pathlib import Path
from datetime import datetime
import pandas as pd
import sys
import os
import glob

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
from dashboard.utils import supabase_db

COMPILED_DIR = BASE_DIR / "data" / "compiled"

# File type mapping based on filename patterns
file_type_mapping = {
    "Labor Hours": {
        "table": "labor_metrics", 
        "columns": ["store", "pc_number", "date", "labour_position", "Reg Hours", 
                   "OT Hours", "Total Hours", "Reg Pay", "OT Pay", "Total Pay", "% Labor"]
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

def get_all_compiled_files():
    """Get all compiled Excel files from data/compiled/"""
    excel_files = list(COMPILED_DIR.glob("*_copy.xlsx"))
    return sorted(excel_files, reverse=True)  # Newest first

def upload_file_to_supabase(excel_path):
    """Upload a single Excel file to Supabase"""
    print(f"\n📁 Processing: {excel_path.name}")
    
    # Detect file type
    file_type = detect_file_type(excel_path.name)
    if not file_type:
        print(f"   ⚠️  Unknown file type, skipping...")
        return False
    
    config = file_type_mapping[file_type]
    table_name = config["table"]
    
    print(f"   📊 Detected type: {file_type} -> {table_name}")
    
    try:
        conn = supabase_db.get_supabase_connection()
    except Exception as e:
        print(f"   ❌ Supabase connection error: {e}")
        return False

    try:
        # Read the Excel file (it should have only one sheet)
        df = pd.read_excel(excel_path)
        
        print(f"   📈 Read {len(df)} rows, {len(df.columns)} columns")
        print(f"   🔍 Columns: {list(df.columns)}")
        
        # Convert date column to proper format
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
        
        # Validate that we have the expected columns
        expected_cols = set(config["columns"])
        actual_cols = set(df.columns)
        
        if not expected_cols.issubset(actual_cols):
            missing = expected_cols - actual_cols
            extra = actual_cols - expected_cols
            print(f"   ⚠️  Column mismatch!")
            if missing:
                print(f"       Missing: {missing}")
            if extra:
                print(f"       Extra: {extra}")
            print(f"   🔄 Proceeding with available columns...")
        
        # Use only the columns that exist in both
        valid_cols = list(expected_cols & actual_cols)
        df_upload = df[valid_cols].copy()
        
        print(f"   📤 Uploading {len(df_upload)} rows to {table_name}")
        
        # Build insert query with conflict handling
        cols = ','.join(df_upload.columns)
        vals_placeholder = ','.join(['%s'] * len(df_upload.columns))
        
        # Use INSERT with ON CONFLICT DO NOTHING to avoid duplicates
        insert_query = f"""
            INSERT INTO {table_name} ({cols}) 
            VALUES ({vals_placeholder})
            ON CONFLICT DO NOTHING
        """
        
        data = df_upload.values.tolist()
        with conn.cursor() as cur:
            cur.executemany(insert_query, data)
            rows_inserted = cur.rowcount
            
        conn.commit()
        print(f"   ✅ Successfully inserted {rows_inserted} rows (duplicates skipped)")
        return True
        
    except Exception as e:
        print(f"   ❌ Error during upload: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    print("🚀 Starting upload of compiled files to Supabase...")
    
    # Get all compiled files
    files = get_all_compiled_files()
    
    if not files:
        print("❌ No compiled Excel files found in data/compiled/")
        return
    
    print(f"📋 Found {len(files)} files to process:")
    for i, file in enumerate(files, 1):
        file_type = detect_file_type(file.name)
        type_str = f" ({file_type})" if file_type else " (unknown type)"
        print(f"   {i}. {file.name}{type_str}")
    
    # Ask for confirmation
    response = input(f"\n🤔 Upload all {len(files)} files to Supabase? (y/n): ").lower().strip()
    if response not in ['y', 'yes']:
        print("❌ Upload cancelled.")
        return
    
    # Process each file
    successful_uploads = 0
    failed_uploads = 0
    
    for i, excel_file in enumerate(files, 1):
        print(f"\n📈 Progress: {i}/{len(files)}")
        
        if upload_file_to_supabase(excel_file):
            successful_uploads += 1
        else:
            failed_uploads += 1
    
    # Summary
    print(f"\n📊 Upload Summary:")
    print(f"   ✅ Successful: {successful_uploads}")
    print(f"   ❌ Failed: {failed_uploads}")
    print(f"   📁 Total processed: {len(files)}")
    
    if successful_uploads == len(files):
        print("🎉 All files uploaded successfully!")
    elif successful_uploads > 0:
        print("⚠️  Some files uploaded successfully, check errors above")
    else:
        print("💥 No files were uploaded successfully")

if __name__ == "__main__":
    main()