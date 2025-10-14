#!/usr/bin/env python3
"""
Upload all compiled Excel files from data/compiled/ to Supabase
This script processes multiple files instead of just the latest one.
"""

from pathlib import Path
from datetime import datetime
import pandas as pd
import sys
import os

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
from dashboard.utils import supabase_db

COMPILED_DIR = BASE_DIR / "data" / "compiled"

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

def get_all_compiled_files():
    """Get all compiled Excel files, sorted by date (newest first)"""
    excel_files = sorted(COMPILED_DIR.glob("compiled_outputs_*.xlsx"), reverse=True)
    return excel_files

def upload_file_to_supabase(excel_path):
    """Upload a single Excel file to Supabase"""
    print(f"\n📁 Processing: {excel_path.name}")
    
    try:
        conn = supabase_db.get_supabase_connection()
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        return False

    sheet_to_table = expected_columns.keys()
    successful_sheets = 0
    total_sheets = len(sheet_to_table)

    try:
        for sheet_name in sheet_to_table:
            table_name = sheet_name
            
            try:
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
            except Exception as e:
                print(f"   ⚠️  Sheet '{sheet_name}' not found in {excel_path.name}, skipping...")
                continue

            # Convert 'Date' column to datetime
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
            
            # Build insert query with conflict handling
            cols = ','.join(df.columns)
            vals_placeholder = ','.join(['%s'] * len(df.columns))
            
            # Try INSERT with ON CONFLICT DO NOTHING to avoid duplicates
            insert_query = f"""
                INSERT INTO {table_name} ({cols}) 
                VALUES ({vals_placeholder})
                ON CONFLICT DO NOTHING
            """
            
            data = df.values.tolist()
            with conn.cursor() as cur:
                cur.executemany(insert_query, data)
                
            successful_sheets += 1
            
        conn.commit()
        print(f"   ✅ Successfully uploaded {successful_sheets}/{total_sheets} sheets")
        return True
        
    except Exception as e:
        print(f"   ❌ Error during upload: {e}")
        return False
    finally:
        conn.close()

def main():
    print("🚀 Starting bulk upload of all compiled files to Supabase...")
    
    # Get all compiled files
    files = get_all_compiled_files()
    
    if not files:
        print("❌ No compiled Excel files found in data/compiled/")
        return
    
    print(f"📋 Found {len(files)} files to process:")
    for i, file in enumerate(files[:5], 1):  # Show first 5
        print(f"   {i}. {file.name}")
    if len(files) > 5:
        print(f"   ... and {len(files) - 5} more files")
    
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