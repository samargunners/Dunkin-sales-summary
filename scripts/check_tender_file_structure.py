"""
Quick check of tender type file structure
"""
import pandas as pd
import glob
import os

# Get the first tender file
files = glob.glob('data/tender_downloads/*.xlsx')
if files:
    print(f"Found {len(files)} files")
    print(f"\nChecking first file: {os.path.basename(files[0])}")
    
    try:
        # Read with header=None to see raw structure
        df_raw = pd.read_excel(files[0], header=None)
        print(f"\n=== RAW DATA (no headers) ===")
        print(f"Shape: {df_raw.shape}")
        print(df_raw.head(15))
        
        print(f"\n=== WITH DEFAULT HEADERS ===")
        df = pd.read_excel(files[0])
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(df.head(15))
        
        print(f"\n=== TRYING header=1 (skip first row) ===")
        df2 = pd.read_excel(files[0], header=1)
        print(f"Shape: {df2.shape}")
        print(f"Columns: {list(df2.columns)}")
        print(df2.head(15))
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("No files found")
