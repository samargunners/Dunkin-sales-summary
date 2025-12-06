import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection

conn = get_supabase_connection()
cursor = conn.cursor()

# Check if Nov 11 data exists
print("="*60)
print("Checking Nov 11, 2025 data:")
print("="*60)

cursor.execute("""
    SELECT store, date, net_sales, gross_sales
    FROM sales_summary 
    WHERE date = '2025-11-11'
    ORDER BY store
""")

rows = cursor.fetchall()
if rows:
    print(f"\nFound {len(rows)} stores with data on Nov 11:")
    for row in rows:
        print(f"  Store: {row[0]}, Date: {row[1]}, Net Sales: ${row[2]:,.2f}, Gross Sales: ${row[3]:,.2f}")
else:
    print("\n❌ No data found for Nov 11, 2025")

print("\n" + "="*60)
print("Checking all dates in November:")
print("="*60)

cursor.execute("""
    SELECT DISTINCT date 
    FROM sales_summary 
    WHERE date BETWEEN '2025-11-01' AND '2025-11-30' 
    ORDER BY date
""")

print("\nDates with data in November:")
rows = cursor.fetchall()
for row in rows:
    print(f"  {row[0]}")

cursor.close()
conn.close()
