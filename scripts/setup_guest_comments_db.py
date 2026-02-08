#!/usr/bin/env python3
"""
Initialize the medallia_reports table in Supabase
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.utils.supabase_db import get_supabase_connection

def create_medallia_reports_table():
    """Create the medallia_reports table and indexes"""
    
    sql_file = Path(__file__).parent.parent / "db" / "guest_comments_schema.sql"
    
    if not sql_file.exists():
        print(f"Error: Schema file not found: {sql_file}")
        return 1
    
    print("Reading schema file...")
    with open(sql_file, 'r') as f:
        schema_sql = f.read()
    
    print("Connecting to Supabase...")
    try:
        conn = get_supabase_connection()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return 1
    
    print("Creating medallia_reports table...")
    cursor = conn.cursor()
    
    try:
        cursor.execute(schema_sql)
        conn.commit()
        print("✓ Table created successfully!")
        
        # Verify table exists
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'medallia_reports'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print(f"\n✓ Verified table structure ({len(columns)} columns):")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
        
        # Check indexes
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'medallia_reports'
        """)
        
        indexes = cursor.fetchall()
        print(f"\n✓ Created {len(indexes)} index(es):")
        for idx in indexes:
            print(f"  - {idx[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("✓ DATABASE SETUP COMPLETE")
        print("="*80)
        print("\nNext steps:")
        print("1. Run: python scripts/run_medallia_pipeline.py")
        print("2. Or manually: python scripts/download_medallia_emails.py")
        print("3. Then: python scripts/process_medallia_data.py")
        
        return 0
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error creating table: {e}")
        cursor.close()
        conn.close()
        return 1


if __name__ == "__main__":
    exit(create_medallia_reports_table())
