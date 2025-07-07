import os
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw_emails"
COMPILED_DIR = BASE_DIR / "data" / "compiled"

def compile_reports():
    COMPILED_DIR.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    order_type_rows = []
    daypart_rows = []
    tender_rows = []
    subcategory_rows = []
    labor_rows = []

    processed_files = []

    for file in RAW_DIR.glob("*.xlsx"):
        print(f"Processing: {file.name}")
        try:
            xl = pd.ExcelFile(file)
            store_date = file.stem.split("_")[-1]
            store_name = file.stem.split("_")[1]

            df = xl.parse(xl.sheet_names[0], header=None)

            # Updated safe_get to look in column 0 for label and return value from column 1
            def safe_get(label):
                result = df[df[0] == label]
                if not result.empty:
                    return result.iloc[0, 1]
                else:
                    print(f"  ⚠️  '{label}' not found in {file.name}")
                    return None

            net_sales = safe_get("Net Sales (DD+BR)")
            guest_count = safe_get("Guest Count")
            avg_check = safe_get("Avg Check - MM")
            tax = safe_get("PA State Tax")
            gross_sales = safe_get("Dunkin Gross Sales")
            gift_card_sales = safe_get("Gift Card Sales")
            refunds = safe_get("Refunds")
            void_amount = safe_get("Void Amount")
            cash_in = safe_get("Cash In")
            deposits = safe_get("Bank Deposits")
            cash_diff = safe_get("Cash Over / Short")

            # If any required value is missing, skip this file
            if None in [net_sales, guest_count, avg_check, tax, gross_sales]:
                print(f"  ❌ Skipping {file.name} due to missing summary fields.")
                continue

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
            })

            for idx, row in df.iterrows():
                if str(row[0]).strip().startswith("Order Type"):
                    order_df = df.iloc[idx+1:idx+14, :7]
                    order_df.columns = ["Order Type", "Net Sales", "% Sales", "Guests", "% Guest", "Avg Check", "EMPTY"]
                    for _, r in order_df.iterrows():
                        order_type_rows.append({
                            "store_id": store_name,
                            "date": store_date,
                            "order_type": r["Order Type"],
                            "net_sales": r["Net Sales"],
                            "guests": r["Guests"],
                            "avg_check": r["Avg Check"]
                        })
                elif str(row[0]).strip().startswith("Daypart"):
                    daypart_df = df.iloc[idx+1:idx+6, 1:7]
                    daypart_df.columns = ["Daypart", "Net Sales", "% Sales", "Check Count", "Avg Check", "EMPTY"]
                    for _, r in daypart_df.iterrows():
                        daypart_rows.append({
                            "store_id": store_name,
                            "date": store_date,
                            "daypart": r["Daypart"],
                            "net_sales": r["Net Sales"],
                            "check_count": r["Check Count"],
                            "avg_check": r["Avg Check"]
                        })
                elif str(row[0]).strip().startswith("Subcategory"):
                    subcat_df = df.iloc[idx+1:, :4]
                    subcat_df.columns = ["Subcategory", "Qty Sold", "Net Sales", "% Sales"]
                    for _, r in subcat_df.iterrows():
                        if pd.notna(r["Subcategory"]):
                            subcategory_rows.append({
                                "store_id": store_name,
                                "date": store_date,
                                "subcategory": r["Subcategory"],
                                "qty_sold": r["Qty Sold"],
                                "net_sales": r["Net Sales"],
                                "percent_sales": r["% Sales"]
                            })
                elif str(row[0]).strip().startswith("Labor Position"):
                    labor_df = df.iloc[idx+1:, :10]
                    labor_df.columns = ["Position", "Reg Hours", "OT Hours", "Total Hours", "Reg Pay", "OT Pay", "Total Pay", "% Labor", "", ""]
                    for _, r in labor_df.iterrows():
                        if pd.notna(r["Position"]):
                            labor_rows.append({
                                "store_id": store_name,
                                "date": store_date,
                                "position": r["Position"],
                                "reg_hours": r["Reg Hours"],
                                "ot_hours": r["OT Hours"],
                                "total_hours": r["Total Hours"],
                                "reg_pay": r["Reg Pay"],
                                "ot_pay": r["OT Pay"],
                                "total_pay": r["Total Pay"],
                                "percent_labor": r["% Labor"]
                            })
            processed_files.append(file)
        except Exception as e:
            print(f"Error processing {file.name}: {e}")

    # Write CSVs after all files processed
    pd.DataFrame(summary_rows).to_csv(COMPILED_DIR / "sales_summary.csv", index=False)
    pd.DataFrame(order_type_rows).to_csv(COMPILED_DIR / "sales_by_order_type.csv", index=False)
    pd.DataFrame(daypart_rows).to_csv(COMPILED_DIR / "sales_by_daypart.csv", index=False)
    pd.DataFrame(subcategory_rows).to_csv(COMPILED_DIR / "sales_by_subcategory.csv", index=False)
    pd.DataFrame(labor_rows).to_csv(COMPILED_DIR / "labor_metrics.csv", index=False)

    # Now delete processed files
    for file in processed_files:
        try:
            os.remove(file)
            print(f"🗑️ Deleted: {file.name}")
        except Exception as e:
            print(f"Could not delete {file.name}: {e}")

# Add this to run when called directly
if __name__ == "__main__":
    compile_reports()


