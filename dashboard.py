import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_folium import st_folium
import folium

# Page config
st.set_page_config(
    page_title="MARIA AP7",
    page_icon="🚗",
    layout="wide"
)

# Title
st.title("🚗 Predicció de Trànsit - MARIA AP7")

# Connect to database
@st.cache_resource
def get_db_connection():
    return duckdb.connect('maria_ap7.duckdb')

con = get_db_connection()

# Sidebar filters
st.sidebar.header("Filters")

# Get unique dates for filter
# Use only predictions table
dates = con.execute("""
    SELECT DISTINCT dat 
    FROM predictions 
    ORDER BY dat
""").fetchdf()['dat'].tolist()

selected_date = st.sidebar.date_input(
    "Select Date",
    value=dates[0].date(),
    min_value=dates[0].date(),
    max_value=dates[-1].date()
)

# Get unique locations for filter (from predictions table)
prediction_locations = con.execute("""
    SELECT DISTINCT via 
    FROM predictions 
    ORDER BY via
""").fetchdf()['via'].tolist()

selected_prediction_location = st.sidebar.selectbox(
    "Select Prediction Location (ID)",
    options=prediction_locations,
    key="prediction_location"
)

# Time filters (each on a separate line)
selected_year = st.sidebar.selectbox(
    "Year",
    options=sorted(list(set(d.date().year for d in dates)))
)
selected_month = st.sidebar.selectbox(
    "Month",
    options=sorted(list(set(d.date().month for d in dates))),
    format_func=lambda x: datetime(2000, x, 1).strftime('%B')
)
selected_day = st.sidebar.selectbox(
    "Day",
    options=sorted(list(set(d.date().day for d in dates)))
)
selected_hour = st.sidebar.selectbox(
    "Hour",
    options=range(24)
)

# Main content
# 1. Overview Metrics
st.header("Overview Metrics")

# Get metrics for selected date and location
metrics = con.execute("""
    SELECT 
        AVG(mean_speed_pred) as avg_speed_pred,
        AVG(intTot_pred) as avg_intensity_pred,
        COUNT(*) as record_count
    FROM predictions
    WHERE dat = ? AND via = ?
""", [selected_date.strftime('%Y-%m-%d'), selected_prediction_location]).fetchdf()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Average Predicted Speed", f"{metrics['avg_speed_pred'][0]:.2f} km/h")
with col2:
    st.metric("Average Predicted Intensity", f"{metrics['avg_intensity_pred'][0]:.2f}")
with col3:
    st.metric("Number of Records", f"{metrics['record_count'][0]:,}")

# 2. PK vs Speed Analysis
st.header("PK vs Speed Analysis")

# Get data for PK vs Speed plot (from predictions table only)
pk_speed_data = con.execute("""
    SELECT 
        pk,
        mean_speed_pred
    FROM predictions
    WHERE EXTRACT(YEAR FROM dat) = ?
            AND EXTRACT(MONTH FROM dat) = ?
            AND EXTRACT(DAY FROM dat) = ?
            AND hor = ?
            AND via = ?
    ORDER BY pk
""", [selected_year, selected_month, selected_day, selected_hour, selected_prediction_location]).fetchdf()

# Create PK vs Speed plot
fig_pk_speed = go.Figure()
fig_pk_speed.add_trace(go.Scatter(
    x=pk_speed_data['pk'],
    y=pk_speed_data['mean_speed_pred'],
    name='Predicted Speed',
    line=dict(color='red', dash='dash')
))

fig_pk_speed.update_layout(
    title=f'Predicted Speed by PK (Year: {selected_year}, Month: {selected_month}, Day: {selected_day}, Hour: {selected_hour})',
    xaxis_title='PK',
    yaxis_title='Predicted Speed (km/h)',
    hovermode='x unified'
)

st.plotly_chart(fig_pk_speed, use_container_width=True)

# 3. Hourly Traffic Patterns
st.header("Hourly Traffic Patterns")

# Get hourly data (from predictions table only)
hourly_data = con.execute("""
    SELECT 
        hor,
        AVG(mean_speed_pred) as avg_speed_pred,
        AVG(intTot_pred) as avg_intensity_pred
    FROM predictions
    WHERE dat = ? AND via = ?
    GROUP BY hor
    ORDER BY hor
""", [selected_date.strftime('%Y-%m-%d'), selected_prediction_location]).fetchdf()

# Create hourly patterns plot
fig_hourly = go.Figure()
fig_hourly.add_trace(go.Scatter(
    x=hourly_data['hor'],
    y=hourly_data['avg_speed_pred'],
    name='Average Predicted Speed',
    line=dict(color='blue')
))
fig_hourly.add_trace(go.Scatter(
    x=hourly_data['hor'],
    y=hourly_data['avg_intensity_pred'],
    name='Average Predicted Intensity',
    line=dict(color='orange'),
    yaxis='y2'
))

fig_hourly.update_layout(
    title='Hourly Predicted Traffic Patterns',
    xaxis_title='Hour',
    yaxis_title='Average Predicted Speed (km/h)',
    yaxis2=dict(
        title='Average Predicted Intensity',
        overlaying='y',
        side='right'
    ),
    hovermode='x unified'
)

st.plotly_chart(fig_hourly, use_container_width=True)

# 4. Data Quality
st.header("Data Quality")

# Check for missing values (from predictions table only)
missing_values = con.execute("""
    SELECT column_name, COUNT(*) as null_count
    FROM (
        SELECT * FROM predictions
        WHERE dat = ? AND via = ?
    ) t
    UNPIVOT (value FOR column_name IN (*))
    WHERE value IS NULL
    GROUP BY column_name
    ORDER BY null_count DESC
""", [selected_date.strftime('%Y-%m-%d'), selected_prediction_location]).fetchdf()

if not missing_values.empty:
    st.warning("Missing values detected:")
    st.dataframe(missing_values)
else:
    st.success("No missing values detected in the selected data.")

# 5. Empty Leaflet Map
st.header("Mapa (Leaflet)")
m = folium.Map(location=[41.3851, 2.1734], zoom_start=6)
st_folium(m, width=700, height=500)

# Close database connection
con.close()