import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.utils.supabase_db import get_supabase_connection

conn = get_supabase_connection()
cur = conn.cursor()

# Check tender_type_metrics for Enola on Nov 1
cur.execute("""
    SELECT store, date, tender_type, detail_amount 
    FROM tender_type_metrics 
    WHERE store = 'Enola' AND date = '2025-11-01'
    ORDER BY tender_type
""")

print("=== tender_type_metrics for Enola on Nov 1, 2025 ===")
print(f"{'Tender Type':<25} | {'Amount':>12}")
print("-" * 42)
for row in cur.fetchall():
    print(f"{row[2]:<25} | ${row[3]:>11,.2f}")

# Check sales_summary for Enola on Nov 1
print("\n=== sales_summary for Enola on Nov 1, 2025 ===")
cur.execute("""
    SELECT store, date, dd_adjusted_no_markup, cash_in, gift_card_sales, pa_sales_tax, paid_out
    FROM sales_summary 
    WHERE store = 'Enola' AND date = '2025-11-01'
""")

row = cur.fetchone()
if row:
    print(f"Store: {row[0]}")
    print(f"Date: {row[1]}")
    print(f"Dunkin Net Sales: ${row[2]:,.2f}")
    print(f"Cash Due: ${row[3]:,.2f}")
    print(f"Gift Card Sales: ${row[4]:,.2f}")
    print(f"Tax: ${row[5]:,.2f}")
    print(f"Paid Out: ${row[6]:,.2f}")

# Check the SQL query result
print("\n=== Testing Report SQL Query for Enola Nov 1 ===")
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
        s.dd_adjusted_no_markup as dunkin_net_sales,
        s.gift_card_sales,
        COALESCE(t1.total_amount, 0) as gc_redeem_from_tender
    FROM sales_summary s
    LEFT JOIN tender_aggregated t1 ON s.store = t1.store_norm AND s.date = t1.date_norm AND t1.tender_type_clean = 'Gift Card Redeem'
    WHERE s.store = 'Enola' AND s.date = '2025-11-01'
""")

row = cur.fetchone()
if row:
    print(f"Store: {row[0]}")
    print(f"Date: {row[1]}")
    print(f"Dunkin Net Sales: ${row[2]:,.2f}")
    print(f"Gift Card Sales (from sales_summary): ${row[3]:,.2f}")
    print(f"GC Redeem (from tender_type_metrics): ${row[4]:,.2f}")

cur.close()
conn.close()
