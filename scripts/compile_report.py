import pandas as pd
from pathlib import Path

# --------- CONFIGURATION ---------
EXCEL_PATH = "data/raw_emails/store_Enola_20250707.xlsx"
SHEET_NAME = "Dunkin Sales Summary 2024"
STORE_NAME = "Enola"
STORE_DATE = "20250707"
OUTPUT_DIR = Path("data/compiled")

# --------- LOAD EXCEL ---------
df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, header=None)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------- INIT OUTPUT ---------
summary = {}
order_type_rows = []
daypart_rows = []
subcategory_rows = []
labor_rows = []
tender_rows = []

# --------- SUMMARY ---------
summary_labels = {
    "Dunkin Gross Sales": "gross_sales",
    "Net Sales (DD+BR)": "net_sales",
    "PA State Tax": "tax",
    "Guest Count": "guest_count",
    "Avg Check - MM": "avg_check",
    "Gift Card Sales": "gift_card_sales",
    "Refunds": "refunds",
    "Void Amount": "void_amount",
    "Cash In": "cash_in",
    "Bank Deposits": "deposits",
    "Cash Over / Short": "cash_over_short",
    "= DD Adjusted Reportable Sales (w/o Delivery Markup)": "sales_w/o_markup"
}

for i, row in df.iterrows():
    key = str(row[0]).strip()
    if key in summary_labels:
        val = row[1]
        if isinstance(val, (int, float)):
            summary[summary_labels[key]] = val

summary.update({"store_id": STORE_NAME, "date": STORE_DATE})

# --------- ORDER TYPE ---------
order_start = df[df[0] == "Order Type (Menu Mix Metrics)"].index[0] + 2
for i in range(order_start, order_start + 20):
    row = df.iloc[i]
    if pd.isna(row[0]) or "Total" in str(row[0]):
        break
    try:
        order_type_rows.append({
            "store_id": STORE_NAME,
            "date": STORE_DATE,
            "order_type": row[0],
            "net_sales": float(row[1]),
            "guests": float(row[3]),
            "avg_check": float(str(row[5]).replace("$", ""))
        })
    except:
        continue

# --------- SUBCATEGORY ---------
subcategory_start = df[df[0] == "Sales by Subcategory"].index[0] + 2
for i in range(subcategory_start, subcategory_start + 40):
    row = df.iloc[i]
    if pd.isna(row[0]) or "Total" in str(row[0]):
        break
    try:
        subcategory_rows.append({
            "store_id": STORE_NAME,
            "date": STORE_DATE,
            "subcategory": row[0],
            "qty_sold": float(row[1]),
            "net_sales": float(row[2]),
            "percent_sales": row[3]
        })
    except:
        continue

# --------- LABOR METRICS ---------
labor_start = df[df[0] == "Labor Metrics"].index[0] + 1
for i in range(labor_start, labor_start + 5):
    row = df.iloc[i]
    if pd.isna(row[0]) or "Total" in str(row[0]):
        break
    try:
        labor_rows.append({
            "store_id": STORE_NAME,
            "date": STORE_DATE,
            "position": row[0],
            "reg_hours": float(row[1]),
            "ot_hours": float(row[2]),
            "total_hours": float(row[3]),
            "reg_pay": float(row[4]),
            "ot_pay": float(row[5]),
            "total_pay": float(row[6]),
            "percent_labor": float(str(row[7]).replace("%", ""))
        })
    except:
        continue

# --------- TENDER TYPE ---------
tender_start = df[df[0] == "Tender Type"].index[0] + 2
for i in range(tender_start, tender_start + 25):
    row = df.iloc[i]
    if pd.isna(row[0]) or "Total" in str(row[0]):
        break
    try:
        tender_rows.append({
            "store_id": STORE_NAME,
            "date": STORE_DATE,
            "tender_type": row[1],
            "amount": float(row[2])
        })
    except:
        continue

# --------- EXPORT ---------
pd.DataFrame([summary]).to_csv(OUTPUT_DIR / "sales_summary.csv", index=False)
pd.DataFrame(order_type_rows).to_csv(OUTPUT_DIR / "sales_by_order_type.csv", index=False)
pd.DataFrame(subcategory_rows).to_csv(OUTPUT_DIR / "sales_by_subcategory.csv", index=False)
pd.DataFrame(labor_rows).to_csv(OUTPUT_DIR / "labor_metrics.csv", index=False)
pd.DataFrame(tender_rows).to_csv(OUTPUT_DIR / "tender_type_metrics.csv", index=False)

# Note: Daypart extraction is omitted here due to inconsistent layout in Excel
