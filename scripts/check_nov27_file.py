"""
Manually compile and upload Nov 27 tender data
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from dashboard.utils.supabase_db import get_supabase_connection

# Read the raw Nov 27 tender file
raw_file = Path(r"C:\Projects\Dunkin-sales-summary\data\raw_emails\20251127_Consolidated Dunkin Sales Summary_Tender Type2025-11-27 to 2025-11-27_20251128T0901.xlsx")

if not raw_file.exists():
    print(f"❌ File not found: {raw_file}")
    sys.exit(1)

print(f"Reading: {raw_file.name}\n")

# The tender files need to be processed similar to compile_store_reports.py
# For now, let's check if it has the right structure
df = pd.read_excel(raw_file, header=None)
print(f"File shape: {df.shape}")
print("\nFirst few rows:")
print(df.iloc[:10, :5].to_string())

# Check if this is already in the right format or needs processing
print("\n\n❌ The Nov 27 raw file needs to be compiled first.")
print("   Run: python scripts\\compile_store_reports.py")
print("   This will process all raw files including Nov 27")
