"""
Compile and Upload Tender Type Files to Supabase

This script processes the downloaded tender type Excel files from data/tender_downloads/
and uploads them to the tender_type_metrics table in Supabase.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
import pandas as pd
import glob

# Add parent directory to path to import utils
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from dashboard.utils.supabase_db import get_supabase_connection

# Directory containing downloaded tender files
TENDER_DIR = BASE_DIR / "data" / "tender_downloads"

# Store/PC mapping
PC_TO_STORE = {
    "301290": "Paxton",
    "343939": "MountJoy",
    "357993": "Enola",
    "358529": "Columbia",
    "359042": "Lititz",
    "363271": "Marietta",
    "364322": "Etown",
}


def extract_date_from_filename(filename):
    """Extract date from filename like '2025-10-20 to 2025-10-20'"""
    match = re.search(r'(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})', filename)
    if match:
        return match.group(1)  # Return the first date
    return None


def process_tender_file(filepath):
    """
    Process a single tender type Excel file.
    Returns a DataFrame with columns: store, pc_number, date, tender_type, detail_amount
    """
    print(f"\n📄 Processing: {filepath.name}")
    
    # Extract date from filename
    file_date = extract_date_from_filename(filepath.name)
    if not file_date:
        print(f"   ❌ Could not extract date from filename")
        return None
    
    print(f"   📅 Date: {file_date}")
    
    try:
        # Read Excel file with header=1 (skip first row)
        df = pd.read_excel(filepath, header=1)
        print(f"   📊 Read {len(df)} rows, {len(df.columns)} columns")
        
        # The tender type is in 'GL Description' column
        tender_col = 'GL Description'
        
        if tender_col not in df.columns:
            print(f"   ❌ Column '{tender_col}' not found. Available columns: {list(df.columns)}")
            return None
        
        print(f"   🔍 Tender type column: '{tender_col}'")
        
        # Get all store columns (exclude 'Sales Mix Tran Type', 'GL Description', 'Total')
        exclude_cols = ['Sales Mix Tran Type', 'GL Description', 'Total']
        store_columns = [col for col in df.columns if col not in exclude_cols]
        print(f"   🏪 Found {len(store_columns)} store columns")
        
        # Reshape data: convert from wide to long format
        rows = []
        
        for idx, row in df.iterrows():
            tender_type = row[tender_col]
            
            # Skip if tender type is NaN, empty, or a total row
            if pd.isna(tender_type) or str(tender_type).strip() == '':
                continue
            
            tender_type = str(tender_type).strip()
            
            # Skip total rows
            if tender_type.lower() in ['total', 'grand total']:
                continue
            
            for store_col in store_columns:
                amount = row[store_col]
                
                # Skip if amount is NaN or 0
                if pd.isna(amount):
                    continue
                
                # Convert amount to float
                try:
                    if isinstance(amount, str):
                        amount = float(re.sub(r'[^\d.\-]', '', amount))
                    else:
                        amount = float(amount)
                except (ValueError, TypeError):
                    continue
                
                # Skip zero amounts
                if amount == 0:
                    continue
                
                # Extract PC number from store column name (format: "301290 - 2820 Paxton St")
                pc_match = re.search(r'(\d{6})', store_col)
                if not pc_match:
                    print(f"   ⚠️  Could not extract PC from column: '{store_col}'")
                    continue
                
                pc_number = pc_match.group(1)
                store_name = PC_TO_STORE.get(pc_number)
                
                if not store_name:
                    print(f"   ⚠️  Unknown PC number: {pc_number}")
                    continue
                
                # Clean tender type name
                tender_type_clean = tender_type.replace('Credit Card - ', '').replace('Delivery: ', '').strip()
                
                rows.append({
                    'store': store_name,
                    'pc_number': pc_number,
                    'date': file_date,
                    'tender_type': tender_type_clean,
                    'detail_amount': amount
                })
        
        if rows:
            result_df = pd.DataFrame(rows)
            print(f"   ✅ Extracted {len(result_df)} records")
            return result_df
        else:
            print(f"   ⚠️  No data extracted")
            return None
            
    except Exception as e:
        print(f"   ❌ Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return None


def upload_to_supabase(df):
    """Upload DataFrame to Supabase tender_type_metrics table"""
    if df is None or len(df) == 0:
        return 0
    
    try:
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        # First, check if records already exist and delete them to avoid duplicates
        print("   🔍 Checking for existing records...")
        
        dates = df['date'].unique().tolist()
        date_list = "','".join(dates)
        
        delete_query = f"""
            DELETE FROM tender_type_metrics 
            WHERE date IN ('{date_list}')
        """
        cursor.execute(delete_query)
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"   🗑️  Deleted {deleted} existing records for these dates")
        
        # Prepare insert query
        insert_query = """
            INSERT INTO tender_type_metrics (store, pc_number, date, tender_type, detail_amount)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        # Convert DataFrame to list of tuples
        data = df[['store', 'pc_number', 'date', 'tender_type', 'detail_amount']].values.tolist()
        
        # Execute batch insert
        cursor.executemany(insert_query, data)
        rows_inserted = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return rows_inserted
        
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    """Main function to process all tender files and upload to Supabase"""
    
    print("=" * 80)
    print("Tender Type Files - Compile & Upload to Supabase")
    print("=" * 80)
    print()
    
    # Get all tender files
    tender_files = sorted(TENDER_DIR.glob("*.xlsx"))
    
    if not tender_files:
        print("❌ No tender files found in data/tender_downloads/")
        return
    
    print(f"📁 Found {len(tender_files)} tender files")
    print()
    
    all_data = []
    processed_count = 0
    failed_count = 0
    
    for filepath in tender_files:
        df = process_tender_file(filepath)
        
        if df is not None and len(df) > 0:
            all_data.append(df)
            processed_count += 1
        else:
            failed_count += 1
    
    if not all_data:
        print("\n❌ No data to upload")
        return
    
    # Combine all DataFrames
    combined_df = pd.concat(all_data, ignore_index=True)
    
    print("\n" + "=" * 80)
    print("COMPILATION SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully processed: {processed_count} files")
    print(f"❌ Failed: {failed_count} files")
    print(f"📊 Total records: {len(combined_df)}")
    print(f"📅 Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
    print(f"🏪 Stores: {combined_df['store'].nunique()} - {sorted(combined_df['store'].unique())}")
    print(f"💳 Tender types: {combined_df['tender_type'].nunique()} - {sorted(combined_df['tender_type'].unique())}")
    
    # Upload to Supabase
    print("\n" + "=" * 80)
    print("UPLOADING TO SUPABASE")
    print("=" * 80)
    print()
    
    rows_affected = upload_to_supabase(combined_df)
    
    if rows_affected > 0:
        print(f"\n✅ Successfully uploaded/updated {rows_affected} records to tender_type_metrics table")
    else:
        print(f"\n❌ Upload failed or no new records to insert")
    
    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
