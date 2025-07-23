import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import get_connection
import tempfile
import base64
import os
from weasyprint import HTML

st.title("💵 Cash Reconciliation")

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
if isinstance(date_selection, tuple) and len(date_selection) == 2:
    # Two dates selected - use as range
    start_date, end_date = date_selection
    st.success(f"📊 Analyzing date range: **{start_date}** to **{end_date}**")
elif hasattr(date_selection, '__iter__') and len(date_selection) == 1:
    # Single date selected
    start_date = end_date = date_selection[0]
    st.success(f"📊 Analyzing single date: **{start_date}**")
else:
    # Single date object (not in tuple/list)
    start_date = end_date = date_selection
    st.success(f"📊 Analyzing single date: **{start_date}**")

if not selected_stores:
    st.warning("Please select at least one store.")
    st.stop()

query = """
SELECT store, date, cash_in
FROM sales_summary
WHERE store IN ({}) AND DATE(date) BETWEEN ? AND ?
""".format(",".join([f"'{s}'" for s in selected_stores]))

df = pd.read_sql(query, conn, params=(str(start_date), str(end_date)))

if df.empty:
    st.warning("No cash data found for selected filters.")
    st.stop()

df["cash_in"] = pd.to_numeric(df["cash_in"], errors="coerce").fillna(0)

# --- KPIs ---
total_cash = df["cash_in"].sum()
avg_cash = df["cash_in"].mean()

c1, c2 = st.columns(2)
c1.metric("Total Cash In", f"${total_cash:,.2f}")
c2.metric("Average Cash In (per record)", f"${avg_cash:,.2f}")

# --- Charts ---
st.subheader("Cash In by Store")
cash_by_store = df.groupby("store")["cash_in"].sum().reset_index()
fig_store = px.bar(cash_by_store, x="store", y="cash_in", text_auto=True)
st.plotly_chart(fig_store, use_container_width=True)

st.subheader("Cash In Over Time")
# Create separate trend lines for each store
cash_by_date_store = df.groupby(["date", "store"])["cash_in"].sum().reset_index()
fig_date = px.line(cash_by_date_store, x="date", y="cash_in", color="store", 
                   markers=True, title="Cash In Trends by Store",
                   labels={"cash_in": "Cash In ($)", "date": "Date", "store": "Store"})
fig_date.update_layout(hovermode='x unified')
st.plotly_chart(fig_date, use_container_width=True)

st.subheader("Cash In Pivot Table (Date x Store)")
st.info("📊 **Note:** This table shows ALL available data regardless of date/store filters above")

# Get ALL data for pivot table (ignore filters)
all_data_query = "SELECT store, date, cash_in FROM sales_summary"
df_all = pd.read_sql(all_data_query, conn)
df_all["cash_in"] = pd.to_numeric(df_all["cash_in"], errors="coerce").fillna(0)
df_all["date"] = pd.to_datetime(df_all["date"]).dt.date

# Create pivot table with all data
pivot_all = df_all.pivot_table(index="date", columns="store", values="cash_in", aggfunc="sum", fill_value=0)

# Sort by date descending to show latest dates first
pivot_all = pivot_all.sort_index(ascending=False)

# Add totals
pivot_all.loc['Total'] = pivot_all.sum()
pivot_all['Total'] = pivot_all.sum(axis=1)

st.dataframe(pivot_all.style.format("${:,.2f}"))

# --- EXPORT TO PDF ---
def export_cash_recon_to_pdf():
    with tempfile.TemporaryDirectory() as tmpdir:
        store_img = os.path.join(tmpdir, "store.jpg")
        date_img = os.path.join(tmpdir, "date.jpg")
        fig_store.write_image(store_img, format="jpg", scale=2)
        fig_date.write_image(date_img, format="jpg", scale=2)

        def img_to_base64(img_path):
            with open(img_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()

        store_b64 = img_to_base64(store_img)
        date_b64 = img_to_base64(date_img)

        # Create simplified tables for PDF
        cash_by_date_summary = cash_by_date_store.groupby("date")["cash_in"].sum().reset_index()
        pivot_for_pdf = pivot_all.drop('Total', axis=1).drop('Total', axis=0) if 'Total' in pivot_all.columns else pivot_all
        pivot_html = pivot_for_pdf.reset_index().to_html(index=False)
        
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
            <h2>Cash Reconciliation</h2>
            <p><strong>{date_info}</strong></p>
            <p><strong>Stores:</strong> {', '.join(selected_stores)}</p>
            <h3>Total Cash In: ${total_cash:,.2f}</h3>
            <h3>Average Cash In (per record): ${avg_cash:,.2f}</h3>
            <h3>Cash In by Store</h3>
            <img src="data:image/jpeg;base64,{store_b64}" />
            {cash_by_store.to_html(index=False)}
            <h3>Cash In Over Time by Store</h3>
            <img src="data:image/jpeg;base64,{date_b64}" />
            {cash_by_date_summary.to_html(index=False)}
            <h3>Cash In Pivot Table (All Data)</h3>
            {pivot_html}
        </body>
        </html>
        """

        pdf_path = os.path.join(tmpdir, "Cash_Reconciliation.pdf")
        try:
            HTML(string=html_content).write_pdf(pdf_path)
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📤 Download PDF",
                data=pdf_bytes,
                file_name="Cash_Reconciliation.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF export failed: {e}")

if st.button("📤 Export This Page to PDF"):
    export_cash_recon_to_pdf()