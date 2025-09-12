# streamlit_app/pages/2_Sales_Mix.py

import streamlit as st
from utils.checkbox_multiselect import checkbox_multiselect
import pandas as pd
from utils.db import get_connection
import plotly.express as px
import base64
from weasyprint import HTML
import tempfile
import os

st.title("📦 Sales Mix Analysis")

conn = get_connection()

# --- FILTERS ---
store_list = pd.read_sql("SELECT DISTINCT store FROM sales_by_order_type", conn)["store"].tolist()
selected_stores = checkbox_multiselect("Select Stores", store_list, key="store")

# Simple date selection
st.subheader("📅 Date Selection")
st.info("💡 **Tip:** Select one date for single day data, or select two dates for a date range (inclusive)")

min_date = pd.read_sql("SELECT MIN(Date) as min_date FROM sales_by_order_type", conn)["min_date"].iloc[0]
max_date = pd.read_sql("SELECT MAX(Date) as max_date FROM sales_by_order_type", conn)["max_date"].iloc[0]
min_date = pd.to_datetime(min_date).date()
max_date = pd.to_datetime(max_date).date()

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

# --- Order Type ---
order_type_query = """
SELECT * FROM sales_by_order_type
WHERE store IN ({}) AND DATE(Date) BETWEEN ? AND ?
""".format(",".join([f"'{s}'" for s in selected_stores]))

order_df = pd.read_sql(order_type_query, conn, params=(str(start_date), str(end_date)))

# --- Subcategory ---
subcat_query = """
SELECT * FROM sales_by_subcategory
WHERE store IN ({}) AND DATE(Date) BETWEEN ? AND ?
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

def export_sales_mix_to_pdf():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save charts as images
        order_img = os.path.join(tmpdir, "order.jpg")
        guest_img = os.path.join(tmpdir, "guest.jpg")
        subcat_img = os.path.join(tmpdir, "subcat.jpg")
        subcat_pie_img = os.path.join(tmpdir, "subcat_pie.jpg")
        fig_order.write_image(order_img, format="jpg", scale=2)
        fig_guest.write_image(guest_img, format="jpg", scale=2)
        fig_subcat.write_image(subcat_img, format="jpg", scale=2)
        fig_subcat_pie.write_image(subcat_pie_img, format="jpg", scale=2)

        def img_to_base64(img_path):
            with open(img_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()

        order_b64 = img_to_base64(order_img)
        guest_b64 = img_to_base64(guest_img)
        subcat_b64 = img_to_base64(subcat_img)
        subcat_pie_b64 = img_to_base64(subcat_pie_img)

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
            <h2>Sales Mix Analysis</h2>
            <p><strong>Date Range:</strong> {start_date} to {end_date}</p>
            <p><strong>Stores:</strong> {', '.join(selected_stores)}</p>
            <h3>Net Sales by Order Type</h3>
            <img src="data:image/jpeg;base64,{order_b64}" />
            {order_grouped.to_html(index=False)}
            <h3>Guest Count by Order Type</h3>
            <img src="data:image/jpeg;base64,{guest_b64}" />
            {guests_grouped.to_html(index=False)}
            <h3>Sales by Product Subcategory</h3>
            <img src="data:image/jpeg;base64,{subcat_b64}" />
            {subcat_sales.to_html(index=False)}
            <h3>Subcategory Share of Total Sales</h3>
            <img src="data:image/jpeg;base64,{subcat_pie_b64}" />
        </body>
        </html>
        """

        pdf_path = os.path.join(tmpdir, "Sales_Mix.pdf")
        try:
            HTML(string=html_content).write_pdf(pdf_path)
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📤 Download PDF",
                data=pdf_bytes,
                file_name="Sales_Mix.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF export failed: {e}")

if st.button("📤 Export This Page to PDF"):
    export_sales_mix_to_pdf()
