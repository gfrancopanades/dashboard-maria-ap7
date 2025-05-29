import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="Traffic Analysis Dashboard",
    page_icon="🚗",
    layout="wide"
)

# Title
st.title("🚗 Traffic Analysis Dashboard")

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
    value=datetime.strptime(dates[0], '%Y-%m-%d').date(),
    min_value=datetime.strptime(dates[0], '%Y-%m-%d').date(),
    max_value=datetime.strptime(dates[-1], '%Y-%m-%d').date()
)

# Get unique locations for filter
locations = con.execute("""
    SELECT DISTINCT via 
    FROM geo_cal_vel 
    ORDER BY via
""").fetchdf()['via'].tolist()

selected_location = st.sidebar.selectbox(
    "Select Location",
    options=locations
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
""", [selected_date.strftime('%Y-%m-%d'), selected_location]).fetchdf()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Average Speed", f"{metrics['avg_speed'][0]:.2f} km/h")
with col2:
    st.metric("Average Intensity", f"{metrics['avg_intensity'][0]:.2f}")
with col3:
    st.metric("Number of Records", f"{metrics['record_count'][0]:,}")

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
""", [selected_date.strftime('%Y-%m-%d'), selected_location]).fetchdf()

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
""", [selected_date.strftime('%Y-%m-%d'), selected_location]).fetchdf()

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
""", [selected_date.strftime('%Y-%m-%d'), selected_location]).fetchdf()

if not missing_values.empty:
    st.warning("Missing values detected:")
    st.dataframe(missing_values)
else:
    st.success("No missing values detected in the selected data.")

# Close database connection
con.close() 