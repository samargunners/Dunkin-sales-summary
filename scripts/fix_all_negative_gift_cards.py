"""
Fix all negative gift_card_sales values in November by flipping their signs
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.utils.supabase_db import get_supabase_connection

conn = get_supabase_connection()
cur = conn.cursor()

# Find all negative values
cur.execute("""
    SELECT store, date, gift_card_sales
    FROM sales_summary
    WHERE gift_card_sales < 0 AND date >= '2025-11-01'
    ORDER BY date, store
""")

records = cur.fetchall()
print(f"Found {len(records)} records with NEGATIVE gift_card_sales\n")

if not records:
    print("No negative values found. Nothing to fix!")
    cur.close()
    conn.close()
    sys.exit(0)

# Show what will be fixed
print("Records to be fixed:")
print(f"{'Store':<12} | {'Date':<12} | {'Current':<10} | {'Fixed':<10}")
print("-" * 60)
for r in records[:10]:  # Show first 10
    print(f"{r[0]:<12} | {r[1]} | ${r[2]:>9,.2f} | ${-r[2]:>9,.2f}")

if len(records) > 10:
    print(f"... and {len(records) - 10} more")

# Ask for confirmation
response = input(f"\n⚠️  Fix {len(records)} records by flipping signs? (yes/no): ")

if response.lower() != 'yes':
    print("❌ Cancelled")
    cur.close()
    conn.close()
    sys.exit(0)

# Perform the fix
print("\nFixing records...")
updated_count = 0

for store, date, current_value in records:
    new_value = -current_value  # Flip the sign
    
    cur.execute("""
        UPDATE sales_summary
        SET gift_card_sales = %s
        WHERE store = %s AND date = %s
    """, (new_value, store, date))
    
    updated_count += 1
    if updated_count % 10 == 0:
        print(f"  ✓ Fixed {updated_count}/{len(records)}...")

conn.commit()

print(f"\n✅ Successfully fixed {updated_count} records!")
print("   All negative gift_card_sales values have been flipped to positive.")

cur.close()
conn.close()

print("\n🔄 Now rerun your report to verify the fix.")
