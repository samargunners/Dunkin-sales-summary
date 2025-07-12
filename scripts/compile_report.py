from pathlib import Path
from datetime import datetime
import pandas as pd
import re
from openpyxl import load_workbook

# --- CONFIGURATION ---
RAW_DIR = Path("data/raw_emails")
OUTPUT_DIR = Path("data/compiled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- OUTPUT CONTAINERS ---
sales_summary, order_type_rows, daypart_rows = [], [], []
subcategory_rows, labor_rows, tender_rows = [], [], []

TENDER_TYPE_MAP = {
    "4000059 Crdit Card - Discover": "Discover",
    "4000061 Credit Card - Visa": "Visa",
    "4000060 Credit Card - Mastercard": "Mastercard",
    "4000058 Credit Card - Amex": "Amex",
    "4000065 Gift Card Redeem": "GC Redeem",
    "4000098": "Grub Hub",
    "4000106": "Uber Eats",
    "4000107": "Doordash"
}

# --- UTILITIES ---
def find_section(ws, header):
    """Return the worksheet row index that contains `header`."""
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if row and header in str(row[0]):
            return i
    return -1

def safe_get(row, idx, default=""):
    return row[idx] if len(row) > idx else default

def is_end_of_section(row, stop_keyword):
    return row and isinstance(row[0], str) and stop_keyword in row[0]

# --- MAIN PROCESSING ---
for xlsx_file in RAW_DIR.glob("*.xlsx"):
    parts = xlsx_file.stem.split("_")
    if len(parts) < 3:
        continue

    store_pc, store_name, data_date = parts[0], parts[1], parts[2]
    try:
        data_date = datetime.strptime(data_date, "%Y%m%d").date()
    except ValueError:
        data_date = None

    wb = load_workbook(xlsx_file, data_only=True)
    ws = wb.active
    rows = [row for row in ws.iter_rows(values_only=True) if any(row)]

    # --- Sales Mix Metrics ---
    idx = find_section(ws, "Sales Mix Metrics")
    if idx != -1:
        metrics = {}
        i = idx + 1
        while i < len(rows) and not is_end_of_section(rows[i], "Sales by Daypart"):
            if rows[i][0]:
                metrics[str(rows[i][0]).strip()] = safe_get(rows[i], 1)
            i += 1

        sales_summary.append({
            "store": store_name,
            "pc_number": store_pc,
            "date": data_date,
            "gross_sales": metrics.get("Dunkin Gross Sales", ""),
            "net_sales": metrics.get("'= DD Net Sales", ""),
            "dd_adjusted_no_markup": metrics.get("DD Adjusted Reportable Sales (w/o Delivery Markup)", ""),
            "PA_Sales_Tax": metrics.get("'+ Sales Tax", ""),
            "DD_Discount": metrics.get("'- DD Discounts", ""),
            "Guest_Count": metrics.get("Guest Count", ""),
            "Avg_Check": metrics.get("Avg Check - MM", ""),
            "Gift_Card_Sales": metrics.get("Gift Card Sales", ""),
            "Void_Amount": metrics.get("Void Amount", ""),
            "Refund": metrics.get("Refunds", ""),
            "Void_Qty": metrics.get("Void Qty", ""),
            "Cash_IN": metrics.get("Cash In", "")
        })

    # --- Sales by Daypart ---
    idx = find_section(ws, "Sales by Daypart")
    if idx != -1:
        for row in rows[idx+2:]:
            if is_end_of_section(row, "Tender Type"):
                break
            if row[0] and not str(row[0]).strip().startswith("Daypart"):
                daypart_rows.append({
                    "Store": store_name,
                    "PC_Number": store_pc,
                    "Date": data_date,
                    "Daypart": row[0],
                    "Net_Sales": safe_get(row, 2),
                    "percent_sales": safe_get(row, 3),
                    "Check_Count": safe_get(row, 4),
                    "Avg_Check": safe_get(row, 5)
                })

    # --- Tender Type ---
    idx = find_section(ws, "Tender Type")
    if idx != -1:
        for row in rows[idx+2:]:
            if is_end_of_section(row, "Labor Metrics"):
                break
            if row[0]:
                tender_key = str(row[0]).strip()
                tender_rows.append({
                    "Store": store_name,
                    "PC_Number": store_pc,
                    "Date": data_date,
                    "Tender_Type": TENDER_TYPE_MAP.get(tender_key, tender_key),
                    "Detail_Amount": safe_get(row, 3)
                })

    # --- Labor Metrics ---
    idx = find_section(ws, "Labor Metrics")
    if idx != -1:
        for row in rows[idx+2:]:
            if row and isinstance(row[0], str) and "Order Type (" in row[0]:
                break
            if row[0]:
                labor_rows.append({
                    "Store": store_name,
                    "PC_Number": store_pc,
                    "Date": data_date,
                    "Labor_Position": row[0],
                    "Reg_Hours": safe_get(row, 1),
                    "OT_Hours": safe_get(row, 2),
                    "Total_Hours": safe_get(row, 3),
                    "Reg_Pay": safe_get(row, 4),
                    "OT_Pay": safe_get(row, 5),
                    "Total_Pay": safe_get(row, 6),
                    "percent_labor": safe_get(row, 7)
                })

    # --- Order Type ---
    idx = find_section(ws, "Order Type (Menu Mix Metrics)")
    if idx != -1:
        for row in rows[idx+2:]:
            if is_end_of_section(row, "Sales by Subcategory"):
                break
            if row[0]:
                order_type_rows.append({
                    "Store": store_name,
                    "PC_Number": store_pc,
                    "Date": data_date,
                    "Order_Type": row[0],
                    "Net_Sales": safe_get(row, 1),
                    "percent_sales": safe_get(row, 2),
                    "Guests": safe_get(row, 3),
                    "percent_guest": safe_get(row, 4),
                    "Avg_Check": safe_get(row, 5)
                })

    # --- Subcategory Sales ---
    idx = find_section(ws, "Sales by Subcategory")
    if idx != -1:
        i = idx + 2
        while i < len(rows):
            row = rows[i]
            if not row[0] or "Total" in str(row[0]):
                break
            subcategory_rows.append({
                "Store": store_name,
                "PC_Number": store_pc,
                "Date": data_date,
                "Subcategory": row[0],
                "Qty_Sold": safe_get(row, 1),
                "Net_Sales": safe_get(row, 2),
                "percent_sales": safe_get(row, 3)
            })
            i += 1

# --- EXPORT RESULTS ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = OUTPUT_DIR / f"compiled_outputs_{timestamp}.xlsx"
with pd.ExcelWriter(output_file) as writer:
    pd.DataFrame(sales_summary).to_excel(writer, sheet_name="sales_summary", index=False)
    pd.DataFrame(order_type_rows).to_excel(writer, sheet_name="sales_by_order_type", index=False)
    pd.DataFrame(subcategory_rows).to_excel(writer, sheet_name="sales_by_subcategory", index=False)
    pd.DataFrame(labor_rows).to_excel(writer, sheet_name="labor_metrics", index=False)
    pd.DataFrame(tender_rows).to_excel(writer, sheet_name="tender_type_metrics", index=False)
    pd.DataFrame(daypart_rows).to_excel(writer, sheet_name="sales_by_daypart", index=False)

print(f"✅ Output written to: {output_file.resolve()}")
