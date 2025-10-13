# scripts/compile_store_reports.py
# Compile consolidated “Consolidated Dunkin Sales Summary v2_*” attachments (all stores per file)
# → single Excel with six sheets EXACTLY matching the schema you provided.

from pathlib import Path
from datetime import datetime
import pandas as pd
import re
import unicodedata

# ───────────────────────────── Paths ─────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[1]  # .../Dunkin-Sales-Summary
RAW_DIR = BASE_DIR / "data" / "raw_emails"
OUTPUT_DIR = BASE_DIR / "data" / "compiled"
LOG_DIR = BASE_DIR / "logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "compile_log.txt"

def log(msg: str) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{msg}\n")

# ───────────────────── Expected schema (order enforced) ──────────
EXPECTED = {
    "sales_summary": [
        "Store", "PC_Number", "Date", "Gross_Sales", "Net_Sales",
        "DD_Adjusted_No_Markup", "PA_Sales_Tax", "DD_Discount", "Guest_Count",
        "Avg_Check", "Gift_Card_Sales", "Void_Amount", "Refund", "Void_Qty",
        "Paid_IN", "Paid_OUT", "Cash_IN"
    ],
    "sales_by_order_type": [
        "Store", "PC_Number", "Date", "Order_Type", "Net_Sales",
        "Percent_Sales", "Guests", "Percent_Guest", "Avg_Check"
    ],
    "sales_by_daypart": [
        "Store", "PC_Number", "Date", "Daypart", "Net_Sales",
        "Percent_Sales", "Check_Count", "Avg_Check"
    ],
    "sales_by_subcategory": [
        "Store", "PC_Number", "Date", "Subcategory", "Qty_Sold",
        "Net_Sales", "Percent_Sales"
    ],
    "labor_metrics": [
        "Store", "PC_Number", "Date", "Labor_Position", "Reg_Hours",
        "OT_Hours", "Total_Hours", "Reg_Pay", "OT_Pay", "Total_Pay", "Percent_Labor"
    ],
    "tender_type_metrics": [
        "Store", "PC_Number", "Date", "Tender_Type", "Detail_Amount"
    ],
}

# ───────────────────────────── Helpers ───────────────────────────
def clean_num(x):
    """Robust numeric cleaner: strips $, commas, %, spaces; keeps sign/decimals."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return pd.NA
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s in {"", "--", "—", "–"}:
        return pd.NA
    s = re.sub(r"[^\d.\-]", "", s)  # keep digits, dot, minus
    if not re.search(r"\d", s):
        return pd.NA
    try:
        return float(s)
    except ValueError:
        return pd.NA

def norm_cols(cols):
    return [re.sub(r"\s+", " ", str(c).strip()).lower() for c in cols]

def find_col(df: pd.DataFrame, patterns):
    """Return the first column whose normalized name matches any regex in patterns."""
    ncols = norm_cols(df.columns)
    for pat in patterns:
        rx = re.compile(pat, re.I)
        for i, c in enumerate(ncols):
            if rx.search(c):
                return df.columns[i]
    return None

def read_any_header(path: Path) -> pd.DataFrame:
    """Try header at rows 0/1/2/None to guess the right one."""
    tries = [{"header": 0}, {"header": 1}, {"header": 2}, {"header": None}]
    last_err = None
    for t in tries:
        try:
            df = pd.read_excel(path, engine="openpyxl", **t)
            if t["header"] is None:
                df.columns = [f"col_{i}" for i in range(df.shape[1])]
            return df
        except Exception as e:
            last_err = e
    raise last_err

def ensure_cols(df: pd.DataFrame, want: dict):
    """Return dict {wanted_name: found_column or None} for provided pattern lists."""
    found = {}
    for name, pats in want.items():
        found[name] = find_col(df, pats)
    return found

def pick_date_value(df: pd.DataFrame, date_col):
    """Pick a single date value from a date-like column if present."""
    if date_col and date_col in df.columns:
        s = pd.to_datetime(df[date_col], errors="coerce").dropna()
        if not s.empty:
            return s.iloc[0].date()
    return pd.NaT

def filename_date_fallback(filename: str):
    """Try to derive YYYY-MM-DD from filename if present."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    if m:
        try:
            return pd.to_datetime(m.group(1)).date()
        except Exception:
            return pd.NaT
    return pd.NaT

def force_schema(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """
    Ensure exactly EXPECTED[sheet_name] columns (order!). Add any missing columns with NA,
    and drop extras. Coerce Date to date (not datetime). PC_Number to string.
    """
    cols = EXPECTED[sheet_name]
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    # Drop extras, reorder
    df = df[cols].copy()

    # Date → date
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date

    # PC_Number → string (don’t lose leading zeros, if any)
    if "PC_Number" in df.columns:
        df["PC_Number"] = df["PC_Number"].astype(str).str.strip()

    return df

# ───────────────────── Output accumulators ───────────────────────
sales_summary = []
daypart_rows = []
tender_rows = []
labor_rows = []
order_type_rows = []
subcategory_rows = []

# ───────────────────── Category processors ───────────────────────
def process_menu_mix_metrics(df, pc_col, store_col, date_col, report_date):
    field_map = {
        "Gross_Sales": [r"gross\s*sales"],
        "Net_Sales": [r"net\s*sales"],
        "DD_Adjusted_No_Markup": [r"adjusted.*reportable.*(w/?o).*markup", r"adjusted.*w/o.*markup"],
        "PA_Sales_Tax": [r"sales\s*tax"],
        "DD_Discount": [r"dd\s*discount"],
        "Guest_Count": [r"guest\s*count"],
        "Avg_Check": [r"avg\s*check"],
        "Gift_Card_Sales": [r"gift\s*card\s*sales"],
        "Void_Amount": [r"void\s*amount"],
        "Refund": [r"refunds?"],
        "Void_Qty": [r"void\s*qty"],
        "Paid_IN": [r"paid\s*in"],
        "Paid_OUT": [r"paid\s*out"],
        "Cash_IN": [r"cash\s*in"],
    }
    colmap = {k: find_col(df, v) for k, v in field_map.items()}
    keep = [c for c in [pc_col, store_col, date_col] if c] + [c for c in colmap.values() if c]
    sub = df[keep].copy()

    ren = {}
    if pc_col: ren[pc_col] = "PC_Number"
    if store_col: ren[store_col] = "Store"
    if date_col: ren[date_col] = "Date"
    for out, col in colmap.items():
        if col: ren[col] = out
    sub = sub.rename(columns=ren)

    # Clean numerics
    for k in field_map.keys():
        if k in sub.columns:
            sub[k] = sub[k].map(clean_num)

    # Date fallback
    if "Date" not in sub.columns:
        sub["Date"] = report_date

    for _, r in sub.iterrows():
        sales_summary.append({
            "Store": r.get("Store", pd.NA),
            "PC_Number": r.get("PC_Number", pd.NA),
            "Date": r.get("Date", report_date),
            "Gross_Sales": r.get("Gross_Sales", pd.NA),
            "Net_Sales": r.get("Net_Sales", pd.NA),
            "DD_Adjusted_No_Markup": r.get("DD_Adjusted_No_Markup", pd.NA),
            "PA_Sales_Tax": r.get("PA_Sales_Tax", pd.NA),
            "DD_Discount": r.get("DD_Discount", pd.NA),
            "Guest_Count": r.get("Guest_Count", pd.NA),
            "Avg_Check": r.get("Avg_Check", pd.NA),
            "Gift_Card_Sales": r.get("Gift_Card_Sales", pd.NA),
            "Void_Amount": r.get("Void_Amount", pd.NA),
            "Refund": r.get("Refund", pd.NA),
            "Void_Qty": r.get("Void_Qty", pd.NA),
            "Paid_IN": r.get("Paid_IN", pd.NA),
            "Paid_OUT": r.get("Paid_OUT", pd.NA),
            "Cash_IN": r.get("Cash_IN", pd.NA),
        })

def process_daypart(df, pc_col, store_col, date_col, report_date):
    daypart_col = find_col(df, [r"^daypart$"])
    net_col     = find_col(df, [r"net\s*sales"])
    pct_col     = find_col(df, [r"(%|percent).*(sales)"])
    checks_col  = find_col(df, [r"check\s*count", r"checks?"])
    avg_col     = find_col(df, [r"avg\s*check"])
    keep = [c for c in [pc_col, store_col, date_col, daypart_col, net_col, pct_col, checks_col, avg_col] if c]
    sub = df[keep].copy()
    ren = {}
    if pc_col: ren[pc_col] = "PC_Number"
    if store_col: ren[store_col] = "Store"
    if date_col: ren[date_col] = "Date"
    if daypart_col: ren[daypart_col] = "Daypart"
    if net_col: ren[net_col] = "Net_Sales"
    if pct_col: ren[pct_col] = "Percent_Sales"
    if checks_col: ren[checks_col] = "Check_Count"
    if avg_col: ren[avg_col] = "Avg_Check"
    sub = sub.rename(columns=ren)

    for k in ["Net_Sales", "Percent_Sales", "Check_Count", "Avg_Check"]:
        if k in sub.columns:
            sub[k] = sub[k].map(clean_num)

    if "Date" not in sub.columns:
        sub["Date"] = report_date

    for _, r in sub.iterrows():
        daypart_rows.append({
            "Store": r.get("Store", pd.NA),
            "PC_Number": r.get("PC_Number", pd.NA),
            "Date": r.get("Date", report_date),
            "Daypart": r.get("Daypart", pd.NA),
            "Net_Sales": r.get("Net_Sales", pd.NA),
            "Percent_Sales": r.get("Percent_Sales", pd.NA),
            "Check_Count": r.get("Check_Count", pd.NA),
            "Avg_Check": r.get("Avg_Check", pd.NA),
        })

def process_tender(df, pc_col, store_col, date_col, report_date):
    tend_col = find_col(df, [r"tender", r"code", r"desc"])
    amt_col  = find_col(df, [r"amount|detail\s*amount|net"])
    keep = [c for c in [pc_col, store_col, date_col, tend_col, amt_col] if c]
    sub = df[keep].copy()
    ren = {}
    if pc_col: ren[pc_col] = "PC_Number"
    if store_col: ren[store_col] = "Store"
    if date_col: ren[date_col] = "Date"
    if tend_col: ren[tend_col] = "Tender_Type"
    if amt_col: ren[amt_col] = "Detail_Amount"
    sub = sub.rename(columns=ren)

    if "Detail_Amount" in sub.columns:
        sub["Detail_Amount"] = sub["Detail_Amount"].map(clean_num)

    tender_map = {
        "4000059": "Discover", "4000061": "Visa", "4000060": "Mastercard",
        "4000058": "Amex", "4000065": "GC Redeem", "4000098": "Grub Hub",
        "4000106": "Uber Eats", "4000107": "Doordash",
    }
    if "Tender_Type" in sub.columns:
        sub["Tender_Type"] = (
            sub["Tender_Type"].astype(str).str.strip()
            .map(lambda x: tender_map.get(x.split()[0], x))
        )

    if "Date" not in sub.columns:
        sub["Date"] = report_date

    for _, r in sub.iterrows():
        tender_rows.append({
            "Store": r.get("Store", pd.NA),
            "PC_Number": r.get("PC_Number", pd.NA),
            "Date": r.get("Date", report_date),
            "Tender_Type": r.get("Tender_Type", pd.NA),
            "Detail_Amount": r.get("Detail_Amount", pd.NA),
        })

def process_labor(df, pc_col, store_col, date_col, report_date):
    pos_col  = find_col(df, [r"labor.*position|^position$"])
    reg_h    = find_col(df, [r"reg(ular)?\s*hours?|straight\s*hours?"])
    ot_h     = find_col(df, [r"ot\s*hours?|overtime\s*hours?"])
    tot_h    = find_col(df, [r"total\s*hours?"])
    reg_pay  = find_col(df, [r"reg(ular)?\s*pay|straight\s*pay"])
    ot_pay   = find_col(df, [r"ot\s*pay|overtime\s*pay"])
    tot_pay  = find_col(df, [r"total\s*pay"])
    pct_lab  = find_col(df, [r"%|percent.*labor"])
    keep = [c for c in [pc_col, store_col, date_col, pos_col, reg_h, ot_h, tot_h, reg_pay, ot_pay, tot_pay, pct_lab] if c]
    sub = df[keep].copy()
    ren = {}
    if pc_col: ren[pc_col] = "PC_Number"
    if store_col: ren[store_col] = "Store"
    if date_col: ren[date_col] = "Date"
    if pos_col: ren[pos_col] = "Labor_Position"
    maps = {reg_h: "Reg_Hours", ot_h: "OT_Hours", tot_h: "Total_Hours",
            reg_pay: "Reg_Pay", ot_pay: "OT_Pay", tot_pay: "Total_Pay",
            pct_lab: "Percent_Labor"}
    for c, n in maps.items():
        if c:
            ren[c] = n
    sub = sub.rename(columns=ren)

    for k in ["Reg_Hours","OT_Hours","Total_Hours","Reg_Pay","OT_Pay","Total_Pay","Percent_Labor"]:
        if k in sub.columns:
            sub[k] = sub[k].map(clean_num)

    if "Date" not in sub.columns:
        sub["Date"] = report_date

    for _, r in sub.iterrows():
        labor_rows.append({
            "Store": r.get("Store", pd.NA),
            "PC_Number": r.get("PC_Number", pd.NA),
            "Date": r.get("Date", report_date),
            "Labor_Position": r.get("Labor_Position", pd.NA),
            "Reg_Hours": r.get("Reg_Hours", pd.NA),
            "OT_Hours": r.get("OT_Hours", pd.NA),
            "Total_Hours": r.get("Total_Hours", pd.NA),
            "Reg_Pay": r.get("Reg_Pay", pd.NA),
            "OT_Pay": r.get("OT_Pay", pd.NA),
            "Total_Pay": r.get("Total_Pay", pd.NA),
            "Percent_Labor": r.get("Percent_Labor", pd.NA),
        })

def process_order_type(df, pc_col, store_col, date_col, report_date):
    ot_col     = find_col(df, [r"^order\s*type$"])
    net_col    = find_col(df, [r"net\s*sales"])
    pct_sales  = find_col(df, [r"(%|percent).*(sales)"])
    guests     = find_col(df, [r"guests?|check\s*count"])
    pct_guest  = find_col(df, [r"(%|percent).*(guest|check)"])
    avg_check  = find_col(df, [r"avg\s*check"])
    keep = [c for c in [pc_col, store_col, date_col, ot_col, net_col, pct_sales, guests, pct_guest, avg_check] if c]
    sub = df[keep].copy()
    ren = {}
    if pc_col: ren[pc_col] = "PC_Number"
    if store_col: ren[store_col] = "Store"
    if date_col: ren[date_col] = "Date"
    if ot_col: ren[ot_col] = "Order_Type"
    if net_col: ren[net_col] = "Net_Sales"
    if pct_sales: ren[pct_sales] = "Percent_Sales"
    if guests: ren[guests] = "Guests"
    if pct_guest: ren[pct_guest] = "Percent_Guest"
    if avg_check: ren[avg_check] = "Avg_Check"
    sub = sub.rename(columns=ren)

    for k in ["Net_Sales","Percent_Sales","Guests","Percent_Guest","Avg_Check"]:
        if k in sub.columns:
            sub[k] = sub[k].map(clean_num)

    if "Date" not in sub.columns:
        sub["Date"] = report_date

    for _, r in sub.iterrows():
        order_type_rows.append({
            "Store": r.get("Store", pd.NA),
            "PC_Number": r.get("PC_Number", pd.NA),
            "Date": r.get("Date", report_date),
            "Order_Type": r.get("Order_Type", pd.NA),
            "Net_Sales": r.get("Net_Sales", pd.NA),
            "Percent_Sales": r.get("Percent_Sales", pd.NA),
            "Guests": r.get("Guests", pd.NA),
            "Percent_Guest": r.get("Percent_Guest", pd.NA),
            "Avg_Check": r.get("Avg_Check", pd.NA),
        })

def process_subcategory(df, pc_col, store_col, date_col, report_date):
    subcat = find_col(df, [r"subcategory"])
    qty    = find_col(df, [r"qty|quantity"])
    net    = find_col(df, [r"net\s*sales"])
    pct    = find_col(df, [r"(%|percent).*(sales)"])
    keep = [c for c in [pc_col, store_col, date_col, subcat, qty, net, pct] if c]
    sub = df[keep].copy()
    ren = {}
    if pc_col: ren[pc_col] = "PC_Number"
    if store_col: ren[store_col] = "Store"
    if date_col: ren[date_col] = "Date"
    if subcat: ren[subcat] = "Subcategory"
    if qty: ren[qty] = "Qty_Sold"
    if net: ren[net] = "Net_Sales"
    if pct: ren[pct] = "Percent_Sales"
    sub = sub.rename(columns=ren)

    if "Subcategory" in sub.columns:
        sub = sub[~sub["Subcategory"].astype(str).str.lower().str.startswith("total")]

    for k in ["Qty_Sold","Net_Sales","Percent_Sales"]:
        if k in sub.columns:
            sub[k] = sub[k].map(clean_num)

    if "Date" not in sub.columns:
        sub["Date"] = report_date

    for _, r in sub.iterrows():
        subcategory_rows.append({
            "Store": r.get("Store", pd.NA),
            "PC_Number": r.get("PC_Number", pd.NA),
            "Date": r.get("Date", report_date),
            "Subcategory": r.get("Subcategory", pd.NA),
            "Qty_Sold": r.get("Qty_Sold", pd.NA),
            "Net_Sales": r.get("Net_Sales", pd.NA),
            "Percent_Sales": r.get("Percent_Sales", pd.NA),
        })

# ─────────────────────────── Main flow ──────────────────────────
def process_file(path: Path):
    name = path.name
    nm_norm = unicodedata.normalize("NFKC", name).replace("\u00A0", " ")
    low = nm_norm.lower()
    log(f"Processing: {name}")

    df = read_any_header(path).dropna(how="all")
    if df.empty:
        log(f"  Skipped (empty): {name}")
        return

    # Auto-detect key columns
    keys = ensure_cols(df, {
        "pc":    [r"^pc\b", r"\bpc[\s_]*number", r"\bstore\s*#"],
        "store": [r"^store\b", r"\blocation", r"\bstore\s*name"],
        "date":  [r"^date\b", r"\breport\s*date", r"\bperiod\b"]
    })
    pc_col, store_col, date_col = keys["pc"], keys["store"], keys["date"]
    report_date = pick_date_value(df, date_col)
    if pd.isna(report_date):
        report_date = filename_date_fallback(nm_norm)

    # Route by filename category
    if "menu mix metrics" in low or "sales mix metrics" in low:
        process_menu_mix_metrics(df, pc_col, store_col, date_col, report_date)
    elif "sales by daypart" in low:
        process_daypart(df, pc_col, store_col, date_col, report_date)
    elif "tender type" in low:
        process_tender(df, pc_col, store_col, date_col, report_date)
    elif "labor hours" in low or "labor metrics" in low:
        process_labor(df, pc_col, store_col, date_col, report_date)
    elif "order type" in low:
        process_order_type(df, pc_col, store_col, date_col, report_date)
    elif "sales by subcategory" in low:
        process_subcategory(df, pc_col, store_col, date_col, report_date)
    else:
        log(f"  Skipped (no recognized category in name): {name}")

def main():
    # Accept both .xls/.xlsx and any prefix (e.g., YYYYMMDD_)
    candidates = list(RAW_DIR.glob("*.xls")) + list(RAW_DIR.glob("*.xlsx"))
    files = []
    for p in candidates:
        nm = unicodedata.normalize("NFKC", p.name).replace("\u00A0", " ").lower()
        if "consolidated dunkin sales summary v2" in nm:
            files.append(p)
    files = sorted(files)

    if not files:
        msg = f"No consolidated files found in {RAW_DIR}"
        log(msg)
        print(msg)
        return

    print(f"Found {len(files)} consolidated files in {RAW_DIR}")
    log(f"Found {len(files)} consolidated files in {RAW_DIR}")

    for p in files:
        try:
            process_file(p)
        except Exception as e:
            log(f"  ERROR processing {p.name}: {e}")

    # Build DataFrames
    sheets = {
        "sales_summary": pd.DataFrame(sales_summary),
        "sales_by_order_type": pd.DataFrame(order_type_rows),
        "sales_by_daypart": pd.DataFrame(daypart_rows),
        "sales_by_subcategory": pd.DataFrame(subcategory_rows),
        "labor_metrics": pd.DataFrame(labor_rows),
        "tender_type_metrics": pd.DataFrame(tender_rows),
    }

    # Force schema and write
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"compiled_outputs_{ts}.xlsx"

    with pd.ExcelWriter(out_path) as xlw:
        for sheet_name, df in sheets.items():
            df = force_schema(df, sheet_name)
            df.to_excel(excel_writer=xlw, sheet_name=sheet_name, index=False)

    # QA summary
    print("Rows written per sheet:")
    for sheet_name, df in sheets.items():
        df = force_schema(df, sheet_name)
        print(f"  - {sheet_name}: {len(df)}")

    print(f"Compiled output written to: {out_path}")
    print(f"Log file at: {LOG_FILE}")

if __name__ == "__main__":
    main()
