#!/usr/bin/env python3
# upload_hme_to_supabase.py — insert transformed HME into public.hme_report (your schema)

from __future__ import annotations
from pathlib import Path
import sys
import os
import re
import pandas as pd

# Paths
THIS_FILE = Path(__file__).resolve()
DATA_DIR  = THIS_FILE.parent                  # .../data/hme
BASE_DIR  = DATA_DIR.parents[1]               # .../Dunkin-Sales-Summary

# Reuse existing Supabase Postgres connection helper
sys.path.append(str(BASE_DIR))
from dashboard.utils import supabase_db  # expects get_supabase_connection()

# Table: public.hme_report (id serial PK)
# Columns to insert (exact names & types):
TARGET_COLS = [
    "date",        # date
    "store",       # bigint (PC number)
    "time_measure",
    "total_cars",  # bigint
    "menu_all",    # bigint
    "greet_all",   # bigint
    "service",     # bigint
    "lane_queue",  # bigint
    "lane_total"   # bigint
]

INSERT_SQL = f"""
insert into public.hme_report ({",".join(TARGET_COLS)})
values (
    %(date)s, %(store)s, %(time_measure)s,
    %(total_cars)s, %(menu_all)s, %(greet_all)s,
    %(service)s, %(lane_queue)s, %(lane_total)s
);
"""

def find_latest_transformed() -> Path | None:
    """Find the transformed file to upload.

    Prefers the daily file (hme_transformed.xlsx) for automation.
    Falls back to bulk file or most recent dated file if daily file doesn't exist.
    """
    transformed_dir = DATA_DIR / "transformed"

    # Prefer daily file for automation (updated by daily pipeline)
    daily_file = transformed_dir / "hme_transformed.xlsx"
    if daily_file.exists():
        return daily_file

    # Fallback: try bulk file
    bulk_file = transformed_dir / "hme_transformed_bulk.xlsx"
    if bulk_file.exists():
        return bulk_file

    # Last resort: find any dated transformed file
    candidates = list(transformed_dir.glob("hme_transformed_*.xlsx"))
    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)

def pc_number_from_store(store_text: str) -> int | None:
    """Extract leading digits as PC number and return as int (bigint compatible)."""
    if not isinstance(store_text, str):
        store_text = str(store_text) if store_text is not None else ""
    m = re.match(r"\s*(\d+)", store_text)
    return int(m.group(1)) if m else None

def load_for_upload(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".xlsx":
        df = pd.read_excel(path)
    else:
        raise ValueError(f"[ERR] Only XLSX files are supported for upload: {path}")

    # Expect columns from transform script
    needed = [
        "Date","store","time_measure","Total Cars","menu_all","greet_all",
        "service","lane_queue","lane_total"
    ]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"[ERR] Missing columns in transformed file: {missing}")

    # Build upload frame matching target schema
    out = pd.DataFrame({
        "date": pd.to_datetime(df["Date"], errors="coerce").dt.date,
        "store": df["store"].apply(pc_number_from_store),
        "time_measure": df["time_measure"].astype(str),
        "total_cars": pd.to_numeric(df["Total Cars"], errors="coerce").astype("Int64"),
        "menu_all":   pd.to_numeric(df["menu_all"],   errors="coerce").astype("Int64"),
        "greet_all":  pd.to_numeric(df["greet_all"],  errors="coerce").astype("Int64"),
        "service":    pd.to_numeric(df["service"],    errors="coerce").astype("Int64"),
        "lane_queue": pd.to_numeric(df["lane_queue"], errors="coerce").astype("Int64"),
        "lane_total": pd.to_numeric(df["lane_total"], errors="coerce").astype("Int64"),
    })

    # Optional: drop rows where store couldn’t be parsed
    out = out[out["store"].notna()].copy()

    # Convert pandas NA to Python None for psycopg
    out = out.astype(object).where(pd.notnull(out), None)
    return out[TARGET_COLS]

def check_existing_data(cursor, date_val, store_val, time_measure_val) -> bool:
    """Check if this specific record already exists"""
    cursor.execute("""
        SELECT COUNT(*) FROM hme_report
        WHERE date = %s AND store = %s AND time_measure = %s
    """, (date_val, store_val, time_measure_val))
    count = cursor.fetchone()[0]
    return count > 0

def main():
    src = find_latest_transformed()
    if not src:
        print("[ERR] Could not find a transformed XLSX file in: transformed/")
        print("      Expected hme_transformed.xlsx or hme_transformed_*.xlsx")
        sys.exit(1)

    print(f"[INFO] Loading: {src.name}")
    df = load_for_upload(src)

    try:
        conn = supabase_db.get_supabase_connection()
    except Exception as e:
        print(f"[ERR] Supabase connection error: {e}")
        sys.exit(1)

    total = len(df)
    print(f"[INFO] Processing {total} rows for upload to public.hme_report")

    # Check for duplicates BEFORE inserting
    rows = df.to_dict(orient="records")
    rows_to_insert = []
    duplicates_found = 0

    try:
        with conn.cursor() as cur:
            print("[INFO] Checking for existing records...")
            for row in rows:
                if not check_existing_data(cur, row['date'], row['store'], row['time_measure']):
                    rows_to_insert.append(row)
                else:
                    duplicates_found += 1

        if duplicates_found > 0:
            print(f"[WARN] Found {duplicates_found} duplicate records (will skip)")

        if not rows_to_insert:
            print("[INFO] No new records to insert (all data already exists)")
            return

        print(f"[INFO] Inserting {len(rows_to_insert)} new rows to public.hme_report")

        with conn:
            with conn.cursor() as cur:
                # batch insert
                batch_size = 1000
                for i in range(0, len(rows_to_insert), batch_size):
                    batch = rows_to_insert[i:i+batch_size]
                    try:
                        cur.executemany(INSERT_SQL, batch)
                        print(f"[INFO] Inserted batch {i//batch_size + 1} ({len(batch)} rows)")
                    except Exception as e:
                        print(f"[ERR] Failed to insert batch {i//batch_size + 1}: {e}")
                        raise

        print(f"[OK] Upload complete. Inserted {len(rows_to_insert)} new rows, skipped {duplicates_found} duplicates.")

    except Exception as e:
        print(f"[ERR] Upload failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
