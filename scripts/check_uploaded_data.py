from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
from dashboard.utils import supabase_db

def check_uploaded_data():
    """Check what data has been successfully uploaded to each table"""
    try:
        conn = supabase_db.get_supabase_connection()
        print("Connected to Supabase successfully\n")
        
        tables = [
            'tender_type_metrics',
            'sales_summary', 
            'sales_by_subcategory',
            'sales_by_daypart',
            'sales_by_order_type',
            'labor_metrics'
        ]
        
        for table in tables:
            try:
                with conn.cursor() as cur:
                    # Get row count
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    
                    # Get date range if data exists
                    if count > 0:
                        cur.execute(f"SELECT MIN(date), MAX(date) FROM {table}")
                        min_date, max_date = cur.fetchone()
                        
                        # Get stores count
                        cur.execute(f"SELECT COUNT(DISTINCT store) FROM {table}")
                        stores = cur.fetchone()[0]
                        
                        print(f"✅ {table}: {count} rows | {stores} stores | {min_date} to {max_date}")
                    else:
                        print(f"❌ {table}: 0 rows (empty)")
                        
            except Exception as e:
                print(f"❌ {table}: Error - {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    check_uploaded_data()