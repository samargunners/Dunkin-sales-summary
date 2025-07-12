#!/usr/bin/env python3
"""
Extract all key sections from each workbook named
    store_<PCNUMBER>_<STORENAME>_<YYYYMMDD>.xlsx
found in  data/raw_emails/
and write a multi-sheet Excel file to data/compiled/ :

    compiled_outputs_<YYYYMMDD>_<HHMMSS>.xlsx
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import pandas as pd
import re
from openpyxl import load_workbook


# ------------------------------------------------------------------------- #
# CONFIGURATION                                                             #
# ------------------------------------------------------------------------- #
RAW_DIR = Path("data/raw_emails")
OUTPUT_DIR = Path("data/compiled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# master containers
sales_summary, order_type_rows, daypart_rows = [], [], []
subcategory_rows, labor_rows, tender_rows   = [], [], []


# ------------------------------------------------------------------------- #
# SMALL UTILITIES                                                           #
# ------------------------------------------------------------------------- #
def find_section(ws, header: str) -> int:
    """Return the 0-based row index of `header` in *column A* (else -1)."""
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if row and isinstance(row[0], str) and header.lower() in row[0].lower():
            return i
    return -1


def safe(row: tuple | list | None, idx: int, default=""):
    """Safely fetch cell idx from a row tuple/list."""
    if row is None or idx >= len(row):
        return default
    return row[idx] if row[idx] is not None else default


def ends(row: tuple | list | None, keyword: str) -> bool:
    """Row[A] contains keyword (case-insensitive)."""
    return (
        row
        and isinstance(row[0], str)
        and keyword.lower() in row[0].lower()
    )


# strip $, commas, % so Excel keeps numbers numeric
# --------------------------------------------------------------------
# CLEAN - convert strings that look like numbers to float
#        return pd.NA when there are no digits at all
# --------------------------------------------------------------------
def clean_num(x):
    """
    • Keeps ints/floats unchanged.
    • Strips $, commas, %, etc.
    • Converts to float **only** if at least one digit remains.
    • Returns pd.NA for placeholders like '--', 'N/A', '', None.
    """
    if isinstance(x, (int, float)):            # already numeric
        return x

    if x is None or (isinstance(x, float) and pd.isna(x)):
        return pd.NA                           # empty Excel cell

    if not isinstance(x, str):
        return pd.NA

    # remove everything except digits, dot, minus
    s = re.sub(r"[^\d.\-]", "", x)

    # if nothing but dashes (or completely empty), treat as missing
    if not re.search(r"\d", s):
        return pd.NA

    try:
        return float(s)
    except ValueError:
        return pd.NA


# ------------------------------------------------------------------------- #
# MAIN                                                                      #
# ------------------------------------------------------------------------- #
for path in RAW_DIR.glob("store_*.xlsx"):
    stem_parts = path.stem.split("_")
    if len(stem_parts) != 4 or not (stem_parts[3].isdigit() and len(stem_parts[3]) == 8):
        print(f"⚠️  Skipping {path.name}: filename not in expected pattern")
        continue

    pc, store, datestr = stem_parts[1:4]
    report_date = datetime.strptime(datestr, "%Y%m%d").date()

    # load workbook once per file
    wb = load_workbook(path, data_only=True, read_only=True)
    ws = wb.active                        # every store workbook has one sheet

    # cache rows so we can index by number
    rows = [r for r in ws.iter_rows(values_only=True) if any(r)]

    # ------------------- SALES MIX METRICS (NO HEADER) -------------------- #
    idx = find_section(ws, "Sales Mix Metrics")
    if idx != -1:
        d, i = {}, idx + 1
        while i < len(rows) and not ends(rows[i], "Sales by Daypart"):
            label = str(rows[i][0]).strip()
            d[label] = clean_num(safe(rows[i], 1))
            i += 1

        sales_summary.append({
            "Store": store,
            "PC_Number": pc,
            "Date": report_date,
            "Gross_Sales":                d.get("Dunkin Gross Sales", ""),
            "Net_Sales":                  d.get("DD Net Sales", ""),
            "DD_Adjusted_No_Markup":      d.get("DD Adjusted Reportable Sales (w/o Delivery Markup)", ""),
            "PA_Sales_Tax":               d.get("Sales Tax", ""),
            "DD_Discount":                d.get("DD Discounts", ""),
            "Guest_Count":                d.get("Guest Count", ""),
            "Avg_Check":                  d.get("Avg Check - MM", ""),
            "Gift_Card_Sales":            d.get("Gift Card Sales", ""),
            "Void_Amount":                d.get("Void Amount", ""),
            "Refund":                     d.get("Refunds", ""),
            "Void_Qty":                   d.get("Void Qty", ""),
            "Cash_IN":                    d.get("Cash In", "")
        })

    # --------------------------- SALES BY DAYPART ------------------------- #
    idx = find_section(ws, "Sales by Daypart")
    if idx != -1:
        # find first row whose Col0 starts with "Daypart"
        i = idx + 1
        while i < len(rows) and not (isinstance(rows[i][0], str) and rows[i][0].lower().startswith("daypart")):
            i += 1
        # read until next section header
        while i < len(rows) and not ends(rows[i], "Tender Type"):
            r = rows[i]
            if r and isinstance(r[0], str) and r[0].lower().startswith("daypart"):
                daypart_rows.append({
                    "Store": store,
                    "PC_Number": pc,
                    "Date": report_date,
                    "Daypart":        r[0],
                    "Net_Sales":      clean_num(safe(r, 2)),
                    "Percent_Sales":  clean_num(safe(r, 3)),
                    "Check_Count":    clean_num(safe(r, 4)),
                    "Avg_Check":      clean_num(safe(r, 5))
                })
            i += 1

    # ------------------------------ TENDER TYPE --------------------------- #
    idx = find_section(ws, "Tender Type")
    if idx != -1:
        i = idx + 1
        # skip header rows (contain 'GL' or 'Metrics')
        while i < len(rows) and ("GL" in str(rows[i][0]) or "Metrics" in str(rows[i][0])):
            i += 1
        while i < len(rows) and not ends(rows[i], "Labor Metrics"):
            r = rows[i]
            if r and r[0]:
                raw_desc = str(r[0]).strip()
                desc = re.sub(r"^\d+\s*-?\s*", "", raw_desc)       # drop leading digits
                desc = desc.replace("Crdit", "Credit")
                desc = desc.split(" - ")[-1]
                desc = desc.split(":")[-1].strip()

                tender_rows.append({
                    "Store": store,
                    "PC_Number": pc,
                    "Date": report_date,
                    "Tender_Type":   desc,
                    "Detail_Amount": clean_num(safe(r, 3))
                })
            i += 1

    # ------------------------------ LABOR METRICS ------------------------- #
    idx = find_section(ws, "Labor Metrics")
    if idx != -1:
        i = idx + 1
        while i < len(rows) and "Labor Position" in str(rows[i][0]):
            i += 1
        while i < len(rows) and not ends(rows[i], "Order Type"):
            r = rows[i]
            if r and r[0]:
                labor_rows.append({
                    "Store": store,
                    "PC_Number": pc,
                    "Date": report_date,
                    "Labor_Position": r[0],
                    "Reg_Hours":      clean_num(safe(r, 1)),
                    "OT_Hours":       clean_num(safe(r, 2)),
                    "Total_Hours":    clean_num(safe(r, 3)),
                    "Reg_Pay":        clean_num(safe(r, 4)),
                    "OT_Pay":         clean_num(safe(r, 5)),
                    "Total_Pay":      clean_num(safe(r, 6)),
                    "Percent_Labor":  clean_num(safe(r, 7))
                })
            i += 1

    # --------------------------- ORDER TYPE (MIX) ------------------------- #
    idx = find_section(ws, "Order Type")
    if idx != -1:
        i = idx + 1
        while i < len(rows) and "Order Type" in str(rows[i][0]):
            i += 1
        while i < len(rows) and not ends(rows[i], "Sales by Subcategory"):
            r = rows[i]
            if r and r[0]:
                order_type_rows.append({
                    "Store": store,
                    "PC_Number": pc,
                    "Date": report_date,
                    "Order_Type":    r[0],
                    "Net_Sales":     clean_num(safe(r, 1)),
                    "Percent_Sales": clean_num(safe(r, 2)),
                    "Guests":        clean_num(safe(r, 3)),
                    "Percent_Guest": clean_num(safe(r, 4)),
                    "Avg_Check":     clean_num(safe(r, 5))
                })
            i += 1

    # ------------------------ SALES BY SUBCATEGORY ------------------------ #
    idx = find_section(ws, "Sales by Subcategory")
    if idx != -1:
        i = idx + 1
        while i < len(rows) and "Subcategory" in str(rows[i][0]):
            i += 1
        while i < len(rows):
            r = rows[i]
            if not r or not r[0] or "Total" in str(r[0]):
                break
            subcategory_rows.append({
                "Store": store,
                "PC_Number": pc,
                "Date": report_date,
                "Subcategory":   r[0],
                "Qty_Sold":      clean_num(safe(r, 1)),
                "Net_Sales":     clean_num(safe(r, 2)),
                "Percent_Sales": clean_num(safe(r, 3))
            })
            i += 1

    wb.close()


# ------------------------------------------------------------------------- #
# EXPORT TO A MULTI-SHEET WORKBOOK                                          #
# ------------------------------------------------------------------------- #
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = OUTPUT_DIR / f"compiled_outputs_{ts}.xlsx"

with pd.ExcelWriter(output_path) as xlw:
    pd.DataFrame(sales_summary).to_excel( xlw, "sales_summary",           index=False)
    pd.DataFrame(order_type_rows).to_excel(xlw, "sales_by_order_type",    index=False)
    pd.DataFrame(subcategory_rows).to_excel(xlw, "sales_by_subcategory",  index=False)
    pd.DataFrame(labor_rows).to_excel(      xlw, "labor_metrics",         index=False)
    pd.DataFrame(tender_rows).to_excel(     xlw, "tender_type_metrics",   index=False)
    pd.DataFrame(daypart_rows).to_excel(    xlw, "sales_by_daypart",      index=False)

print(f"✅ Compiled workbook written to: {output_path.resolve()}")
