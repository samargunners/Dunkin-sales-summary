"""
Check unique tender types in Supabase tender_type_metrics table
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import utils
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from dashboard.utils.supabase_db import get_supabase_connection

def check_unique_tender_types():
    """Check unique tender types in the database"""
    
    print("=" * 80)
    print("Unique Tender Types in tender_type_metrics Table")
    print("=" * 80)
    print()
    
    try:
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        # Get unique tender types with count
        query = """
            SELECT 
                tender_type,
                COUNT(*) as record_count,
                MIN(date) as first_date,
                MAX(date) as last_date
            FROM tender_type_metrics
            GROUP BY tender_type
            ORDER BY tender_type;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"Total unique tender types: {len(results)}\n")
        print("-" * 80)
        print(f"{'Tender Type':<40} {'Count':>10} {'First Date':>12} {'Last Date':>12}")
        print("-" * 80)
        
        for row in results:
            tender_type, count, first_date, last_date = row
            print(f"{tender_type:<40} {count:>10} {str(first_date):>12} {str(last_date):>12}")
        
        print("-" * 80)
        
        # Get total records
        cursor.execute("SELECT COUNT(*) FROM tender_type_metrics")
        total = cursor.fetchone()[0]
        print(f"\nTotal records in table: {total}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_unique_tender_types()
