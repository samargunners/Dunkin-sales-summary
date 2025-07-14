# streamlit_app/pages/1_Executive_Summary.py

import streamlit as st
import pandas as pd
from utils.db import get_connection
from datetime import datetime
import plotly.express as px
from utils.exports import export_page_as_pdf
from io import StringIO

st.title("📊 Executive Summary")

# --- FILTER CONTEXT ---
conn = get_connection()

# Get available stores from the database
store_list = pd.read_sql("SELECT DISTINCT Store FROM sales_summary", conn)["store"].tolist()

# Store filter
selected_stores = st.multiselect("Select Stores", store_list, default=store_list)

# Date range filter
min_date = pd.read_sql("SELECT MIN(date) as min_date FROM sales_summary", conn)["min_date"].iloc[0]
max_date = pd.read_sql("SELECT MAX(date) as max_date FROM sales_summary", conn)["max_date"].iloc[0]

min_date = pd.to_datetime(min_date).date()
max_date = pd.to_datetime(max_date).date()

# Default: last 7 days or just min/max if not enough data
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

# Ensure date_range is a tuple of two dates
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    st.warning("Please select a valid date range.")
    st.stop()

if not selected_stores:
    st.warning("Please select at least one store.")
    st.stop()

query = """
SELECT * FROM sales_summary
WHERE Store IN ({})
  AND Date BETWEEN ? AND ?
""".format(
    ",".join([f"'{store}'" for store in selected_stores])
)

df = pd.read_sql(query, conn, params=(str(start_date), str(end_date)))

if df.empty:
    st.warning("No data found for selected filters.")
    st.stop()

# --- KPI METRICS ---
total_sales = df['net_sales'].sum()
total_guests = df['guest_count'].sum()
avg_check = df['avg_check'].mean()
total_discounts = df['dd_discount'].sum()

t1, t2, t3, t4 = st.columns(4)
t1.metric("Net Sales", f"${total_sales:,.2f}")
t2.metric("Guest Count", f"{int(total_guests):,}")
t3.metric("Avg Check", f"${avg_check:,.2f}")
t4.metric("Discounts Given", f"${total_discounts:,.2f}")

# --- CHARTS ---
st.markdown("---")
st.subheader("Sales Trend by Store")
trend = df.groupby(['date', 'store'])['net_sales'].sum().reset_index()
fig = px.line(trend, x='date', y='net_sales', color='store', markers=True)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Guest Count Distribution")
guest_fig = px.bar(df.groupby("store")["guest_count"].sum().reset_index(),
                   x="store", y="guest_count", text_auto=True)
st.plotly_chart(guest_fig, use_container_width=True)

st.subheader("Sales by Store")
pie_fig = px.pie(df, names='store', values='net_sales', hole=0.4)
st.plotly_chart(pie_fig, use_container_width=True)

# --- EXPORT TO PDF ---
with StringIO() as buffer:
    buffer.write("<h2>Executive Summary</h2>")
    buffer.write(f"<p><strong>Total Sales:</strong> ${total_sales:,.2f}</p>")
    buffer.write(f"<p><strong>Guest Count:</strong> {int(total_guests):,}</p>")
    buffer.write(f"<p><strong>Avg Check:</strong> ${avg_check:,.2f}</p>")
    buffer.write(f"<p><strong>Discounts Given:</strong> ${total_discounts:,.2f}</p>")
    buffer.write(df.to_html(index=False))
    st.session_state["_html_export_content"] = buffer.getvalue()

if st.button("📤 Export This Page to PDF"):
    export_page_as_pdf()
