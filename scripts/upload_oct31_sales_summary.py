"""
Upload October 31, 2025 Sales Summary Data to Supabase

This script manually uploads the sales summary data for October 31st that was missing from the database.
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection

# Store mapping (PC number to store name)
PC_TO_STORE = {
    "301290": "Paxton",
    "343939": "MountJoy", 
    "357993": "Enola",
    "358529": "Columbia",
    "359042": "Lititz",
    "363271": "Marietta",
    "364322": "Etown",
}

def upload_oct31_sales_summary():
    """Upload sales summary data for October 31, 2025."""
    
    # Define the data based on the spreadsheet provided
    # Format: [pc_number, net_sales, gross_sales, dd_adjusted_no_markup, pa_sales_tax, 
    #          dd_discount, guest_count, avg_check, gift_card_sales, void_amount, 
    #          refund, void_qty, cash_in, paid_in, paid_out]
    
    data_rows = [
        # 301290 - Paxton
        ["301290", 3973.76, 4265.52, 3945.18, 177.87, 291.76, 454, 8.75, 0.00, 0.00, 4.69, 0, 1025.02, 0.00, 0.00],
        # 343939 - MountJoy
        ["343939", 4869.73, 5346.15, 4801.42, 242.44, 426.42, 546, 8.92, 50.00, 8.67, 0.00, 3, 761.13, 0.00, 0.00],
        # 357993 - Enola
        ["357993", 7003.77, 7686.91, 6961.51, 339.88, 608.14, 813, 8.61, 75.00, 17.94, 10.78, 3, 1093.24, 0.00, 0.00],
        # 358529 - Columbia
        ["358529", 5844.37, 6429.23, 5793.90, 306.15, 472.86, 651, 8.98, 112.00, 34.32, 23.08, 7, 896.02, 0.00, 0.00],
        # 359042 - Lititz
        ["359042", 5471.32, 6030.28, 5402.68, 246.74, 528.96, 579, 9.45, 30.00, 3.29, 22.04, 1, 609.36, 0.00, 14.76],
        # 363271 - Marietta
        ["363271", 4729.11, 5196.49, 4691.92, 232.51, 367.38, 543, 8.71, 100.00, 4.38, 31.97, 1, 725.39, 0.00, 0.00],
        # 364322 - Etown
        ["364322", 6743.34, 7410.02, 6738.26, 313.72, 646.68, 694, 9.72, 20.00, 47.02, 51.70, 8, 749.66, 0.00, 0.00],
    ]
    
    # Create DataFrame with proper column names matching sales_summary table
    df = pd.DataFrame(data_rows, columns=[
        "pc_number", "net_sales", "gross_sales", "dd_adjusted_no_markup", "pa_sales_tax",
        "dd_discount", "guest_count", "avg_check", "gift_card_sales", "void_amount",
        "refund", "void_qty", "cash_in", "paid_in", "paid_out"
    ])
    
    # Add store names and date
    df['store'] = df['pc_number'].map(PC_TO_STORE)
    df['date'] = '2025-10-31'
    
    # Reorder columns to match database schema
    df = df[[
        'store', 'pc_number', 'date', 'gross_sales', 'net_sales', 
        'dd_adjusted_no_markup', 'pa_sales_tax', 'dd_discount', 
        'guest_count', 'avg_check', 'gift_card_sales', 'void_amount',
        'refund', 'void_qty', 'cash_in', 'paid_in', 'paid_out'
    ]]
    
    print("="*60)
    print("October 31, 2025 Sales Summary Upload")
    print("="*60)
    print(f"\nRecords to upload: {len(df)}")
    print("\nData preview:")
    print(df.to_string(index=False))
    print()
    
    # Confirm before uploading
    response = input("Proceed with upload to Supabase? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Upload cancelled.")
        return
    
    try:
        print("\nConnecting to Supabase...")
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        # Check if data already exists for this date
        cursor.execute("""
            SELECT COUNT(*) FROM sales_summary WHERE date = '2025-10-31'
        """)
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"\n⚠️  Warning: {existing_count} records already exist for 2025-10-31")
            response = input("Delete existing records and re-upload? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                cursor.execute("DELETE FROM sales_summary WHERE date = '2025-10-31'")
                print(f"✓ Deleted {existing_count} existing records")
            else:
                print("Upload cancelled.")
                cursor.close()
                conn.close()
                return
        
        # Insert data
        print("\nInserting records...")
        insert_query = """
            INSERT INTO sales_summary (
                store, pc_number, date, gross_sales, net_sales,
                dd_adjusted_no_markup, pa_sales_tax, dd_discount,
                guest_count, avg_check, gift_card_sales, void_amount,
                refund, void_qty, cash_in, paid_in, paid_out
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        records_inserted = 0
        for _, row in df.iterrows():
            cursor.execute(insert_query, (
                row['store'], row['pc_number'], row['date'], row['gross_sales'], 
                row['net_sales'], row['dd_adjusted_no_markup'], row['pa_sales_tax'],
                row['dd_discount'], row['guest_count'], row['avg_check'], 
                row['gift_card_sales'], row['void_amount'], row['refund'], 
                row['void_qty'], row['cash_in'], row['paid_in'], row['paid_out']
            ))
            records_inserted += 1
            print(f"  ✓ Inserted: {row['store']} (PC: {row['pc_number']})")
        
        conn.commit()
        
        print(f"\n✅ Successfully uploaded {records_inserted} records to sales_summary table")
        
        # Verify the upload
        cursor.execute("""
            SELECT store, date, net_sales, gross_sales, guest_count
            FROM sales_summary
            WHERE date = '2025-10-31'
            ORDER BY store
        """)
        
        print("\n" + "="*60)
        print("Verification - Data in Database:")
        print("="*60)
        for row in cursor.fetchall():
            print(f"  {row[0]}: Date={row[1]}, Net Sales=${row[2]:,.2f}, Gross Sales=${row[3]:,.2f}, Guests={row[4]}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("Upload Complete!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error during upload: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()


if __name__ == "__main__":
    upload_oct31_sales_summary()
