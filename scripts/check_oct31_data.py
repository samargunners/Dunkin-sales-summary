"""
Check what data exists in Supabase for October 31, 2025
"""

import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection


def check_oct31_data():
    """Check data for October 31, 2025."""
    
    try:
        print("Connecting to Supabase...")
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        # Check sales_summary table
        print("\n" + "="*60)
        print("SALES SUMMARY TABLE - October 31, 2025")
        print("="*60)
        cursor.execute("""
            SELECT store, date, dd_adjusted_no_markup, cash_in, gift_card_sales
            FROM sales_summary
            WHERE date = '2025-10-31'
            ORDER BY store
        """)
        sales_rows = cursor.fetchall()
        
        if sales_rows:
            print(f"Found {len(sales_rows)} records:")
            for row in sales_rows:
                print(f"  Store: {row[0]}, Date: {row[1]}, Net Sales: ${row[2]:,.2f}, Cash: ${row[3]:,.2f}, GC Sales: ${row[4]:,.2f}")
        else:
            print("❌ No records found in sales_summary for 2025-10-31")
        
        # Check tender_type_metrics table
        print("\n" + "="*60)
        print("TENDER TYPE METRICS TABLE - October 31, 2025")
        print("="*60)
        cursor.execute("""
            SELECT store, date, tender_type, detail_amount
            FROM tender_type_metrics
            WHERE date = '2025-10-31'
            ORDER BY store, tender_type
        """)
        tender_rows = cursor.fetchall()
        
        if tender_rows:
            print(f"Found {len(tender_rows)} records:")
            stores = {}
            for row in tender_rows:
                store = row[0]
                if store not in stores:
                    stores[store] = []
                stores[store].append((row[2], row[3]))
            
            for store, tenders in stores.items():
                print(f"\n  Store: {store}")
                for tender_type, amount in tenders:
                    print(f"    {tender_type}: ${amount:,.2f}")
        else:
            print("❌ No records found in tender_type_metrics for 2025-10-31")
        
        # Check date range in both tables
        print("\n" + "="*60)
        print("DATE RANGE ANALYSIS")
        print("="*60)
        
        cursor.execute("""
            SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(DISTINCT date) as total_days
            FROM sales_summary
            WHERE date >= '2025-10-01' AND date <= '2025-10-31'
        """)
        date_range = cursor.fetchone()
        print(f"Sales Summary: {date_range[0]} to {date_range[1]} ({date_range[2]} days)")
        
        cursor.execute("""
            SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(DISTINCT date) as total_days
            FROM tender_type_metrics
            WHERE date >= '2025-10-01' AND date <= '2025-10-31'
        """)
        date_range = cursor.fetchone()
        print(f"Tender Metrics: {date_range[0]} to {date_range[1]} ({date_range[2]} days)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_oct31_data()
