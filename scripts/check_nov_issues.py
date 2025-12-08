import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection

conn = get_supabase_connection()
cursor = conn.cursor()

print("="*70)
print("CHECKING NOV 7 AND NOV 27 DATA")
print("="*70)

# Check Nov 7
print("\n1. NOVEMBER 7, 2025:")
print("-"*70)
cursor.execute("""
    SELECT store, date, net_sales, gift_card_sales
    FROM sales_summary
    WHERE date = '2025-11-07'
    ORDER BY store
""")
rows = cursor.fetchall()
if rows:
    print(f"   ✓ Found {len(rows)} records for Nov 7:")
    for row in rows:
        print(f"   {row[0]:<15} ${row[2]:>10,.2f} net sales, ${row[3]:>8,.2f} GC sales")
else:
    print("   ❌ NO DATA for Nov 7")

# Check Nov 27
print("\n2. NOVEMBER 27, 2025 (Thanksgiving):")
print("-"*70)
cursor.execute("""
    SELECT store, date, net_sales, gift_card_sales
    FROM sales_summary
    WHERE date = '2025-11-27'
    ORDER BY store
""")
rows = cursor.fetchall()
if rows:
    print(f"   Found {len(rows)} records for Nov 27:")
    for row in rows:
        print(f"   {row[0]:<15} ${row[2]:>10,.2f} net sales, ${row[3]:>8,.2f} GC sales")
else:
    print("   ✓ NO DATA for Nov 27 - EXPECTED (Thanksgiving, stores closed)")

# Check surrounding dates for context
print("\n3. DATES AROUND NOV 7:")
print("-"*70)
cursor.execute("""
    SELECT date, COUNT(DISTINCT store) as stores, SUM(net_sales) as total_sales
    FROM sales_summary
    WHERE date BETWEEN '2025-11-05' AND '2025-11-09'
    GROUP BY date
    ORDER BY date
""")
print(f"   {'Date':<15} {'Stores':<10} {'Total Sales'}")
print(f"   {'-'*15} {'-'*10} {'-'*15}")
for row in cursor.fetchall():
    print(f"   {row[0]} {row[1]:<10} ${row[2]:>13,.2f}")

print("\n4. DATES AROUND NOV 27:")
print("-"*70)
cursor.execute("""
    SELECT date, COUNT(DISTINCT store) as stores, SUM(net_sales) as total_sales
    FROM sales_summary
    WHERE date BETWEEN '2025-11-25' AND '2025-11-29'
    GROUP BY date
    ORDER BY date
""")
print(f"   {'Date':<15} {'Stores':<10} {'Total Sales'}")
print(f"   {'-'*15} {'-'*10} {'-'*15}")
for row in cursor.fetchall():
    print(f"   {row[0]} {row[1]:<10} ${row[2]:>13,.2f}")

# Check compiled files for these dates
print("\n5. COMPILED FILES CHECK:")
print("-"*70)
import glob
compiled_files = glob.glob("C:/Projects/Dunkin-sales-summary/data/compiled/*_copy.xlsx")
nov7_files = [f for f in compiled_files if '20251107' in f]
nov27_files = [f for f in compiled_files if '20251127' in f]

print(f"   Nov 7 files found: {len(nov7_files)}")
if nov7_files:
    for f in nov7_files[:3]:
        print(f"     - {os.path.basename(f)}")

print(f"   Nov 27 files found: {len(nov27_files)}")
if nov27_files:
    for f in nov27_files[:3]:
        print(f"     - {os.path.basename(f)}")

print("\n" + "="*70)
print("CHECK COMPLETE")
print("="*70)

cursor.close()
conn.close()
