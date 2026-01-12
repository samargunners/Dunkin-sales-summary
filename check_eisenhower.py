"""Check if Eisenhower store is in the CSV"""
import pandas as pd
from pathlib import Path

csv_file = list(Path(r"C:\Users\dunki\Downloads").glob("*DSS*.csv"))[0]
df = pd.read_csv(csv_file, header=None)

# Row 2 has store locations
locations = df.iloc[2, 1:].tolist()

# Find Eisenhower columns
eisenhower_cols = []
for i, loc in enumerate(locations):
    loc_str = str(loc)
    if '362913' in loc_str or 'Eisenhower' in loc_str:
        eisenhower_cols.append((i, loc_str))

print(f"Eisenhower store found in {len(eisenhower_cols)} columns")
print(f"\nSample locations:")
for idx, loc in eisenhower_cols[:10]:
    print(f"  Col {idx}: {loc}")

# Check if there's data for Eisenhower (check a few metric rows)
print(f"\nChecking for data in Eisenhower columns...")
if eisenhower_cols:
    sample_col = eisenhower_cols[0][0] + 1  # +1 because we skipped first column
    print(f"Sample column index: {sample_col}")
    print(f"Date for this column: {df.iloc[1, sample_col]}")
    print(f"Net Sales value: {df.iloc[3, sample_col]}")  # Row 3 is Net Sales
else:
    print("No Eisenhower columns found!")

