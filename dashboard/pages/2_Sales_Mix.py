# streamlit_app/pages/2_Sales_Mix.py

import streamlit as st
import pandas as pd
from utils.db import get_connection
import plotly.express as px

st.title("📦 Sales Mix Analysis")

conn = get_connection()
stores = st.session_state.get("selected_stores", [])
dates = st.session_state.get("date_range", [])

# --- Order Type ---
order_type_query = """
SELECT * FROM sales_by_order_type
WHERE Store IN ({}) AND Date BETWEEN ? AND ?
""".format(",".join([f"'{s}'" for s in stores]))

order_df = pd.read_sql(order_type_query, conn, params=(str(dates[0]), str(dates[1])))

# --- Subcategory ---
subcat_query = """
SELECT * FROM sales_by_subcategory
WHERE Store IN ({}) AND Date BETWEEN ? AND ?
""".format(",".join([f"'{s}'" for s in stores]))

subcat_df = pd.read_sql(subcat_query, conn, params=(str(dates[0]), str(dates[1])))

if order_df.empty and subcat_df.empty:
    st.warning("No data for selected filters.")
    st.stop()

# --- Order Type Charts ---
st.subheader("Net Sales by Order Type")
order_grouped = order_df.groupby("Order_Type")["Net_Sales"].sum().reset_index()
fig_order = px.bar(order_grouped, x="Order_Type", y="Net_Sales", text_auto=True)
st.plotly_chart(fig_order, use_container_width=True)

st.subheader("Guest Count by Order Type")
guests_grouped = order_df.groupby("Order_Type")["Guests"].sum().reset_index()
fig_guest = px.pie(guests_grouped, names="Order_Type", values="Guests")
st.plotly_chart(fig_guest, use_container_width=True)

# --- Subcategory Charts ---
st.subheader("Sales by Product Subcategory")
subcat_sales = subcat_df.groupby("Subcategory")["Net_Sales"].sum().reset_index()
fig_subcat = px.bar(subcat_sales, x="Subcategory", y="Net_Sales", text_auto=True)
st.plotly_chart(fig_subcat, use_container_width=True)

st.subheader("Subcategory Share of Total Sales")
fig_subcat_pie = px.pie(subcat_sales, names="Subcategory", values="Net_Sales")
st.plotly_chart(fig_subcat_pie, use_container_width=True)
