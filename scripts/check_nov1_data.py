"""
Check November 1st data specifically
"""

import os
import sys
from datetime import datetime
import pandas as pd

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection


def check_nov1_data():
    """Check November 1st data in detail."""
    
    try:
        print(f"Connecting to Supabase...")
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        # Check sales_summary for Nov 1
        print(f"\n=== November 1, 2025 - sales_summary ===")
        
        cursor.execute("""
            SELECT 
                date,
                store,
                dd_adjusted_no_markup,
                cash_in,
                gift_card_sales,
                pa_sales_tax,
                paid_out
            FROM sales_summary 
            WHERE date = '2025-11-01'
            ORDER BY store;
        """)
        
        sales_rows = cursor.fetchall()
        print(f"\n✓ Found {len(sales_rows)} rows in sales_summary for Nov 1")
        
        if len(sales_rows) > 0:
            column_names = [desc[0] for desc in cursor.description]
            df_sales = pd.DataFrame(sales_rows, columns=column_names)
            print("\nNov 1 data from sales_summary:")
            print(df_sales.to_string())
        
        # Check tender_type_metrics for Nov 1
        print(f"\n=== November 1, 2025 - tender_type_metrics ===")
        
        cursor.execute("""
            SELECT 
                date,
                store,
                tender_type,
                detail_amount
            FROM tender_type_metrics 
            WHERE date = '2025-11-01'
            ORDER BY store, tender_type;
        """)
        
        tender_rows = cursor.fetchall()
        print(f"\n✓ Found {len(tender_rows)} rows in tender_type_metrics for Nov 1")
        
        if len(tender_rows) > 0:
            column_names = [desc[0] for desc in cursor.description]
            df_tender = pd.DataFrame(tender_rows, columns=column_names)
            print("\nNov 1 data from tender_type_metrics:")
            print(df_tender.to_string())
            print(f"\nTender types for Nov 1:")
            print(df_tender.groupby('tender_type')['detail_amount'].sum())
        else:
            print("\n❌ No tender type data found for November 1st")
            print("\nThis means tender data upload might have started from Nov 2")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("November 1st Data Checker")
    print("=" * 60)
    
    check_nov1_data()
