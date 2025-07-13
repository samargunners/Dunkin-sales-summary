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
stores = st.session_state.get("selected_stores", [])
dates = st.session_state.get("date_range", [])

query = """
SELECT * FROM sales_summary
WHERE Store IN ({})
  AND Date BETWEEN ? AND ?
""".format(
    ",".join([f"'{store}'" for store in stores])
)

df = pd.read_sql(query, conn, params=(str(dates[0]), str(dates[1])))

if df.empty:
    st.warning("No data found for selected filters.")
    st.stop()

# --- KPI METRICS ---
total_sales = df['Net_Sales'].sum()
total_guests = df['Guest_Count'].sum()
avg_check = df['Avg_Check'].mean()
total_discounts = df['DD_Discount'].sum()

t1, t2, t3, t4 = st.columns(4)
t1.metric("Net Sales", f"${total_sales:,.2f}")
t2.metric("Guest Count", f"{int(total_guests):,}")
t3.metric("Avg Check", f"${avg_check:,.2f}")
t4.metric("Discounts Given", f"${total_discounts:,.2f}")

# --- CHARTS ---
st.markdown("---")
st.subheader("Sales Trend by Store")
trend = df.groupby(['Date', 'Store'])['Net_Sales'].sum().reset_index()
fig = px.line(trend, x='Date', y='Net_Sales', color='Store', markers=True)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Guest Count Distribution")
guest_fig = px.bar(df.groupby("Store")["Guest_Count"].sum().reset_index(),
                   x="Store", y="Guest_Count", text_auto=True)
st.plotly_chart(guest_fig, use_container_width=True)

st.subheader("Sales by Store")
pie_fig = px.pie(df, names='Store', values='Net_Sales', hole=0.4)
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
