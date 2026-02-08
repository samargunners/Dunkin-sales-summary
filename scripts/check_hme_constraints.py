import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dashboard.utils.supabase_db import get_supabase_connection

def check_constraints():
    """Check if hme_report table has any unique constraints"""
    conn = get_supabase_connection()
    cur = conn.cursor()

    print("=" * 80)
    print("HME_REPORT TABLE CONSTRAINTS")
    print("=" * 80)

    # Check for unique constraints
    cur.execute("""
        SELECT
            conname as constraint_name,
            contype as constraint_type,
            pg_get_constraintdef(c.oid) as constraint_definition
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE conrelid = 'public.hme_report'::regclass
        ORDER BY conname
    """)

    constraints = cur.fetchall()
    if constraints:
        print("\nConstraints found:")
        for constraint in constraints:
            print(f"\n  Name: {constraint[0]}")
            print(f"  Type: {constraint[1]}")
            print(f"  Definition: {constraint[2]}")
    else:
        print("\n⚠️  NO CONSTRAINTS FOUND - This means duplicates can be inserted!")

    print("\n" + "=" * 80)

    cur.close()
    conn.close()

if __name__ == "__main__":
    check_constraints()
