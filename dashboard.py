import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_folium import st_folium
import folium
import os

# Page config
st.set_page_config(
    page_title="MARIA AP7",
    page_icon="🚗",
    layout="wide"
)

# Title
st.title("🚗 Predicció de Trànsit - MARIA AP7")

# Start with basic debugging
st.write("✅ App started successfully")

# Check database file
db_path = 'maria_ap7.duckdb'
st.write(f"Database path: {os.path.abspath(db_path)}")
st.write(f"Database exists: {os.path.exists(db_path)}")

if not os.path.exists(db_path):
    st.error(f"❌ Database file not found at: {os.path.abspath(db_path)}")
    st.write("Please make sure the database file exists in the correct location.")
    st.stop()

st.write("✅ Database file found")

# Try to connect to database
try:
    con = duckdb.connect(db_path)
    st.write("✅ Connected to database")
except Exception as e:
    st.error(f"❌ Failed to connect to database: {str(e)}")
    st.stop()

# Try to list tables
try:
    tables = con.execute("SHOW TABLES").fetchall()
    st.write("✅ Successfully listed tables")
    st.write("Available tables:", tables)
    
    if not tables:
        st.error("❌ No tables found in database")
        st.stop()
        
except Exception as e:
    st.error(f"❌ Failed to list tables: {str(e)}")
    st.stop()

# Check if predictions table exists
table_names = [table[0] for table in tables]
if 'predictions' not in table_names:
    st.error(f"❌ 'predictions' table not found. Available tables: {table_names}")
    st.stop()

st.write("✅ 'predictions' table found")

# Try a simple query on predictions table
try:
    result = con.execute("SELECT COUNT(*) FROM predictions").fetchall()
    row_count = result[0][0]
    st.write(f"✅ Predictions table has {row_count} rows")
except Exception as e:
    st.error(f"❌ Failed to query predictions table: {str(e)}")
    st.stop()

# Try to get column information
try:
    columns = con.execute("DESCRIBE predictions").fetchdf()
    st.write("✅ Successfully described predictions table")
    st.write("Columns in predictions table:")
    st.dataframe(columns)
except Exception as e:
    st.error(f"❌ Failed to describe predictions table: {str(e)}")
    st.stop()

# Try the date query
try:
    dates = con.execute("""
        SELECT DISTINCT MAKE_DATE(Anyo, mes, dia) as date
        FROM predictions
        ORDER BY date   
        LIMIT 5
    """).fetchdf()
    st.write("✅ Successfully executed date query")
    st.write("Sample dates:", dates)
except Exception as e:
    st.error(f"❌ Failed to execute date query: {str(e)}")
    st.write("This might be due to:")
    st.write("- Missing columns (Anyo, mes, dia)")
    st.write("- Data type issues")
    st.write("- NULL values in date columns")
    st.stop()

st.write("✅ All basic checks passed!")

# Simple sidebar
st.sidebar.header("Basic Filters")
st.sidebar.write("Database connection successful!")

# Simple main content
st.header("Database Status")
st.success("All database checks passed successfully!")

# Close connection
con.close()