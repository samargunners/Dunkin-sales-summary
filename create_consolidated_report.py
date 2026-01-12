"""
Create consolidated tender sales report from extracted DSS CSV data
Formats data to match the standard tender sales report format
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def create_consolidated_report(sales_summary_file, tender_type_file, output_file=None):
    """
    Create consolidated report from extracted DSS data
    
    Args:
        sales_summary_file: Path to sales_summary Excel file
        tender_type_file: Path to tender_type_metrics Excel file
        output_file: Optional output file path
    """
    
    print("="*80)
    print("CREATING CONSOLIDATED TENDER SALES REPORT")
    print("="*80)
    print()
    
    # Read the extracted data
    print(f"Reading sales summary: {Path(sales_summary_file).name}")
    df_sales = pd.read_excel(sales_summary_file)
    print(f"  Records: {len(df_sales)}")
    
    print(f"\nReading tender type metrics: {Path(tender_type_file).name}")
    df_tender = pd.read_excel(tender_type_file)
    print(f"  Records: {len(df_tender)}")
    
    # Convert date columns to datetime
    df_sales['date'] = pd.to_datetime(df_sales['date']).dt.date
    df_tender['date'] = pd.to_datetime(df_tender['date']).dt.date
    
    # Pivot tender type data to wide format
    print("\nProcessing tender type data...")
    
    # Normalize tender type names to match expected format
    tender_mapping = {
        'Visa': 'Visa',
        'Mastercard': 'Mastercard',
        'Discover': 'Discover',
        'Amex': 'Amex',
        'Gift Card Redeem': 'Gift Card Redeem',
        'Uber Eats': 'Uber Eats',
        'Doordash': 'Door Dash',
        'Door Dash': 'Door Dash',
        'Grub Hub': 'Grubhub',
        'Grubhub': 'Grubhub',
    }
    
    df_tender['tender_type_clean'] = df_tender['tender_type'].map(tender_mapping).fillna(df_tender['tender_type'])
    
    # Pivot tender data
    tender_pivot = df_tender.pivot_table(
        index=['store', 'date'],
        columns='tender_type_clean',
        values='detail_amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # Merge sales summary with tender data
    print("Merging data...")
    df_merged = df_sales.merge(
        tender_pivot,
        on=['store', 'date'],
        how='left'
    )
    
    # Create the consolidated report with exact column format
    print("Formatting report...")
    
    # Get day of week
    df_merged['date_dt'] = pd.to_datetime(df_merged['date'])
    df_merged['day'] = df_merged['date_dt'].dt.strftime('%a')
    df_merged['Date'] = df_merged['date_dt'].dt.strftime('%m/%d/%y')
    
    # Build the final report dataframe
    report_df = pd.DataFrame({
        'Store': df_merged['store'],
        'Date': df_merged['Date'],
        'day': df_merged['day'],
        'Dunkin Net Sales': df_merged.get('dd_adjusted_no_markup', 0).fillna(0),
        'Tax': df_merged.get('pa_sales_tax', 0).fillna(0),
        'Gift Card Sales': df_merged.get('gift_card_sales', 0).fillna(0).abs(),
        'Total': (
            df_merged.get('dd_adjusted_no_markup', 0).fillna(0) +
            df_merged.get('pa_sales_tax', 0).fillna(0) +
            df_merged.get('gift_card_sales', 0).fillna(0).abs()
        ),
        'Cash Due': df_merged.get('cash_in', 0).fillna(0),
        'Mastercard': df_merged.get('Mastercard', 0).fillna(0),
        'Visa': df_merged.get('Visa', 0).fillna(0),
        'Discover': df_merged.get('Discover', 0).fillna(0),
        'Amex': df_merged.get('Amex', 0).fillna(0),
        'Gift Card Redeem': df_merged.get('Gift Card Redeem', 0).fillna(0),
        'Uber Eats': df_merged.get('Uber Eats', 0).fillna(0),
        'Door Dash': df_merged.get('Door Dash', 0).fillna(0),
        'Grubhub': df_merged.get('Grubhub', 0).fillna(0),
        'Paid Out': df_merged.get('paid_out', 0).fillna(0),
    })
    
    # Sort by Store and Date
    report_df = report_df.sort_values(['Store', 'Date']).reset_index(drop=True)
    
    # Generate output filename if not provided
    if output_file is None:
        exports_dir = Path('exports')
        exports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Get date range from data
        min_date = df_merged['date'].min()
        max_date = df_merged['date'].max()
        date_range = f"{min_date.strftime('%Y%m%d')}_to_{max_date.strftime('%Y%m%d')}"
        
        output_file = exports_dir / f'tender_sales_report_{date_range}_{timestamp}.xlsx'
    
    # Save to Excel
    print(f"\nSaving report to: {output_file}")
    report_df.to_excel(output_file, index=False, sheet_name='Tender Sales Report')
    
    print(f"\n{'='*80}")
    print("REPORT GENERATED SUCCESSFULLY!")
    print(f"{'='*80}")
    print(f"Total rows: {len(report_df)}")
    print(f"Stores: {report_df['Store'].nunique()}")
    print(f"Date range: {report_df['Date'].min()} to {report_df['Date'].max()}")
    print(f"\nFile saved to: {output_file}")
    
    # Display summary statistics
    print("\n--- Summary Statistics ---")
    print(f"Total Dunkin Net Sales: ${report_df['Dunkin Net Sales'].sum():,.2f}")
    print(f"Total Tax: ${report_df['Tax'].sum():,.2f}")
    print(f"Total Gift Card Sales: ${report_df['Gift Card Sales'].sum():,.2f}")
    print(f"Total: ${report_df['Total'].sum():,.2f}")
    print(f"Total Cash Due: ${report_df['Cash Due'].sum():,.2f}")
    print(f"Total Mastercard: ${report_df['Mastercard'].sum():,.2f}")
    print(f"Total Visa: ${report_df['Visa'].sum():,.2f}")
    print(f"Total Discover: ${report_df['Discover'].sum():,.2f}")
    print(f"Total Amex: ${report_df['Amex'].sum():,.2f}")
    print(f"Total Gift Card Redeem: ${report_df['Gift Card Redeem'].sum():,.2f}")
    print(f"Total Uber Eats: ${report_df['Uber Eats'].sum():,.2f}")
    print(f"Total Door Dash: ${report_df['Door Dash'].sum():,.2f}")
    print(f"Total Grubhub: ${report_df['Grubhub'].sum():,.2f}")
    print(f"Total Paid Out: ${report_df['Paid Out'].sum():,.2f}")
    
    return output_file


if __name__ == "__main__":
    # Find the most recent extracted files
    exports_dir = Path('exports')
    
    # Look for the most recent dec2025 files
    sales_files = sorted(exports_dir.glob('sales_summary_dec2025_*.xlsx'), reverse=True)
    tender_files = sorted(exports_dir.glob('tender_type_dec2025_*.xlsx'), reverse=True)
    
    if not sales_files or not tender_files:
        print("ERROR: Could not find extracted DSS data files.")
        print("Please run extract_dss_data.py first to extract the data.")
        exit(1)
    
    sales_file = sales_files[0]
    tender_file = tender_files[0]
    
    print(f"Using files:")
    print(f"  Sales Summary: {sales_file.name}")
    print(f"  Tender Type: {tender_file.name}")
    print()
    
    # Create the consolidated report
    output_file = create_consolidated_report(sales_file, tender_file)
    
    print(f"\n{'='*80}")
    print("CONSOLIDATED REPORT CREATED!")
    print(f"{'='*80}")

