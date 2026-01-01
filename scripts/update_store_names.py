
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import dashboard.utils.supabase_db as db

def update_store_names():
    conn = db.get_supabase_connection()
    cur = conn.cursor()
    # List of tables and the store column
    tables = [
        'sales_summary',
        'tender_type_metrics',
        'labor_metrics',
        'sales_by_daypart',
        'sales_by_subcategory',
        'sales_by_order_type'
    ]
    # Store name corrections
    corrections = [
        (['Etown'], 'ETown'),
        (['MountJoy', 'Mount Joy', 'MT JOY', 'MT Joy'], 'Mt Joy')
    ]
    total_updates = 0
    for table in tables:
        for old_names, new_name in corrections:
            for old_name in old_names:
                cur.execute(f"UPDATE {table} SET store=%s WHERE store=%s", (new_name, old_name))
                print(f"{table}: Updated '{old_name}' to '{new_name}' - Rows: {cur.rowcount}")
                total_updates += cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    print(f"Total rows updated: {total_updates}")

if __name__ == "__main__":
    update_store_names()
