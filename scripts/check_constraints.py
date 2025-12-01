import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.utils.supabase_db import get_supabase_connection

conn = get_supabase_connection()
cur = conn.cursor()

# Get unique constraints on sales_summary table
cur.execute("""
    SELECT conname, contype, pg_get_constraintdef(oid)
    FROM pg_constraint
    WHERE conrelid = 'sales_summary'::regclass
    ORDER BY conname
""")

print("Constraints on sales_summary table:\n")
for row in cur.fetchall():
    print(f"Name: {row[0]}")
    print(f"Type: {row[1]}")
    print(f"Definition: {row[2]}\n")

cur.close()
conn.close()
