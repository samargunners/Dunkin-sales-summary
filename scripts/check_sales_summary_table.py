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

def check_sales_summary():
    try:
        conn = supabase_db.get_supabase_connection()
        safe_print("✅ Connected to Supabase successfully\n")
        
        with conn.cursor() as cur:
            # Get table structure
            safe_print("=" * 80)
            safe_print("SALES_SUMMARY TABLE STRUCTURE")
            safe_print("=" * 80)
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'sales_summary'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            safe_print("\nColumns:")
            for col_name, col_type in columns:
                safe_print(f"  - {col_name}: {col_type}")
            
            # Get summary statistics
            safe_print("\n" + "=" * 80)
            safe_print("DATA SUMMARY")
            safe_print("=" * 80)
            
            # Total rows
            cur.execute("SELECT COUNT(*) FROM sales_summary")
            total = cur.fetchone()[0]
            safe_print(f"\nTotal rows: {total:,}")
            
            # Date range
            cur.execute("SELECT MIN(date), MAX(date) FROM sales_summary")
            min_date, max_date = cur.fetchone()
            safe_print(f"Date range: {min_date} to {max_date}")
            
            # Rows per store
            cur.execute("""
                SELECT store, COUNT(*) as row_count
                FROM sales_summary
                GROUP BY store
                ORDER BY store
            """)
            safe_print("\nRows per store:")
            for store, count in cur.fetchall():
                safe_print(f"  {store}: {count:,} rows")
            
            # Recent dates per store
            safe_print("\n" + "=" * 80)
            safe_print("MOST RECENT DATA PER STORE")
            safe_print("=" * 80)
            cur.execute("""
                SELECT store, MAX(date) as latest_date, COUNT(*) as days_of_data
                FROM sales_summary
                GROUP BY store
                ORDER BY store
            """)
            safe_print("\nLatest date per store:")
            for store, latest_date, days in cur.fetchall():
                safe_print(f"  {store}: {latest_date} ({days:,} days of data)")
            
            # Sample of recent data
            safe_print("\n" + "=" * 80)
            safe_print("SAMPLE: MOST RECENT 10 ROWS")
            safe_print("=" * 80)
            cur.execute("""
                SELECT store, date, net_sales, guest_count, avg_check
                FROM sales_summary
                ORDER BY date DESC, store
                LIMIT 10
            """)
            safe_print(f"\n{'Store':<20} {'Date':<12} {'Net Sales':>12} {'Guests':>8} {'Avg Check':>10}")
            safe_print("-" * 80)
            for row in cur.fetchall():
                store, date, net_sales, guests, avg_check = row
                safe_print(f"{store:<20} {str(date):<12} ${net_sales:>11,.2f} {guests:>8} ${avg_check:>9,.2f}")
            
            # Check for gaps in recent dates
            safe_print("\n" + "=" * 80)
            safe_print("CHECKING FOR RECENT DATE GAPS (Last 7 days)")
            safe_print("=" * 80)
            cur.execute("""
                WITH date_series AS (
                    SELECT generate_series(
                        (SELECT MAX(date) FROM sales_summary) - INTERVAL '6 days',
                        (SELECT MAX(date) FROM sales_summary),
                        '1 day'::interval
                    )::date AS date
                )
                SELECT 
                    ds.date,
                    COUNT(ss.store) as stores_with_data
                FROM date_series ds
                LEFT JOIN sales_summary ss ON ds.date = ss.date
                GROUP BY ds.date
                ORDER BY ds.date DESC
            """)
            safe_print(f"\n{'Date':<12} {'Stores with data':>20}")
            safe_print("-" * 35)
            for date, store_count in cur.fetchall():
                safe_print(f"{str(date):<12} {store_count:>20}")
            
        conn.close()
        
    except Exception as e:
        safe_print(f"❌ Error: {e}")
        import traceback
        safe_print(traceback.format_exc())

if __name__ == "__main__":
    check_sales_summary()
