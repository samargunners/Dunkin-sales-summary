"""
Download Tender & Sales Report for September 2025

This script executes a SQL query that combines sales summary data with tender type metrics,
categorizes tender types, and exports the results to a CSV file.
"""

import os
import sys
from datetime import datetime
import pandas as pd

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection


def download_tender_sales_report(start_date, end_date):
    """Execute SQL query and download tender sales report."""
    
    sql_query = f"""
    WITH tender_normalized AS (
      SELECT
        TRIM(LOWER(t.store)) AS store_norm,
        DATE(t.date) AS date_norm,
        CASE
          -- Normalize Gift Card variations
          WHEN LOWER(t.tender_type) IN ('gc redeem', 'gift card redeem', 'gift card redeem offline') 
            THEN 'Gift Card Redeem'
          -- Normalize Visa variations
          WHEN LOWER(t.tender_type) IN ('visa', 'visa - kiosk', 'visa-kiosk') 
            THEN 'Visa'
          -- Normalize Mastercard variations
          WHEN LOWER(t.tender_type) IN ('mastercard', 'mastercard - kiosk') 
            THEN 'Mastercard'
          -- Standardize others
          WHEN LOWER(t.tender_type) = 'amex' THEN 'Amex'
          WHEN LOWER(t.tender_type) = 'discover' THEN 'Discover'
          WHEN LOWER(t.tender_type) = 'doordash' THEN 'Doordash'
          WHEN LOWER(t.tender_type) = 'grub hub' THEN 'Grub Hub'
          WHEN LOWER(t.tender_type) = 'uber eats' THEN 'Uber Eats'
          ELSE t.tender_type
        END AS tender_type_clean,
        t.detail_amount
      FROM tender_type_metrics t
      WHERE t.date BETWEEN '{start_date}' AND '{end_date}'
    ),
    tender_aggregated AS (
      SELECT
        store_norm,
        date_norm,
        tender_type_clean,
        SUM(detail_amount) AS total_amount
      FROM tender_normalized
      GROUP BY store_norm, date_norm, tender_type_clean
    )
    SELECT
      s.store AS "Store",
      s.date  AS "Date",
      s.dd_adjusted_no_markup AS "Dunkin Net Sales",
      s.cash_in              AS "Cash Due",
      s.gift_card_sales      AS "Gift Card Sales",
      s.pa_sales_tax         AS "Tax",
      s.paid_out             AS "Paid Out",

      -- Tender values (aggregated and normalized)
      COALESCE(gc.total_amount, 0) AS "Gift Card Redeem",
      COALESCE(ue.total_amount, 0) AS "Uber Eats",
      COALESCE(dd.total_amount, 0) AS "Door Dash",
      COALESCE(gh.total_amount, 0) AS "Grubhub",
      COALESCE(vi.total_amount, 0) AS "Visa",
      COALESCE(mc.total_amount, 0) AS "Mastercard",
      COALESCE(ax.total_amount, 0) AS "Amex",
      COALESCE(di.total_amount, 0) AS "Discover"

    FROM sales_summary s
    LEFT JOIN tender_aggregated gc ON TRIM(LOWER(s.store)) = gc.store_norm AND DATE(s.date) = gc.date_norm AND gc.tender_type_clean = 'Gift Card Redeem'
    LEFT JOIN tender_aggregated ue ON TRIM(LOWER(s.store)) = ue.store_norm AND DATE(s.date) = ue.date_norm AND ue.tender_type_clean = 'Uber Eats'
    LEFT JOIN tender_aggregated dd ON TRIM(LOWER(s.store)) = dd.store_norm AND DATE(s.date) = dd.date_norm AND dd.tender_type_clean = 'Doordash'
    LEFT JOIN tender_aggregated gh ON TRIM(LOWER(s.store)) = gh.store_norm AND DATE(s.date) = gh.date_norm AND gh.tender_type_clean = 'Grub Hub'
    LEFT JOIN tender_aggregated vi ON TRIM(LOWER(s.store)) = vi.store_norm AND DATE(s.date) = vi.date_norm AND vi.tender_type_clean = 'Visa'
    LEFT JOIN tender_aggregated mc ON TRIM(LOWER(s.store)) = mc.store_norm AND DATE(s.date) = mc.date_norm AND mc.tender_type_clean = 'Mastercard'
    LEFT JOIN tender_aggregated ax ON TRIM(LOWER(s.store)) = ax.store_norm AND DATE(s.date) = ax.date_norm AND ax.tender_type_clean = 'Amex'
    LEFT JOIN tender_aggregated di ON TRIM(LOWER(s.store)) = di.store_norm AND DATE(s.date) = di.date_norm AND di.tender_type_clean = 'Discover'
    WHERE s.date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY s.store, s.date;
    """
    
    try:
        print("Connecting to Supabase...")
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        print("Executing SQL query...")
        cursor.execute(sql_query)
        
        # Fetch all results
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        
        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=column_names)
        
        # Close cursor and connection
        cursor.close()
        conn.close()
        
        if len(df) > 0:
            # Create exports directory if it doesn't exist
            exports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
            os.makedirs(exports_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            date_range_str = f"{start_date.replace('-', '')}_to_{end_date.replace('-', '')}"
            output_file = os.path.join(exports_dir, f'tender_sales_report_{date_range_str}_{timestamp}.xlsx')
            
            # Save to Excel
            df.to_excel(output_file, index=False, sheet_name='Tender Sales Report')
            
            print(f"\n✓ Report generated successfully!")
            print(f"✓ Total rows: {len(df)}")
            print(f"✓ File saved to: {output_file}")
            
            # Display summary statistics
            print("\n--- Summary Statistics ---")
            print(f"Stores included: {df['Store'].nunique()}")
            print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
            print(f"Total Dunkin Net Sales: ${df['Dunkin Net Sales'].sum():,.2f}")
            print(f"Total Gift Card Redeem: ${df['Gift Card Redeem'].sum():,.2f}")
            print(f"Total Uber Eats: ${df['Uber Eats'].sum():,.2f}")
            print(f"Total Door Dash: ${df['Door Dash'].sum():,.2f}")
            print(f"Total Grubhub: ${df['Grubhub'].sum():,.2f}")
            print(f"Total Visa: ${df['Visa'].sum():,.2f}")
            print(f"Total Mastercard: ${df['Mastercard'].sum():,.2f}")
            print(f"Total Amex: ${df['Amex'].sum():,.2f}")
            print(f"Total Discover: ${df['Discover'].sum():,.2f}")
            
            return output_file
        else:
            print("No data returned from query.")
            return None
            
    except Exception as e:
        print(f"Error executing query: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("Tender & Sales Report Generator")
    print("=" * 60)
    print()
    
    # Prompt user for date range
    print("Enter the date range for the report:")
    start_date = input("Start date (YYYY-MM-DD): ").strip()
    end_date = input("End date (YYYY-MM-DD): ").strip()
    
    # Validate date format
    try:
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        print("\n❌ Invalid date format. Please use YYYY-MM-DD format.")
        sys.exit(1)
    
    print()
    print(f"Generating report for: {start_date} to {end_date}")
    print()
    
    output_file = download_tender_sales_report(start_date, end_date)
    
    if output_file:
        print("\n" + "=" * 60)
        print("Report generation complete!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Report generation failed.")
        print("=" * 60)
        sys.exit(1)
