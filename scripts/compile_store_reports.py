from pathlib import Path
from datetime import datetime
import pandas as pd
import re
from openpyxl import load_workbook

RAW_DIR = Path("data/raw_emails")
OUTPUT_DIR = Path("data/compiled")
LOG_DIR = Path("logs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / "compile_log.txt"

sales_summary, order_type_rows, daypart_rows = [], [], []
subcategory_rows, labor_rows, tender_rows = [], [], []

def log(msg):
    with open(log_file, "a") as f:
        f.write(f"{msg}\\n")

def clean_label(x):
    if not isinstance(x, str):
        return str(x)
    return re.sub(r"^[^a-zA-Z0-9]*", "", x).strip()

def clean_num(x):
    if isinstance(x, (int, float)):
        return x
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return pd.NA
    if not isinstance(x, str):
        return pd.NA
    s = re.sub(r"[^\d.\\-]", "", x)
    if not re.search(r"\\d", s):
        return pd.NA
    try:
        return float(s)
    except ValueError:
        return pd.NA

for path in RAW_DIR.glob("store_*.xlsx"):
    stem_parts = path.stem.split("_")
    if len(stem_parts) != 4 or not (stem_parts[3].isdigit() and len(stem_parts[3]) == 8):
        log(f"⚠️ Skipping {path.name}: invalid filename format")
        continue

    pc, store, datestr = stem_parts[1:4]
    report_date = datetime.strptime(datestr, "%Y%m%d").date()

    wb = load_workbook(path, data_only=True, read_only=True)
    ws = wb.active
    rows = [r for r in ws.iter_rows(values_only=True) if any(r)]
    wb.close()

    # Section detection
    section_titles = [
        "Sales Mix Metrics", "Sales by Daypart", "Tender Type",
        "Labor Metrics", "Order Type", "Sales by Subcategory"
    ]
    section_indices = {}
    for idx, row in enumerate(rows):
        label = str(row[0]) if row and row[0] else ""
        for section in section_titles:
            if section.lower() in label.lower():
                section_indices[section] = idx

    # --- SALES MIX METRICS ---
    start = section_indices.get("Sales Mix Metrics", -1) + 1
    end = section_indices.get("Sales by Daypart", len(rows))
    d = {}
    for i in range(start, end):
        label = str(rows[i][0]) if rows[i] and rows[i][0] else ""
        key = clean_label(label)
        value = rows[i][1] if len(rows[i]) > 1 else None
        if key:
            d[key] = value
    sales_summary.append({
        "Store": store, "PC_Number": pc, "Date": report_date,
        "Gross_Sales": d.get("Dunkin Gross Sales", pd.NA),
        "Net_Sales": d.get("DD Net Sales", pd.NA),
        "DD_Adjusted_No_Markup": d.get("DD Adjusted Reportable Sales (w/o Delivery Markup)", pd.NA),
        "PA_Sales_Tax": d.get("Sales Tax", pd.NA),
        "DD_Discount": d.get("DD Discounts", pd.NA),
        "Guest_Count": d.get("Guest Count", pd.NA),
        "Avg_Check": d.get("Avg Check - MM", pd.NA),
        "Gift_Card_Sales": d.get("Gift Card Sales", pd.NA),
        "Void_Amount": d.get("Void Amount", pd.NA),
        "Refund": d.get("Refunds", pd.NA),
        "Void_Qty": d.get("Void Qty", pd.NA),
        "Cash_IN": d.get("Cash In", pd.NA)
    })

    # --- SALES BY DAYPART ---
    start = section_indices.get("Sales by Daypart", -1) + 1
    end = section_indices.get("Tender Type", len(rows))
    for i in range(start, end):
        r = rows[i]
        if r and isinstance(r[0], str) and r[0].strip().lower() not in {"daypart", "net sales"}:
            daypart_rows.append({
                "Store": store, "PC_Number": pc, "Date": report_date,
                "Daypart": r[0],
                "Net_Sales": clean_num(r[2]) if len(r) > 2 else pd.NA,
                "Percent_Sales": clean_num(r[3]) if len(r) > 3 else pd.NA,
                "Check_Count": clean_num(r[4]) if len(r) > 4 else pd.NA,
                "Avg_Check": clean_num(r[5]) if len(r) > 5 else pd.NA
            })

    # --- TENDER TYPE ---
    tender_map = {
        "4000059": "Discover",
        "4000061": "Visa",
        "4000060": "Mastercard",
        "4000058": "Amex",
        "4000065": "GC Redeem",
        "4000098": "Grub Hub",
        "4000106": "Uber Eats",
        "4000107": "Doordash"
    }

    start = section_indices.get("Tender Type", -1) + 1
    end = section_indices.get("Labor Metrics", len(rows))
    for i in range(start, end):
        r = rows[i]
        if r and isinstance(r[0], str):
            raw = r[0]
            if raw.strip().upper() == "GL":
                continue  # Skip GL row
            code = raw.strip().split()[0]
            desc = tender_map.get(code, code)
            tender_rows.append({
                "Store": store, "PC_Number": pc, "Date": report_date,
                "Tender_Type": desc,
                "Detail_Amount": clean_num(r[3]) if len(r) > 3 else pd.NA
            })


    # --- LABOR METRICS ---
    start = section_indices.get("Labor Metrics", -1) + 1
    end = section_indices.get("Order Type", len(rows))
    for i in range(start, end):
        r = rows[i]
        if (
            r and r[0] and isinstance(r[0], str)
            and str(r[0]).strip().lower() not in {"labor position", "order type (menu mix metrics)"}
        ):
            labor_rows.append({
                "Store": store, "PC_Number": pc, "Date": report_date,
                "Labor_Position": r[0],
                "Reg_Hours": clean_num(r[1]) if len(r) > 1 else pd.NA,
                "OT_Hours": clean_num(r[2]) if len(r) > 2 else pd.NA,
                "Total_Hours": clean_num(r[3]) if len(r) > 3 else pd.NA,
                "Reg_Pay": clean_num(r[4]) if len(r) > 4 else pd.NA,
                "OT_Pay": clean_num(r[5]) if len(r) > 5 else pd.NA,
                "Total_Pay": clean_num(r[6]) if len(r) > 6 else pd.NA,
                "Percent_Labor": clean_num(r[7]) if len(r) > 7 else pd.NA
            })

    # --- ORDER TYPE ---
    start = section_indices.get("Order Type", -1) + 1
    end = section_indices.get("Sales by Subcategory", len(rows))
    for i in range(start, end):
        r = rows[i]
        if r and r[0] and str(r[0]).strip().lower() != "order type":
            order_type_rows.append({
                "Store": store, "PC_Number": pc, "Date": report_date,
                "Order_Type": r[0],
                "Net_Sales": clean_num(r[1]) if len(r) > 1 else pd.NA,
                "Percent_Sales": clean_num(r[2]) if len(r) > 2 else pd.NA,
                "Guests": clean_num(r[3]) if len(r) > 3 else pd.NA,
                "Percent_Guest": clean_num(r[4]) if len(r) > 4 else pd.NA,
                "Avg_Check": clean_num(r[5]) if len(r) > 5 else pd.NA
            })

    # --- SALES BY SUBCATEGORY ---
    start = section_indices.get("Sales by Subcategory", -1) + 1
    for i in range(start, len(rows)):
        r = rows[i]
        if r and isinstance(r[0], str) and not r[0].lower().startswith("total") and r[0].lower() != "subcategory":
            subcategory_rows.append({
                "Store": store, "PC_Number": pc, "Date": report_date,
                "Subcategory": r[0],
                "Qty_Sold": clean_num(r[1]) if len(r) > 1 else pd.NA,
                "Net_Sales": clean_num(r[2]) if len(r) > 2 else pd.NA,
                "Percent_Sales": clean_num(r[3]) if len(r) > 3 else pd.NA
            })

# Export
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = OUTPUT_DIR / f"compiled_outputs_{ts}.xlsx"

with pd.ExcelWriter(output_path) as xlw:
    pd.DataFrame(sales_summary).to_excel(xlw, "sales_summary", index=False)
    pd.DataFrame(order_type_rows).to_excel(xlw, "sales_by_order_type", index=False)
    pd.DataFrame(subcategory_rows).to_excel(xlw, "sales_by_subcategory", index=False)
    pd.DataFrame(labor_rows).to_excel(xlw, "labor_metrics", index=False)
    pd.DataFrame(tender_rows).to_excel(xlw, "tender_type_metrics", index=False)
    pd.DataFrame(daypart_rows).to_excel(xlw, "sales_by_daypart", index=False)

# --- CLEANUP: Delete processed files ---
processed_files = list(RAW_DIR.glob("store_*.xlsx"))
deleted_count = 0

for file_path in processed_files:
    try:
        file_path.unlink()  # Delete the file
        deleted_count += 1
        log(f"✅ Deleted: {file_path.name}")
    except Exception as e:
        log(f"❌ Failed to delete {file_path.name}: {e}")

print(f"✅ Compiled output written to: {output_path.resolve()}")
print(f"🗑️  Deleted {deleted_count} processed files from {RAW_DIR}")
print(f"📄 Log file at: {log_file.resolve()}")