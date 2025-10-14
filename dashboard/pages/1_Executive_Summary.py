# streamlit_app/pages/1_Executive_Summary.py

import streamlit as st
from utils.checkbox_multiselect import checkbox_multiselect
import pandas as pd
from utils.supabase_db import get_supabase_connection
from datetime import datetime
import plotly.express as px
from utils.exports import export_page_as_pdf
from io import StringIO
import tempfile
import subprocess
import base64
import os
from weasyprint import HTML

st.title("📊 Executive Summary")

# --- FILTER CONTEXT ---
conn = get_supabase_connection()


# Get available stores from the database (Postgres is case-sensitive, use lowercase column names)
store_list = pd.read_sql("SELECT DISTINCT store FROM sales_summary", conn)["store"].tolist()

# Store filter (checkbox multiselect)
selected_stores = checkbox_multiselect("Select Stores", store_list, key="store")

# Simple date selection
st.subheader("📅 Date Selection")
st.info("💡 **Tip:** Select one date for single day data, or select two dates for a date range (inclusive)")

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

date_selection = st.date_input(
    "Select Date(s)",
    value=(default_start, max_date),
    min_value=min_date,
    max_value=max_date,
    help="Select one date for single day analysis, or two dates for a range"
)

# Handle different selection scenarios
if isinstance(date_selection, tuple):
    if len(date_selection) == 2:
        # Two dates selected - use as range
        start_date, end_date = date_selection
        st.success(f"📊 Analyzing date range: **{start_date}** to **{end_date}**")
    elif len(date_selection) == 1:
        # Single date in tuple
        start_date = end_date = date_selection[0]
        st.success(f"📊 Analyzing single date: **{start_date}**")
    else:
        st.error("Invalid date selection. Please select one or two dates.")
        st.stop()
else:
    # Single date object (not in tuple)
    start_date = end_date = date_selection
    st.success(f"📊 Analyzing single date: **{start_date}**")

if not selected_stores:
    st.warning("Please select at least one store.")
    st.stop()

# Use lowercase column names and %s placeholders for Postgres
query = """
SELECT * FROM sales_summary
WHERE store IN ({})
    AND date BETWEEN %s AND %s
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
def export_exec_summary_to_pdf():
    with tempfile.TemporaryDirectory() as tmpdir:
        trend_img = os.path.join(tmpdir, "trend.jpg")
        guest_img = os.path.join(tmpdir, "guest.jpg")
        pie_img = os.path.join(tmpdir, "pie.jpg")
        fig.write_image(trend_img, format="jpg", scale=2)
        guest_fig.write_image(guest_img, format="jpg", scale=2)
        pie_fig.write_image(pie_img, format="jpg", scale=2)

        def img_to_base64(img_path):
            with open(img_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()

        trend_b64 = img_to_base64(trend_img)
        guest_b64 = img_to_base64(guest_img)
        pie_b64 = img_to_base64(pie_img)

        html_content = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h2 {{ color: #d17a22; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
                th {{ background-color: #f2f2f2; }}
                img {{ display: block; margin: 20px auto; max-width: 700px; }}
            </style>
        </head>
        <body>
            <h2>Executive Summary</h2>
            <p><strong>Total Sales:</strong> ${total_sales:,.2f}</p>
            <p><strong>Guest Count:</strong> {int(total_guests):,}</p>
            <p><strong>Avg Check:</strong> ${avg_check:,.2f}</p>
            <p><strong>Discounts Given:</strong> ${total_discounts:,.2f}</p>
            <h3>Sales Trend by Store</h3>
            <img src="data:image/jpeg;base64,{trend_b64}" />
            <h3>Guest Count Distribution</h3>
            <img src="data:image/jpeg;base64,{guest_b64}" />
            <h3>Sales by Store</h3>
            <img src="data:image/jpeg;base64,{pie_b64}" />
            <h3>Raw Data</h3>
            {df.to_html(index=False)}
        </body>
        </html>
        """

        pdf_path = os.path.join(tmpdir, "Executive_Summary.pdf")
        try:
            HTML(string=html_content).write_pdf(pdf_path)
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📤 Download PDF",
                data=pdf_bytes,
                file_name="Executive_Summary.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF export failed: {e}")

if st.button("📤 Export This Page to PDF"):
    export_exec_summary_to_pdf()
