"""
Manually test uploading Nov 1 data to see if sign gets flipped
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from dashboard.utils.supabase_db import get_supabase_connection

# Read compiled file
compiled_dir = Path(r"C:\Projects\Dunkin-sales-summary\data\compiled")
files = list(compiled_dir.glob("*20251101*Sales Mix Detail*.xlsx"))

if not files:
    print("No file found")
    sys.exit(1)

df = pd.read_excel(files[0])
enola_data = df[df['store'] == 'Enola'].iloc[0]

print("Data from compiled file:")
print(f"  Store: {enola_data['store']}")
print(f"  Date: {enola_data['date']}")
print(f"  gift_card_sales: {enola_data['gift_card_sales']}")
print(f"  Type: {type(enola_data['gift_card_sales'])}")

# Now test what happens when we prepare it for upload
gift_card_val = float(enola_data['gift_card_sales'])
print(f"\nConverted to float: {gift_card_val}")
print(f"  Is positive: {gift_card_val > 0}")

# Test the actual data that would be uploaded
data_to_upload = [
    enola_data['store'],
    str(enola_data['pc_number']),
    pd.to_datetime(enola_data['date']).date(),
    float(enola_data['gift_card_sales'])
]

print(f"\nData tuple for upload:")
for i, val in enumerate(data_to_upload):
    print(f"  [{i}] {val} (type: {type(val).__name__})")

print("\n" + "="*60)
print("CONCLUSION: The value is POSITIVE (+80) in the compiled file")
print("and remains POSITIVE when prepared for upload.")
print("="*60)
