"""
Check tender_type_metrics table structure and sample data
"""

import os
import sys
from datetime import datetime
import pandas as pd

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection


def check_tender_data():
    """Check tender type metrics table."""
    
    try:
        print("Connecting to Supabase...")
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        # Check table columns
        print("\n=== Checking table structure ===")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'tender_type_metrics'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print("\nColumns in tender_type_metrics:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
        
        # Check sample data
        print("\n=== Sample data from tender_type_metrics ===")
        cursor.execute("""
            SELECT * FROM tender_type_metrics 
            WHERE date >= '2025-09-01' AND date <= '2025-09-30'
            LIMIT 20;
        """)
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=column_names)
        print(f"\nFound {len(rows)} sample rows")
        print(df.to_string())
        
        # Check distinct tender types
        print("\n=== Distinct tender types for September 2025 ===")
        cursor.execute("""
            SELECT DISTINCT tender_type, COUNT(*) as count
            FROM tender_type_metrics 
            WHERE date >= '2025-09-01' AND date <= '2025-09-30'
            GROUP BY tender_type
            ORDER BY count DESC;
        """)
        tender_types = cursor.fetchall()
        print("\nTender types found:")
        for tt in tender_types:
            print(f"  - {tt[0]}: {tt[1]} records")
        
        # Check date range
        print("\n=== Date range in tender_type_metrics ===")
        cursor.execute("""
            SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(*) as total_records
            FROM tender_type_metrics;
        """)
        date_info = cursor.fetchone()
        print(f"Date range: {date_info[0]} to {date_info[1]}")
        print(f"Total records: {date_info[2]}")
        
        # Check stores
        print("\n=== Stores in tender_type_metrics for September 2025 ===")
        cursor.execute("""
            SELECT DISTINCT store, COUNT(*) as count
            FROM tender_type_metrics 
            WHERE date >= '2025-09-01' AND date <= '2025-09-30'
            GROUP BY store
            ORDER BY store;
        """)
        stores = cursor.fetchall()
        print("\nStores found:")
        for store in stores:
            print(f"  - {store[0]}: {store[1]} records")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_tender_data()
