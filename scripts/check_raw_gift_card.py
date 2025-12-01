import pandas as pd
from pathlib import Path

raw_dir = Path(r"C:\Projects\Dunkin-sales-summary\data\raw_emails")
files = list(raw_dir.glob("*Sales Mix Detail*2025-11-01*.xlsx"))

if files:
    print(f"Checking: {files[0].name}\n")
    df = pd.read_excel(files[0], header=None)
    
    print("Searching for 'Gift Card' rows:")
    print("=" * 80)
    for i in range(len(df)):
        val = str(df.iloc[i, 0]).lower()
        if 'gift' in val:
            print(f"\nRow {i}: {df.iloc[i, 0]}")
            print(f"  Enola column value: {df.iloc[i, 3]}")  # Enola is typically column 3
            print(f"  All store values: {list(df.iloc[i, 1:8])}")
else:
    print("No Sales Mix Detail file found for 2025-11-01")
