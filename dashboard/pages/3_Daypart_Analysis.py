# streamlit_app/pages/3_Daypart_Analysis.py

import streamlit as st
import pandas as pd
from utils.db import get_connection
import plotly.express as px

st.title("⏰ Sales by Daypart")

# --- DB Connection ---
conn = get_connection()
stores = st.session_state.get("selected_stores", [])
dates = st.session_state.get("date_range", [])

query = """
SELECT * FROM sales_by_daypart
WHERE Store IN ({}) AND Date BETWEEN ? AND ?
""".format(",".join([f"'{s}'" for s in stores]))

df = pd.read_sql(query, conn, params=(str(dates[0]), str(dates[1])))

if df.empty:
    st.warning("No data found for selected filters.")
    st.stop()

# --- Charts ---
st.subheader("Net Sales by Daypart")
daypart_sales = df.groupby("Daypart")["Net_Sales"].sum().reset_index()
fig_sales = px.bar(daypart_sales, x="Daypart", y="Net_Sales", text_auto=True)
st.plotly_chart(fig_sales, use_container_width=True)

st.subheader("Avg Check by Daypart")
check_avg = df.groupby("Daypart")["Avg_Check"].mean().reset_index()
fig_check = px.bar(check_avg, x="Daypart", y="Avg_Check", text_auto=True)
st.plotly_chart(fig_check, use_container_width=True)

st.subheader("Check Count by Daypart")
check_count = df.groupby("Daypart")["Check_Count"].sum().reset_index()
fig_count = px.pie(check_count, names="Daypart", values="Check_Count")
st.plotly_chart(fig_count, use_container_width=True)
