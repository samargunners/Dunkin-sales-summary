import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dashboard.utils.supabase_db import get_supabase_connection

def safe_print(msg):
    """Print with Unicode error handling for Windows console"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

def check_latest_dates():
    """Check the latest available dates for HME and Medallia reports in Supabase"""
    conn = get_supabase_connection()
    cur = conn.cursor()

    safe_print("=" * 80)
    safe_print("CHECKING LATEST DATA IN SUPABASE")
    safe_print("=" * 80)

    # Check HME Report data
    safe_print("\n📊 HME REPORT DATA")
    safe_print("-" * 40)
    try:
        cur.execute("""
            SELECT MIN(date) as earliest, MAX(date) as latest, COUNT(*) as total_rows
            FROM hme_report
        """)
        row = cur.fetchone()
        if row and row[1]:
            safe_print(f"   Earliest Date: {row[0]}")
            safe_print(f"   Latest Date:   {row[1]}")
            safe_print(f"   Total Rows:    {row[2]:,}")

            # Get store count
            cur.execute("SELECT COUNT(DISTINCT store) FROM hme_report")
            store_count = cur.fetchone()[0]
            safe_print(f"   Stores:        {store_count}")
        else:
            safe_print("   ⚠️  No data found in hme_report table")
    except Exception as e:
        safe_print(f"   ❌ Error: {e}")

    # Check Medallia Reports data
    safe_print("\n📊 MEDALLIA REPORT DATA")
    safe_print("-" * 40)
    try:
        cur.execute("""
            SELECT MIN(report_date) as earliest, MAX(report_date) as latest, COUNT(*) as total_rows
            FROM medallia_report
        """)
        row = cur.fetchone()
        if row and row[1]:
            safe_print(f"   Earliest Date: {row[0]}")
            safe_print(f"   Latest Date:   {row[1]}")
            safe_print(f"   Total Rows:    {row[2]:,}")

            # Get PC number count
            cur.execute("SELECT COUNT(DISTINCT pc_number) FROM medallia_report")
            pc_count = cur.fetchone()[0]
            safe_print(f"   Stores:        {pc_count}")
        else:
            safe_print("   ⚠️  No data found in medallia_report table")
    except Exception as e:
        safe_print(f"   ❌ Error: {e}")

    safe_print("\n" + "=" * 80)

    cur.close()
    conn.close()

if __name__ == "__main__":
    check_latest_dates()
