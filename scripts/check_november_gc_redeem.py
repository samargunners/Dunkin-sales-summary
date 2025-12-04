import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.utils.supabase_db import get_supabase_connection

conn = get_supabase_connection()
cur = conn.cursor()

# Check gift card redeem data in tender_type_metrics for November
cur.execute("""
    SELECT 
        date,
        COUNT(*) as record_count,
        SUM(detail_amount) as total_amount
    FROM tender_type_metrics
    WHERE LOWER(tender_type) LIKE '%gift%card%redeem%'
      AND date >= '2025-11-01' 
      AND date < '2025-12-01'
    GROUP BY date
    ORDER BY date
""")

print("Gift Card Redeem data in tender_type_metrics (November 2025):\n")
print(f"{'Date':<12} | {'Records':>8} | {'Total Amount':>15}")
print("-" * 42)

rows = cur.fetchall()
if rows:
    total_records = 0
    total_amount = 0
    for row in rows:
        print(f"{row[0]} | {row[1]:>8} | ${row[2]:>14,.2f}")
        total_records += row[1]
        total_amount += row[2]
    
    print("-" * 42)
    print(f"{'TOTAL':<12} | {total_records:>8} | ${total_amount:>14,.2f}")
    print(f"\n✓ Found data for {len(rows)} days in November")
else:
    print("❌ NO gift card redeem data found for November!")

# Check unique tender types to see variations
print("\n" + "="*60)
print("All Gift Card related tender types in November:\n")
cur.execute("""
    SELECT DISTINCT tender_type, COUNT(*) as count
    FROM tender_type_metrics
    WHERE LOWER(tender_type) LIKE '%gift%'
      AND date >= '2025-11-01' 
      AND date < '2025-12-01'
    GROUP BY tender_type
    ORDER BY tender_type
""")

for row in cur.fetchall():
    print(f"  {row[0]:<30} : {row[1]:>4} records")

cur.close()
conn.close()
