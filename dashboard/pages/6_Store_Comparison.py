# streamlit_app/pages/6_Store_Comparison.py

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import get_connection

st.title("🏪 Store Comparison Dashboard")

conn = get_connection()
dates = st.session_state.get("date_range", [])

query = """
SELECT * FROM sales_summary
WHERE Date BETWEEN ? AND ?
"""

df = pd.read_sql(query, conn, params=(str(dates[0]), str(dates[1])))

if df.empty:
    st.warning("No sales summary data available.")
    st.stop()

# --- Aggregated Store Comparison ---
grouped = df.groupby("Store").agg({
    "Net_Sales": "sum",
    "Guest_Count": "sum",
    "Avg_Check": "mean",
    "DD_Discount": "sum",
    "Void_Amount": "sum",
    "Refund": "sum"
}).reset_index()

# --- Charts ---
st.subheader("Net Sales by Store")
fig_sales = px.bar(grouped, x="Store", y="Net_Sales", text_auto=True)
st.plotly_chart(fig_sales, use_container_width=True)

st.subheader("Guest Count by Store")
fig_guests = px.bar(grouped, x="Store", y="Guest_Count", text_auto=True)
st.plotly_chart(fig_guests, use_container_width=True)

st.subheader("Average Check by Store")
fig_check = px.bar(grouped, x="Store", y="Avg_Check", text_auto=True)
st.plotly_chart(fig_check, use_container_width=True)

st.subheader("Discount, Voids & Refunds by Store")
fig_misc = px.bar(
    grouped.melt(id_vars="Store", value_vars=["DD_Discount", "Void_Amount", "Refund"]),
    x="Store", y="value", color="variable", barmode="group"
)
st.plotly_chart(fig_misc, use_container_width=True)
