# Re-import necessary modules after kernel reset
from pathlib import Path
import pandas as pd
import re

# CONFIGURATION
RAW_DIR = Path("data/raw_emails")
OUTPUT_DIR = Path("data/compiled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# INIT OUTPUT LISTS
summaries = []
order_type_rows = []
daypart_rows = []
subcategory_rows = []
labor_rows = []
tender_rows = []

# Read and process .txt files
for txt_file in RAW_DIR.glob("*.txt"):
    with open(txt_file, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Extract store info from filename
    parts = txt_file.stem.split("_")
    store_pc = parts[1]
    store_name = parts[2]

    # Clean and parse key-value pairs
    text = "\n".join(lines)

    def extract_value(label, default=""):
        pattern = rf"{label}\s*\n*\$?(-?\$?\d[\d,.]*)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else default

    summary = {
        "Store": store_name,
        "PC Number": store_pc,
        "Gross Sales": extract_value("Dunkin Gross Sales"),
        "Net Sales": extract_value("Net Sales \\(DD\\+BR\\)"),
        "DD Adjusted w/0 Markup": extract_value("DD Adjusted Reportable Sales \\(w/o\\ Delivery\\ Markup\\)"),
        "PA Sales Tax": extract_value("PA State Tax"),
        "DD Discount": extract_value("DD Discounts"),
        "Guest Count": extract_value("Guest Count"),
        "Avg Check": extract_value("Avg Check - MM"),
        "Gift Card Sales": extract_value("Gift Card Sales"),
        "Void Amount": extract_value("Void Amount"),
        "Refund": extract_value("Refunds"),
        "Void Qty": extract_value("Void Qty"),
        "Cash IN": extract_value("Cash In")
    }
    summaries.append(summary)

    # Extract table from sections
    def extract_table(start_label, num_columns):
        table = []
        if start_label in text:
            start_index = lines.index(start_label)
            headers = lines[start_index + 1:start_index + 1 + num_columns]
            i = start_index + 1 + num_columns
            while i < len(lines) and not lines[i].startswith("Total") and not re.match(r"[A-Za-z ]+:$", lines[i]):
                row = lines[i:i + num_columns]
                if len(row) == num_columns:
                    table.append(row)
                    i += num_columns
                else:
                    break
        return table

    # Order Type
    order_type_table = extract_table("Order Type (Menu Mix Metrics)", 6)
    for row in order_type_table:
        order_type_rows.append({
            "Store": store_name,
            "PC Number": store_pc,
            "Order Type": row[0],
            "Net Sales": row[1],
            "% Sales": row[2],
            "Guests": row[3]
        })

    # Daypart
    if "Sales by Daypart" in text:
        start_idx = lines.index("Sales by Daypart") + 1
        for i in range(start_idx, len(lines), 5):
            row = lines[i:i + 5]
            if len(row) == 5 and re.match(r"Daypart \d", row[0]):
                daypart_rows.append({
                    "Store ": store_name,
                    "PC Number": store_pc,
                    "Daypart": row[0],
                    "metrics": row[1],
                    "netsales": row[2],
                    "% Sales": row[3],
                    "Check Count": row[4]
                })
            else:
                break

    # Subcategory
    if "Sales by Subcategory" in text:
        start_idx = lines.index("Sales by Subcategory") + 1
        for i in range(start_idx, len(lines), 4):
            row = lines[i:i + 4]
            if len(row) == 4 and row[0] not in ["Total"]:
                subcategory_rows.append({
                    "Store": store_name,
                    "PC Number": store_pc,
                    "Subcategory": row[0],
                    "Qty Sold": row[1],
                    "Net Sales": row[2]
                })
            else:
                break

    # Labor
    if "Labor Metrics" in text:
        start_idx = lines.index("Labor Metrics") + 1
        for i in range(start_idx, len(lines), 8):
            row = lines[i:i + 8]
            if len(row) == 8 and row[0] != "Total":
                labor_rows.append({
                    "store ": store_name,
                    "pc number": store_pc,
                    "Labor Position": row[0],
                    "Reg Hours": row[1],
                    "OT Hours": row[2],
                    "Total Hours": row[3],
                    "Reg Pay": row[4],
                    "OT Pay": row[5],
                    "Total Pay": row[6],
                    "% Labor": row[7]
                })
            else:
                break

    # Tender Type
    if "Tender Type" in text:
        start_idx = lines.index("Tender Type") + 1
        for i in range(start_idx, len(lines), 4):
            row = lines[i:i + 4]
            if len(row) == 4 and row[0] not in ["Total"]:
                tender_rows.append({
                    "Store": store_name,
                    "PC number": store_pc,
                    "Metrics": row[2],
                    "Detail Amount": row[3]
                })
            else:
                break

# EXPORT TO EXCEL
output_file = OUTPUT_DIR / "compiled_outputs.xlsx"
with pd.ExcelWriter(output_file) as writer:
    pd.DataFrame(summaries).to_excel(writer, sheet_name="sales_summary", index=False)
    pd.DataFrame(order_type_rows).to_excel(writer, sheet_name="sales_by_order_type", index=False)
    pd.DataFrame(subcategory_rows).to_excel(writer, sheet_name="sales_by_subcategory", index=False)
    pd.DataFrame(labor_rows).to_excel(writer, sheet_name="labor_metrics", index=False)
    pd.DataFrame(tender_rows).to_excel(writer, sheet_name="tender_type_metrics", index=False)
    pd.DataFrame(daypart_rows).to_excel(writer, sheet_name="sales_by_daypart", index=False)

output_file.name
