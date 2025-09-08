import streamlit as st
import pandas as pd
from utils.db import get_connection
from utils.supabase_db import get_supabase_connection

st.title("💵 Payroll Metrics Dashboard")

conn = get_connection()
supabase_conn = get_supabase_connection()

# --- FILTERS ---
store_list = pd.read_sql("SELECT DISTINCT store FROM labor_metrics", conn)["store"].tolist()
selected_store = st.selectbox("Select Store", store_list)

st.subheader("📅 Date Selection")
range_mode = st.checkbox("Select a date range instead of a single date?")

min_date = pd.read_sql("SELECT MIN(date) as min_date FROM labor_metrics", conn)["min_date"].iloc[0]
max_date = pd.read_sql("SELECT MAX(date) as max_date FROM labor_metrics", conn)["max_date"].iloc[0]
min_date = pd.to_datetime(min_date).date()
max_date = pd.to_datetime(max_date).date()

if range_mode:
    date_range = st.date_input(
        "Select Date Range",
        value=(max_date - pd.Timedelta(days=6), max_date),
        min_value=min_date,
        max_value=max_date,
        help="Select start and end date for analysis"
    )
    start_date, end_date = date_range
else:
    selected_date = st.date_input(
        "Select Date",
        value=max_date,
        min_value=min_date,
        max_value=max_date,
        help="Select a single date for analysis"
    )
    start_date = selected_date - pd.Timedelta(days=6)
    end_date = selected_date

from datetime import date, timedelta

# Helper functions
def get_period_dates(ref_date, period):
    if period == "week":
        start = ref_date - timedelta(days=6)
        end = ref_date
    elif period == "month":
        start = ref_date.replace(day=1)
        end = ref_date
    elif period == "quarter":
        q = (ref_date.month - 1) // 3 + 1
        start = date(ref_date.year, 3 * q - 2, 1)
        end = ref_date
    elif period == "year":
        start = date(ref_date.year, 1, 1)
        end = ref_date
    return start, end

def get_prev_period_dates(ref_date, period):
    if period == "week":
        end = ref_date - timedelta(days=7)
        start = end - timedelta(days=6)
    elif period == "month":
        first = ref_date.replace(day=1)
        end = first - timedelta(days=1)
        start = end.replace(day=1)
    elif period == "quarter":
        q = (ref_date.month - 1) // 3 + 1
        if q == 1:
            end = date(ref_date.year - 1, 12, 31)
            start = date(ref_date.year - 1, 10, 1)
        else:
            end = date(ref_date.year, 3 * (q - 1), 1) - timedelta(days=1)
            start = date(end.year, 3 * (q - 1) - 2, 1)
    elif period == "year":
        end = date(ref_date.year - 1, 12, 31)
        start = date(ref_date.year - 1, 1, 1)
    return start, end

def safe_div(a, b):
    return (a / b * 100) if b and b > 0 else None

# --- METRICS BOX 1: Labor Metrics ---
st.markdown("## Labor Metrics")
periods = ["week", "month", "quarter", "year"]
labels = ["Weekly", "MTD", "QTD", "YTD"]
labor_metrics = []
for period in periods:
    s, e = get_period_dates(end_date, period)
    payroll = pd.read_sql(
        "SELECT SUM(total_pay) as payroll_total FROM labor_metrics WHERE store = ? AND date BETWEEN ? AND ?",
        conn, params=[selected_store, s, e])["payroll_total"].iloc[0]
    sales = pd.read_sql(
        "SELECT SUM(net_sales) as sales_total FROM sales_summary WHERE store = ? AND date BETWEEN ? AND ?",
        conn, params=[selected_store, s, e])["sales_total"].iloc[0]
    pct = safe_div(payroll, sales)
    labor_metrics.append((labels[periods.index(period)], pct))
cols = st.columns(4)
for i, (label, pct) in enumerate(labor_metrics):
    if pct is not None:
        cols[i].metric(f"Labor % to Sales ({label})", f"{pct:.2f}%")
    else:
        cols[i].metric(f"Labor % to Sales ({label})", "N/A")

# --- METRICS BOX 2: Sales Metrics ---
st.markdown("## Sales Metrics")
sales_changes = []
for period in periods:
    curr_s, curr_e = get_period_dates(end_date, period)
    prev_s, prev_e = get_prev_period_dates(end_date, period)
    curr_sales = pd.read_sql(
        "SELECT SUM(net_sales) as sales_total FROM sales_summary WHERE store = ? AND date BETWEEN ? AND ?",
        conn, params=[selected_store, curr_s, curr_e])["sales_total"].iloc[0]
    prev_sales = pd.read_sql(
        "SELECT SUM(net_sales) as sales_total FROM sales_summary WHERE store = ? AND date BETWEEN ? AND ?",
        conn, params=[selected_store, prev_s, prev_e])["sales_total"].iloc[0]
    change = safe_div(curr_sales - prev_sales, prev_sales)
    sales_changes.append((labels[periods.index(period)], change))
cols = st.columns(4)
for i, (label, change) in enumerate(sales_changes):
    if change is not None:
        cols[i].metric(f"Sales % Change ({label})", f"{change:.2f}%")
    else:
        cols[i].metric(f"Sales % Change ({label})", "N/A")

# --- METRICS BOX 3: Guest Count Metrics ---
st.markdown("## Guest Count Metrics")
guest_changes = []
for period in periods:
    curr_s, curr_e = get_period_dates(end_date, period)
    prev_s, prev_e = get_prev_period_dates(end_date, period)
    curr_guests = pd.read_sql(
        "SELECT SUM(guest_count) as guest_total FROM sales_summary WHERE store = ? AND date BETWEEN ? AND ?",
        conn, params=[selected_store, curr_s, curr_e])["guest_total"].iloc[0]
    prev_guests = pd.read_sql(
        "SELECT SUM(guest_count) as guest_total FROM sales_summary WHERE store = ? AND date BETWEEN ? AND ?",
        conn, params=[selected_store, prev_s, prev_e])["guest_total"].iloc[0]
    change = safe_div(curr_guests - prev_guests, prev_guests)
    guest_changes.append((labels[periods.index(period)], change))
cols = st.columns(4)
for i, (label, change) in enumerate(guest_changes):
    if change is not None:
        cols[i].metric(f"Guest % Change ({label})", f"{change:.2f}%")
    else:
        cols[i].metric(f"Guest % Change ({label})", "N/A")


# --- METRICS BOX 4: Void Counts ---
st.markdown("## Void Counts")
void_counts = []
for period in periods:
    s, e = get_period_dates(end_date, period)
    void_qty = pd.read_sql(
        "SELECT SUM(void_qty) as void_total FROM sales_summary WHERE store = ? AND date BETWEEN ? AND ?",
        conn, params=[selected_store, s, e])["void_total"].iloc[0]
    void_counts.append((labels[periods.index(period)], void_qty))
cols = st.columns(4)
for i, (label, void_qty) in enumerate(void_counts):
    if void_qty is not None:
        cols[i].metric(f"Void Count ({label})", f"{int(void_qty)}")
    else:
        cols[i].metric(f"Void Count ({label})", "N/A")


# helper to compure weighted averages. 

def weighted_avg(series, weights):
    if series is None or weights is None:
        return None
    s = pd.Series(series)
    w = pd.Series(weights)
    denom = w.sum(skipna=True)
    return float((s * w).sum(skipna=True) / denom) if denom and denom > 0 else None

def format_secs(x):
    return f"{x:.0f} sec" if x is not None else "N/A"


#Period HME metrics (Weekly / MTD / QTD / YTD)

st.markdown("## 🚗 HME (Drive-Thru) Metrics")

hme_labels = ["Weekly", "MTD", "QTD", "YTD"]
hme_periods = ["week", "month", "quarter", "year"]

def fetch_hme(store, start, end):
    q = """
        SELECT date, time_measure, total_cars, menu_all, greet_all, service, lane_queue, lane_total
        FROM hme_report
        WHERE store = %s AND date BETWEEN %s AND %s
    """
    df = pd.read_sql(q, supabase_conn, params=[store, start, end])
    return df

def summarize_hme(df):
    if df is None or df.empty:
        return {
            "cars": 0,
            "menu_all": None,
            "greet_all": None,
            "service": None,
            "lane_queue": None,
            "lane_total": None
        }
    cars = df["total_cars"].fillna(0)
    return {
        "cars": int(cars.sum()),
        "menu_all": weighted_avg(df["menu_all"], cars),
        "greet_all": weighted_avg(df["greet_all"], cars),
        "service": weighted_avg(df["service"], cars),
        "lane_queue": weighted_avg(df["lane_queue"], cars),
        "lane_total": weighted_avg(df["lane_total"], cars),
    }

def pct_change(curr, prev):
    if prev is None or prev == 0 or curr is None:
        return None
    return (curr - prev) / prev * 100.0


# Build metric rows for each period + previous-period deltas
hme_rows = []
for per, label in zip(hme_periods, hme_labels):
    curr_s, curr_e = get_period_dates(end_date, per)
    prev_s, prev_e = get_prev_period_dates(end_date, per)

    df_curr = fetch_hme(selected_store, curr_s, curr_e)
    df_prev = fetch_hme(selected_store, prev_s, prev_e)

    s_curr = summarize_hme(df_curr)
    s_prev = summarize_hme(df_prev)

    hme_rows.append({
        "label": label,
        "curr": s_curr,
        "prev": s_prev,
        "delta": {
            "cars": pct_change(s_curr["cars"], s_prev["cars"]) if s_prev["cars"] else None,
            "menu_all": pct_change(s_curr["menu_all"], s_prev["menu_all"]),
            "greet_all": pct_change(s_curr["greet_all"], s_prev["greet_all"]),
            "service": pct_change(s_curr["service"], s_prev["service"]),
            "lane_queue": pct_change(s_curr["lane_queue"], s_prev["lane_queue"]),
            "lane_total": pct_change(s_curr["lane_total"], s_prev["lane_total"]),
        }
    })

# Top-line: Lane Total (primary), then Service, Greet, Menu, Cars
kpi_titles = [
    ("Lane Total (avg)", "lane_total"),
    ("Service (avg)", "service"),
    ("Greet (avg)", "greet_all"),
    ("Menu (avg)", "menu_all"),
    ("Cars (total)", "cars"),
]

for (title, key) in kpi_titles:
    cols = st.columns(4)
    for i, row in enumerate(hme_rows):
        curr_val = row["curr"][key]
        delta = row["delta"][key]

        if key == "cars":
            display = f"{int(curr_val) if curr_val is not None else 0}"
        else:
            display = format_secs(curr_val)

        if delta is None:
            cols[i].metric(f"{title} — {row['label']}", display)
        else:
            # For time-based metrics, a NEGATIVE % delta is GOOD (faster).
            # Streamlit’s metric "delta" arrow up=bad for time, but we can still show the %.
            # We’ll pass delta as-is; your team knows that ↓ is good on timing KPIs.
            cols[i].metric(f"{title} — {row['label']}", display, f"{delta:.1f}%")


st.markdown("### Daypart Breakdown (selected period)")

df_sel = fetch_hme(selected_store, start_date, end_date)

if df_sel.empty:
    st.info("No HME records for the selected period.")
else:
    # Aggregate by time_measure (daypart)
    agg = (
        df_sel
        .assign(total_cars=df_sel["total_cars"].fillna(0))
        .groupby("time_measure", dropna=False, as_index=False)
        .apply(lambda g: pd.Series({
            "total_cars": int(g["total_cars"].sum()),
            "menu_all_avg": weighted_avg(g["menu_all"], g["total_cars"]),
            "greet_all_avg": weighted_avg(g["greet_all"], g["total_cars"]),
            "service_avg": weighted_avg(g["service"], g["total_cars"]),
            "lane_queue_avg": weighted_avg(g["lane_queue"], g["total_cars"]),
            "lane_total_avg": weighted_avg(g["lane_total"], g["total_cars"]),
        }))
        .sort_values(by="time_measure")
        .reset_index(drop=True)
    )

    # Pretty formatting
    def fsec(v): return f"{v:.0f}" if v is not None else "—"
    agg_display = agg.copy()
    agg_display["menu_all_avg"] = agg_display["menu_all_avg"].map(fsec)
    agg_display["greet_all_avg"] = agg_display["greet_all_avg"].map(fsec)
    agg_display["service_avg"] = agg_display["service_avg"].map(fsec)
    agg_display["lane_queue_avg"] = agg_display["lane_queue_avg"].map(fsec)
    agg_display["lane_total_avg"] = agg_display["lane_total_avg"].map(fsec)
    agg_display.rename(columns={
        "time_measure": "Daypart",
        "total_cars": "Cars",
        "menu_all_avg": "Menu (avg sec)",
        "greet_all_avg": "Greet (avg sec)",
        "service_avg": "Service (avg sec)",
        "lane_queue_avg": "Lane Queue (avg sec)",
        "lane_total_avg": "Lane Total (avg sec)",
    }, inplace=True)

    st.dataframe(agg_display, use_container_width=True)

st.write(st.secrets.get("supabase", {}))
