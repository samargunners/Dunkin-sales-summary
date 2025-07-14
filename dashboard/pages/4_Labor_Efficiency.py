# streamlit_app/pages/4_Labor_Efficiency.py

import streamlit as st
import pandas as pd
from utils.db import get_connection
import plotly.express as px
import tempfile
import base64
import os
from weasyprint import HTML

st.title("👷 Labor Efficiency Analysis")

conn = get_connection()

# --- FILTERS ---
store_list = pd.read_sql("SELECT DISTINCT store FROM labor_metrics", conn)["store"].tolist()
selected_stores = st.multiselect("Select Stores", store_list, default=store_list)

min_date = pd.read_sql("SELECT MIN(date) as min_date FROM labor_metrics", conn)["min_date"].iloc[0]
max_date = pd.read_sql("SELECT MAX(date) as max_date FROM labor_metrics", conn)["max_date"].iloc[0]
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
SELECT * FROM labor_metrics
WHERE store IN ({}) AND date BETWEEN ? AND ?
""".format(",".join([f"'{s}'" for s in selected_stores]))

df = pd.read_sql(query, conn, params=(str(start_date), str(end_date)))

if df.empty:
    st.warning("No labor data for selected filters.")
    st.stop()

# --- Labor Cost KPIs ---
total_hours = df['total_hours'].sum()
total_pay = df['total_pay'].sum()
avg_percent_labor = df['percent_labor'].sum()

c1, c2, c3 = st.columns(3)
c1.metric("Total Labor Hours", f"{total_hours:.2f}")
c2.metric("Total Labor Cost", f"${total_pay:,.2f}")
c3.metric("Avg % Labor", f"{avg_percent_labor:.2%}")

# --- Charts ---
st.markdown("---")
st.subheader("Total Hours by Labor Position")
hr_by_role = df.groupby("labor_position")["total_hours"].sum().reset_index()
fig_hr = px.bar(hr_by_role, x="labor_position", y="total_hours", text_auto=True)
st.plotly_chart(fig_hr, use_container_width=True)

st.subheader("Total Pay by Labor Position")
pay_by_role = df.groupby("labor_position")["total_pay"].sum().reset_index()
fig_pay = px.bar(pay_by_role, x="labor_position", y="total_pay", text_auto=True)
st.plotly_chart(fig_pay, use_container_width=True)

st.subheader("Labor % by Position")
percent_labor = df.groupby("labor_position")["percent_labor"].mean().reset_index()
fig_percent = px.bar(percent_labor, x="labor_position", y="percent_labor", text_auto=True)
st.plotly_chart(fig_percent, use_container_width=True)

# --- EXPORT TO PDF ---
def export_labor_to_pdf():
    with tempfile.TemporaryDirectory() as tmpdir:
        hr_img = os.path.join(tmpdir, "hr.jpg")
        pay_img = os.path.join(tmpdir, "pay.jpg")
        percent_img = os.path.join(tmpdir, "percent.jpg")
        fig_hr.write_image(hr_img, format="jpg", scale=2)
        fig_pay.write_image(pay_img, format="jpg", scale=2)
        fig_percent.write_image(percent_img, format="jpg", scale=2)

        def img_to_base64(img_path):
            with open(img_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()

        hr_b64 = img_to_base64(hr_img)
        pay_b64 = img_to_base64(pay_img)
        percent_b64 = img_to_base64(percent_img)

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
            <h2>Labor Efficiency Analysis</h2>
            <p><strong>Date Range:</strong> {start_date} to {end_date}</p>
            <p><strong>Stores:</strong> {', '.join(selected_stores)}</p>
            <h3>Total Hours by Labor Position</h3>
            <img src="data:image/jpeg;base64,{hr_b64}" />
            {hr_by_role.to_html(index=False)}
            <h3>Total Pay by Labor Position</h3>
            <img src="data:image/jpeg;base64,{pay_b64}" />
            {pay_by_role.to_html(index=False)}
            <h3>Labor % by Position</h3>
            <img src="data:image/jpeg;base64,{percent_b64}" />
            {percent_labor.to_html(index=False)}
        </body>
        </html>
        """

        pdf_path = os.path.join(tmpdir, "Labor_Efficiency.pdf")
        try:
            HTML(string=html_content).write_pdf(pdf_path)
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📤 Download PDF",
                data=pdf_bytes,
                file_name="Labor_Efficiency.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF export failed: {e}")

if st.button("📤 Export This Page to PDF"):
    export_labor_to_pdf()
