import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.utils.supabase_db import get_supabase_connection

conn = get_supabase_connection()
cur = conn.cursor()

# Check tender_type_metrics
cur.execute("""
    SELECT date, store, tender_type, detail_amount 
    FROM tender_type_metrics 
    WHERE date IN ('2025-10-18', '2025-10-19') 
    ORDER BY date, store, tender_type
""")

rows = cur.fetchall()
print(f"\n=== tender_type_metrics data for Oct 18-19 ===")
print(f"Total rows: {len(rows)}\n")

if rows:
    print(f"{'Date':<12} | {'Store':<15} | {'Tender Type':<20} | {'Amount':>12}")
    print("-" * 75)
    for r in rows[:30]:  # Show first 30 rows
        print(f"{r[0]} | {r[1]:<15} | {r[2]:<20} | ${r[3]:>11,.2f}")
else:
    print("❌ NO DATA FOUND!")

# Check what the SQL query in download_tender_sales_report.py would return
print("\n\n=== Testing report SQL query for Oct 18-19 ===")
cur.execute("""
    WITH tender_normalized AS (
        SELECT 
            store,
            date,
            CASE 
                WHEN LOWER(tender_type) IN ('gc redeem', 'gift card redeem', 'gift card redeem offline') 
                    THEN 'Gift Card Redeem'
                WHEN LOWER(tender_type) IN ('visa', 'visa-kiosk', 'visa - kiosk') 
                    THEN 'Visa'
                WHEN LOWER(tender_type) IN ('mastercard', 'mastercard - kiosk') 
                    THEN 'Mastercard'
                WHEN LOWER(tender_type) = 'amex' 
                    THEN 'Amex'
                WHEN LOWER(tender_type) = 'discover' 
                    THEN 'Discover'
                WHEN LOWER(tender_type) = 'doordash' 
                    THEN 'Doordash'
                WHEN LOWER(tender_type) = 'uber eats' 
                    THEN 'Uber Eats'
                WHEN LOWER(tender_type) = 'grub hub' 
                    THEN 'Grub Hub'
                ELSE tender_type
            END as tender_type_clean,
            detail_amount
        FROM tender_type_metrics
    ),
    tender_aggregated AS (
        SELECT 
            store as store_norm,
            date as date_norm,
            tender_type_clean,
            SUM(detail_amount) as total_amount
        FROM tender_normalized
        GROUP BY store, date, tender_type_clean
    )
    SELECT 
        s.store,
        s.date,
        COALESCE(t1.total_amount, 0) as gift_card_redeem,
        COALESCE(t2.total_amount, 0) as uber_eats,
        COALESCE(t3.total_amount, 0) as doordash,
        COALESCE(t4.total_amount, 0) as grubhub,
        COALESCE(t5.total_amount, 0) as visa,
        COALESCE(t6.total_amount, 0) as mastercard,
        COALESCE(t7.total_amount, 0) as amex,
        COALESCE(t8.total_amount, 0) as discover
    FROM sales_summary s
    LEFT JOIN tender_aggregated t1 ON s.store = t1.store_norm AND s.date = t1.date_norm AND t1.tender_type_clean = 'Gift Card Redeem'
    LEFT JOIN tender_aggregated t2 ON s.store = t2.store_norm AND s.date = t2.date_norm AND t2.tender_type_clean = 'Uber Eats'
    LEFT JOIN tender_aggregated t3 ON s.store = t3.store_norm AND s.date = t3.date_norm AND t3.tender_type_clean = 'Doordash'
    LEFT JOIN tender_aggregated t4 ON s.store = t4.store_norm AND s.date = t4.date_norm AND t4.tender_type_clean = 'Grub Hub'
    LEFT JOIN tender_aggregated t5 ON s.store = t5.store_norm AND s.date = t5.date_norm AND t5.tender_type_clean = 'Visa'
    LEFT JOIN tender_aggregated t6 ON s.store = t6.store_norm AND s.date = t6.date_norm AND t6.tender_type_clean = 'Mastercard'
    LEFT JOIN tender_aggregated t7 ON s.store = t7.store_norm AND s.date = t7.date_norm AND t7.tender_type_clean = 'Amex'
    LEFT JOIN tender_aggregated t8 ON s.store = t8.store_norm AND s.date = t8.date_norm AND t8.tender_type_clean = 'Discover'
    WHERE s.date IN ('2025-10-18', '2025-10-19')
    ORDER BY s.date, s.store
""")

rows = cur.fetchall()
print(f"Query returned: {len(rows)} rows\n")

if rows:
    print(f"{'Store':<20} | {'Date':<12} | {'GC':>8} | {'Visa':>10} | {'MC':>10} | {'Amex':>8}")
    print("-" * 90)
    for r in rows:
        print(f"{r[0]:<20} | {r[1]} | ${r[2]:>7,.0f} | ${r[4]:>9,.0f} | ${r[5]:>9,.0f} | ${r[6]:>7,.0f}")

cur.close()
conn.close()
