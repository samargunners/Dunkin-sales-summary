#!/usr/bin/env python3
"""
bulk_transform_hme.py — Process all HME raw Excel files in data/hme/raw and combine into a single transformed output.
"""
import pandas as pd
from pathlib import Path
from transform_hme import parse_hme_to_desired
import sys

def main():
    raw_dir = Path(__file__).parent / "raw"
    outdir = Path(__file__).parent / "transformed"
    outdir.mkdir(parents=True, exist_ok=True)
    xlsx_path = outdir / "hme_transformed_bulk.xlsx"
    
    # Find all files matching hme_report_YYYYMMDD.xlsx
    files = sorted(raw_dir.glob("hme_report_*.xlsx"))
    if not files:
        print("[ERR] No HME raw files found.")
        sys.exit(1)
    
    all_dfs = []
    for f in files:
        try:
            df = parse_hme_to_desired(f)
            all_dfs.append(df)
            print(f"[OK] Processed: {f.name} ({len(df)} rows)")
        except Exception as e:
            print(f"[ERR] Failed to process {f.name}: {e}")
    
    if not all_dfs:
        print("[ERR] No data processed.")
        sys.exit(1)
    
    df_all = pd.concat(all_dfs, ignore_index=True)
    df_all.to_excel(xlsx_path, index=False)
    print(f"[OK] Wrote {len(df_all)} rows to: {xlsx_path.resolve()}")

if __name__ == "__main__":
    main()
