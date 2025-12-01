import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.utils.supabase_db import get_supabase_connection

conn = get_supabase_connection()
cur = conn.cursor()

# Find all negative gift card sales in November
cur.execute("""
    SELECT store, date, gift_card_sales
    FROM sales_summary
    WHERE gift_card_sales < 0 AND date >= '2025-11-01'
    ORDER BY date, store
""")

rows = cur.fetchall()
print(f"Found {len(rows)} records with NEGATIVE gift card sales in November:\n")
print(f"{'Store':<12} | {'Date':<12} | {'Gift Card Sales':>18}")
print("-" * 50)
for r in rows:
    print(f"{r[0]:<12} | {r[1]} | ${r[2]:>17,.2f}")

if rows:
    print(f"\n⚠️  These records have NEGATIVE gift card sales values.")
    print("   This suggests the sign is being flipped during data upload.")

cur.close()
conn.close()
