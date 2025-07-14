# streamlit_app/pages/2_Sales_Mix.py

import streamlit as st
import pandas as pd
from utils.db import get_connection
import plotly.express as px

st.title("📦 Sales Mix Analysis")

conn = get_connection()

# --- FILTERS ---
store_list = pd.read_sql("SELECT DISTINCT store FROM sales_by_order_type", conn)["store"].tolist()
selected_stores = st.multiselect("Select stores", store_list, default=store_list)

min_date = pd.read_sql("SELECT MIN(Date) as min_date FROM sales_by_order_type", conn)["min_date"].iloc[0]
max_date = pd.read_sql("SELECT MAX(Date) as max_date FROM sales_by_order_type", conn)["max_date"].iloc[0]
min_date = pd.to_datetime(min_date).date()
max_date = pd.to_datetime(max_date).date()

if (max_date - min_date).days >= 6:
    default_start = max_date - pd.Timedelta(days=6)
else:
    default_start = min_date

date_range = st.date_input(
    "Select Date Range",
    value=(default_start, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    st.warning("Please select a valid date range.")
    st.stop()

if not selected_stores:
    st.warning("Please select at least one store.")
    st.stop()

# --- Order Type ---
order_type_query = """
SELECT * FROM sales_by_order_type
WHERE store IN ({}) AND Date BETWEEN ? AND ?
""".format(",".join([f"'{s}'" for s in selected_stores]))

order_df = pd.read_sql(order_type_query, conn, params=(str(start_date), str(end_date)))

# --- Subcategory ---
subcat_query = """
SELECT * FROM sales_by_subcategory
WHERE store IN ({}) AND Date BETWEEN ? AND ?
""".format(",".join([f"'{s}'" for s in selected_stores]))

subcat_df = pd.read_sql(subcat_query, conn, params=(str(start_date), str(end_date)))

if order_df.empty and subcat_df.empty:
    st.warning("No data for selected filters.")
    st.stop()

# --- Order Type Charts ---
st.subheader("Net Sales by Order Type")
order_grouped = order_df.groupby("order_type")["net_sales"].sum().reset_index()
fig_order = px.bar(order_grouped, x="order_type", y="net_sales", text_auto=True)
st.plotly_chart(fig_order, use_container_width=True)

st.subheader("Guest Count by Order Type")
guests_grouped = order_df.groupby("order_type")["guests"].sum().reset_index()
fig_guest = px.pie(guests_grouped, names="order_type", values="guests")
st.plotly_chart(fig_guest, use_container_width=True)

# --- Subcategory Charts ---
st.subheader("Sales by Product Subcategory")
subcat_sales = subcat_df.groupby("subcategory")["net_sales"].sum().reset_index()
fig_subcat = px.bar(subcat_sales, x="subcategory", y="net_sales", text_auto=True)
st.plotly_chart(fig_subcat, use_container_width=True)

st.subheader("Subcategory Share of Total Sales")
fig_subcat_pie = px.pie(subcat_sales, names="subcategory", values="net_sales")
st.plotly_chart(fig_subcat_pie, use_container_width=True)
