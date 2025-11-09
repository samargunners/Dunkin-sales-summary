"""
Check data availability in Supabase for specific date range
"""

import os
import sys
from datetime import datetime
import pandas as pd

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection


def check_data_availability(start_date, end_date):
    """Check if data exists for the specified date range."""
    
    try:
        print(f"Connecting to Supabase...")
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        # Check sales_summary table
        print(f"\n=== Checking sales_summary table ===")
        print(f"Date range: {start_date} to {end_date}")
        
        cursor.execute(f"""
            SELECT 
                date,
                store,
                dd_adjusted_no_markup,
                cash_in
            FROM sales_summary 
            WHERE date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY date, store;
        """)
        
        sales_rows = cursor.fetchall()
        print(f"\n✓ Found {len(sales_rows)} rows in sales_summary")
        
        if len(sales_rows) > 0:
            column_names = [desc[0] for desc in cursor.description]
            df_sales = pd.DataFrame(sales_rows, columns=column_names)
            print("\nSample data from sales_summary:")
            print(df_sales.head(20).to_string())
            
            print(f"\n--- Sales Summary Statistics ---")
            print(f"Unique dates: {df_sales['date'].nunique()}")
            print(f"Date range found: {df_sales['date'].min()} to {df_sales['date'].max()}")
            print(f"Stores: {df_sales['store'].unique()}")
        else:
            print("❌ No data found in sales_summary for this date range")
        
        # Check tender_type_metrics table
        print(f"\n=== Checking tender_type_metrics table ===")
        
        cursor.execute(f"""
            SELECT 
                date,
                store,
                tender_type,
                detail_amount
            FROM tender_type_metrics 
            WHERE date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY date, store, tender_type;
        """)
        
        tender_rows = cursor.fetchall()
        print(f"\n✓ Found {len(tender_rows)} rows in tender_type_metrics")
        
        if len(tender_rows) > 0:
            column_names = [desc[0] for desc in cursor.description]
            df_tender = pd.DataFrame(tender_rows, columns=column_names)
            print("\nSample data from tender_type_metrics:")
            print(df_tender.head(20).to_string())
            
            print(f"\n--- Tender Type Statistics ---")
            print(f"Unique dates: {df_tender['date'].nunique()}")
            print(f"Date range found: {df_tender['date'].min()} to {df_tender['date'].max()}")
            print(f"Stores: {df_tender['store'].unique()}")
            print(f"\nTender types breakdown:")
            print(df_tender.groupby('tender_type').size())
        else:
            print("❌ No data found in tender_type_metrics for this date range")
        
        # Check for missing dates
        if len(sales_rows) > 0:
            print(f"\n=== Checking for missing dates ===")
            cursor.execute(f"""
                SELECT generate_series(
                    '{start_date}'::date,
                    '{end_date}'::date,
                    '1 day'::interval
                )::date AS expected_date;
            """)
            all_dates = [row[0] for row in cursor.fetchall()]
            
            cursor.execute(f"""
                SELECT DISTINCT date 
                FROM sales_summary 
                WHERE date BETWEEN '{start_date}' AND '{end_date}'
                ORDER BY date;
            """)
            actual_dates = [row[0] for row in cursor.fetchall()]
            
            missing_dates = set(all_dates) - set(actual_dates)
            if missing_dates:
                print(f"\n❌ Missing dates in sales_summary ({len(missing_dates)} days):")
                for d in sorted(missing_dates):
                    print(f"  - {d}")
            else:
                print("\n✓ All dates present in the range")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("Data Availability Checker")
    print("=" * 60)
    print()
    
    start_date = "2025-11-01"
    end_date = "2025-11-09"
    
    check_data_availability(start_date, end_date)
