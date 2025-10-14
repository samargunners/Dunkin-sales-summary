#!/usr/bin/env python3
"""
Simple script to upload recent compiled Excel files to Supabase
"""

from pathlib import Path
import pandas as pd
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
from dashboard.utils import supabase_db

COMPILED_DIR = BASE_DIR / "data" / "compiled"

def simple_upload():
    """Upload the 3 most recent files"""
    
    # Get the 3 most recent files
    files = sorted(COMPILED_DIR.glob("compiled_outputs_*.xlsx"), reverse=True)[:3]
    
    if not files:
        print("❌ No compiled files found")
        return
    
    print(f"📋 Uploading {len(files)} most recent files:")
    for f in files:
        print(f"   • {f.name}")
    
    try:
        conn = supabase_db.get_supabase_connection()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    for excel_file in files:
        print(f"\n📁 Processing: {excel_file.name}")
        
        # Get all sheet names
        try:
            xl_file = pd.ExcelFile(excel_file)
            sheet_names = xl_file.sheet_names
            print(f"   📊 Found sheets: {', '.join(sheet_names)}")
            
            for sheet_name in sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                print(f"   📈 Sheet '{sheet_name}': {len(df)} rows, {len(df.columns)} columns")
                
                # Convert Date column if exists
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
                
                # Simple insert with conflict ignore
                cols = ','.join([f'"{col}"' for col in df.columns])  # Quote column names
                placeholders = ','.join(['%s'] * len(df.columns))
                
                insert_sql = f'INSERT INTO "{sheet_name}" ({cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'
                
                data = df.values.tolist()
                
                with conn.cursor() as cur:
                    cur.executemany(insert_sql, data)
                    
                print(f"   ✅ Uploaded sheet '{sheet_name}'")
                
        except Exception as e:
            print(f"   ❌ Error with {excel_file.name}: {e}")
            continue
    
    conn.commit()
    conn.close()
    print("\n🎉 Upload complete!")

if __name__ == "__main__":
    simple_upload()