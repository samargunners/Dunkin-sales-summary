# streamlit_app/pages/6_Store_Comparison.py

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import get_connection
import tempfile
import base64
import os
from weasyprint import HTML

st.title("🏪 Store Comparison Dashboard")

conn = get_connection()

# --- FILTERS ---
store_list = pd.read_sql("SELECT DISTINCT store FROM sales_summary", conn)["store"].tolist()
selected_stores = st.multiselect("Select Stores", store_list, default=store_list)

min_date = pd.read_sql("SELECT MIN(date) as min_date FROM sales_summary", conn)["min_date"].iloc[0]
max_date = pd.read_sql("SELECT MAX(date) as max_date FROM sales_summary", conn)["max_date"].iloc[0]
min_date = pd.to_datetime(min_date).date()
max_date = pd.to_datetime(max_date).date()

# Simple date selection
st.subheader("📅 Date Selection")
st.info("💡 **Tip:** Select one date for single day data, or select two dates for a date range (inclusive)")

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

query = """
SELECT * FROM sales_summary
WHERE store IN ({}) AND DATE(date) BETWEEN ? AND ?
""".format(",".join([f"'{s}'" for s in selected_stores]))

df = pd.read_sql(query, conn, params=(str(start_date), str(end_date)))

if df.empty:
    st.warning("No sales summary data available for the selected filters.")
    # Quick check for available dates
    all_dates_query = "SELECT DISTINCT DATE(date) as date FROM sales_summary ORDER BY date DESC LIMIT 10"
    all_dates_df = pd.read_sql(all_dates_query, conn)
    st.write("**Recent available dates:**")
    st.dataframe(all_dates_df)
    st.stop()

# Ensure all relevant columns are numeric and fill NaN with 0
for col in ["net_sales", "guest_count", "avg_check", "dd_discount", "void_amount", "refund","dd_adjusted_no_markup"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# --- Aggregated Store Comparison ---
grouped = df.groupby("store").agg({
    "net_sales": "sum",
    "guest_count": "sum",
    "avg_check": "mean",
    "dd_discount": "sum",
    "void_amount": "sum",
    "refund": "sum",
    "dd_adjusted_no_markup": "sum"
}).reset_index()

# --- Charts ---
st.subheader("Net Sales by Store")
fig_sales = px.bar(grouped, x="store", y="dd_adjusted_no_markup", text_auto=True)
st.plotly_chart(fig_sales, use_container_width=True)

st.subheader("Guest Count by Store")
fig_guests = px.bar(grouped, x="store", y="guest_count", text_auto=True)
st.plotly_chart(fig_guests, use_container_width=True)

st.subheader("Average Check by Store")
fig_check = px.bar(grouped, x="store", y="avg_check", text_auto=True)
st.plotly_chart(fig_check, use_container_width=True)

st.subheader("Discount, Voids & Refunds by Store")
melted = grouped.melt(id_vars="store", value_vars=["dd_discount", "void_amount", "refund"])
fig_misc = px.bar(
    melted,
    x="store", y="value", color="variable", barmode="group",text_auto=True,
)
st.plotly_chart(fig_misc, use_container_width=True)

# --- EXPORT TO PDF ---
def export_store_comparison_to_pdf():
    with tempfile.TemporaryDirectory() as tmpdir:
        sales_img = os.path.join(tmpdir, "sales.jpg")
        guests_img = os.path.join(tmpdir, "guests.jpg")
        check_img = os.path.join(tmpdir, "check.jpg")
        misc_img = os.path.join(tmpdir, "misc.jpg")
        fig_sales.write_image(sales_img, format="jpg", scale=2)
        fig_guests.write_image(guests_img, format="jpg", scale=2)
        fig_check.write_image(check_img, format="jpg", scale=2)
        fig_misc.write_image(misc_img, format="jpg", scale=2)

        def img_to_base64(img_path):
            with open(img_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()

        sales_b64 = img_to_base64(sales_img)
        guests_b64 = img_to_base64(guests_img)
        check_b64 = img_to_base64(check_img)
        misc_b64 = img_to_base64(misc_img)

        # Format date selection info for PDF
        if start_date == end_date:
            date_info = f"Single Date: {start_date}"
        else:
            date_info = f"Date Range: {start_date} to {end_date}"

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
            <h2>Store Comparison Dashboard</h2>
            <p><strong>{date_info}</strong></p>
            <p><strong>Stores:</strong> {', '.join(selected_stores)}</p>
            <h3>Net Sales by Store</h3>
            <img src="data:image/jpeg;base64,{sales_b64}" />
            <h3>Guest Count by Store</h3>
            <img src="data:image/jpeg;base64,{guests_b64}" />
            <h3>Average Check by Store</h3>
            <img src="data:image/jpeg;base64,{check_b64}" />
            <h3>Discount, Voids & Refunds by Store</h3>
            <img src="data:image/jpeg;base64,{misc_b64}" />
            <h3>Aggregated Data</h3>
            {grouped.to_html(index=False)}
        </body>
        </html>
        """

        pdf_path = os.path.join(tmpdir, "Store_Comparison.pdf")
        try:
            HTML(string=html_content).write_pdf(pdf_path)
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📤 Download PDF",
                data=pdf_bytes,
                file_name="Store_Comparison.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF export failed: {e}")

if st.button("📤 Export This Page to PDF"):
    export_store_comparison_to_pdf()
