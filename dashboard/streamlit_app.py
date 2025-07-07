import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

DB_PATH = "../db/sales.db"

def load_data(table):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df

st.title("Dunkin Sales Dashboard")

# Load summary data
summary = load_data("sales_summary")

st.header("Sales Summary")
st.dataframe(summary)

# Plot gross sales over time
st.subheader("Gross Sales Over Time")
if not summary.empty:
    summary['date'] = pd.to_datetime(summary['date'], errors='coerce')
    summary = summary.sort_values('date')
    fig, ax = plt.subplots()
    for store_id, group in summary.groupby('store_id'):
        ax.plot(group['date'], group['gross_sales'], marker='o', label=store_id)
    ax.set_xlabel("Date")
    ax.set_ylabel("Gross Sales")
    ax.legend(title="Store")
    st.pyplot(fig)
else:
    st.write("No sales data available.")

#  add more visualizations for order type, daypart, etc.