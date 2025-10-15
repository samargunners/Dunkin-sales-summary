#!/usr/bin/env python3
"""
Clean up duplicate data in Supabase tables.
Keeps the most recent version of each unique (store, pc_number, date) combination.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
from dashboard.utils import supabase_db

def clean_duplicates():
    """Remove duplicate rows from all tables"""
    
    tables = [
        'labor_metrics', 
        'sales_summary', 
        'sales_by_subcategory', 
        'sales_by_daypart', 
        'sales_by_order_type', 
        'tender_type_metrics'
    ]
    
    try:
        conn = supabase_db.get_supabase_connection()
        
        print("🧹 Starting duplicate cleanup...")
        print("=" * 50)
        
        with conn.cursor() as cur:
            for table in tables:
                print(f"\n📊 Cleaning {table}...")
                
                # Get current count
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                before_count = cur.fetchone()[0]
                
                # Delete duplicates, keeping the row with the highest ID (most recent)
                cleanup_query = f"""
                DELETE FROM {table} 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM {table} 
                    GROUP BY store, pc_number, date
                )
                """
                
                cur.execute(cleanup_query)
                deleted_count = cur.rowcount
                
                # Get new count
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                after_count = cur.fetchone()[0]
                
                print(f"   Before: {before_count} rows")
                print(f"   Deleted: {deleted_count} duplicates")
                print(f"   After: {after_count} rows")
                print(f"   ✅ Cleaned successfully")
        
        conn.commit()
        print(f"\n🎉 All tables cleaned successfully!")
        
        # Verify cleanup
        print(f"\n📋 Verification:")
        print("=" * 30)
        
        with conn.cursor() as cur:
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                total_count = cur.fetchone()[0]
                
                cur.execute(f"SELECT COUNT(DISTINCT store || pc_number || date) FROM {table}")
                unique_combinations = cur.fetchone()[0]
                
                if total_count == unique_combinations:
                    print(f"✅ {table}: {total_count} rows (no duplicates)")
                else:
                    print(f"⚠️  {table}: {total_count} total, {unique_combinations} unique")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        conn.rollback()
        conn.close()

if __name__ == "__main__":
    # Ask for confirmation
    print("⚠️  This will remove duplicate data from Supabase tables.")
    print("   Only the most recent version of each (store, pc_number, date) will be kept.")
    response = input("\n🤔 Continue with cleanup? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        clean_duplicates()
    else:
        print("❌ Cleanup cancelled.")