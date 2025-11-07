from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
from dashboard.utils import supabase_db

def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

def check_november_data():
    try:
        conn = supabase_db.get_supabase_connection()
        
        with conn.cursor() as cur:
            # Check November data in sales_summary
            safe_print("Checking for November 2025 data in sales_summary...")
            cur.execute("""
                SELECT date, COUNT(*) as stores, SUM(net_sales) as total_sales
                FROM sales_summary
                WHERE date >= '2025-11-01' AND date <= '2025-11-06'
                GROUP BY date
                ORDER BY date
            """)
            results = cur.fetchall()
            
            if results:
                safe_print(f"\n{'Date':<12} {'Stores':>8} {'Total Sales':>15}")
                safe_print("-" * 40)
                for date, stores, sales in results:
                    safe_print(f"{str(date):<12} {stores:>8} ${sales:>14,.2f}")
            else:
                safe_print("\n❌ NO November 2025 data found in sales_summary table!")
                
                # Check what the actual latest dates are
                safe_print("\nChecking latest 10 dates in sales_summary...")
                cur.execute("""
                    SELECT DISTINCT date
                    FROM sales_summary
                    ORDER BY date DESC
                    LIMIT 10
                """)
                latest_dates = cur.fetchall()
                safe_print("\nLatest dates:")
                for (date,) in latest_dates:
                    safe_print(f"  {date}")
        
        conn.close()
        
    except Exception as e:
        safe_print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_november_data()
