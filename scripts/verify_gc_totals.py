"""
Verify Gift Card Redeem totals with corrected pattern
"""

import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection


def verify_gc_totals():
    """Verify GC Redeem totals."""
    
    try:
        print("Connecting to Supabase...")
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        # Check raw totals
        print("\n" + "="*80)
        print("RAW GIFT CARD REDEEM TOTALS (all records)")
        print("="*80)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                SUM(detail_amount) as total_amount
            FROM tender_type_metrics
            WHERE date BETWEEN '2025-10-01' AND '2025-10-31'
            AND tender_type ILIKE '%gift%card%redeem%'
        """)
        
        result = cursor.fetchone()
        print(f"Total records: {result[0]}")
        print(f"Total amount: ${result[1]:,.2f}")
        
        # Check with deduplication (ROW_NUMBER)
        print("\n" + "="*80)
        print("WITH DEDUPLICATION (rn = 1)")
        print("="*80)
        
        cursor.execute("""
            WITH tender_labeled AS (
              SELECT
                t.store,
                t.date,
                t.detail_amount,
                t.tender_type,
                CASE
                  WHEN t.tender_type ILIKE '%gift%card%redeem%' THEN 'gift_card_redeem'
                  ELSE NULL
                END AS tcat,
                ROW_NUMBER() OVER (
                  PARTITION BY t.store, t.date,
                               CASE
                                 WHEN t.tender_type ILIKE '%gift%card%redeem%' THEN 'gift_card_redeem'
                                 ELSE NULL
                               END
                  ORDER BY t.id
                ) AS rn
              FROM tender_type_metrics t
              WHERE t.date BETWEEN '2025-10-01' AND '2025-10-31'
              AND t.tender_type ILIKE '%gift%card%redeem%'
            )
            SELECT 
                COUNT(*) as total_records,
                SUM(detail_amount) as total_amount,
                COUNT(CASE WHEN rn = 1 THEN 1 END) as deduplicated_count,
                SUM(CASE WHEN rn = 1 THEN detail_amount END) as deduplicated_amount
            FROM tender_labeled
        """)
        
        result = cursor.fetchone()
        print(f"Total records before dedup: {result[0]}")
        print(f"Total amount before dedup: ${result[1]:,.2f}")
        print(f"Records after dedup (rn=1): {result[2]}")
        print(f"Amount after dedup (rn=1): ${result[3]:,.2f}")
        
        # Show duplicates
        print("\n" + "="*80)
        print("DUPLICATES (records where rn > 1)")
        print("="*80)
        
        cursor.execute("""
            WITH tender_labeled AS (
              SELECT
                t.store,
                t.date,
                t.detail_amount,
                t.tender_type,
                CASE
                  WHEN t.tender_type ILIKE '%gift%card%redeem%' THEN 'gift_card_redeem'
                  ELSE NULL
                END AS tcat,
                ROW_NUMBER() OVER (
                  PARTITION BY t.store, t.date,
                               CASE
                                 WHEN t.tender_type ILIKE '%gift%card%redeem%' THEN 'gift_card_redeem'
                                 ELSE NULL
                               END
                  ORDER BY t.id
                ) AS rn
              FROM tender_type_metrics t
              WHERE t.date BETWEEN '2025-10-01' AND '2025-10-31'
              AND t.tender_type ILIKE '%gift%card%redeem%'
            )
            SELECT date, store, tender_type, detail_amount, rn
            FROM tender_labeled
            WHERE rn > 1
            ORDER BY date, store, rn
        """)
        
        dupes = cursor.fetchall()
        if dupes:
            print(f"Found {len(dupes)} duplicate records:")
            for row in dupes:
                print(f"  {row[0]} | {row[1]:12} | {row[2]:30} | ${row[3]:,.2f} | rn={row[4]}")
        else:
            print("No duplicates found")
        
        # Check by date range
        print("\n" + "="*80)
        print("BREAKDOWN BY DATE RANGE")
        print("="*80)
        
        for date_range in [('2025-10-01', '2025-10-17'), ('2025-10-18', '2025-10-31')]:
            cursor.execute("""
                WITH tender_labeled AS (
                  SELECT
                    t.store,
                    t.date,
                    t.detail_amount,
                    CASE
                      WHEN t.tender_type ILIKE '%gift%card%redeem%' THEN 'gift_card_redeem'
                      ELSE NULL
                    END AS tcat,
                    ROW_NUMBER() OVER (
                      PARTITION BY t.store, t.date,
                                   CASE
                                     WHEN t.tender_type ILIKE '%gift%card%redeem%' THEN 'gift_card_redeem'
                                     ELSE NULL
                                   END
                      ORDER BY t.id
                    ) AS rn
                  FROM tender_type_metrics t
                  WHERE t.date BETWEEN %s AND %s
                  AND t.tender_type ILIKE '%gift%card%redeem%'
                )
                SELECT 
                    SUM(CASE WHEN rn = 1 THEN detail_amount END) as deduplicated_amount
                FROM tender_labeled
            """, date_range)
            
            result = cursor.fetchone()
            print(f"{date_range[0]} to {date_range[1]}: ${result[0]:,.2f}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    verify_gc_totals()
