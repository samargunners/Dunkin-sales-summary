import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.utils.supabase_db import get_supabase_connection

conn = get_supabase_connection()
cur = conn.cursor()

# Check what dates have tender data in November
cur.execute("""
    SELECT DISTINCT date
    FROM tender_type_metrics
    WHERE date >= '2025-11-01' AND date < '2025-12-01'
    ORDER BY date
""")

dates_with_data = [row[0] for row in cur.fetchall()]

print("Dates with tender data in November:\n")
for d in dates_with_data:
    print(f"  ✓ {d}")

print(f"\nTotal: {len(dates_with_data)} days with data")

# Check which dates are missing
import datetime
all_november_dates = [datetime.date(2025, 11, i) for i in range(1, 31)]
missing_dates = [d for d in all_november_dates if d not in dates_with_data]

if missing_dates:
    print(f"\n❌ Missing data for {len(missing_dates)} days:")
    for d in missing_dates:
        print(f"  ✗ {d}")
else:
    print("\n✅ All November dates have tender data!")

cur.close()
conn.close()
