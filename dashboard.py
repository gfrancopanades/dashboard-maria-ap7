import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
dates = con.execute("""
    SELECT DISTINCT dat 
    FROM geo_cal_vel 
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
    options=range(1, 13),
    format_func=lambda x: datetime(2000, x, 1).strftime('%B')
)
selected_day = st.sidebar.selectbox(
    "Day",
    options=range(1, 32)
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
        AVG(mean_speed) as avg_speed,
        AVG(intTot) as avg_intensity,
        COUNT(*) as record_count
    FROM geo_cal_vel
    WHERE dat = ? AND via = ?
""", [selected_date.strftime('%Y-%m-%d'), selected_prediction_location]).fetchdf()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Average Speed", f"{metrics['avg_speed'][0]:.2f} km/h")
with col2:
    st.metric("Average Intensity", f"{metrics['avg_intensity'][0]:.2f}")
with col3:
    st.metric("Number of Records", f"{metrics['record_count'][0]:,}")

# New section: PK vs Speed Analysis
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

# 2. Hourly Traffic Patterns
st.header("Hourly Traffic Patterns")

# Get hourly data
hourly_data = con.execute("""
    SELECT 
        hor,
        AVG(mean_speed) as avg_speed,
        AVG(intTot) as avg_intensity
    FROM geo_cal_vel
    WHERE dat = ? AND via = ?
    GROUP BY hor
    ORDER BY hor
""", [selected_date.strftime('%Y-%m-%d'), selected_prediction_location]).fetchdf()

# Create hourly patterns plot
fig_hourly = go.Figure()
fig_hourly.add_trace(go.Scatter(
    x=hourly_data['hor'],
    y=hourly_data['avg_speed'],
    name='Average Speed',
    line=dict(color='blue')
))
fig_hourly.add_trace(go.Scatter(
    x=hourly_data['hor'],
    y=hourly_data['avg_intensity'],
    name='Average Intensity',
    line=dict(color='orange'),
    yaxis='y2'
))

fig_hourly.update_layout(
    title='Hourly Traffic Patterns',
    xaxis_title='Hour',
    yaxis_title='Average Speed (km/h)',
    yaxis2=dict(
        title='Average Intensity',
        overlaying='y',
        side='right'
    ),
    hovermode='x unified'
)

st.plotly_chart(fig_hourly, use_container_width=True)

# 3. Prediction Analysis
st.header("Prediction Analysis")

# Get actual vs predicted data
prediction_data = con.execute("""
    SELECT 
        g.hor,
        g.mean_speed as actual_speed,
        p.mean_speed_pred as predicted_speed,
        g.intTot as actual_intensity,
        p.intTot_pred as predicted_intensity
    FROM geo_cal_vel g
    JOIN predictions p
    ON g.dat = p.dat
    AND g.via = p.via
    AND g.pk = p.pk
    AND g.sen = p.sen
    WHERE g.dat = ? AND g.via = ?
    ORDER BY g.hor
""", [selected_date.strftime('%Y-%m-%d'), selected_prediction_location]).fetchdf()

# Create prediction comparison plot
fig_pred = go.Figure()
fig_pred.add_trace(go.Scatter(
    x=prediction_data['hor'],
    y=prediction_data['actual_speed'],
    name='Actual Speed',
    line=dict(color='blue')
))
fig_pred.add_trace(go.Scatter(
    x=prediction_data['hor'],
    y=prediction_data['predicted_speed'],
    name='Predicted Speed',
    line=dict(color='red', dash='dash')
))

fig_pred.update_layout(
    title='Speed: Actual vs Predicted',
    xaxis_title='Hour',
    yaxis_title='Speed (km/h)',
    hovermode='x unified'
)

st.plotly_chart(fig_pred, use_container_width=True)

# 4. Error Analysis
st.header("Prediction Error Analysis")

# Calculate errors
prediction_data['speed_error'] = prediction_data['predicted_speed'] - prediction_data['actual_speed']
prediction_data['intensity_error'] = prediction_data['predicted_intensity'] - prediction_data['actual_intensity']

# Create error distribution plot
fig_error = go.Figure()
fig_error.add_trace(go.Histogram(
    x=prediction_data['speed_error'],
    name='Speed Error',
    nbinsx=20
))

fig_error.update_layout(
    title='Speed Prediction Error Distribution',
    xaxis_title='Error (km/h)',
    yaxis_title='Count',
    showlegend=False
)

st.plotly_chart(fig_error, use_container_width=True)

# 5. Data Quality
st.header("Data Quality")

# Check for missing values
missing_values = con.execute("""
    SELECT column_name, COUNT(*) as null_count
    FROM (
        SELECT * FROM geo_cal_vel
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

# Close database connection
con.close() 