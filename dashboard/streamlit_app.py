import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

# --- CONFIGURATION ---
DB_PATH = Path("db/sales.db")

# --- FUNCTIONS ---
def load_data(table_name):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading data from {table_name}: {e}")
        return pd.DataFrame()

# --- SIDEBAR FILTERS ---
st.sidebar.title("Filters")
selected_table = st.sidebar.selectbox("Choose a data table", [
    "sales_summary",
    "sales_by_order_type",
    "sales_by_daypart",
    "sales_by_subcategory",
    "labor_metrics",
    "tender_type_metrics"
])

# --- MAIN DASHBOARD ---
st.title("📊 Sales and Operations Dashboard")

# Load the selected table
df = load_data(selected_table)

if df.empty:
    st.warning("No data available.")
else:
    # Optional filters by store and date
    with st.sidebar.expander("🔍 Filter by Store and Date"):
        store_options = sorted(df["store"].dropna().unique())
        selected_stores = st.multiselect("Store(s)", store_options, default=store_options)

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            min_date, max_date = df["date"].min(), df["date"].max()
            date_range = st.date_input("Date range", (min_date, max_date))
            if isinstance(date_range, tuple):
                start_date, end_date = date_range
                df = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]

        df = df[df["store"].isin(selected_stores)]

    st.subheader(f"📋 Data Preview: {selected_table}")
    st.dataframe(df, use_container_width=True)

    # Summary metrics
    st.subheader("📈 Summary Metrics")
    num_rows = len(df)
    num_stores = df["store"].nunique() if "store" in df.columns else "-"
    date_span = f"{df['date'].min().date()} to {df['date'].max().date()}" if "date" in df.columns else "-"
    st.markdown(f"**Rows:** {num_rows} | **Stores:** {num_stores} | **Date Range:** {date_span}")

    # Optional: Plotting for numeric fields
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        metric_to_plot = st.selectbox("📊 Select metric to plot", numeric_cols)
        st.line_chart(df.groupby("date")[metric_to_plot].sum().reset_index() if "date" in df.columns else df[[metric_to_plot]])
