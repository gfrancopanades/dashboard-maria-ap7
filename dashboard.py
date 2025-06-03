import streamlit as st
import duckdb
import pandas as pd
import os

# Page config
st.set_page_config(
    page_title="MARIA AP7",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Predicció de Trànsit - MARIA AP7")

# Step 1: Check if database file exists
st.write("## Step 1: Database Connection")
db_path = 'maria_ap7.duckdb'
st.write(f"Looking for database: {db_path}")

if os.path.exists(db_path):
    st.success(f"✅ Database file found at: {os.path.abspath(db_path)}")
    
    # Step 2: Connect to database
    try:
        con = duckdb.connect(db_path)
        st.success("✅ Connected to database successfully")
        
        # Step 3: List tables
        st.write("## Step 2: Available Tables")
        tables = con.execute("SHOW TABLES").fetchall()
        table_names = [table[0] for table in tables]
        st.write("Tables found:", table_names)
        
        # Step 4: Check predictions table
        if 'predictions' in table_names:
            st.success("✅ Predictions table found")
            
            # Step 5: Get basic info about predictions table
            st.write("## Step 3: Predictions Table Info")
            
            # Get row count
            row_count = con.execute("SELECT COUNT(*) FROM predictions").fetchall()[0][0]
            st.write(f"Total rows in predictions table: {row_count:,}")
            
            # Get column info
            columns_info = con.execute("DESCRIBE predictions").fetchdf()
            st.write("### Columns in predictions table:")
            st.dataframe(columns_info)
            
            # Step 6: Sample data
            st.write("## Step 4: Sample Data")
            sample_data = con.execute("SELECT * FROM predictions LIMIT 5").fetchdf()
            st.write("### First 5 rows:")
            st.dataframe(sample_data)
            
            # Step 7: Basic statistics
            st.write("## Step 5: Basic Statistics")
            
            # Check unique values for key columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                unique_years = con.execute("SELECT DISTINCT Anyo FROM predictions ORDER BY Anyo").fetchdf()
                st.write("**Available Years:**")
                st.write(unique_years['Anyo'].tolist())
            
            with col2:
                unique_vias = con.execute("SELECT DISTINCT via FROM predictions ORDER BY via").fetchdf()
                st.write("**Available Vias:**")
                st.write(unique_vias['via'].tolist())
            
            with col3:
                unique_hours = con.execute("SELECT DISTINCT hor FROM predictions ORDER BY hor").fetchdf()
                st.write("**Available Hours:**")
                st.write(unique_hours['hor'].tolist())
            
            # Close connection
            con.close()
            st.success("✅ Database connection closed successfully")
            
        else:
            st.error("❌ Predictions table not found!")
            st.write("Available tables:", table_names)
    
    except Exception as e:
        st.error(f"❌ Database connection failed: {str(e)}")

else:
    st.error(f"❌ Database file not found at: {os.path.abspath(db_path)}")
    st.write("Available files in current directory:")
    files = [f for f in os.listdir('.') if f.endswith('.duckdb')]
    if files:
        st.write("DuckDB files found:", files)
    else:
        st.write("No .duckdb files found in current directory")

st.write("---")
st.info("Next step: Add filters and basic visualizations")