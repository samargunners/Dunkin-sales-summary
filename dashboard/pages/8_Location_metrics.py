import streamlit as st
import pandas as pd
from utils.db import get_connection

st.title("💵 Payroll Metrics Dashboard")

conn = get_connection()

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
