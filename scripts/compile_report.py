import os
import re
import pandas as pd
from pathlib import Path
import pdfplumber

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw_emails"
COMPILED_DIR = BASE_DIR / "data" / "compiled"

def extract_value(label, text, default=None, floatify=True):
    pattern = rf"{re.escape(label)}\s*\$?([-\d\.,]+)"
    match = re.search(pattern, text)
    if match:
        val = match.group(1).replace("$", "").replace(",", "")
        try:
            return float(val) if floatify else val
        except Exception:
            return val
    return default

def extract_table(section_title, text, columns, row_pattern, col_types=None):
    section = text.split(section_title, 1)[-1]
    lines = section.splitlines()
    rows = []
    for line in lines:
        m = re.match(row_pattern, line.strip())
        if m:
            row = list(m.groups())
            if col_types:
                for i, typ in enumerate(col_types):
                    if typ == "float":
                        try:
                            row[i] = float(row[i].replace("$", "").replace(",", ""))
                        except:
                            row[i] = None
            rows.append(dict(zip(columns, row)))
        elif not line.strip() or line.startswith("Total"):
            break
    return rows

def extract_labor_table(section_title, text, columns):
    section = text.split(section_title, 1)[-1]
    lines = section.splitlines()
    rows = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("Total"):
            continue
        parts = re.split(r'\s{2,}', line)
        if len(parts) == 8:
            try:
                row = {
                    columns[0]: parts[0],
                    columns[1]: float(parts[1]),
                    columns[2]: float(parts[2]),
                    columns[3]: float(parts[3]),
                    columns[4]: float(parts[4].replace("$", "").replace(",", "")),
                    columns[5]: float(parts[5].replace("$", "").replace(",", "")),
                    columns[6]: float(parts[6].replace("$", "").replace(",", "")),
                    columns[7]: float(parts[7].replace("%", ""))
                }
                rows.append(row)
            except Exception as e:
                print(f"⚠️ Error parsing labor row: {line} | {e}")
    return rows

def extract_daypart_table(section_title, text, columns):
    section = text.split(section_title, 1)[-1]
    lines = section.splitlines()
    rows = []
    for line in lines:
        line = line.strip()
        if re.match(r"^\$[\d\.,]+\s+[\d\.]+%\s+[\d\.,]+\s+\$[\d\.,]+$", line):
            try:
                parts = re.findall(r"[\d\.,]+", line)
                row = {
                    columns[0]: f"Daypart {len(rows)+1}",
                    columns[1]: float(parts[0].replace(",", "")),
                    columns[2]: float(parts[1]),
                    columns[3]: float(parts[2].replace(",", "")),
                    columns[4]: float(parts[3].replace(",", ""))
                }
                rows.append(row)
            except Exception as e:
                print(f"⚠️ Error parsing daypart row: {line} | {e}")
        elif "Total" in line:
            break
    return rows

def extract_tender_type_table(section_title, text, columns):
    section = text.split(section_title, 1)[-1]
    lines = section.splitlines()
    rows = []
    for line in lines:
        line = line.strip()
        if not line or "Total" in line:
            continue
        m = re.match(r"^\d+\s+(.+?)\s+\$([\d\.,\-]+)$", line)
        if m:
            tender, amount = m.groups()
            try:
                rows.append({
                    columns[0]: tender.strip(),
                    columns[1]: float(amount.replace(",", ""))
                })
            except Exception as e:
                print(f"⚠️ Error parsing tender: {line} | {e}")
    return rows

def compile_reports():
    COMPILED_DIR.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    order_type_rows = []
    daypart_rows = []
    subcategory_rows = []
    labor_rows = []
    tender_type_rows = []
    processed_files = []

    for file in RAW_DIR.glob("*.pdf"):
        print(f"📄 Processing: {file.name}")
        try:
            with pdfplumber.open(file) as pdf:
                text = "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )

            net_sales = extract_value("Net Sales (DD+BR)", text)
            guest_count = extract_value("Guest Count", text, floatify=False)
            avg_check = extract_value("Avg Check - MM", text)
            tax = extract_value("PA State Tax", text)
            gross_sales = extract_value("Dunkin Gross Sales", text)
            gift_card_sales = extract_value("Gift Card Sales", text)
            refunds = extract_value("Refunds", text)
            void_amount = extract_value("Void Amount", text)
            cash_in = extract_value("Cash In", text)
            deposits = extract_value("Bank Deposits", text)
            cash_diff = extract_value("Cash Over / Short", text)
            dd_sales_markup = extract_value("= DD Adjusted Reportable Sales (w/o Delivery Markup)", text)

            if None in [net_sales, guest_count, avg_check, tax, gross_sales]:
                print(f"❌ Skipping {file.name} due to missing summary fields.")
                continue

            store_date = file.stem.split("_")[-1]
            store_name = file.stem.split("_")[1] if "_" in file.stem else "UNKNOWN"

            summary_rows.append({
                "store_id": store_name,
                "date": store_date,
                "gross_sales": gross_sales,
                "net_sales": net_sales,
                "tax": tax,
                "guest_count": guest_count,
                "avg_check": avg_check,
                "gift_card_sales": gift_card_sales,
                "refunds": refunds,
                "void_amount": void_amount,
                "cash_in": cash_in,
                "deposits": deposits,
                "cash_over_short": cash_diff,
                "sales_w/o_markup": dd_sales_markup
            })

            # Order Type
            order_type_pattern = r"([A-Za-z: ]+)\s+\$?([\d\.,\-]+)\s+([\d\.]+%)\s+([\d\.,]+)\s+([\d\.]+%)\s+\$?([\d\.,\-]+)"
            order_types = extract_table("Order Type", text,
                ["order_type", "net_sales", "percent_sales", "guests", "percent_guest", "avg_check"],
                order_type_pattern,
                col_types=["str", "float", "float", "float", "float", "float"]
            )
            for r in order_types:
                order_type_rows.append({
                    "store_id": store_name,
                    "date": store_date,
                    "order_type": r["order_type"],
                    "net_sales": r["net_sales"],
                    "guests": r["guests"],
                    "avg_check": r["avg_check"]
                })

            # Daypart Table
            dayparts = extract_daypart_table("Sales by Daypart", text,
                ["daypart", "net_sales", "percent_sales", "check_count", "avg_check"]
            )
            for r in dayparts:
                daypart_rows.append({
                    "store_id": store_name,
                    "date": store_date,
                    **r
                })

            # Subcategory Table
            subcat_pattern = r"([A-Za-z &]+)\s+([\d,]+)\s+\$?([\d\.,\-]+)\s+([\d\.]+%)"
            subcats = extract_table("Sales by Subcategory", text,
                ["subcategory", "qty_sold", "net_sales", "percent_sales"],
                subcat_pattern,
                col_types=["str", "float", "float", "str"]
            )
            for r in subcats:
                subcategory_rows.append({
                    "store_id": store_name,
                    "date": store_date,
                    "subcategory": r["subcategory"],
                    "qty_sold": r["qty_sold"],
                    "net_sales": r["net_sales"],
                    "percent_sales": r["percent_sales"]
                })

            # Labor Table
            labors = extract_labor_table("Labor Metrics", text,
                ["position", "reg_hours", "ot_hours", "total_hours", "reg_pay", "ot_pay", "total_pay", "percent_labor"]
            )
            for r in labors:
                labor_rows.append({
                    "store_id": store_name,
                    "date": store_date,
                    **r
                })

            # Tender Type Table
            tenders = extract_tender_type_table("Tender Type", text, ["tender_type", "amount"])
            for r in tenders:
                tender_type_rows.append({
                    "store_id": store_name,
                    "date": store_date,
                    **r
                })

            processed_files.append(file)

        except Exception as e:
            print(f"❌ Error processing {file.name}: {e}")

    # Export CSVs
    pd.DataFrame(summary_rows).to_csv(COMPILED_DIR / "sales_summary.csv", index=False)
    pd.DataFrame(order_type_rows).to_csv(COMPILED_DIR / "sales_by_order_type.csv", index=False)
    pd.DataFrame(daypart_rows).to_csv(COMPILED_DIR / "sales_by_daypart.csv", index=False)
    pd.DataFrame(subcategory_rows).to_csv(COMPILED_DIR / "sales_by_subcategory.csv", index=False)
    pd.DataFrame(labor_rows).to_csv(COMPILED_DIR / "labor_metrics.csv", index=False)
    pd.DataFrame(tender_type_rows).to_csv(COMPILED_DIR / "tender_type_metrics.csv", index=False)

    # Optional: Delete processed files
    # for file in processed_files:
    #     try:
    #         os.remove(file)
    #         print(f"🗑️ Deleted: {file.name}")
    #     except Exception as e:
    #         print(f"Could not delete {file.name}: {e}")

if __name__ == "__main__":
    compile_reports()
