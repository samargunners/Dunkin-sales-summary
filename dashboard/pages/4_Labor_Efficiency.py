# streamlit_app/pages/4_Labor_Efficiency.py

import streamlit as st
import pandas as pd
from utils.db import get_connection
import plotly.express as px

st.title("👷 Labor Efficiency Analysis")

conn = get_connection()
stores = st.session_state.get("selected_stores", [])
dates = st.session_state.get("date_range", [])

query = """
SELECT * FROM labor_metrics
WHERE Store IN ({}) AND Date BETWEEN ? AND ?
""".format(",".join([f"'{s}'" for s in stores]))

df = pd.read_sql(query, conn, params=(str(dates[0]), str(dates[1])))

if df.empty:
    st.warning("No labor data for selected filters.")
    st.stop()

# --- Labor Cost KPIs ---
total_hours = df['Total_Hours'].sum()
total_pay = df['Total_Pay'].sum()
avg_percent_labor = df['Percent_Labor'].mean()

c1, c2, c3 = st.columns(3)
c1.metric("Total Labor Hours", f"{total_hours:.2f}")
c2.metric("Total Labor Cost", f"${total_pay:,.2f}")
c3.metric("Avg % Labor", f"{avg_percent_labor:.2%}")

# --- Charts ---
st.markdown("---")
st.subheader("Total Hours by Labor Position")
hr_by_role = df.groupby("Labor_Position")["Total_Hours"].sum().reset_index()
fig_hr = px.bar(hr_by_role, x="Labor_Position", y="Total_Hours", text_auto=True)
st.plotly_chart(fig_hr, use_container_width=True)

st.subheader("Total Pay by Labor Position")
pay_by_role = df.groupby("Labor_Position")["Total_Pay"].sum().reset_index()
fig_pay = px.bar(pay_by_role, x="Labor_Position", y="Total_Pay", text_auto=True)
st.plotly_chart(fig_pay, use_container_width=True)

st.subheader("Labor % by Position")
percent_labor = df.groupby("Labor_Position")["Percent_Labor"].mean().reset_index()
fig_percent = px.bar(percent_labor, x="Labor_Position", y="Percent_Labor", text_auto=True)
st.plotly_chart(fig_percent, use_container_width=True)
