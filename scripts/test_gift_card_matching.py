import pandas as pd
from pathlib import Path

# Simulate the parsing logic
metric_mapping = {
    "net sales": "net_sales",
    "dunkin gross sales": "gross_sales", 
    "dd adjusted reportable sales": "dd_adjusted_no_markup",
    "sales tax": "pa_sales_tax",
    "discounts": "dd_discount",
    "guest count": "guest_count",
    "avg check": "avg_check",
    "gift card sales": "gift_card_sales",
    "void amount": "void_amount",
    "refunds": "refund",
    "void transactions": "void_qty",
    "cash in": "cash_in",
    "paid in": "paid_in",
    "paid out": "paid_out"
}

raw_dir = Path(r"C:\Projects\Dunkin-sales-summary\data\raw_emails")
files = list(raw_dir.glob("*Sales Mix Detail*2025-11-01*.xlsx"))

if files:
    df = pd.read_excel(files[0], header=None)
    
    print("Testing metric matching for gift card rows:\n")
    print("="*80)
    
    # Check rows that contain 'gift'
    for row_idx in range(len(df)):
        metric_name = str(df.iloc[row_idx, 0]).strip().lower()
        
        if 'gift' in metric_name:
            print(f"\nRow {row_idx}: '{df.iloc[row_idx, 0]}'")
            print(f"  Normalized: '{metric_name}'")
            
            # Check if it matches
            db_column = None
            for file_metric, db_col in metric_mapping.items():
                if metric_name.startswith(file_metric):
                    db_column = db_col
                    print(f"  ✓ MATCHES '{file_metric}' -> {db_col}")
                    break
            
            if not db_column:
                print(f"  ✗ NO MATCH")
            
            # Show Enola's value (column 3)
            enola_value = df.iloc[row_idx, 3]
            print(f"  Enola value: {enola_value}")
