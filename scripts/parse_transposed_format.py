"""
Parse transposed format sales data and prepare for upload to Supabase

This script reads the transposed format where:
- Row 1: Dates
- Row 2: Store locations  
- Row 3+: Metrics with values for each store/date combination

It will map metrics to the appropriate database tables:
- sales_summary
- tender_type_metrics
- labor_metrics
"""

import os
import sys
import pandas as pd
import re
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Store mapping (PC number to store name)
LOC_TO_PC = {
    "301290 - 2820 Paxton St": "301290",
    "343939 - 807 E Main St": "343939",
    "357993 - 423 N Enola Rd": "357993",
    "358529 - 3929 Columbia Avenue": "358529",
    "359042 - 737 South Broad Street": "359042",
    "363271 - 1154 River Road": "363271",
    "364322 - 820 South Market Street": "364322",
}

PC_TO_STORE = {
    "301290": "Paxton",
    "343939": "MountJoy",
    "357993": "Enola",
    "358529": "Columbia",
    "359042": "Lititz",
    "363271": "Marietta",
    "364322": "Etown",
}

def normalize_location(loc_str):
    """Normalize location string to match our mapping"""
    loc_str = str(loc_str).strip()
    # Try exact match first
    if loc_str in LOC_TO_PC:
        return LOC_TO_PC[loc_str]
    # Try partial match
    for key, pc in LOC_TO_PC.items():
        if key in loc_str or loc_str in key:
            return pc
    return None

def clean_currency(value):
    """Convert currency string to float"""
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    # Remove $ and commas
    cleaned = str(value).replace('$', '').replace(',', '').strip()
    if cleaned == '' or cleaned == '-':
        return 0.0
    try:
        return float(cleaned)
    except:
        return 0.0

def parse_transposed_file(filepath):
    """
    Parse a transposed format Excel/CSV file.
    
    Returns dictionaries for each table:
    - sales_summary_data
    - tender_type_data  
    - labor_data
    """
    
    print("="*80)
    print("PARSING TRANSPOSED FORMAT FILE")
    print("="*80)
    print(f"File: {filepath}")
    print()
    
    # Read the file
    if str(filepath).endswith('.csv'):
        df = pd.read_csv(filepath, header=None)
    else:
        df = pd.read_excel(filepath, header=None)
    
    print(f"Loaded {len(df)} rows x {len(df.columns)} columns")
    
    # Row 0: Dates
    # Row 1: Locations
    # Row 2+: Metrics
    
    dates_row = df.iloc[0, 1:].tolist()  # Skip first column (metric name column)
    locations_row = df.iloc[1, 1:].tolist()
    
    # Parse dates
    dates = []
    for d in dates_row:
        if pd.isna(d):
            dates.append(None)
        else:
            try:
                if isinstance(d, str):
                    dates.append(pd.to_datetime(d).date())
                else:
                    dates.append(pd.to_datetime(d).date())
            except:
                dates.append(None)
    
    # Parse locations to PC numbers
    pc_numbers = []
    for loc in locations_row:
        pc = normalize_location(loc)
        pc_numbers.append(pc)
    
    print(f"\nFound {len([d for d in dates if d])} unique dates")
    print(f"Found {len([p for p in pc_numbers if p])} valid store locations")
    
    # Create mappings for sales_summary metrics
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
        "Cash Due": "cash_in",  # Same as Cash In
        "Paid In": "paid_in",
        "Paid Out": "paid_out",
    }
    
    # Tender type metrics mapping
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
        "Non Cash Media 3, 4000110,Clover Go": "Clover Go",
    }
    
    # Initialize data storage
    sales_summary_records = []
    tender_type_records = []
    labor_records = []
    
    # Process each metric row
    for row_idx in range(2, len(df)):
        metric_name = str(df.iloc[row_idx, 0]).strip()
        
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
                    record_key = (pc, date)
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
                
                if date and pc and value > 0:  # Only add non-zero values
                    tender_type_records.append({
                        'store': PC_TO_STORE.get(pc, ''),
                        'pc_number': pc,
                        'date': date,
                        'tender_type': tender_type,
                        'detail_amount': value
                    })
        
        # Check if it's a labor metric (contains "Total Hours" or "Total Value")
        elif "Total Hours" in metric_name or "Total Value" in metric_name:
            # Extract position name (e.g., "DD Crew Plus Total Hours" -> "DD Crew Plus")
            position = metric_name.replace(" Total Hours", "").replace(" Total Value", "").strip()
            
            for col_idx in range(1, len(df.columns)):
                date = dates[col_idx - 1] if col_idx - 1 < len(dates) else None
                pc = pc_numbers[col_idx - 1] if col_idx - 1 < len(pc_numbers) else None
                value = clean_currency(df.iloc[row_idx, col_idx])
                
                if date and pc and value > 0:
                    # Find or create labor record
                    record_key = (pc, date, position)
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
                    
                    # Determine which field to update
                    if "Total Hours" in metric_name:
                        existing_record['total_hours'] = value
                    elif "Total Value" in metric_name:
                        existing_record['total_pay'] = value
    
    print("\n" + "="*80)
    print("PARSING RESULTS")
    print("="*80)
    print(f"Sales Summary Records: {len(sales_summary_records)}")
    print(f"Tender Type Records: {len(tender_type_records)}")
    print(f"Labor Records: {len(labor_records)}")
    
    # Show samples
    if sales_summary_records:
        print("\nSample Sales Summary Record:")
        sample = sales_summary_records[0]
        for key, val in sample.items():
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


if __name__ == "__main__":
    # Example usage - you would provide the path to your file
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        print("Usage: python parse_transposed_format.py <path_to_file>")
        print("\nPlease provide the path to your transposed format Excel or CSV file.")
        sys.exit(1)
    
    # Parse the file
    data = parse_transposed_file(filepath)
    
    print("\n" + "="*80)
    print("READY FOR UPLOAD")
    print("="*80)
    print("Data has been parsed and structured for database upload.")
    print("Next steps:")
    print("1. Review the output above")
    print("2. If everything looks correct, we can create an upload script")
    print("3. Delete existing October data from Supabase")
    print("4. Upload the new formatted data")
