from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
from dashboard.utils import supabase_db

def safe_print(msg):
    """Print with Unicode error handling for Windows console"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

def check_supabase_data():
    try:
        conn = supabase_db.get_supabase_connection()
        safe_print("✅ Connected to Supabase successfully\n")
        
        # List of tables to check
        tables = [
            'sales_summary',
            'sales_by_daypart', 
            'sales_by_subcategory',
            'tender_type_metrics',
            'labor_metrics',
            'menu_mix_metrics'
        ]
        
        with conn.cursor() as cur:
            safe_print("=" * 80)
            safe_print("SUPABASE DATA SUMMARY")
            safe_print("=" * 80)
            
            for table in tables:
                try:
                    # Get total row count
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    
                    # Get date range if date column exists
                    cur.execute(f"""
                        SELECT MIN(date), MAX(date) 
                        FROM {table} 
                        WHERE date IS NOT NULL
                    """)
                    date_range = cur.fetchone()
                    
                    # Get distinct stores
                    cur.execute(f"SELECT COUNT(DISTINCT store) FROM {table}")
                    store_count = cur.fetchone()[0]
                    
                    safe_print(f"\n📊 {table.upper()}")
                    safe_print(f"   Total rows: {count:,}")
                    if date_range and date_range[0]:
                        safe_print(f"   Date range: {date_range[0]} to {date_range[1]}")
                    safe_print(f"   Stores: {store_count}")
                    
                except Exception as e:
                    safe_print(f"\n❌ {table.upper()}: Error - {e}")
            
            safe_print("\n" + "=" * 80)
            
        conn.close()
        
    except Exception as e:
        safe_print(f"❌ Error connecting to Supabase: {e}")

if __name__ == "__main__":
    check_supabase_data()
