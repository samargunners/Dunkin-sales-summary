"""
Check Gift Card Redeem data for October 18-31, 2025
"""

import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection


def check_gc_redeem_data():
    """Check Gift Card Redeem data for October 18-31."""
    
    try:
        print("Connecting to Supabase...")
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        # Check all tender types for Oct 18-31 to see what we have
        print("\n" + "="*80)
        print("ALL TENDER TYPE DATA - October 18-31, 2025")
        print("="*80)
        cursor.execute("""
            SELECT date, store, tender_type, detail_amount
            FROM tender_type_metrics
            WHERE date BETWEEN '2025-10-18' AND '2025-10-31'
            AND tender_type ILIKE '%gift%'
            ORDER BY date, store, tender_type
        """)
        
        gc_rows = cursor.fetchall()
        
        if gc_rows:
            print(f"Found {len(gc_rows)} Gift Card related records:")
            for row in gc_rows:
                print(f"  {row[0]} | {row[1]:12} | {row[2]:30} | ${row[3]:,.2f}")
        else:
            print("❌ No Gift Card related records found")
        
        # Check what tender types exist for those dates
        print("\n" + "="*80)
        print("DISTINCT TENDER TYPES - October 18-31, 2025")
        print("="*80)
        cursor.execute("""
            SELECT DISTINCT tender_type, COUNT(*) as count
            FROM tender_type_metrics
            WHERE date BETWEEN '2025-10-18' AND '2025-10-31'
            GROUP BY tender_type
            ORDER BY tender_type
        """)
        
        tender_types = cursor.fetchall()
        print(f"Found {len(tender_types)} distinct tender types:")
        for row in tender_types:
            print(f"  {row[0]:30} : {row[1]:3} records")
        
        # Check the report query results for those dates
        print("\n" + "="*80)
        print("REPORT QUERY RESULTS - Sample dates (Oct 18, 25, 31)")
        print("="*80)
        
        for test_date in ['2025-10-18', '2025-10-25', '2025-10-31']:
            cursor.execute("""
                WITH tender_labeled AS (
                  SELECT
                    t.store,
                    t.date,
                    t.detail_amount,
                    CASE
                      WHEN t.tender_type ILIKE 'GC Redeem' THEN 'gift_card_redeem'
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
                                     WHEN t.tender_type ILIKE 'GC Redeem' THEN 'gift_card_redeem'
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
                  WHERE t.date = %s
                ),
                tender_clean AS (
                  SELECT store, date, tcat, detail_amount
                  FROM tender_labeled
                  WHERE tcat IS NOT NULL AND rn = 1
                )
                SELECT s.store, s.date, COALESCE(gc.detail_amount, 0) AS gift_card_redeem
                FROM sales_summary s
                LEFT JOIN tender_clean gc ON gc.store = s.store AND gc.date = s.date AND gc.tcat = 'gift_card_redeem'
                WHERE s.date = %s
                ORDER BY s.store
            """, (test_date, test_date))
            
            results = cursor.fetchall()
            print(f"\n{test_date}:")
            if results:
                for row in results:
                    print(f"  {row[0]:12} | GC Redeem: ${row[2]:,.2f}")
            else:
                print("  No data")
        
        # Check raw tender_type values that contain 'gift'
        print("\n" + "="*80)
        print("EXACT TENDER_TYPE VALUES containing 'gift' - Oct 18-31")
        print("="*80)
        cursor.execute("""
            SELECT DISTINCT tender_type, date, COUNT(*) as cnt
            FROM tender_type_metrics
            WHERE date BETWEEN '2025-10-18' AND '2025-10-31'
            AND tender_type ILIKE '%gift%'
            GROUP BY tender_type, date
            ORDER BY date, tender_type
        """)
        
        gift_types = cursor.fetchall()
        if gift_types:
            print(f"Found {len(gift_types)} date/type combinations:")
            for row in gift_types:
                print(f"  {row[1]} | '{row[0]}' : {row[2]} records")
        else:
            print("❌ No tender types containing 'gift' found")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_gc_redeem_data()
