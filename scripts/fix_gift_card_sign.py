import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.utils.supabase_db import get_supabase_connection

conn = get_supabase_connection()
cur = conn.cursor()

# Check current value
cur.execute("""
    SELECT store, date, gift_card_sales
    FROM sales_summary
    WHERE store = 'Enola' AND date = '2025-11-01'
""")
print("BEFORE UPDATE:")
row = cur.fetchone()
print(f"  Store: {row[0]}, Date: {row[1]}, Gift Card Sales: ${row[2]}")

# Update to positive
cur.execute("""
    UPDATE sales_summary
    SET gift_card_sales = 80.00
    WHERE store = 'Enola' AND date = '2025-11-01'
""")
conn.commit()

# Check after update
cur.execute("""
    SELECT store, date, gift_card_sales
    FROM sales_summary
    WHERE store = 'Enola' AND date = '2025-11-01'
""")
print("\nAFTER UPDATE:")
row = cur.fetchone()
print(f"  Store: {row[0]}, Date: {row[1]}, Gift Card Sales: ${row[2]}")

cur.close()
conn.close()

print("\n✅ Fixed! Now rerun your report to verify.")
