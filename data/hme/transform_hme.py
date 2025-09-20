#!/usr/bin/env python3
# transform_hme.py — parse raw HME report → Supabase-ready output
# Usage:
#   python transform_hme.py raw/hme_report.xlsx
#   python transform_hme.py raw/hme_report.xlsx --outdir transformed --csv custom.csv --xlsx custom.xlsx

import re
from datetime import datetime
from pathlib import Path
import argparse
import pandas as pd
import numpy as np

DESIRED_SHEET = "Paginated Summary Multi Store R"
EXPECTED_OUTPUT_COLS = [
    "Date","store","time_measure","Total Cars","menu_all","greet_all",
    "Menu Board","Greet","Menu 1","Greet 1","Menu 2","Greet 2",
    "service","lane_queue","lane_total",
]

def _read_hme_sheet(hme_path: Path) -> pd.DataFrame:
    xls = pd.ExcelFile(hme_path)
    sheet = DESIRED_SHEET if DESIRED_SHEET in xls.sheet_names else xls.sheet_names[0]
    return pd.read_excel(xls, sheet_name=sheet)

def _extract_report_date(df: pd.DataFrame) -> datetime.date:
    for col in df.columns:
        for val in df[col].astype(str).fillna(""):
            m = re.search(r"Day:\s*(\d{2}/\d{2}/\d{4})", val)
            if m:
                return datetime.strptime(m.group(1), "%m/%d/%Y").date()
    raise RuntimeError("Could not find a 'Day: mm/dd/yyyy' date in the report.")

def _nz(v):
    """Return value if numeric > 0, else None."""
    try:
        x = float(v)
        return x if x > 0 else None
    except Exception:
        return None

def parse_hme_to_desired(hme_path: Path) -> pd.DataFrame:
    df = _read_hme_sheet(hme_path)
    report_date = _extract_report_date(df)

    # ---- Find the header row (contains "Time Measure") ----
    header_row_idx = None
    for i in range(len(df)):
        if (df.iloc[i] == "Time Measure").any():
            header_row_idx = i
            break
    if header_row_idx is None:
        raise RuntimeError("Could not find 'Time Measure' header row in the sheet.")

    header_row = df.iloc[header_row_idx]
    tm_matches = np.where(header_row.values == "Time Measure")[0]
    if len(tm_matches) == 0:
        raise RuntimeError("Header row found, but no 'Time Measure' column index.")
    time_measure_col = int(tm_matches[0])

    # ---- Map the columns we care about to their indices ----
    wanted = {
        "Total Cars": "Total Cars",
        "Menu Board": "Menu Board",
        "Greet": "Greet",
        "Menu 1": "Menu 1",
        "Greet 1": "Greet 1",
        "Menu 2": "Menu 2",
        "Greet 2": "Greet 2",
        "Service": "service",
        "Lane Queue": "lane_queue",
        "Lane Total": "lane_total",
    }
    idx_map = {}
    for j, v in enumerate(header_row):
        if isinstance(v, str) and v in wanted:
            idx_map[wanted[v]] = j

    records = []
    current_store = None

    for r in range(header_row_idx + 1, len(df)):
        row = df.iloc[r]
        if pd.isna(row).all():
            continue

        # Update current store when we hit a row with a non-empty first cell
        v0 = row.iloc[0]
        if isinstance(v0, str) and v0.strip():
            current_store = " ".join(v0.strip().split())  # collapse whitespace

        if not current_store:
            continue

        time_measure = row.iloc[time_measure_col]
        if pd.isna(time_measure):
            continue

        def get_val(key):
            j = idx_map.get(key)
            if j is None:
                return None
            v = row.iloc[j]
            try:
                return float(v)
            except Exception:
                return pd.to_numeric(pd.Series([v]), errors="coerce").iloc[0]

        menu_board = get_val("Menu Board")
        greet      = get_val("Greet")
        menu1      = get_val("Menu 1")
        greet1     = get_val("Greet 1")

        rec = {
            "Date": pd.to_datetime(report_date),
            "store": current_store,
            "time_measure": str(time_measure),
            "Total Cars": get_val("Total Cars"),
            "Menu Board": menu_board,
            "Greet":      greet,
            "Menu 1":     menu1,
            "Greet 1":    greet1,
            "Menu 2":     get_val("Menu 2"),
            "Greet 2":    get_val("Greet 2"),
            "service":    get_val("service"),
            "lane_queue": get_val("lane_queue"),
            "lane_total": get_val("lane_total"),
        }

        # Fallbacks: use Menu Board/Greet ONLY if > 0; else use Menu 1/Greet 1
        rec["menu_all"]  = _nz(menu_board) if _nz(menu_board) is not None else _nz(menu1)
        rec["greet_all"] = _nz(greet)      if _nz(greet)      is not None else _nz(greet1)

        records.append(rec)

    out = pd.DataFrame.from_records(records)

    # Normalize types
    if "Date" in out.columns:
        out["Date"] = pd.to_datetime(out["Date"], errors="coerce").dt.date

    numeric_cols = [
        "Total Cars","menu_all","greet_all","Menu Board","Greet",
        "Menu 1","Greet 1","Menu 2","Greet 2","service","lane_queue","lane_total"
    ]
    for c in numeric_cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")

    # Final order + stable sort (keeps original block ordering where ties)
    out = out[EXPECTED_OUTPUT_COLS].sort_values(["store","time_measure"], kind="stable").reset_index(drop=True)
    return out

def main():
    parser = argparse.ArgumentParser(description="Transform raw HME report → Supabase-ready output.")
    parser.add_argument("input", help="Path to HME Excel (e.g., raw/hme_report.xlsx)")
    parser.add_argument("--outdir", default="transformed", help="Output folder (default: transformed)")
    parser.add_argument("--csv",  default=None, help="Output CSV filename (default: hme_transformed.csv)")
    parser.add_argument("--xlsx", default=None, help="Output XLSX filename (default: hme_transformed.xlsx)")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        raise SystemExit(f"[ERR] Input file not found: {input_path}")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    xlsx_name = args.xlsx or "hme_transformed.xlsx"
    xlsx_path = outdir / xlsx_name

    df_out = parse_hme_to_desired(input_path)
    df_out.to_excel(xlsx_path, index=False)

    print(f"[OK] Wrote {len(df_out)} rows to:")
    print(f" - {xlsx_path.resolve()}")

if __name__ == "__main__":
    main()
