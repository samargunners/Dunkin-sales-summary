# streamlit_app/app.py

import streamlit as st
from utils.db import get_connection
from utils.exports import export_page_as_pdf
from pathlib import Path
import sqlite3
import pandas as pd

# --- APP CONFIG ---
st.set_page_config(page_title="Dunkin Sales Dashboard", layout="wide")
st.title("🍩 Dunkin' Donuts - Sales Insights")

# --- SIDEBAR FILTERS ---
conn = get_connection()
stores = pd.read_sql("SELECT DISTINCT store FROM sales_summary", conn)['store'].tolist()
dates = pd.read_sql("SELECT DISTINCT date FROM sales_summary ORDER BY Date DESC", conn)['date']

with st.sidebar:
    st.header("Filters")
    selected_stores = st.multiselect("Select Store(s):", stores, default=stores)
    date_range = st.date_input("Select Date Range:", [dates.min(), dates.max()])
    st.markdown("---")
    if st.button("📄 Export this page to PDF"):
        export_page_as_pdf()

# --- MAIN ---
st.markdown("### Use the sidebar to select a page or filter the data.")
st.markdown("Pages available:")
st.markdown("- Executive Summary")
st.markdown("- Sales Mix")
st.markdown("- Daypart Analysis")
st.markdown("- Labor Efficiency")
st.markdown("- Tender Type")
st.markdown("- Store Comparison")
