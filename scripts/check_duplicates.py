from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
from dashboard.utils import supabase_db

def check_for_duplicates():
    """Check for duplicate records in each table"""
    try:
        conn = supabase_db.get_supabase_connection()
        print("Connected to Supabase successfully\n")
        
        # Define the unique key combinations for each table
        tables_and_keys = {
            'tender_type_metrics': ['store', 'pc_number', 'date', 'tender_type'],
            'sales_summary': ['store', 'pc_number', 'date'],
            'sales_by_subcategory': ['store', 'pc_number', 'date', 'subcategory'], 
            'sales_by_daypart': ['store', 'pc_number', 'date', 'daypart'],
            'sales_by_order_type': ['store', 'pc_number', 'date', 'order_type'],
            'labor_metrics': ['store', 'pc_number', 'date', 'labor_position']
        }
        
        for table, key_cols in tables_and_keys.items():
            try:
                with conn.cursor() as cur:
                    # Get total row count
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    total_rows = cur.fetchone()[0]
                    
                    if total_rows == 0:
                        print(f"❌ {table}: No data to check")
                        continue
                    
                    # Get count of unique combinations
                    key_cols_str = ', '.join(key_cols)
                    cur.execute(f"SELECT COUNT(DISTINCT ({key_cols_str})) FROM {table}")
                    unique_rows = cur.fetchone()[0]
                    
                    # Check for duplicates
                    duplicates = total_rows - unique_rows
                    
                    if duplicates == 0:
                        print(f"✅ {table}: {total_rows} rows, NO DUPLICATES")
                    else:
                        print(f"⚠️  {table}: {total_rows} total rows, {unique_rows} unique, {duplicates} DUPLICATES FOUND!")
                        
                        # Show sample duplicates
                        duplicate_query = f"""
                        SELECT {key_cols_str}, COUNT(*) as count
                        FROM {table} 
                        GROUP BY {key_cols_str}
                        HAVING COUNT(*) > 1
                        LIMIT 5
                        """
                        cur.execute(duplicate_query)
                        duplicate_examples = cur.fetchall()
                        
                        print(f"   Sample duplicates:")
                        for row in duplicate_examples:
                            print(f"     {row}")
                        
            except Exception as e:
                print(f"❌ {table}: Error checking duplicates - {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    check_for_duplicates()