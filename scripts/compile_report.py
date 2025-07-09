import pandas as pd
from pathlib import Path

# --------- CONFIGURATION ---------
RAW_DIR = Path("data/raw_emails")
OUTPUT_DIR = Path("data/compiled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------- INIT OUTPUT ---------
summaries = []
order_type_rows = []
daypart_rows = []
subcategory_rows = []
labor_rows = []
tender_rows = []

# --------- LOOP THROUGH FILES ---------
for excel_path in RAW_DIR.glob("*.xlsx"):
    try:
        df = pd.read_excel(excel_path, header=None)
    except Exception as e:
        print(f"⚠️ Could not read {excel_path.name}: {e}")
        continue

    store_parts = excel_path.stem.split("_")
    store_pc = store_parts[0]
    store_name = store_parts[1] if len(store_parts) > 1 else "UNKNOWN"

    # --------- SUMMARY ---------
    summary = {
        "Store": store_name,
        "PC Number": store_pc
    }
    summary_labels = {
        "Dunkin Gross Sales": "Gross Sales",
        "Net Sales (DD+BR)": "Net Sales",
        "= DD Adjusted Reportable Sales (w/o Delivery Markup)": "DD Adjusted w/0 Markup",
        "PA State Tax": "PA Sales Tax",
        "DD Discount": "DD Discount",
        "Guest Count": "Guest Count",
        "Avg Check - MM": "Avg Check",
        "Gift Card Sales": "Gift Card Sales",
        "Void Amount": "Void Amount",
        "Refunds": "Refund",
        "Void Qty": "Void Qty",
        "Cash In": "Cash IN"
    }
    for _, row in df.iterrows():
        label = str(row[0]).strip()
        if label in summary_labels:
            summary[summary_labels[label]] = row[1]
    summaries.append(summary)

    # --------- ORDER TYPE ---------
    try:
        order_start = df[df[0] == "Order Type (Menu Mix Metrics)"].index[0] + 2
        for i in range(order_start, order_start + 20):
            row = df.iloc[i]
            if pd.isna(row[0]) or "Total" in str(row[0]): break
            order_type_rows.append({
                "Store": store_name,
                "PC Number": store_pc,
                "Order Type": row[0],
                "Net Sales": row[1],
                "% Sales": row[2],
                "Guests": row[3]
            })
    except: pass

    # --------- SUBCATEGORY ---------
    try:
        sub_start = df[df[0] == "Sales by Subcategory"].index[0] + 2
        for i in range(sub_start, sub_start + 40):
            row = df.iloc[i]
            if pd.isna(row[0]) or "Total" in str(row[0]): break
            subcategory_rows.append({
                "Store": store_name,
                "PC Number": store_pc,
                "Subcategory": row[0],
                "Qty Sold": row[1],
                "Net Sales": row[2]
            })
    except: pass

    # --------- LABOR METRICS ---------
    try:
        labor_start = df[df[0] == "Labor Metrics"].index[0] + 1
        for i in range(labor_start, labor_start + 10):
            row = df.iloc[i]
            if pd.isna(row[0]) or "Total" in str(row[0]): break
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
    except: pass

    # --------- TENDER TYPE ---------
    try:
        tender_start = df[df[0] == "Tender Type"].index[0] + 2
        for i in range(tender_start, tender_start + 25):
            row = df.iloc[i]
            if pd.isna(row[0]) or "Total" in str(row[0]): break
            tender_rows.append({
                "Store": store_name,
                "PC number": store_pc,
                "Metrics": row[1],
                "Detail Amount": row[2]
            })
    except: pass

    # --------- DAYPART ---------
    try:
        daypart_start = df[df[0] == "Sales by Daypart"].index[0] + 2
        for i in range(daypart_start, daypart_start + 20):
            row = df.iloc[i]
            if pd.isna(row[0]) or "Total" in str(row[0]): break
            daypart_rows.append({
                "Store ": store_name,
                "PC Number": store_pc,
                "Daypart": row[0],
                "metrics": row[1],
                "netsales": row[2],
                "% Sales": row[3],
                "Check Count": row[4],
                "Avg Check ": row[5]
            })
    except: pass

# --------- EXPORT TO XLSX ---------
with pd.ExcelWriter(OUTPUT_DIR / "compiled_outputs.xlsx") as writer:
    pd.DataFrame(summaries).to_excel(writer, sheet_name="sales_summary", index=False)
    pd.DataFrame(order_type_rows).to_excel(writer, sheet_name="sales_by_order_type", index=False)
    pd.DataFrame(subcategory_rows).to_excel(writer, sheet_name="sales_by_subcategory", index=False)
    pd.DataFrame(labor_rows).to_excel(writer, sheet_name="labor_metrics", index=False)
    pd.DataFrame(tender_rows).to_excel(writer, sheet_name="tender_type_metrics", index=False)
    pd.DataFrame(daypart_rows).to_excel(writer, sheet_name="sales_by_daypart", index=False)
