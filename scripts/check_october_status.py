"""
Check what October+ data exists in Supabase before deleting
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection

def check_october_data():
    """Check what October+ data exists."""
    
    try:
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        print("="*80)
        print("CHECKING OCTOBER+ DATA IN SUPABASE")
        print("="*80)
        
        # Check sales_summary
        cursor.execute("""
            SELECT COUNT(*), MIN(date), MAX(date)
            FROM sales_summary
            WHERE date >= '2025-10-01'
        """)
        count, min_date, max_date = cursor.fetchone()
        print(f"\nsales_summary: {count} records from {min_date} to {max_date}")
        
        # Check tender_type_metrics
        cursor.execute("""
            SELECT COUNT(*), MIN(date), MAX(date)
            FROM tender_type_metrics
            WHERE date >= '2025-10-01'
        """)
        count, min_date, max_date = cursor.fetchone()
        print(f"tender_type_metrics: {count} records from {min_date} to {max_date}")
        
        # Check labor_metrics
        cursor.execute("""
            SELECT COUNT(*), MIN(date), MAX(date)
            FROM labor_metrics
            WHERE date >= '2025-10-01'
        """)
        count, min_date, max_date = cursor.fetchone()
        print(f"labor_metrics: {count} records from {min_date} to {max_date}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_october_data()
