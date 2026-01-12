"""Extract data from DSS CSV file - Custom parser for this specific format"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import re

sys.path.insert(0, 'scripts')
from parse_transposed_format import PC_TO_STORE, clean_currency, normalize_location, LOC_TO_PC

# Update the mapping to include Eisenhower store
LOC_TO_PC["362913 - 900 Eisenhower Blvd"] = "362913"
PC_TO_STORE["362913"] = "Eisenhower"

# Sales summary metrics mapping
sales_summary_metrics = {
    "Net Sales": "net_sales",
    "Dunkin Gross Sales": "gross_sales",
    "DD Adjusted Reportable Sales": "dd_adjusted_no_markup",
    "Sales Tax": "pa_sales_tax",
    "Discounts": "dd_discount",
    "Guest Count": "guest_count",
    "Avg Sales/ Guest Count": "avg_check",
    "Gift Card Sales": "gift_card_sales",
    "Void Amount": "void_amount",
    "Refunds": "refund",
    "Void Transactions": "void_qty",
    "Cash In": "cash_in",
    "Cash Due": "cash_in",
    "Paid In": "paid_in",
    "Paid Out": "paid_out",
}

# Tender type mapping
tender_type_mapping = {
    "Non Cash Media 1, 4000061,Credit Card - Visa": "Visa",
    "Non Cash Media 1, 4000059,Credit Card - Discover": "Discover",
    "Non Cash Media 1, 4000060,Credit Card - Mastercard": "Mastercard",
    "Non Cash Media 1, 4000058,Credit Card - Amex": "Amex",
    "Non Cash Media 2, 4000065,Gift Card Redeem": "Gift Card Redeem",
    "Non Cash Media 2, 4000094,Gift Card Redeem - Kiosk": "Gift Card Redeem",
    "Non Cash Media 3, 4000107,Delivery: Doordash": "Doordash",
    "Non Cash Media 3, 4000106,Delivery: Uber Eats": "Uber Eats",
    "Non Cash Media 3, 4000098,Delivery: Grubhub": "Grub Hub",
}

def parse_dss_csv(filepath):
    """Parse DSS CSV file with custom format"""
    print("="*80)
    print("PARSING DSS CSV FILE")
    print("="*80)
    print(f"File: {Path(filepath).name}\n")
    
    # Read CSV
    df = pd.read_csv(filepath, header=None)
    print(f"Loaded {len(df)} rows x {len(df.columns)} columns\n")
    
    # Row 0: Header (can ignore)
    # Row 1: Dates (starting from column 1)
    # Row 2: Store locations (starting from column 1)
    # Row 3+: Metrics
    
    dates_row = df.iloc[1, 1:].tolist()  # Skip first column
    locations_row = df.iloc[2, 1:].tolist()  # Skip first column
    
    # Parse dates
    dates = []
    for d in dates_row:
        if pd.isna(d):
            dates.append(None)
        else:
            try:
                if isinstance(d, str):
                    # Try parsing MM/DD/YYYY format
                    dates.append(pd.to_datetime(d, format='%m/%d/%Y').date())
                else:
                    dates.append(pd.to_datetime(d).date())
            except:
                dates.append(None)
    
    # Parse locations to PC numbers
    pc_numbers = []
    for loc in locations_row:
        if pd.isna(loc):
            pc_numbers.append(None)
        else:
            pc = normalize_location(str(loc))
            pc_numbers.append(pc)
    
    print(f"Found {len([d for d in dates if d])} unique dates")
    print(f"Found {len([p for p in pc_numbers if p])} valid store locations\n")
    
    # Initialize data storage
    sales_summary_records = []
    tender_type_records = []
    labor_records = []
    
    # Process each metric row (starting from row 3, index 3)
    for row_idx in range(3, len(df)):
        metric_name = str(df.iloc[row_idx, 0]).strip()
        
        if pd.isna(df.iloc[row_idx, 0]) or metric_name == '' or metric_name == 'nan':
            continue
        
        # Check if it's a sales_summary metric
        if metric_name in sales_summary_metrics:
            db_column = sales_summary_metrics[metric_name]
            
            # Process each store/date combination
            for col_idx in range(1, len(df.columns)):
                date = dates[col_idx - 1] if col_idx - 1 < len(dates) else None
                pc = pc_numbers[col_idx - 1] if col_idx - 1 < len(pc_numbers) else None
                value = df.iloc[row_idx, col_idx]
                
                if date and pc:
                    # Find or create record for this store/date
                    existing_record = None
                    for rec in sales_summary_records:
                        if rec['pc_number'] == pc and rec['date'] == date:
                            existing_record = rec
                            break
                    
                    if not existing_record:
                        existing_record = {
                            'store': PC_TO_STORE.get(pc, ''),
                            'pc_number': pc,
                            'date': date,
                            'gross_sales': 0.0,
                            'net_sales': 0.0,
                            'dd_adjusted_no_markup': 0.0,
                            'pa_sales_tax': 0.0,
                            'dd_discount': 0.0,
                            'guest_count': 0,
                            'avg_check': 0.0,
                            'gift_card_sales': 0.0,
                            'void_amount': 0.0,
                            'refund': 0.0,
                            'void_qty': 0,
                            'cash_in': 0.0,
                            'paid_in': 0.0,
                            'paid_out': 0.0,
                        }
                        sales_summary_records.append(existing_record)
                    
                    # Update the value
                    if db_column in ['guest_count', 'void_qty']:
                        existing_record[db_column] = int(clean_currency(value))
                    else:
                        existing_record[db_column] = clean_currency(value)
        
        # Check if it's a tender type metric
        elif metric_name in tender_type_mapping:
            tender_type = tender_type_mapping[metric_name]
            
            for col_idx in range(1, len(df.columns)):
                date = dates[col_idx - 1] if col_idx - 1 < len(dates) else None
                pc = pc_numbers[col_idx - 1] if col_idx - 1 < len(pc_numbers) else None
                value = clean_currency(df.iloc[row_idx, col_idx])
                
                if date and pc and value != 0:
                    tender_type_records.append({
                        'store': PC_TO_STORE.get(pc, ''),
                        'pc_number': pc,
                        'date': date,
                        'tender_type': tender_type,
                        'detail_amount': value
                    })
        
        # Check for tender types that might match patterns
        elif 'Credit Card' in metric_name or 'Gift Card' in metric_name or 'Delivery:' in metric_name:
            # Try to match tender type patterns
            tender_type = None
            if 'Visa' in metric_name:
                tender_type = 'Visa'
            elif 'Mastercard' in metric_name or 'Master Card' in metric_name:
                tender_type = 'Mastercard'
            elif 'Discover' in metric_name:
                tender_type = 'Discover'
            elif 'Amex' in metric_name or 'American Express' in metric_name:
                tender_type = 'Amex'
            elif 'Gift Card Redeem' in metric_name:
                tender_type = 'Gift Card Redeem'
            elif 'Doordash' in metric_name or 'Door Dash' in metric_name:
                tender_type = 'Doordash'
            elif 'Uber Eats' in metric_name:
                tender_type = 'Uber Eats'
            elif 'Grubhub' in metric_name or 'Grub Hub' in metric_name:
                tender_type = 'Grub Hub'
            
            if tender_type:
                for col_idx in range(1, len(df.columns)):
                    date = dates[col_idx - 1] if col_idx - 1 < len(dates) else None
                    pc = pc_numbers[col_idx - 1] if col_idx - 1 < len(pc_numbers) else None
                    value = clean_currency(df.iloc[row_idx, col_idx])
                    
                    if date and pc and value != 0:
                        tender_type_records.append({
                            'store': PC_TO_STORE.get(pc, ''),
                            'pc_number': pc,
                            'date': date,
                            'tender_type': tender_type,
                            'detail_amount': value
                        })
        
        # Check if it's a labor metric
        elif "Total Hours" in metric_name or "Total Value" in metric_name:
            position = metric_name.replace(" Total Hours", "").replace(" Total Value", "").strip()
            
            for col_idx in range(1, len(df.columns)):
                date = dates[col_idx - 1] if col_idx - 1 < len(dates) else None
                pc = pc_numbers[col_idx - 1] if col_idx - 1 < len(pc_numbers) else None
                value = clean_currency(df.iloc[row_idx, col_idx])
                
                if date and pc and value > 0:
                    existing_record = None
                    for rec in labor_records:
                        if (rec['pc_number'] == pc and rec['date'] == date and 
                            rec['labor_position'] == position):
                            existing_record = rec
                            break
                    
                    if not existing_record:
                        existing_record = {
                            'store': PC_TO_STORE.get(pc, ''),
                            'pc_number': pc,
                            'date': date,
                            'labor_position': position,
                            'reg_hours': 0.0,
                            'ot_hours': 0.0,
                            'total_hours': 0.0,
                            'reg_pay': 0.0,
                            'ot_pay': 0.0,
                            'total_pay': 0.0,
                            'percent_labor': 0.0,
                        }
                        labor_records.append(existing_record)
                    
                    if "Total Hours" in metric_name:
                        existing_record['total_hours'] = value
                    elif "Total Value" in metric_name:
                        existing_record['total_pay'] = value
    
    print("="*80)
    print("PARSING RESULTS")
    print("="*80)
    print(f"Sales Summary Records: {len(sales_summary_records)}")
    print(f"Tender Type Records: {len(tender_type_records)}")
    print(f"Labor Records: {len(labor_records)}")
    
    if sales_summary_records:
        print("\nSample Sales Summary Record:")
        sample = sales_summary_records[0]
        for key, val in list(sample.items())[:5]:
            print(f"  {key}: {val}")
    
    if tender_type_records:
        print("\nSample Tender Type Records:")
        for rec in tender_type_records[:3]:
            print(f"  {rec['date']} | {rec['store']:10} | {rec['tender_type']:20} | ${rec['detail_amount']:,.2f}")
    
    return {
        'sales_summary': sales_summary_records,
        'tender_type_metrics': tender_type_records,
        'labor_metrics': labor_records
    }

# Main execution
if __name__ == "__main__":
    # Find the file
    downloads = Path(r"C:\Users\dunki\Downloads")
    files = list(downloads.glob("*DSS*.csv"))
    
    if not files:
        print("ERROR: No DSS CSV file found!")
        sys.exit(1)
    
    csv_file = str(files[0])
    print(f"Processing: {csv_file}\n")
    
    # Process the file
    data = parse_dss_csv(csv_file)
    
    print(f"\n{'='*60}")
    print("EXTRACTION RESULTS")
    print(f"{'='*60}")
    print(f"Sales Summary Records: {len(data['sales_summary'])}")
    print(f"Tender Type Records: {len(data['tender_type_metrics'])}")
    print(f"Labor Records: {len(data['labor_metrics'])}")
    
    # Save to exports
    exports_dir = Path('exports')
    exports_dir.mkdir(exist_ok=True)
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    
    if data['sales_summary']:
        df = pd.DataFrame(data['sales_summary'])
        out_file = exports_dir / f'sales_summary_dec2025_{timestamp}.xlsx'
        df.to_excel(out_file, index=False)
        print(f"\n[OK] Sales Summary saved: {out_file}")
        print(f"   Records: {len(df)}")
    
    if data['tender_type_metrics']:
        df = pd.DataFrame(data['tender_type_metrics'])
        out_file = exports_dir / f'tender_type_dec2025_{timestamp}.xlsx'
        df.to_excel(out_file, index=False)
        print(f"[OK] Tender Type Metrics saved: {out_file}")
        print(f"   Records: {len(df)}")
    
    if data['labor_metrics']:
        df = pd.DataFrame(data['labor_metrics'])
        out_file = exports_dir / f'labor_metrics_dec2025_{timestamp}.xlsx'
        df.to_excel(out_file, index=False)
        print(f"[OK] Labor Metrics saved: {out_file}")
        print(f"   Records: {len(df)}")
    
    print(f"\n{'='*60}")
    print("EXTRACTION COMPLETE!")
    print(f"{'='*60}")
