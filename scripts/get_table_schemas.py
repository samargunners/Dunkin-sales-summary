#!/usr/bin/env python3
"""Get schema information for database tables"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.utils.supabase_db import get_supabase_connection

def get_table_schema(cursor, table_name):
    """Get column information for a table"""
    cursor.execute(f"""
        SELECT 
            column_name, 
            data_type, 
            is_nullable, 
            column_default,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' 
        ORDER BY ordinal_position
    """)
    return cursor.fetchall()

def get_table_stats(cursor, table_name):
    """Get basic statistics for a table"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name IN ('date', 'created_at', 'report_date')
            LIMIT 1
        """)
        date_col = cursor.fetchone()
        
        if date_col:
            date_col = date_col[0]
            cursor.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM {table_name}")
            date_range = cursor.fetchone()
            return count, date_range
        else:
            return count, (None, None)
    except Exception as e:
        return None, (None, None)

def main():
    conn = get_supabase_connection()
    cursor = conn.cursor()
    
    tables = ['hme_report', 'guest_comments']
    
    # Check for labour tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%labour%'
    """)
    labour_tables = [row[0] for row in cursor.fetchall()]
    
    print("=" * 80)
    print("DATABASE TABLE SCHEMAS")
    print("=" * 80)
    
    for table in tables:
        print(f"\n\n{'='*80}")
        print(f"TABLE: {table.upper()}")
        print('='*80)
        
        schema = get_table_schema(cursor, table)
        count, date_range = get_table_stats(cursor, table)
        
        print(f"\nTotal Records: {count:,}" if count else "\nTotal Records: N/A")
        if date_range[0]:
            print(f"Date Range: {date_range[0]} to {date_range[1]}")
        
        print("\nCOLUMNS:")
        print("-" * 80)
        print(f"{'Column Name':<25} {'Type':<20} {'Nullable':<10} {'Default':<20}")
        print("-" * 80)
        
        for col in schema:
            col_name, data_type, nullable, default, max_len = col
            if max_len and data_type in ('character varying', 'varchar'):
                data_type = f"{data_type}({max_len})"
            default_str = str(default)[:18] if default else '-'
            print(f"{col_name:<25} {data_type:<20} {nullable:<10} {default_str:<20}")
    
    if labour_tables:
        print(f"\n\n{'='*80}")
        print("LABOUR TABLES FOUND:")
        print('='*80)
        for table in labour_tables:
            print(f"  - {table}")
            schema = get_table_schema(cursor, table)
            count, date_range = get_table_stats(cursor, table)
            
            print(f"    Records: {count:,}" if count else "    Records: N/A")
            print("    Columns:")
            for col in schema:
                print(f"      - {col[0]} ({col[1]})")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
