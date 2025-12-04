"""
Manually upload tender type files for missing November dates
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from dashboard.utils.supabase_db import get_supabase_connection

compiled_dir = Path(r"C:\Projects\Dunkin-sales-summary\data\compiled")

# Find Nov 27 file (look for any file with 20251127 in name)
nov27_files = [f for f in compiled_dir.glob("*.xlsx") if "20251127" in f.name and "Tender" in f.name]
if not nov27_files:
    print("❌ Nov 27 tender file not found in compiled folder")
    sys.exit(1)

print(f"Found file: {nov27_files[0].name}\n")

# Read the file
df = pd.read_excel(nov27_files[0])
print(f"Loaded {len(df)} rows\n")

print("Sample data:")
print(df.head().to_string())

# Connect to database
conn = get_supabase_connection()
cur = conn.cursor()

# Check if data already exists
cur.execute("""
    SELECT COUNT(*) FROM tender_type_metrics
    WHERE date = '2025-11-27'
""")
existing_count = cur.fetchone()[0]
print(f"\nExisting records for Nov 27: {existing_count}")

if existing_count > 0:
    print("\n⚠️  Data already exists. Deleting old data first...")
    cur.execute("DELETE FROM tender_type_metrics WHERE date = '2025-11-27'")
    conn.commit()
    print(f"✓ Deleted {cur.rowcount} old records")

# Prepare data for upload
df['pc_number'] = df['pc_number'].astype(str)
df['date'] = pd.to_datetime(df['date']).dt.date

# Insert new data
insert_query = """
    INSERT INTO tender_type_metrics (store, pc_number, date, tender_type, detail_amount)
    VALUES (%s, %s, %s, %s, %s)
"""

records_inserted = 0
for _, row in df.iterrows():
    cur.execute(insert_query, (
        row['store'],
        row['pc_number'],
        row['date'],
        row['tender_type'],
        float(row['detail_amount'])
    ))
    records_inserted += 1

conn.commit()
print(f"\n✅ Successfully inserted {records_inserted} records for Nov 27")

cur.close()
conn.close()
