# scripts/compile_store_reports.py

from pathlib import Path
from openpyxl import load_workbook
import pandas as pd
import re
import unicodedata

# =================== CONFIG ===================
DEBUG = True
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR  = BASE_DIR / "data" / "raw_emails"
OUT_DIR  = BASE_DIR / "data" / "compiled"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ========= STORE / PC MAPPING =========
LOC_TO_PC = {
    "301290 - 2820 Paxton St": "301290",
    "343939 - 807 E Main St": "343939",
    "357993 - 423 N Enola Rd": "357993",
    "358529 - 3929 Columbia Avenue": "358529",
    "359042 - 737 South Broad Street": "359042",
    "363271 - 1154 River Road": "363271",
    "364322 - 820 South Market Street": "364322",
}
PC_TO_STORE = {
    "301290":"Paxton","343939":"MountJoy","357993":"Enola",
    "358529":"Columbia","359042":"Lititz","363271":"Marietta","364322":"Etown",
}
# =====================================

# ---------------- Utilities ----------------
def log(msg: str) -> None:
    if DEBUG: print(msg)

def norm(s: str) -> str:
    if s is None: return ""
    return unicodedata.normalize("NFKC", str(s)).replace("\u00A0"," ").replace("\u2011","-").strip()

def key_loc(s: str) -> str:
    s = norm(s).lower()
    s = re.sub(r"[.,]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s

# location mapping (also accept tail-only address)
LOC_TO_PC_NORM = { key_loc(k): v for k, v in LOC_TO_PC.items() }
for k, pc in list(LOC_TO_PC_NORM.items()):
    m = re.match(r"^\d{6}\s*-\s*(.+)$", k)
    if m:
        LOC_TO_PC_NORM[m.group(1).strip()] = pc

def map_store_pc(location_name: str):
    k = key_loc(location_name)
    pc = LOC_TO_PC_NORM.get(k)
    if not pc:
        for kk, v in LOC_TO_PC_NORM.items():
            if kk in k or k in kk:
                pc = v; break
    store = PC_TO_STORE.get(pc) if pc else None
    return store, pc

def parse_first_date_from_filename(p: Path):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", p.name)
    return pd.to_datetime(m.group(1)).date() if m else None

def clean_num(x):
    if x is None or (isinstance(x, float) and pd.isna(x)): return pd.NA
    try:
        return float(re.sub(r"[^\d.\-]", "", str(x)))
    except Exception:
        return pd.NA

def drop_totals(df: pd.DataFrame, label_col: str) -> pd.DataFrame:
    if label_col not in df.columns:
        return df
    lab = df[label_col].astype(str).str.strip().str.lower()
    mask = lab.str.startswith("total") | lab.isin({"grand total","store total","overall total","totals"})
    return df.loc[~mask].copy()

# ------------- Excel Reading Helpers -------------

# --------- DETECTORS (by filename) -------------
def is_labor(name: str) -> bool: return "labor hours" in name
def is_menu_mix(name: str) -> bool: return "menu mix metrics" in name
def is_daypart(name: str) -> bool: return "sales by daypart" in name
def is_subcat(name: str) -> bool: return "sales by subcategory" in name
def is_tender(name: str) -> bool: return "tender type" in name or ("tender" in name and "type" in name)
def is_sales_summary(name: str) -> bool: return "sales mix detail" in name
def is_order_type(name: str) -> bool: return "menu mix metrics" in name

# ------------- CORE FLATTENER (shared) -------------
def flatten_blocked_sheet(raw_path: Path, subheaders: list[str], label_regex: str, label_out: str, fill_row2=True) -> Path:
    """
    Generic flattener for the "horizontal blocks per location" pattern.

    Steps:
      1) Read Excel file directly (without unmerging)
      2) Detect header row that contains label_regex (e.g. 'Labor Position Name' / 'Daypart' / 'Subcategory' / 'Revenue Center')
      3) Row 2 is location names; for each block (contiguous subheaders) slice data, map store/pc, add date
      4) Drop totals; numeric coercion on numeric-like columns
    """
    df0 = pd.read_excel(raw_path, header=None, sheet_name=0)  # first sheet

    # 2) Find header row by label_regex
    hdr_row_idx = None
    pattern = re.compile(label_regex, re.I)
    for i in range(min(30, len(df0))):
        row_texts = [norm(x) for x in df0.iloc[i].tolist()]
        if any(pattern.search(x) for x in row_texts):
            hdr_row_idx = i
            break
    if hdr_row_idx is None:
        raise ValueError(f"Header row not found by /{label_regex}/.")

    # 3) Locations are in row 2 (Excel indexing) => index 1
    loc_row = [norm(x) for x in df0.iloc[1].tolist()]

    headers = [norm(x) for x in df0.iloc[hdr_row_idx].tolist()]
    df = df0.iloc[hdr_row_idx + 1:].copy()
    df.columns = headers

    # Find label column index
    label_col = None
    for j, h in enumerate(headers):
        if pattern.search(h or ""):
            label_col = j; break
    if label_col is None:
        raise ValueError("Label column not found.")

    # Find all block starts by matching contiguous subheaders
    def headers_match(file_headers, expected_subheaders):
        """Check if file headers match expected subheaders with flexible matching"""
        if len(file_headers) != len(expected_subheaders):
            return False
        
        # Create mapping from expected to actual patterns
        mapping = {
            "reg_hours": ["reg hours", "regular hours"],
            "ot_hours": ["ot hours", "overtime hours"],
            "total_hours": ["total hours"],
            "reg_pay": ["reg pay", "regular pay"],
            "ot_pay": ["ot pay", "overtime pay"], 
            "total_pay": ["total pay"],
            "percent_labor": ["% labor", "percent labor", "labor %"],
            "net_sales": ["sales", "net sales"],
            "percent_sales": ["% sales", "% of sales", "percent sales"],
            "percent_guest": ["% guests", "percent guests"],
            "check_count": ["guest count", "check count"],
            "guests": ["guests", "guest count"],
            "avg_check": ["avg check", "average check"],
            "qty_sold": ["qty sold", "quantity sold"],
            "daypart": ["daypart"],
            "subcategory": ["subcategory", "subcategory name"],
            "order_type": ["revenue center"]
        }
        
        for i, expected in enumerate(expected_subheaders):
            file_header = file_headers[i].lower()
            patterns = mapping.get(expected.lower(), [expected.lower()])
            if not any(file_header.startswith(p) or p in file_header for p in patterns):
                return False
        return True
    
    starts = []
    L = len(subheaders) 
    for j in range(label_col + 1, len(headers) - L + 2):
        seq = [norm(x) for x in headers[j:j+L]]
        if headers_match(seq, subheaders):
            starts.append(j)
    if not starts:
        raise ValueError("No per-location blocks detected.")

    # 4) Build output
    date_val = parse_first_date_from_filename(raw_path)
    out_rows = []
    for st in starts:
        loc_name = loc_row[st] if st < len(loc_row) else ""
        store, pc = map_store_pc(loc_name)
        
        # Select columns by index position to avoid duplicate column name issues
        block_col_indices = [label_col] + list(range(st, st + L))
        blk = df.iloc[:, block_col_indices].copy()
        
        # Set proper column names directly
        new_columns = [label_out] + subheaders
        blk.columns = new_columns

        blk.insert(0, "store", store)
        blk.insert(1, "pc_number", str(pc) if pc else None)
        blk.insert(2, "date", pd.to_datetime(date_val))
        out_rows.append(blk)

    out_df = pd.concat(out_rows, ignore_index=True)
    out_df = drop_totals(out_df, label_out)

    # numeric coercion for numeric-ish columns
    for c in out_df.columns:
        lc = c.lower()
        if any(x in lc for x in ["hours","pay","net","%","qty","check","sales","amount","guests"]):
            if c not in {"store","pc_number","date",label_out}:
                out_df[c] = out_df[c].map(clean_num)

    # ordering
    metric_cols = [c for c in out_df.columns if c not in {"store","pc_number","date",label_out}]
    out_df = out_df[["store","pc_number","date",label_out] + metric_cols]

    out_path = OUT_DIR / (raw_path.stem + "_copy.xlsx")
    with pd.ExcelWriter(out_path) as xlw:
        out_df.to_excel(xlw, index=False, sheet_name="Sheet1")
    return out_path

# --------- Transformers using the shared core ---------
def flatten_labor_file(raw_path: Path) -> Path:
    subheaders = ["Reg Hours","OT Hours","Total Hours","Reg Pay","OT Pay","Total Pay","% Labor"]
    out_path = flatten_blocked_sheet(
        raw_path=raw_path,
        subheaders=subheaders,
        label_regex=r"labor\s*position\s*name",
        label_out="labor_position",
        fill_row2=True
    )
    
    # Post-process the labor file to match desired format
    df = pd.read_excel(out_path)
    
    # Filter out total rows and empty store/pc_number rows
    df = df[
        (df['store'].notna()) & 
        (df['store'] != '') & 
        (~df['labor_position'].astype(str).str.lower().str.startswith('total'))
    ].copy()
    
    # Format date as MM/DD/YY
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%m/%d/%y')
    
    # Keep pc_number as string (remove decimal point for integers)
    df['pc_number'] = df['pc_number'].fillna(0).astype(int).astype(str)
    
    # Save back to same path
    with pd.ExcelWriter(out_path) as xlw:
        df.to_excel(xlw, index=False, sheet_name="Sheet1")
    
    return out_path

def flatten_menu_mix_file(raw_path: Path) -> Path:
    """
    Handle Menu Mix Metrics files for sales_by_order_type table.
    This uses the blocked sheet format.
    """
    subheaders = ["net_sales","percent_sales","guests","percent_guest","avg_check"]
    return flatten_blocked_sheet(
        raw_path=raw_path,
        subheaders=subheaders,
        label_regex=r"revenue\s*center",
        label_out="order_type",
        fill_row2=True
    )

def flatten_sales_by_daypart_file(raw_path: Path) -> Path:
    # Updated subheaders based on actual file structure (4 columns per store)
    subheaders = ["net_sales","percent_sales","check_count","avg_check"]
    return flatten_blocked_sheet(
        raw_path=raw_path,
        subheaders=subheaders,
        label_regex=r"daypart",
        label_out="daypart",
        fill_row2=True
    )

def flatten_sales_by_subcategory_file(raw_path: Path) -> Path:
    # Updated subheaders based on actual file structure
    subheaders = ["qty_sold","net_sales","percent_sales"]
    return flatten_blocked_sheet(
        raw_path=raw_path,
        subheaders=subheaders,
        label_regex=r"subcategory.*name",
        label_out="subcategory",
        fill_row2=True
    )

# --------- Sales_summary (transpose + special output name) ---------
def build_sales_summary_outname(raw_path: Path) -> Path:
    name = raw_path.name
    m = re.match(r"^(.*?v2_)(.*?)(\s+\d{4}-\d{2}-\d{2}\s+to\s+\d{4}-\d{2}-\d{2}_\d{8}T\d{4})(\.xlsx)$", name, flags=re.I)
    if not m:
        newname = name.replace("Sales Mix Metrics", "Sales_summary")
        newname = newname.replace("Menu Mix Metrics", "Sales_summary")
        newname = re.sub(r"\.xlsx$", "_copy.xlsx", newname)
        return OUT_DIR / newname
    prefix, _cat, daterange, _ext = m.groups()
    return OUT_DIR / f"{prefix}Sales_summary{daterange}_copy.xlsx"

def flatten_sales_summary_horizontal(raw_path: Path) -> Path:
    """
    Handle Sales Mix Detail files with horizontal structure: locations as columns, metrics as rows.
    This transforms it into the sales_summary table format.
    """
    df = pd.read_excel(raw_path, header=None, sheet_name=0)
    
    # Row 1 contains location names (columns 1-7)
    locations = [norm(str(x)) for x in df.iloc[1].tolist()[1:] if norm(str(x)) != "" and str(x) != "nan"]
    
    # Create metric mapping from file rows to database columns
    metric_mapping = {
        "net sales": "net_sales",
        "dunkin gross sales": "gross_sales", 
        "dd adjusted reportable sales": "dd_adjusted_no_markup",
        "sales tax": "pa_sales_tax",
        "discounts": "dd_discount",
        "guest count": "guest_count",
        "avg check": "avg_check",
        "gift card sales": "gift_card_sales",
        "void amount": "void_amount",
        "refunds": "refund",
        "void transactions": "void_qty",
        "cash in": "cash_in",
        "paid in": "paid_in",
        "paid out": "paid_out"
    }
    
    # Extract data for each metric
    date_val = parse_first_date_from_filename(raw_path)
    sales_summary_rows = []
    
    # Process each location (column)
    for i, location in enumerate(locations):
        store, pc = map_store_pc(location)
        if not store or not pc:
            continue
            
        row_data = {
            "store": store,
            "pc_number": str(pc),
            "date": pd.to_datetime(date_val),
            "gross_sales": pd.NA,
            "net_sales": pd.NA,
            "dd_adjusted_no_markup": pd.NA,
            "pa_sales_tax": pd.NA,
            "dd_discount": pd.NA,
            "guest_count": pd.NA,
            "avg_check": pd.NA,
            "gift_card_sales": pd.NA,
            "void_amount": pd.NA,
            "refund": pd.NA,
            "void_qty": pd.NA,
            "cash_in": pd.NA,
            "paid_in": pd.NA,
            "paid_out": pd.NA
        }
        
        # Extract values for each metric from the corresponding row
        for row_idx in range(2, len(df)):  # Skip header rows 0-1
            metric_name = norm(str(df.iloc[row_idx, 0])).lower()
            
            # Find matching metric in mapping
            db_column = None
            for file_metric, db_col in metric_mapping.items():
                if metric_name.startswith(file_metric):
                    db_column = db_col
                    break
                    
            if db_column and i + 1 < df.shape[1]:  # +1 because locations start at column 1
                value_str = str(df.iloc[row_idx, i + 1])
                if value_str.lower() not in ["nan", ""]:
                    try:
                        if db_column in ["guest_count", "void_qty"]:
                            row_data[db_column] = int(float(value_str))
                        else:
                            row_data[db_column] = float(value_str)
                    except (ValueError, TypeError):
                        pass  # Keep as pd.NA
        
        sales_summary_rows.append(row_data)
    
    result_df = pd.DataFrame(sales_summary_rows)
    
    out_path = build_sales_summary_outname(raw_path)
    with pd.ExcelWriter(out_path) as xlw:
        result_df.to_excel(xlw, index=False, sheet_name="Sheet1")
    return out_path

# --------- Tender Type (mapping) ---------
TENDER_MAP = {
    "credit card - amex": "Amex",
    "credit card - discover": "Discover",
    "credit card - mastercard": "Mastercard",
    "credit card - visa": "Visa",
    "visa - kiosk": "Visa-Kiosk",
    "gift card redeem": "GC Redeem",
    "clover go": "Clover Go",
    "delivery: doordash": "Doordash",
    "delivery: uber eats": "Uber Eats",
    "grub hub": "Grub Hub",
}
def map_tender_label(s: str) -> str:
    k = norm(s).lower()
    for pat, out in TENDER_MAP.items():
        if k == pat or pat in k:
            return out
    return norm(s)

def flatten_tender_type_file(raw_path: Path) -> Path:
    """
    Handle Tender Type files with horizontal structure: locations as columns, tender types as rows.
    Structure:
    Row 0: "Sum of Amount", "nan", "LOCATION NAME", ...
    Row 1: "Sales Mix Tran Type", "GL Description", "301290 - 2820 Paxton St", "343939 - 807 E Main St", ...
    Row 2+: "Category", "Tender Type", amount1, amount2, amount3, ...
    """
    df = pd.read_excel(raw_path, header=None, sheet_name=0)
    
    # For this format, row 1 contains location names starting from column 2
    location_row = df.iloc[1].tolist()
    locations = [norm(str(x)) for x in location_row[2:] if norm(str(x)) != "" and str(x) != "nan"]
    
    # Remove "Total" column if it exists
    if locations and locations[-1].lower() == "total":
        locations = locations[:-1]
    
    if not locations:
        raise ValueError("TENDER: No locations found in header row")
    
    # Build output rows
    date_val = parse_first_date_from_filename(raw_path)
    out_rows = []
    
    for i in range(2, len(df)):  # Start from row 2 (data rows)
        row_data = df.iloc[i].tolist()
        category = norm(str(row_data[0])) if len(row_data) > 0 else ""
        tender_type = norm(str(row_data[1])) if len(row_data) > 1 else ""
        
        # Skip if both category and tender_type are empty/nan, or if it's a total row
        if (category.lower() in ["nan", ""] and tender_type.lower() in ["nan", ""]) or \
           category.lower().startswith("total") or tender_type.lower().startswith("total"):
            continue
            
        # Use tender_type if available, otherwise use category
        tender_label = tender_type if tender_type and tender_type.lower() != "nan" else category
        if not tender_label or tender_label.lower() in ["nan", ""]:
            continue
            
        # Map the tender label
        tender_label = map_tender_label(tender_label)
        
        # Process amounts for each location
        for j, location in enumerate(locations):
            amount_col_idx = j + 2  # Amounts start at column 2
            if amount_col_idx < len(row_data):
                amount_str = str(row_data[amount_col_idx])
                if amount_str.lower() not in ["nan", ""]:
                    amount = clean_num(amount_str)
                    if pd.notna(amount) and amount != 0:  # Only include non-zero amounts
                        store, pc = map_store_pc(location)
                        out_rows.append({
                            "store": store,
                            "pc_number": str(pc) if pc else None, 
                            "date": pd.to_datetime(date_val),
                            "tender_type": tender_label,
                            "detail_amount": amount
                        })
    
    if not out_rows:
        raise ValueError("TENDER: No valid data rows found")
        
    out_df = pd.DataFrame(out_rows)
    
    out_path = OUT_DIR / (raw_path.stem + "_copy.xlsx")
    with pd.ExcelWriter(out_path) as xlw:
        out_df.to_excel(xlw, index=False, sheet_name="Sheet1")
    return out_path

# ------------- Dispatcher -------------
def process_one_input(path: Path) -> bool:
    name_low = norm(path.name).lower()
    log(f"\n=== Processing: {path.name} ===")
    try:
        if is_labor(name_low):
            outp = flatten_labor_file(path); log(f"OK (labor) → {outp.name}"); return True
        if is_order_type(name_low):
            outp = flatten_menu_mix_file(path); log(f"OK (order_type) → {outp.name}"); return True
        if is_daypart(name_low):
            outp = flatten_sales_by_daypart_file(path); log(f"OK (daypart) → {outp.name}"); return True
        if is_subcat(name_low):
            outp = flatten_sales_by_subcategory_file(path); log(f"OK (subcategory) → {outp.name}"); return True
        if is_tender(name_low):
            outp = flatten_tender_type_file(path); log(f"OK (tender) → {outp.name}"); return True
        if is_sales_summary(name_low):
            outp = flatten_sales_summary_horizontal(path); log(f"OK (sales_summary) → {outp.name}"); return True

        log("SKIP: No matching transformer for this file.")
        return False
    except Exception as e:
        log(f"ERROR: {e}")
        return False

def main():
    files = [p for p in sorted(RAW_DIR.glob("*.xlsx")) + sorted(RAW_DIR.glob("*.xls"))
             if not p.name.endswith("_copy.xlsx")]
    if not files:
        log(f"No raw Excel files in {RAW_DIR}")
        return
    ok = fail = 0
    for f in files:
        if process_one_input(f): ok += 1
        else: fail += 1
    log(f"\nDone. Success: {ok}  Failed: {fail}")

if __name__ == "__main__":
    main()
