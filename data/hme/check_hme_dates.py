
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dashboard.utils.supabase_db import get_supabase_connection

def check_hme_dates():
    conn = get_supabase_connection()
    cur = conn.cursor()
    print("Checking HME data date coverage...")
    cur.execute("""
        SELECT MIN(date) as earliest, MAX(date) as latest, COUNT(DISTINCT date) as total_dates
        FROM hme_report
    """)
    row = cur.fetchone()
    print(f"   Earliest Date: {row[0]}")
    print(f"   Latest Date: {row[1]}")
    print(f"   Total Dates: {row[2]}")
    print("\nStore coverage:")
    cur.execute("""
        SELECT store, COUNT(DISTINCT date) as days_with_data
        FROM hme_report
        GROUP BY store
        ORDER BY store
    """)
    print(f"   {'Store':<10} {'Days with Data'}")
    print(f"   {'-'*10} {'-'*14}")
    for row in cur.fetchall():
        print(f"   {row[0]:<10} {row[1]}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_hme_dates()
