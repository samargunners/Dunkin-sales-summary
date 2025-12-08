import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection

conn = get_supabase_connection()
cursor = conn.cursor()

print("="*70)
print("DATABASE HEALTH CHECK - December 8, 2025")
print("="*70)

# 1. Check date coverage
print("\n1. DATE COVERAGE:")
print("-"*70)
cursor.execute("""
    SELECT MIN(date) as earliest, MAX(date) as latest, COUNT(DISTINCT date) as total_dates
    FROM sales_summary
""")
row = cursor.fetchone()
print(f"   Earliest Date: {row[0]}")
print(f"   Latest Date: {row[1]}")
print(f"   Total Dates: {row[2]}")

# 2. Check store coverage
print("\n2. STORE COVERAGE:")
print("-"*70)
cursor.execute("""
    SELECT store, COUNT(DISTINCT date) as days_with_data
    FROM sales_summary
    GROUP BY store
    ORDER BY store
""")
print(f"   {'Store':<15} {'Days with Data'}")
print(f"   {'-'*15} {'-'*14}")
for row in cursor.fetchall():
    print(f"   {row[0]:<15} {row[1]}")

# 3. Check Gift Card Sales
print("\n3. GIFT CARD SALES (should be POSITIVE):")
print("-"*70)
cursor.execute("""
    SELECT 
        COUNT(*) as total_records,
        COUNT(CASE WHEN gift_card_sales > 0 THEN 1 END) as positive_count,
        COUNT(CASE WHEN gift_card_sales < 0 THEN 1 END) as negative_count,
        COUNT(CASE WHEN gift_card_sales = 0 THEN 1 END) as zero_count,
        MIN(gift_card_sales) as min_value,
        MAX(gift_card_sales) as max_value,
        AVG(gift_card_sales) as avg_value,
        SUM(gift_card_sales) as total_sales
    FROM sales_summary
    WHERE date >= '2025-11-01'
""")
row = cursor.fetchone()
print(f"   Total Records: {row[0]}")
print(f"   Positive Values: {row[1]} ({'✓ GOOD' if row[1] == row[0] - row[3] else '❌ ISSUE'})")
print(f"   Negative Values: {row[2]} ({'❌ BAD - Should be 0' if row[2] > 0 else '✓ GOOD'})")
print(f"   Zero Values: {row[3]}")
print(f"   Min Value: ${row[4]:,.2f}")
print(f"   Max Value: ${row[5]:,.2f}")
print(f"   Average: ${row[6]:,.2f}")
print(f"   Total Nov-Dec: ${row[7]:,.2f}")

# 4. Check GC Redeem in tender_type_metrics
print("\n4. GC REDEEM TENDER TYPE:")
print("-"*70)
cursor.execute("""
    SELECT 
        COUNT(*) as total_records,
        SUM(detail_amount) as total_amount,
        MIN(detail_amount) as min_amount,
        MAX(detail_amount) as max_amount
    FROM tender_type_metrics
    WHERE (tender_type ILIKE '%gc%redeem%' OR tender_type ILIKE '%gift%card%redeem%')
    AND date >= '2025-11-01'
""")
row = cursor.fetchone()
if row[0] > 0:
    print(f"   ✓ GC Redeem Records Found: {row[0]}")
    print(f"   Total Amount: ${row[1]:,.2f}")
    print(f"   Min: ${row[2]:,.2f}")
    print(f"   Max: ${row[3]:,.2f}")
    print(f"   Avg: ${row[1]/row[0]:,.2f}")
else:
    print(f"   ❌ NO GC Redeem records found!")

# 5. Sample GC Redeem tender types
print("\n5. GC REDEEM TENDER TYPE VARIATIONS:")
print("-"*70)
cursor.execute("""
    SELECT DISTINCT tender_type, COUNT(*) as count
    FROM tender_type_metrics
    WHERE (tender_type ILIKE '%gc%' OR tender_type ILIKE '%gift%card%')
    AND date >= '2025-11-01'
    GROUP BY tender_type
    ORDER BY tender_type
""")
rows = cursor.fetchall()
for row in rows:
    print(f"   '{row[0]}': {row[1]} records")

# 6. Check recent data quality (last 7 days)
print("\n6. RECENT DATA QUALITY (Last 7 Days):")
print("-"*70)
cursor.execute("""
    SELECT 
        date,
        COUNT(DISTINCT store) as stores,
        SUM(net_sales) as total_sales,
        SUM(gift_card_sales) as total_gc_sales
    FROM sales_summary
    WHERE date >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY date
    ORDER BY date DESC
    LIMIT 7
""")
print(f"   {'Date':<12} {'Stores':<8} {'Net Sales':<15} {'GC Sales'}")
print(f"   {'-'*12} {'-'*8} {'-'*15} {'-'*12}")
for row in cursor.fetchall():
    print(f"   {row[0]} {row[1]:<8} ${row[2]:>13,.2f} ${row[3]:>10,.2f}")

# 7. Check for missing dates in November
print("\n7. MISSING DATES CHECK (November):")
print("-"*70)
cursor.execute("""
    WITH date_series AS (
        SELECT generate_series(
            '2025-11-01'::date,
            '2025-11-30'::date,
            '1 day'::interval
        )::date as check_date
    )
    SELECT check_date
    FROM date_series
    WHERE check_date NOT IN (
        SELECT DISTINCT date FROM sales_summary WHERE date BETWEEN '2025-11-01' AND '2025-11-30'
    )
    ORDER BY check_date
""")
missing = cursor.fetchall()
if missing:
    print(f"   ⚠️  Missing dates: {', '.join([str(row[0]) for row in missing])}")
else:
    print(f"   ✓ No missing dates - Complete coverage!")

# 8. Table record counts
print("\n8. TABLE RECORD COUNTS:")
print("-"*70)
tables = ['sales_summary', 'tender_type_metrics', 'labor_metrics', 
          'sales_by_daypart', 'sales_by_subcategory', 'sales_by_order_type']
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"   {table:<25} {count:>8} rows")

print("\n" + "="*70)
print("DATABASE HEALTH CHECK COMPLETE")
print("="*70)

cursor.close()
conn.close()
