# dashboard/pages/9_Guest_Reviews.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.supabase_db import get_supabase_connection
from utils.checkbox_multiselect import checkbox_multiselect

st.set_page_config(page_title="Guest Reviews", page_icon="💬", layout="wide")

st.title("💬 Guest Reviews & Comments")
st.markdown("Analysis of customer feedback from Medallia surveys")

# --- DATABASE CONNECTION ---
try:
    conn = get_supabase_connection()
except Exception as e:
    st.error(f"Failed to connect to database: {e}")
    st.stop()

# --- CHECK IF TABLE EXISTS ---
try:
    test_query = "SELECT COUNT(*) FROM guest_comments LIMIT 1"
    pd.read_sql(test_query, conn)
except Exception as e:
    st.error("Guest comments table not found. Please run the database schema setup first:")
    st.code("psql <connection_string> < db/guest_comments_schema.sql", language="bash")
    st.stop()

# --- FILTERS SECTION ---
st.sidebar.header("🔍 Filters")

# Get available date range
date_range = pd.read_sql("""
    SELECT MIN(report_date) as min_date, MAX(report_date) as max_date 
    FROM guest_comments
""", conn)

if date_range.empty or pd.isna(date_range['min_date'].iloc[0]):
    st.warning("No guest comments data available. Please download and process Medallia emails first.")
    st.info("""
    **Steps to import data:**
    1. Download emails: `python scripts/download_medallia_emails.py`
    2. Process data: `python scripts/process_medallia_data.py`
    """)
    st.stop()

min_date = pd.to_datetime(date_range['min_date'].iloc[0]).date()
max_date = pd.to_datetime(date_range['max_date'].iloc[0]).date()

# Date range selector
default_start = max(min_date, max_date - timedelta(days=30))

date_selection = st.sidebar.date_input(
    "Select Date Range",
    value=(default_start, max_date),
    min_value=min_date,
    max_value=max_date
)

# Handle date selection
if isinstance(date_selection, tuple) and len(date_selection) == 2:
    start_date, end_date = date_selection
elif isinstance(date_selection, tuple) and len(date_selection) == 1:
    start_date = end_date = date_selection[0]
else:
    start_date = end_date = date_selection

# Get available stores
stores_df = pd.read_sql("""
    SELECT DISTINCT restaurant_pc, restaurant_address 
    FROM guest_comments 
    ORDER BY restaurant_pc
""", conn)

store_options = [f"{row['restaurant_pc']} - {row['restaurant_address']}" 
                 for _, row in stores_df.iterrows()]

selected_stores = st.sidebar.multiselect(
    "Select Stores",
    options=store_options,
    default=store_options
)

# Extract PC numbers from selections
if selected_stores:
    selected_pcs = [s.split(" - ")[0] for s in selected_stores]
else:
    st.warning("Please select at least one store")
    st.stop()

# Score filters
st.sidebar.subheader("Score Filters")
col1, col2 = st.sidebar.columns(2)
with col1:
    min_osat = st.slider("Min OSAT", 1, 5, 1)
with col2:
    min_ltr = st.slider("Min LTR", 0, 10, 0)

# Accuracy filter
accuracy_filter = st.sidebar.multiselect(
    "Accuracy",
    options=["Yes", "No"],
    default=["Yes", "No"]
)

# Order channel filter
channel_filter = st.sidebar.multiselect(
    "Order Channel",
    options=["In-store", "Other"],
    default=["In-store", "Other"]
)

# --- LOAD DATA ---
placeholders = ','.join(['%s'] * len(selected_pcs))
accuracy_placeholders = ','.join(['%s'] * len(accuracy_filter))
channel_placeholders = ','.join(['%s'] * len(channel_filter))

query = f"""
    SELECT *
    FROM guest_comments
    WHERE report_date BETWEEN %s AND %s
    AND restaurant_pc IN ({placeholders})
    AND osat >= %s
    AND ltr >= %s
    AND accuracy IN ({accuracy_placeholders})
    AND order_channel IN ({channel_placeholders})
    ORDER BY response_datetime DESC
"""

params = [start_date, end_date] + selected_pcs + [min_osat, min_ltr] + accuracy_filter + channel_filter

df = pd.read_sql(query, conn, params=params)

if df.empty:
    st.warning("No reviews found matching the selected filters")
    st.stop()

# --- METRICS SECTION ---
st.header("📊 Overview Metrics")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_reviews = len(df)
    st.metric("Total Reviews", f"{total_reviews:,}")

with col2:
    avg_osat = df['osat'].mean()
    st.metric("Avg OSAT", f"{avg_osat:.2f}/5")

with col3:
    avg_ltr = df['ltr'].mean()
    st.metric("Avg LTR", f"{avg_ltr:.1f}/10")

with col4:
    accuracy_rate = (df['accuracy'] == 'Yes').sum() / len(df) * 100
    st.metric("Accuracy Rate", f"{accuracy_rate:.1f}%")

with col5:
    promoters = (df['ltr'] >= 9).sum() / len(df) * 100
    st.metric("Promoters %", f"{promoters:.1f}%")

st.divider()

# --- CHARTS SECTION ---
st.header("📈 Trends & Insights")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # OSAT Distribution
    osat_counts = df['osat'].value_counts().sort_index()
    fig_osat = px.bar(
        x=osat_counts.index,
        y=osat_counts.values,
        labels={'x': 'OSAT Score', 'y': 'Count'},
        title='OSAT Score Distribution',
        color=osat_counts.index,
        color_continuous_scale='RdYlGn'
    )
    fig_osat.update_layout(showlegend=False)
    st.plotly_chart(fig_osat, use_container_width=True)

with chart_col2:
    # LTR Distribution
    ltr_counts = df['ltr'].value_counts().sort_index()
    fig_ltr = px.bar(
        x=ltr_counts.index,
        y=ltr_counts.values,
        labels={'x': 'LTR Score', 'y': 'Count'},
        title='Likelihood to Return Distribution',
        color=ltr_counts.index,
        color_continuous_scale='RdYlGn'
    )
    fig_ltr.update_layout(showlegend=False)
    st.plotly_chart(fig_ltr, use_container_width=True)

# Scores over time
df['report_date'] = pd.to_datetime(df['report_date'])
daily_scores = df.groupby('report_date').agg({
    'osat': 'mean',
    'ltr': 'mean',
    'id': 'count'
}).reset_index()
daily_scores.columns = ['Date', 'Avg OSAT', 'Avg LTR', 'Review Count']

fig_timeline = go.Figure()
fig_timeline.add_trace(go.Scatter(
    x=daily_scores['Date'],
    y=daily_scores['Avg OSAT'],
    name='Avg OSAT',
    mode='lines+markers',
    yaxis='y'
))
fig_timeline.add_trace(go.Scatter(
    x=daily_scores['Date'],
    y=daily_scores['Avg LTR'],
    name='Avg LTR',
    mode='lines+markers',
    yaxis='y2'
))

fig_timeline.update_layout(
    title='Scores Over Time',
    xaxis=dict(title='Date'),
    yaxis=dict(title='Avg OSAT', side='left', range=[0, 5]),
    yaxis2=dict(title='Avg LTR', side='right', overlaying='y', range=[0, 10]),
    hovermode='x unified'
)
st.plotly_chart(fig_timeline, use_container_width=True)

# Store comparison
store_scores = df.groupby('restaurant_pc').agg({
    'osat': 'mean',
    'ltr': 'mean',
    'id': 'count'
}).reset_index()
store_scores.columns = ['Store', 'Avg OSAT', 'Avg LTR', 'Count']
store_scores = store_scores.sort_values('Avg OSAT', ascending=False)

fig_stores = go.Figure()
fig_stores.add_trace(go.Bar(
    x=store_scores['Store'],
    y=store_scores['Avg OSAT'],
    name='Avg OSAT',
    marker_color='lightblue'
))
fig_stores.update_layout(
    title='Average OSAT by Store',
    xaxis_title='Store PC',
    yaxis_title='Average OSAT',
    yaxis=dict(range=[0, 5])
)
st.plotly_chart(fig_stores, use_container_width=True)

st.divider()

# --- REVIEWS TABLE ---
st.header("💬 Individual Reviews")

# View options
view_option = st.radio(
    "Filter by sentiment:",
    ["All Reviews", "Positive (OSAT 4-5, LTR 7-10)", "Negative (OSAT 1-2, LTR 0-5)", "Order Accuracy Issues"],
    horizontal=True
)

display_df = df.copy()

if view_option == "Positive (OSAT 4-5, LTR 7-10)":
    display_df = display_df[(display_df['osat'] >= 4) & (display_df['ltr'] >= 7)]
elif view_option == "Negative (OSAT 1-2, LTR 0-5)":
    display_df = display_df[(display_df['osat'] <= 2) | (display_df['ltr'] <= 5)]
elif view_option == "Order Accuracy Issues":
    display_df = display_df[display_df['accuracy'] == 'No']

st.write(f"Showing {len(display_df)} review(s)")

# Display reviews as cards
for idx, row in display_df.head(50).iterrows():
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**Store {row['restaurant_pc']}** - {row['restaurant_address']}")
        with col2:
            st.markdown(f"📅 {row['report_date']}")
        with col3:
            st.markdown(f"⏰ {row['response_datetime'].strftime('%I:%M %p')}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            osat_color = "🟢" if row['osat'] >= 4 else "🟡" if row['osat'] == 3 else "🔴"
            st.markdown(f"{osat_color} **OSAT:** {row['osat']}/5")
        with col2:
            ltr_color = "🟢" if row['ltr'] >= 7 else "🟡" if row['ltr'] >= 4 else "🔴"
            st.markdown(f"{ltr_color} **LTR:** {row['ltr']}/10")
        with col3:
            acc_icon = "✅" if row['accuracy'] == 'Yes' else "❌"
            st.markdown(f"{acc_icon} **Accuracy:** {row['accuracy']}")
        with col4:
            st.markdown(f"📍 **Channel:** {row['order_channel']}")
        
        if row['comment']:
            st.markdown(f"> {row['comment']}")
        
        st.divider()

if len(display_df) > 50:
    st.info(f"Showing first 50 reviews. Total matching reviews: {len(display_df)}")

# --- EXPORT SECTION ---
st.divider()
st.header("📥 Export Data")

col1, col2 = st.columns(2)

with col1:
    # CSV export
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name=f"guest_reviews_{start_date}_to_{end_date}.csv",
        mime="text/csv"
    )

with col2:
    # Summary stats
    if st.button("Show Summary Statistics"):
        st.subheader("Summary Statistics")
        st.dataframe(df[['osat', 'ltr']].describe())

conn.close()
