import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.utils.supabase_db import get_supabase_connection

conn = get_supabase_connection()
cur = conn.cursor()

cur.execute("""
    SELECT DISTINCT date 
    FROM sales_summary 
    WHERE date >= '2025-10-28' AND date <= '2025-11-02'
    ORDER BY date
""")

print("Dates in sales_summary (Oct 28 - Nov 2):")
for row in cur.fetchall():
    print(f"  {row[0]}")

cur.close()
conn.close()
