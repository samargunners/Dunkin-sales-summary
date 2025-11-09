"""
Upload tender data for October 18-19, 2025 from manual data entry
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from dashboard.utils.supabase_db import get_supabase_connection

# Store name to PC number and short name mapping
STORE_MAPPING = {
    "301290 - 2820 Paxton St": {"pc": "301290", "name": "Paxton"},
    "343939 - 807 E Main St": {"pc": "343939", "name": "MountJoy"},
    "357993 - 423 N Enola Rd": {"pc": "357993", "name": "Enola"},
    "358529 - 3929 Columbia Avenue": {"pc": "358529", "name": "Columbia"},
    "359042 - 737 South Broad Street": {"pc": "359042", "name": "Lititz"},
    "363271 - 1154 River Road": {"pc": "363271", "name": "Marietta"},
    "364322 - 820 South Market Street": {"pc": "364322", "name": "Etown"}
}

# GL Description to tender type mapping (normalized)
GL_TO_TENDER = {
    "Credit Card - Amex": "Amex",
    "Credit Card - Discover": "Discover",
    "Credit Card - Mastercard": "Mastercard",
    "Credit Card - Visa": "Visa",
    "Gift Card Redeem": "Gift Card Redeem",
    "Delivery: Doordash": "Doordash",
    "Delivery: Uber Eats": "Uber Eats",
    "Grub Hub": "Grub Hub"
}

# October 19, 2025 data
oct19_data = {
    "Credit Card - Amex": {
        "301290 - 2820 Paxton St": 33.41,
        "343939 - 807 E Main St": 19.66,
        "357993 - 423 N Enola Rd": 141.14,
        "358529 - 3929 Columbia Avenue": 31.50,
        "359042 - 737 South Broad Street": 78.52,
        "363271 - 1154 River Road": 48.14,
        "364322 - 820 South Market Street": 36.08
    },
    "Credit Card - Discover": {
        "301290 - 2820 Paxton St": 50.54,
        "343939 - 807 E Main St": 34.45,
        "357993 - 423 N Enola Rd": 101.91,
        "358529 - 3929 Columbia Avenue": 59.85,
        "359042 - 737 South Broad Street": 203.71,
        "363271 - 1154 River Road": 105.10,
        "364322 - 820 South Market Street": 195.73
    },
    "Credit Card - Mastercard": {
        "301290 - 2820 Paxton St": 332.09,
        "343939 - 807 E Main St": 573.17,
        "357993 - 423 N Enola Rd": 580.32,
        "358529 - 3929 Columbia Avenue": 689.46,
        "359042 - 737 South Broad Street": 689.51,
        "363271 - 1154 River Road": 309.78,
        "364322 - 820 South Market Street": 787.66
    },
    "Credit Card - Visa": {
        "301290 - 2820 Paxton St": 1743.65,
        "343939 - 807 E Main St": 2671.99,
        "357993 - 423 N Enola Rd": 3229.14,
        "358529 - 3929 Columbia Avenue": 3113.33,
        "359042 - 737 South Broad Street": 2403.37,
        "363271 - 1154 River Road": 2877.54,
        "364322 - 820 South Market Street": 3870.74
    },
    "Gift Card Redeem": {
        "301290 - 2820 Paxton St": 143.69,
        "343939 - 807 E Main St": 907.84,
        "357993 - 423 N Enola Rd": 1137.96,
        "358529 - 3929 Columbia Avenue": 811.48,
        "359042 - 737 South Broad Street": 749.55,
        "363271 - 1154 River Road": 613.64,
        "364322 - 820 South Market Street": 742.95
    },
    "Delivery: Doordash": {
        "301290 - 2820 Paxton St": 0,
        "343939 - 807 E Main St": 328.70,
        "357993 - 423 N Enola Rd": 159.41,
        "358529 - 3929 Columbia Avenue": 333.95,
        "359042 - 737 South Broad Street": 196.31,
        "363271 - 1154 River Road": 336.48,
        "364322 - 820 South Market Street": 0
    },
    "Delivery: Uber Eats": {
        "301290 - 2820 Paxton St": 77.75,
        "343939 - 807 E Main St": 0,
        "357993 - 423 N Enola Rd": 81.05,
        "358529 - 3929 Columbia Avenue": 91.31,
        "359042 - 737 South Broad Street": 0,
        "363271 - 1154 River Road": 0,
        "364322 - 820 South Market Street": 17.07
    },
    "Grub Hub": {
        "301290 - 2820 Paxton St": 26.94,
        "343939 - 807 E Main St": 21.54,
        "357993 - 423 N Enola Rd": 65.44,
        "358529 - 3929 Columbia Avenue": 0,
        "359042 - 737 South Broad Street": 28.61,
        "363271 - 1154 River Road": 0,
        "364322 - 820 South Market Street": 4.22
    }
}

# October 18, 2025 data
oct18_data = {
    "Credit Card - Amex": {
        "301290 - 2820 Paxton St": 79.63,
        "343939 - 807 E Main St": 39.01,
        "357993 - 423 N Enola Rd": 175.25,
        "358529 - 3929 Columbia Avenue": 132.88,
        "359042 - 737 South Broad Street": 113.89,
        "363271 - 1154 River Road": 49.51,
        "364322 - 820 South Market Street": 61.26
    },
    "Credit Card - Discover": {
        "301290 - 2820 Paxton St": 28.59,
        "343939 - 807 E Main St": 125.01,
        "357993 - 423 N Enola Rd": 110.49,
        "358529 - 3929 Columbia Avenue": 129.19,
        "359042 - 737 South Broad Street": 140.95,
        "363271 - 1154 River Road": 93.94,
        "364322 - 820 South Market Street": 158.15
    },
    "Credit Card - Mastercard": {
        "301290 - 2820 Paxton St": 253.28,
        "343939 - 807 E Main St": 564.11,
        "357993 - 423 N Enola Rd": 1053.36,
        "358529 - 3929 Columbia Avenue": 736.81,
        "359042 - 737 South Broad Street": 747.39,
        "363271 - 1154 River Road": 474.76,
        "364322 - 820 South Market Street": 953.13
    },
    "Credit Card - Visa": {
        "301290 - 2820 Paxton St": 2016.65,
        "343939 - 807 E Main St": 2795.10,
        "357993 - 423 N Enola Rd": 5007.43,
        "358529 - 3929 Columbia Avenue": 3507.35,
        "359042 - 737 South Broad Street": 2648.35,
        "363271 - 1154 River Road": 3337.29,
        "364322 - 820 South Market Street": 4171.22
    },
    "Gift Card Redeem": {
        "301290 - 2820 Paxton St": 238.69,
        "343939 - 807 E Main St": 753.52,
        "357993 - 423 N Enola Rd": 1271.35,
        "358529 - 3929 Columbia Avenue": 1029.69,
        "359042 - 737 South Broad Street": 608.81,
        "363271 - 1154 River Road": 852.68,
        "364322 - 820 South Market Street": 1279.70
    },
    "Delivery: Doordash": {
        "301290 - 2820 Paxton St": 227.63,
        "343939 - 807 E Main St": 407.41,
        "357993 - 423 N Enola Rd": 188.36,
        "358529 - 3929 Columbia Avenue": 334.17,
        "359042 - 737 South Broad Street": 329.60,
        "363271 - 1154 River Road": 394.36,
        "364322 - 820 South Market Street": 0
    },
    "Delivery: Uber Eats": {
        "301290 - 2820 Paxton St": 40.14,
        "343939 - 807 E Main St": 0,
        "357993 - 423 N Enola Rd": 24.97,
        "358529 - 3929 Columbia Avenue": 48.56,
        "359042 - 737 South Broad Street": 21.35,
        "363271 - 1154 River Road": 57.77,
        "364322 - 820 South Market Street": 17.96
    },
    "Grub Hub": {
        "301290 - 2820 Paxton St": 17.38,
        "343939 - 807 E Main St": 17.71,
        "357993 - 423 N Enola Rd": 43.96,
        "358529 - 3929 Columbia Avenue": 0,
        "359042 - 737 South Broad Street": 0,
        "363271 - 1154 River Road": 24.67,
        "364322 - 820 South Market Street": 42.30
    }
}

def prepare_data_for_upload(date_str, data_dict):
    """Convert the nested dictionary into rows for database upload"""
    rows = []
    for gl_desc, store_amounts in data_dict.items():
        tender_type = GL_TO_TENDER[gl_desc]
        for store_name, amount in store_amounts.items():
            if amount > 0:  # Only insert non-zero amounts
                store_info = STORE_MAPPING[store_name]
                rows.append({
                    'store': store_info['name'],  # Use short name like "Paxton"
                    'pc_number': store_info['pc'],
                    'date': date_str,
                    'tender_type': tender_type,
                    'detail_amount': amount
                })
    return rows

def upload_to_supabase(rows):
    """Upload rows to Supabase tender_type_metrics table"""
    if not rows:
        print("No data to upload")
        return
    
    df = pd.DataFrame(rows)
    conn = get_supabase_connection()
    cur = conn.cursor()
    
    try:
        # Delete existing records for these dates (if any)
        dates = df['date'].unique()
        for date in dates:
            delete_sql = "DELETE FROM tender_type_metrics WHERE date = %s"
            cur.execute(delete_sql, (date,))
            print(f"Deleted existing records for {date}")
        
        # Insert new records
        insert_sql = """
            INSERT INTO tender_type_metrics (store, pc_number, date, tender_type, detail_amount)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        # Convert to list of tuples with proper Python types
        data_to_insert = [
            (row['store'], row['pc_number'], row['date'], row['tender_type'], float(row['detail_amount']))
            for _, row in df.iterrows()
        ]
        
        cur.executemany(insert_sql, data_to_insert)
        conn.commit()
        
        print(f"\n✅ Successfully uploaded {len(data_to_insert)} tender records")
        print(f"   Dates: {', '.join(dates)}")
        print(f"   Stores: {df['store'].nunique()}")
        print(f"   Tender types: {df['tender_type'].nunique()}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error uploading data: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("Processing October 18-19, 2025 tender data...\n")
    
    # Prepare data
    oct18_rows = prepare_data_for_upload('2025-10-18', oct18_data)
    oct19_rows = prepare_data_for_upload('2025-10-19', oct19_data)
    
    all_rows = oct18_rows + oct19_rows
    
    print(f"Prepared {len(oct18_rows)} rows for Oct 18")
    print(f"Prepared {len(oct19_rows)} rows for Oct 19")
    print(f"Total: {len(all_rows)} rows\n")
    
    # Upload to database
    upload_to_supabase(all_rows)
    
    print("\n✅ Done! You can now run your report for October.")
