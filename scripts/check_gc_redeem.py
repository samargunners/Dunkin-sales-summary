import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection

# Check what tender types exist for gift card redeem
conn = get_supabase_connection()
cursor = conn.cursor()

print("Checking gift card related tender types in database:\n")

# Query 1: All distinct tender types with 'redeem' or 'gc'
cursor.execute("""
    SELECT DISTINCT tender_type 
    FROM tender_type_metrics 
    WHERE tender_type ILIKE '%redeem%' OR tender_type ILIKE '%gc%'
    ORDER BY tender_type
""")

print("Gift Card related tender types:")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"  - '{row[0]}'")
else:
    print("  No matching tender types found!")

print("\n" + "="*60)

# Query 2: Check if any GC Redeem data exists and show sample
cursor.execute("""
    SELECT store, date, tender_type, detail_amount
    FROM tender_type_metrics 
    WHERE tender_type ILIKE '%redeem%' OR tender_type ILIKE '%gc%'
    ORDER BY date DESC
    LIMIT 10
""")

print("\nSample GC Redeem records:")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"  Store: {row[0]}, Date: {row[1]}, Type: '{row[2]}', Amount: ${row[3]}")
else:
    print("  No records found!")

print("\n" + "="*60)

# Query 3: Check total count and sum
cursor.execute("""
    SELECT COUNT(*), SUM(detail_amount)
    FROM tender_type_metrics 
    WHERE tender_type ILIKE '%redeem%' OR tender_type ILIKE '%gc%'
""")

row = cursor.fetchone()
print(f"\nTotal GC Redeem records: {row[0]}")
print(f"Total GC Redeem amount: ${row[1] if row[1] else 0:,.2f}")

cursor.close()
conn.close()
