"""
Delete all data from Nov 1 onwards (including Nov 1) from Supabase
This includes ALL tables affected by the upload script
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "dashboard" / "utils"))
from supabase_db import get_supabase_connection

def delete_november_december_data():
    """Delete all data from Nov 1, 2025 onwards from ALL tables"""
    
    conn = get_supabase_connection()
    if not conn:
        print("❌ Failed to connect to Supabase")
        return False
    
    # All tables that get data uploaded from the pipeline
    tables = [
        "sales_summary",
        "tender_type_metrics", 
        "labor_metrics",
        "sales_by_daypart",
        "sales_by_subcategory",
        "sales_by_order_type"
    ]
    
    try:
        cursor = conn.cursor()
        total_deleted = 0
        
        for table in tables:
            print(f"\n🗑️  Deleting from {table} table...")
            delete_query = f"""
                DELETE FROM {table} 
                WHERE date >= '2025-11-01'
            """
            cursor.execute(delete_query)
            rows_deleted = cursor.rowcount
            total_deleted += rows_deleted
            print(f"✅ Deleted {rows_deleted} rows from {table}")
        
        # Commit the changes
        conn.commit()
        print(f"\n{'='*60}")
        print(f"✅ Total deleted: {total_deleted} rows across {len(tables)} tables")
        print("✅ All November and December 2025 data has been deleted from Supabase")
        print(f"{'='*60}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error deleting data: {e}")
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("DELETE NOVEMBER & DECEMBER 2025 DATA FROM SUPABASE")
    print("=" * 60)
    print("\n⚠️  This will delete ALL data from Nov 1, 2025 onwards")
    print("   from the following tables:")
    print("   - sales_summary")
    print("   - tender_type_metrics")
    print("   - labor_metrics")
    print("   - sales_by_daypart")
    print("   - sales_by_subcategory")
    print("   - sales_by_order_type")
    print()
    
    confirm = input("Type 'DELETE' to confirm: ")
    
    if confirm == "DELETE":
        success = delete_november_december_data()
        if success:
            print("\n✅ Database cleanup completed successfully!")
            print("You can now fix the upload script and re-upload the data.")
        else:
            print("\n❌ Database cleanup failed. Please check the errors above.")
    else:
        print("\n❌ Deletion cancelled. No data was deleted.")
