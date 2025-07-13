# streamlit_app/pages/5_Tender_Type.py

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import get_connection

st.title("💳 Tender Type Analysis")

conn = get_connection()
stores = st.session_state.get("selected_stores", [])
dates = st.session_state.get("date_range", [])

query = """
SELECT * FROM tender_type_metrics
WHERE Store IN ({}) AND Date BETWEEN ? AND ?
""".format(",".join([f"'{s}'" for s in stores]))

df = pd.read_sql(query, conn, params=(str(dates[0]), str(dates[1])))

if df.empty:
    st.warning("No tender data found for selected filters.")
    st.stop()

# --- Tender Type Standardization ---
rename_map = {
    "4000059 Crdit Card - Discover": "Discover",
    "4000061 Credit Card - Visa": "Visa",
    "4000060 Credit Card - Mastercard": "Mastercard",
    "4000058 Credir Card - Amex": "Amex",
    "4000065 Gift Card Redeem": "GC Redeem",
    "4000098": "Grubhub",
    "4000106": "Uber Eats",
    "4000107": "Doordash"
}
df = df[~df['Tender_Type'].str.lower().str.contains("gl")]  # Remove GL lines
df['Tender_Type'] = df['Tender_Type'].replace(rename_map)

# --- Summary Chart ---
st.subheader("Total Amount by Tender Type")
tender_totals = df.groupby("Tender_Type")["Detail_Amount"].sum().reset_index()
fig_tender = px.bar(tender_totals, x="Tender_Type", y="Detail_Amount", text_auto=True)
st.plotly_chart(fig_tender, use_container_width=True)

# --- Store-Level Comparison ---
st.subheader("Tender Breakdown by Store")
df_grouped = df.groupby(["Store", "Tender_Type"])["Detail_Amount"].sum().reset_index()
fig_store = px.bar(df_grouped, x="Store", y="Detail_Amount", color="Tender_Type", barmode="stack")
st.plotly_chart(fig_store, use_container_width=True)
