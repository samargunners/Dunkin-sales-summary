# streamlit_app/pages/5_Tender_Type.py

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import get_connection
import tempfile
import base64
import os
from weasyprint import HTML

st.title("💳 Tender Type Analysis")

conn = get_connection()

# --- FILTERS ---
store_list = pd.read_sql("SELECT DISTINCT store FROM tender_type_metrics", conn)["store"].tolist()
selected_stores = st.multiselect("Select Stores", store_list, default=store_list)

min_date = pd.read_sql("SELECT MIN(date) as min_date FROM tender_type_metrics", conn)["min_date"].iloc[0]
max_date = pd.read_sql("SELECT MAX(date) as max_date FROM tender_type_metrics", conn)["max_date"].iloc[0]
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
SELECT * FROM tender_type_metrics
WHERE store IN ({}) AND date BETWEEN ? AND ?
""".format(",".join([f"'{s}'" for s in selected_stores]))

df = pd.read_sql(query, conn, params=(str(start_date), str(end_date)))

if df.empty:
    st.warning("No tender data found for selected filters.")
    st.stop()

# --- Tender Type Standardization ---
rename_map = {
    "4000059 crdit card - discover": "Discover",
    "4000061 credit card - visa": "Visa",
    "4000060 credit card - mastercard": "Mastercard",
    "4000058 credir card - amex": "Amex",
    "4000065 gift card redeem": "GC Redeem",
    "4000098": "Grubhub",
    "4000106": "Uber Eats",
    "4000107": "Doordash"
}
df = df[~df['tender_type'].str.lower().str.contains("gl")]  # Remove GL lines
df['tender_type'] = df['tender_type'].str.lower().replace(rename_map)

# --- Summary Chart ---
st.subheader("Total Amount by Tender Type")
tender_totals = df.groupby("tender_type")["detail_amount"].sum().reset_index()
fig_tender = px.bar(tender_totals, x="tender_type", y="detail_amount", text_auto=True)
st.plotly_chart(fig_tender, use_container_width=True)

# --- Store-Level Comparison ---
st.subheader("Tender Breakdown by Store")
df_grouped = df.groupby(["store", "tender_type"])["detail_amount"].sum().reset_index()
fig_store = px.bar(df_grouped, x="store", y="detail_amount", color="tender_type", barmode="stack")
st.plotly_chart(fig_store, use_container_width=True)

# --- EXPORT TO PDF ---
def export_tender_to_pdf():
    with tempfile.TemporaryDirectory() as tmpdir:
        tender_img = os.path.join(tmpdir, "tender.jpg")
        store_img = os.path.join(tmpdir, "store.jpg")
        fig_tender.write_image(tender_img, format="jpg", scale=2)
        fig_store.write_image(store_img, format="jpg", scale=2)

        def img_to_base64(img_path):
            with open(img_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()

        tender_b64 = img_to_base64(tender_img)
        store_b64 = img_to_base64(store_img)

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
            <h2>Tender Type Analysis</h2>
            <p><strong>Date Range:</strong> {start_date} to {end_date}</p>
            <p><strong>Stores:</strong> {', '.join(selected_stores)}</p>
            <h3>Total Amount by Tender Type</h3>
            <img src="data:image/jpeg;base64,{tender_b64}" />
            {tender_totals.to_html(index=False)}
            <h3>Tender Breakdown by Store</h3>
            <img src="data:image/jpeg;base64,{store_b64}" />
            {df_grouped.to_html(index=False)}
        </body>
        </html>
        """

        pdf_path = os.path.join(tmpdir, "Tender_Type_Analysis.pdf")
        try:
            HTML(string=html_content).write_pdf(pdf_path)
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📤 Download PDF",
                data=pdf_bytes,
                file_name="Tender_Type_Analysis.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF export failed: {e}")

if st.button("📤 Export This Page to PDF"):
    export_tender_to_pdf()
