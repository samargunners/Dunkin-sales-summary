"""
Upload parsed transposed data to Supabase

This script takes the parsed data and uploads it to the appropriate Supabase tables.
"""

import os
import sys
from parse_transposed_format import parse_transposed_file

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection


def upload_to_supabase(data):
    """Upload parsed data to Supabase tables."""
    
    print("="*80)
    print("UPLOADING TO SUPABASE")
    print("="*80)
    
    try:
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        # Upload sales_summary
        if data['sales_summary']:
            print(f"\nUploading {len(data['sales_summary'])} records to sales_summary...")
            
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
            
            success_count = 0
            error_count = 0
            for record in data['sales_summary']:
                try:
                    cursor.execute(insert_query, (
                        record['store'], record['pc_number'], record['date'],
                        record['gross_sales'], record['net_sales'],
                        record['dd_adjusted_no_markup'], record['pa_sales_tax'],
                        record['dd_discount'], record['guest_count'],
                        record['avg_check'], record['gift_card_sales'],
                        record['void_amount'], record['refund'],
                        record['void_qty'], record['cash_in'],
                        record['paid_in'], record['paid_out']
                    ))
                    conn.commit()  # Commit each record individually
                    success_count += 1
                    if success_count % 50 == 0:
                        print(f"  ✓ {success_count} records uploaded...")
                except Exception as e:
                    conn.rollback()  # Rollback failed insert
                    error_count += 1
                    if error_count <= 5:  # Only show first 5 errors
                        print(f"  ❌ Error uploading record: {record['store']} {record['date']} - {e}")
            
            if error_count > 5:
                print(f"  ❌ ... and {error_count - 5} more errors")
            print(f"✅ Uploaded {success_count}/{len(data['sales_summary'])} sales_summary records")
        
        # Upload tender_type_metrics
        if data['tender_type_metrics']:
            print(f"\nUploading {len(data['tender_type_metrics'])} records to tender_type_metrics...")
            
            insert_query = """
                INSERT INTO tender_type_metrics (
                    store, pc_number, date, tender_type, detail_amount
                ) VALUES (
                    %s, %s, %s, %s, %s
                )
            """
            
            success_count = 0
            error_count = 0
            for record in data['tender_type_metrics']:
                try:
                    cursor.execute(insert_query, (
                        record['store'], record['pc_number'], record['date'],
                        record['tender_type'], record['detail_amount']
                    ))
                    conn.commit()  # Commit each record individually
                    success_count += 1
                    if success_count % 100 == 0:
                        print(f"  ✓ {success_count} records uploaded...")
                except Exception as e:
                    conn.rollback()  # Rollback failed insert
                    error_count += 1
                    if error_count <= 5:  # Only show first 5 errors
                        print(f"  ❌ Error uploading record: {record['store']} {record['date']} {record['tender_type']} - {e}")
            
            if error_count > 5:
                print(f"  ❌ ... and {error_count - 5} more errors")
            print(f"✅ Uploaded {success_count}/{len(data['tender_type_metrics'])} tender_type_metrics records")
        
        # Upload labor_metrics
        if data['labor_metrics']:
            print(f"\nUploading {len(data['labor_metrics'])} records to labor_metrics...")
            
            insert_query = """
                INSERT INTO labor_metrics (
                    store, pc_number, date, labor_position, reg_hours,
                    ot_hours, total_hours, reg_pay, ot_pay, total_pay, percent_labor
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            success_count = 0
            error_count = 0
            for record in data['labor_metrics']:
                try:
                    cursor.execute(insert_query, (
                        record['store'], record['pc_number'], record['date'],
                        record['labor_position'], record['reg_hours'],
                        record['ot_hours'], record['total_hours'],
                        record['reg_pay'], record['ot_pay'],
                        record['total_pay'], record['percent_labor']
                    ))
                    conn.commit()  # Commit each record individually
                    success_count += 1
                    if success_count % 100 == 0:
                        print(f"  ✓ {success_count} records uploaded...")
                except Exception as e:
                    conn.rollback()  # Rollback failed insert
                    error_count += 1
                    if error_count <= 5:  # Only show first 5 errors
                        print(f"  ❌ Error uploading record: {record['store']} {record['date']} {record['labor_position']} - {e}")
            
            if error_count > 5:
                print(f"  ❌ ... and {error_count - 5} more errors")
            print(f"✅ Uploaded {success_count}/{len(data['labor_metrics'])} labor_metrics records")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("UPLOAD COMPLETE!")
        print("="*80)
        print("All data has been uploaded to Supabase successfully.")
        
    except Exception as e:
        print(f"\n❌ Error during upload: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        print("Usage: python upload_transposed_data.py <path_to_file>")
        print("\nExample: python upload_transposed_data.py /Users/samarpatel/Downloads/october_data.xlsx")
        sys.exit(1)
    
    # Parse the file
    print("Step 1: Parsing file...")
    data = parse_transposed_file(filepath)
    
    # Confirm upload
    print("\n" + "="*80)
    print("READY TO UPLOAD")
    print("="*80)
    print(f"Sales Summary: {len(data['sales_summary'])} records")
    print(f"Tender Type Metrics: {len(data['tender_type_metrics'])} records")
    print(f"Labor Metrics: {len(data['labor_metrics'])} records")
    print()
    
    response = input("Proceed with upload to Supabase? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("\n❌ Upload cancelled.")
        sys.exit(0)
    
    # Upload
    print("\nStep 2: Uploading to Supabase...")
    upload_to_supabase(data)
