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
    SELECT DISTINCT MAKE_DATE("Any", "mes", "dia") as date
    FROM predictions
    ORDER BY date
""").fetchdf()['date'].tolist()

selected_date = st.sidebar.date_input(
    "Select Date",
    value=dates[0],
    min_value=dates[0],
    max_value=dates[-1]
)
selected_year = selected_date.year
selected_month = selected_date.month
selected_day = selected_date.day
selected_hour = st.sidebar.selectbox(
    "Hour",
    options=range(24)
)

# Get unique locations for filter (from predictions table)
prediction_locations = con.execute("""
    SELECT DISTINCT via 
    FROM predictions 
    ORDER BY via
""").fetchdf()['via'].tolist()

selected_via = st.sidebar.selectbox(
    "Select Prediction Location (ID)",
    options=prediction_locations,
    key="prediction_location"
)

# Main content

# 2. PK vs Speed Analysis
st.header("Predicció de velocitat mitjana per PK")

# Predicted Speed by PK
pk_speed_data = con.execute("""
    SELECT 
        pk,
        mean_speed_pred
    FROM predictions
    WHERE any = ? AND mes = ? AND dia = ? AND hor = ? AND via = ?
    ORDER BY pk
""", [selected_year, selected_month, selected_day, selected_hour, selected_via]).fetchdf()

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

# Percentile 10 Prediction by PK
st.header("Predicció del percentil 10 de velocitat per PK")
pk_percentile10_data = con.execute("""
    SELECT 
        pk,
        percentile_10_pred
    FROM predictions
    WHERE any = ? AND mes = ? AND dia = ? AND hor = ? AND via = ?
    ORDER BY pk
""", [selected_year, selected_month, selected_day, selected_hour, selected_via]).fetchdf()

fig_pk_percentile10 = go.Figure()
fig_pk_percentile10.add_trace(go.Scatter(
    x=pk_percentile10_data['pk'],
    y=pk_percentile10_data['percentile_10_pred'],
    name='Percentile 10 Predicted',
    line=dict(color='green', dash='dot')
))
fig_pk_percentile10.update_layout(
    title=f'Percentile 10 Predicted by PK (Year: {selected_year}, Month: {selected_month}, Day: {selected_day}, Hour: {selected_hour})',
    xaxis_title='PK',
    yaxis_title='Percentile 10 Predicted',
    hovermode='x unified'
)
st.plotly_chart(fig_pk_percentile10, use_container_width=True)

# Total Intensity Prediction by PK
st.header("Predicció de la intensitat total per PK")
pk_inttot_data = con.execute("""
    SELECT 
        pk,
        intTot_pred
    FROM predictions
    WHERE any = ? AND mes = ? AND dia = ? AND hor = ? AND via = ?
    ORDER BY pk
""", [selected_year, selected_month, selected_day, selected_hour, selected_via]).fetchdf()

fig_pk_inttot = go.Figure()
fig_pk_inttot.add_trace(go.Scatter(
    x=pk_inttot_data['pk'],
    y=pk_inttot_data['intTot_pred'],
    name='Total Intensity Predicted',
    line=dict(color='orange', dash='solid')
))
fig_pk_inttot.update_layout(
    title=f'Total Intensity Predicted by PK (Year: {selected_year}, Month: {selected_month}, Day: {selected_day}, Hour: {selected_hour})',
    xaxis_title='PK',
    yaxis_title='Total Intensity Predicted',
    hovermode='x unified'
)
st.plotly_chart(fig_pk_inttot, use_container_width=True)

# IntP Prediction by PK
st.header("Predicció de la intensitat de vehicles pesats per PK")
pk_intp_data = con.execute("""
    SELECT 
        pk,
        intP_pred
    FROM predictions
    WHERE any = ? AND mes = ? AND dia = ? AND hor = ? AND via = ?
    ORDER BY pk
""", [selected_year, selected_month, selected_day, selected_hour, selected_via]).fetchdf()

fig_pk_intp = go.Figure()
fig_pk_intp.add_trace(go.Scatter(
    x=pk_intp_data['pk'],
    y=pk_intp_data['intP_pred'],
    name='IntP Predicted',
    line=dict(color='purple', dash='dash')
))
fig_pk_intp.update_layout(
    title=f'IntP Predicted by PK (Year: {selected_year}, Month: {selected_month}, Day: {selected_day}, Hour: {selected_hour})',
    xaxis_title='PK',
    yaxis_title='IntP Predicted',
    hovermode='x unified'
)
st.plotly_chart(fig_pk_intp, use_container_width=True)

# 5. Empty Leaflet Map
st.header("Mapa (Leaflet)")
m = folium.Map(location=[41.3851, 2.1734], zoom_start=6)
st_folium(m, width=700, height=500)

# Close database connection
con.close()