"""
Check what value gets passed to the upload function
"""
import pandas as pd
from pathlib import Path

compiled_dir = Path(r"C:\Projects\Dunkin-sales-summary\data\compiled")
files = list(compiled_dir.glob("*20251101*Sales Mix Detail*.xlsx"))

if files:
    print(f"Checking compiled file: {files[0].name}\n")
    df = pd.read_excel(files[0])
    
    enola_row = df[df['store'] == 'Enola']
    
    if not enola_row.empty:
        print("Enola data from compiled file:")
        print(f"  store: {enola_row['store'].values[0]}")
        print(f"  date: {enola_row['date'].values[0]}")
        print(f"  gift_card_sales: {enola_row['gift_card_sales'].values[0]}")
        print(f"  gift_card_sales type: {type(enola_row['gift_card_sales'].values[0])}")
        
        # Check if it's a proper float
        val = enola_row['gift_card_sales'].values[0]
        if pd.notna(val):
            print(f"  As float: {float(val)}")
            print(f"  Is positive: {float(val) > 0}")
