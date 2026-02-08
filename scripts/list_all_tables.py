import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dashboard.utils.supabase_db import get_supabase_connection

def list_tables():
    """List all tables in the Supabase database"""
    conn = get_supabase_connection()
    cur = conn.cursor()

    print("=" * 80)
    print("ALL TABLES IN SUPABASE DATABASE")
    print("=" * 80)

    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    tables = cur.fetchall()
    print(f"\nFound {len(tables)} tables:\n")

    for table in tables:
        table_name = table[0]

        # Get row count
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cur.fetchone()[0]
            print(f"  - {table_name:<40} ({count:,} rows)")
        except Exception as e:
            print(f"  - {table_name:<40} (Error: {e})")

    print("\n" + "=" * 80)

    cur.close()
    conn.close()

if __name__ == "__main__":
    list_tables()
