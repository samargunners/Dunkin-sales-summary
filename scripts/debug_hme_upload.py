#!/usr/bin/env python3
"""Debug script to test HME upload and see what's happening"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.utils.supabase_db import get_supabase_connection

def safe_print(msg):
    """Print with Unicode error handling for Windows console"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

def check_recent_uploads():
    """Check what was uploaded recently to hme_report"""
    conn = get_supabase_connection()
    cur = conn.cursor()

    print("=" * 80)
    print("CHECKING RECENT HME UPLOADS")
    print("=" * 80)

    # Check last 10 records inserted
    cur.execute("""
        SELECT id, date, store, time_measure, total_cars
        FROM hme_report
        ORDER BY id DESC
        LIMIT 10
    """)

    print("\nLast 10 records inserted (by ID):")
    print(f"{'ID':<8} {'Date':<12} {'Store':<8} {'Time Measure':<15} {'Cars':<6}")
    print("-" * 80)
    for row in cur.fetchall():
        print(f"{row[0]:<8} {row[1]!s:<12} {row[2]:<8} {row[3]:<15} {row[4]:<6}")

    # Check if Feb 5, 6, 7 data exists
    print("\n" + "=" * 80)
    print("CHECKING FOR MISSING DATES (Feb 5-8)")
    print("=" * 80)

    for date_str in ['2026-02-05', '2026-02-06', '2026-02-07', '2026-02-08']:
        cur.execute("SELECT COUNT(*) FROM hme_report WHERE date = %s", (date_str,))
        count = cur.fetchone()[0]
        status = "EXISTS" if count > 0 else "MISSING"
        safe_print(f"{date_str}: {count:3} rows {status}")

    # Check for duplicate constraint
    print("\n" + "=" * 80)
    print("CHECKING FOR DUPLICATE DATA")
    print("=" * 80)

    cur.execute("""
        SELECT date, store, time_measure, COUNT(*) as duplicates
        FROM hme_report
        GROUP BY date, store, time_measure
        HAVING COUNT(*) > 1
        ORDER BY date DESC
        LIMIT 10
    """)

    dupes = cur.fetchall()
    if dupes:
        safe_print("\nWARNING: Found duplicate records:")
        for row in dupes:
            safe_print(f"  {row[0]} - Store {row[1]} - {row[2]}: {row[3]} duplicates")
    else:
        safe_print("\nNo duplicate records found")

    print("\n" + "=" * 80)

    cur.close()
    conn.close()

if __name__ == "__main__":
    check_recent_uploads()
