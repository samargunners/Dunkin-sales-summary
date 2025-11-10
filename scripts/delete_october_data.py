"""
Delete all data from October 1, 2025 onwards from sales_summary and tender_type_metrics tables

This script will clear all data from Oct 1 onwards so we can re-upload it cleanly.
"""

import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection


def delete_october_data():
    """Delete all data from October 1, 2025 onwards from both tables."""
    
    try:
        print("="*80)
        print("DELETE DATA FROM OCTOBER 1, 2025 ONWARDS")
        print("="*80)
        
        print("\nConnecting to Supabase...")
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        # First, check what data exists
        print("\n" + "="*80)
        print("CURRENT DATA FROM OCTOBER 1, 2025 ONWARDS")
        print("="*80)
        
        cursor.execute("""
            SELECT COUNT(*), MIN(date), MAX(date)
            FROM sales_summary
            WHERE date >= '2025-10-01'
        """)
        sales_count = cursor.fetchone()
        print(f"sales_summary: {sales_count[0]} records ({sales_count[1]} to {sales_count[2]})")
        
        cursor.execute("""
            SELECT COUNT(*), MIN(date), MAX(date)
            FROM tender_type_metrics
            WHERE date >= '2025-10-01'
        """)
        tender_count = cursor.fetchone()
        print(f"tender_type_metrics: {tender_count[0]} records ({tender_count[1]} to {tender_count[2]})")
        
        # Confirm deletion
        print("\n" + "="*80)
        print("⚠️  WARNING: This will delete ALL data from October 1, 2025 onwards!")
        print("="*80)
        print(f"- {sales_count[0]} records from sales_summary")
        print(f"- {tender_count[0]} records from tender_type_metrics")
        print()
        
        response = input("Are you sure you want to delete this data? (type 'DELETE' to confirm): ").strip()
        
        if response != 'DELETE':
            print("\n❌ Deletion cancelled. Data was NOT deleted.")
            cursor.close()
            conn.close()
            return
        
        # Delete from sales_summary
        print("\n" + "="*80)
        print("DELETING DATA...")
        print("="*80)
        
        print("\nDeleting from sales_summary...")
        cursor.execute("""
            DELETE FROM sales_summary
            WHERE date >= '2025-10-01'
        """)
        sales_deleted = cursor.rowcount
        print(f"✓ Deleted {sales_deleted} records from sales_summary")
        
        # Delete from tender_type_metrics
        print("\nDeleting from tender_type_metrics...")
        cursor.execute("""
            DELETE FROM tender_type_metrics
            WHERE date >= '2025-10-01'
        """)
        tender_deleted = cursor.rowcount
        print(f"✓ Deleted {tender_deleted} records from tender_type_metrics")
        
        # Commit the changes
        conn.commit()
        
        # Verify deletion
        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80)
        
        cursor.execute("""
            SELECT COUNT(*) FROM sales_summary
            WHERE date >= '2025-10-01'
        """)
        remaining_sales = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM tender_type_metrics
            WHERE date >= '2025-10-01'
        """)
        remaining_tender = cursor.fetchone()[0]
        
        print(f"sales_summary: {remaining_sales} records remaining")
        print(f"tender_type_metrics: {remaining_tender} records remaining")
        
        if remaining_sales == 0 and remaining_tender == 0:
            print("\n✅ All data from October 1, 2025 onwards successfully deleted!")
        else:
            print("\n⚠️  Warning: Some data may still remain")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("NEXT STEPS:")
        print("="*80)
        print("1. Re-run your data upload scripts for October 2025 onwards")
        print("2. For sales_summary: Process the sales mix detail files")
        print("3. For tender_type_metrics: Process the tender type files")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()


if __name__ == "__main__":
    delete_october_data()
