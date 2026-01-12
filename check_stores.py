"""Check stores in the reports"""
import pandas as pd
from pathlib import Path

# Check consolidated report
print("="*60)
print("CONSOLIDATED REPORT STORES")
print("="*60)
df_report = pd.read_excel('exports/tender_sales_report_20251201_to_20251231_20260107_094346.xlsx')
stores_report = sorted(df_report['Store'].unique())
print(f"\nStores in consolidated report ({len(stores_report)}):")
for i, store in enumerate(stores_report, 1):
    count = len(df_report[df_report['Store'] == store])
    print(f"  {i}. {store} ({count} records)")

# Check extracted sales summary
print("\n" + "="*60)
print("EXTRACTED SALES SUMMARY STORES")
print("="*60)
df_sales = pd.read_excel('exports/sales_summary_dec2025_20260107_094039.xlsx')
stores_sales = sorted(df_sales['store'].unique())
print(f"\nStores in extracted sales summary ({len(stores_sales)}):")
for i, store in enumerate(stores_sales, 1):
    count = len(df_sales[df_sales['store'] == store])
    print(f"  {i}. {store} ({count} records)")

# Check what stores should be there
print("\n" + "="*60)
print("EXPECTED STORES (from PC_TO_STORE mapping)")
print("="*60)
import sys
sys.path.insert(0, 'scripts')
from parse_transposed_format import PC_TO_STORE
expected_stores = sorted(PC_TO_STORE.values())
print(f"\nExpected stores ({len(expected_stores)}):")
for i, store in enumerate(expected_stores, 1):
    print(f"  {i}. {store}")

# Check for missing stores
print("\n" + "="*60)
print("MISSING STORES")
print("="*60)
missing = set(expected_stores) - set(stores_report)
if missing:
    print(f"\nMissing from report ({len(missing)}):")
    for store in sorted(missing):
        print(f"  - {store}")
else:
    print("\nAll expected stores are present in the report!")

# Check the original CSV for all store locations
print("\n" + "="*60)
print("CHECKING ORIGINAL CSV FOR ALL STORES")
print("="*60)
from pathlib import Path
import pandas as pd

csv_file = list(Path(r"C:\Users\dunki\Downloads").glob("*DSS*.csv"))[0]
df_csv = pd.read_csv(csv_file, header=None)

# Row 2 has store locations
locations_row = df_csv.iloc[2, 1:].tolist()
unique_locations = sorted(set([str(loc).strip() for loc in locations_row if pd.notna(loc) and str(loc).strip() != '']))

print(f"\nUnique store locations in CSV ({len(unique_locations)}):")
for i, loc in enumerate(unique_locations, 1):
    print(f"  {i}. {loc}")

