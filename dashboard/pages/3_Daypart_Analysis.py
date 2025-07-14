# streamlit_app/pages/3_Daypart_Analysis.py

import streamlit as st
import pandas as pd
from utils.db import get_connection
import plotly.express as px
from utils.exports import export_page_as_pdf
from io import StringIO
import tempfile
import subprocess
import base64
import os
from weasyprint import HTML

st.title("⏰ Sales by Daypart")

# --- DB Connection ---
conn = get_connection()

# --- FILTERS ---
store_list = pd.read_sql("SELECT DISTINCT store FROM sales_by_daypart", conn)["store"].tolist()
selected_stores = st.multiselect("Select stores", store_list, default=store_list)

min_date = pd.read_sql("SELECT MIN(date) as min_date FROM sales_by_daypart", conn)["min_date"].iloc[0]
max_date = pd.read_sql("SELECT MAX(date) as max_date FROM sales_by_daypart", conn)["max_date"].iloc[0]
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

query = """
SELECT * FROM sales_by_daypart
WHERE store IN ({}) AND date BETWEEN ? AND ?
""".format(",".join([f"'{s}'" for s in selected_stores]))

df = pd.read_sql(query, conn, params=(str(start_date), str(end_date)))

if df.empty:
    st.warning("No data found for selected filters.")
    st.stop()

# --- Charts ---
st.subheader("Net Sales by Daypart")
daypart_sales = df.groupby("daypart")["net_sales"].sum().reset_index()
fig_sales = px.bar(daypart_sales, x="daypart", y="net_sales", text_auto=True)
st.plotly_chart(fig_sales, use_container_width=True)

st.subheader("Avg Check by Daypart")
check_avg = df.groupby("daypart")["avg_check"].mean().reset_index()
fig_check = px.bar(check_avg, x="daypart", y="avg_check", text_auto=True)
st.plotly_chart(fig_check, use_container_width=True)

st.subheader("Check Count by daypart")
check_count = df.groupby("daypart")["check_count"].sum().reset_index()
fig_count = px.pie(check_count, names="daypart", values="check_count")
st.plotly_chart(fig_count, use_container_width=True)

# --- EXPORT TO PDF USING weasyprint ---
def export_daypart_to_pdf():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save charts as images (JPEG for best compatibility)
        sales_img = os.path.join(tmpdir, "sales.jpg")
        check_img = os.path.join(tmpdir, "check.jpg")
        count_img = os.path.join(tmpdir, "count.jpg")
        fig_sales.write_image(sales_img, format="jpg", scale=2)
        fig_check.write_image(check_img, format="jpg", scale=2)
        fig_count.write_image(count_img, format="jpg", scale=2)

        def img_to_base64(img_path):
            with open(img_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()

        sales_b64 = img_to_base64(sales_img)
        check_b64 = img_to_base64(check_img)
        count_b64 = img_to_base64(count_img)

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
            <h2>Sales by Daypart</h2>
            <p><strong>Date Range:</strong> {start_date} to {end_date}</p>
            <p><strong>Stores:</strong> {', '.join(selected_stores)}</p>
            <h3>Net Sales by Daypart</h3>
            <img src="data:image/jpeg;base64,{sales_b64}" />
            {daypart_sales.to_html(index=False)}
            <h3>Avg Check by Daypart</h3>
            <img src="data:image/jpeg;base64,{check_b64}" />
            {check_avg.to_html(index=False)}
            <h3>Check Count by Daypart</h3>
            <img src="data:image/jpeg;base64,{count_b64}" />
            {check_count.to_html(index=False)}
        </body>
        </html>
        """

        pdf_path = os.path.join(tmpdir, "Sales_by_Daypart.pdf")
        try:
            HTML(string=html_content).write_pdf(pdf_path)
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📤 Download PDF",
                data=pdf_bytes,
                file_name="Sales_by_Daypart.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF export failed: {e}")

if st.button("📤 Export This Page to PDF"):
    export_daypart_to_pdf()
