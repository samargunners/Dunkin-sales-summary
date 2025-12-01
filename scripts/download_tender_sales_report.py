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
    WITH tender_labeled AS (
      SELECT
        t.store,
        t.date,
        t.detail_amount,
        CASE
          WHEN t.tender_type ILIKE '%gift%card%redeem%' THEN 'gift_card_redeem'
          WHEN t.tender_type ILIKE '%uber%eats%' THEN 'uber_eats'
          WHEN t.tender_type ILIKE '%door%dash%' THEN 'door_dash'
          WHEN t.tender_type ILIKE '%grub%hub%' THEN 'grubhub'
          WHEN t.tender_type ILIKE '%visa%' THEN 'visa'
          WHEN t.tender_type ILIKE '%american express%' OR t.tender_type ILIKE '%amex%' THEN 'amex'
          WHEN t.tender_type ILIKE '%discover%' THEN 'discover'
          WHEN t.tender_type ILIKE '%mastercard%' OR t.tender_type ILIKE '%master card%' THEN 'mastercard'
          ELSE NULL
        END AS tcat,
        ROW_NUMBER() OVER (
          PARTITION BY t.store, t.date,
                       CASE
                         WHEN t.tender_type ILIKE '%gift%card%redeem%' THEN 'gift_card_redeem'
                         WHEN t.tender_type ILIKE '%uber%eats%' THEN 'uber_eats'
                         WHEN t.tender_type ILIKE '%door%dash%' THEN 'door_dash'
                         WHEN t.tender_type ILIKE '%grub%hub%' THEN 'grubhub'
                         WHEN t.tender_type ILIKE '%visa%' THEN 'visa'
                         WHEN t.tender_type ILIKE '%american express%' OR t.tender_type ILIKE '%amex%' THEN 'amex'
                         WHEN t.tender_type ILIKE '%discover%' THEN 'discover'
                         WHEN t.tender_type ILIKE '%mastercard%' OR t.tender_type ILIKE '%master card%' THEN 'mastercard'
                         ELSE NULL
                       END
          ORDER BY t.id
        ) AS rn
      FROM tender_type_metrics t
      WHERE t.date BETWEEN '{start_date}' AND '{end_date}'
    ),
    tender_clean AS (
      SELECT store, date, tcat, detail_amount
      FROM tender_labeled
      WHERE tcat IS NOT NULL AND rn = 1
    )
    SELECT
      s.store AS "Store",
      TO_CHAR(s.date, 'MM/DD/YY') AS "Date",
      s.dd_adjusted_no_markup AS "Dunkin Net Sales",
      s.cash_in AS "Cash Due",
      ABS(s.gift_card_sales) AS "Gift Card Sales",
      s.pa_sales_tax AS "Tax",
      s.paid_out AS "Paid Out",
      COALESCE(gc.detail_amount, 0) AS "Gift Card Redeem",
      COALESCE(ue.detail_amount, 0) AS "Uber Eats",
      COALESCE(dd.detail_amount, 0) AS "Door Dash",
      COALESCE(gh.detail_amount, 0) AS "Grubhub",
      COALESCE(vi.detail_amount, 0) AS "Visa",
      COALESCE(ma.detail_amount, 0) AS "Mastercard",
      COALESCE(di.detail_amount, 0) AS "Discover",
      COALESCE(ax.detail_amount, 0) AS "Amex"
    FROM sales_summary s
    LEFT JOIN tender_clean gc ON gc.store = s.store AND gc.date = s.date AND gc.tcat = 'gift_card_redeem'
    LEFT JOIN tender_clean ue ON ue.store = s.store AND ue.date = s.date AND ue.tcat = 'uber_eats'
    LEFT JOIN tender_clean dd ON dd.store = s.store AND dd.date = s.date AND dd.tcat = 'door_dash'
    LEFT JOIN tender_clean gh ON gh.store = s.store AND gh.date = s.date AND gh.tcat = 'grubhub'
    LEFT JOIN tender_clean vi ON vi.store = s.store AND vi.date = s.date AND vi.tcat = 'visa'
    LEFT JOIN tender_clean ma ON ma.store = s.store AND ma.date = s.date AND ma.tcat = 'mastercard'
    LEFT JOIN tender_clean ax ON ax.store = s.store AND ax.date = s.date AND ax.tcat = 'amex'
    LEFT JOIN tender_clean di ON di.store = s.store AND di.date = s.date AND di.tcat = 'discover'
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
