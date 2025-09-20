#!/usr/bin/env python3
# upload_hme_to_supabase.py — insert transformed HME into public.hme_report (your schema)

from __future__ import annotations
from pathlib import Path
import sys
import os
import re
import pandas as pd
import toml

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
    # Prefer XLSX; fallback to CSV; consider dated variants too
    candidates = list((DATA_DIR / "transformed").glob("hme_transformed.xlsx"))
    candidates += list((DATA_DIR / "transformed").glob("hme_transformed.csv"))
    if not candidates:
        candidates += sorted((DATA_DIR / "transformed").glob("hme_transformed_*.xlsx"), reverse=True)
        candidates += sorted((DATA_DIR / "transformed").glob("hme_transformed_*.csv"), reverse=True)
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
        df = pd.read_csv(path)

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

def main():
    # Find all transformed files
    transformed_dir = Path(__file__).parent / "transformed"
    files = list(transformed_dir.glob("hme_transformed_*.xlsx"))
    files += list(transformed_dir.glob("hme_transformed_*.csv"))
    if not files:
        print("[ERR] No transformed files found in: transformed/")
        return

    try:
        conn = supabase_db.get_supabase_connection()
    except Exception as e:
        print(f"[ERR] Supabase connection error: {e}")
        return

    with conn:
        with conn.cursor() as cur:
            for src in sorted(files):
                print(f"[INFO] Loading: {src.name}")
                try:
                    df = load_for_upload(src)
                except Exception as e:
                    print(f"[ERR] Skipping {src.name}: {e}")
                    continue
                total = len(df)
                print(f"[INFO] Inserting {total} rows to public.hme_report")
                batch_size = 1000
                rows = df.to_dict(orient="records")
                for i in range(0, total, batch_size):
                    cur.executemany(INSERT_SQL, rows[i:i+batch_size])
                print(f"[OK] Uploaded {src.name}")

if __name__ == "__main__":
    print(toml.load("C:/Projects/Dunkin-sales-summary/.streamlit/secrets.toml"))
    main()
