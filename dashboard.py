import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# Step 1: Check if database file exists
st.write("## Step 1: Database Connection")
db_path = 'maria_ap7.duckdb'

if os.path.exists(db_path):
    st.success(f"✅ Database file found")
    
    # Step 2: Connect to database
    try:
        con = duckdb.connect(db_path)
        st.success("✅ Connected to database successfully")
        
        # Step 3: Get available values for filters
        st.write("## Step 2: Setting up Filters")
        
        # Get unique values for filters
        unique_years = con.execute("SELECT DISTINCT Anyo FROM predictions ORDER BY Anyo").fetchdf()['Anyo'].tolist()
        unique_months = con.execute("SELECT DISTINCT mes FROM predictions ORDER BY mes").fetchdf()['mes'].tolist()
        unique_days = con.execute("SELECT DISTINCT dia FROM predictions ORDER BY dia").fetchdf()['dia'].tolist()
        unique_hours = con.execute("SELECT DISTINCT hor FROM predictions ORDER BY hor").fetchdf()['hor'].tolist()
        unique_vias = con.execute("SELECT DISTINCT via FROM predictions ORDER BY via").fetchdf()['via'].tolist()
        
        st.success("✅ Filter options loaded successfully")
        
        # Sidebar filters
        st.sidebar.header("📅 Filters")
        
        selected_year = st.sidebar.selectbox(
            "Select Year (Anyo)",
            options=unique_years,
            index=0
        )
        
        selected_month = st.sidebar.selectbox(
            "Select Month (mes)",
            options=unique_months,
            index=0
        )
        
        selected_day = st.sidebar.selectbox(
            "Select Day (dia)",
            options=unique_days,
            index=0
        )
        
        selected_hour = st.sidebar.selectbox(
            "Select Hour (hor)",
            options=unique_hours,
            index=0
        )
        
        selected_via = st.sidebar.selectbox(
            "Select Via",
            options=unique_vias,
            index=0
        )
        
        # Display selected filters
        st.sidebar.write("---")
        st.sidebar.write("**Selected Filters:**")
        st.sidebar.write(f"Year: {selected_year}")
        st.sidebar.write(f"Month: {selected_month}")
        st.sidebar.write(f"Day: {selected_day}")
        st.sidebar.write(f"Hour: {selected_hour}")
        st.sidebar.write(f"Via: {selected_via}")
        
        # Step 4: Query filtered data
        st.write("## Step 3: Filtered Data")
        
        query = """
        SELECT 
            pk,
            intP_pred,
            via,
            Anyo,
            mes,
            dia,
            hor
        FROM predictions
        WHERE Anyo = ? AND mes = ? AND dia = ? AND hor = ? AND via = ?
        ORDER BY pk
        """
        
        filtered_data = con.execute(query, [selected_year, selected_month, selected_day, selected_hour, selected_via]).fetchdf()
        
        st.write(f"Found {len(filtered_data)} records for the selected filters")
        
        if len(filtered_data) > 0:
            # Show sample of filtered data
            st.write("### Sample of filtered data:")
            st.dataframe(filtered_data.head())
            
            # Step 5: Create line plot
            st.write("## Step 4: IntP Prediction by PK")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=filtered_data['pk'],
                y=filtered_data['intP_pred'],
                mode='lines+markers',
                name='IntP Predicted',
                line=dict(color='purple', width=2),
                marker=dict(size=4)
            ))
            
            fig.update_layout(
                title=f'IntP Prediction by PK (Year: {selected_year}, Month: {selected_month}, Day: {selected_day}, Hour: {selected_hour}, Via: {selected_via})',
                xaxis_title='PK (Punto Kilométrico)',
                yaxis_title='IntP Predicted (Heavy Vehicle Intensity)',
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Additional statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Min IntP", f"{filtered_data['intP_pred'].min():.2f}")
            with col2:
                st.metric("Max IntP", f"{filtered_data['intP_pred'].max():.2f}")
            with col3:
                st.metric("Mean IntP", f"{filtered_data['intP_pred'].mean():.2f}")
                
        else:
            st.warning("⚠️ No data found for the selected filters. Try different values.")
        
        # Close connection
        con.close()
        st.success("✅ Database connection closed successfully")
    
    except Exception as e:
        st.error(f"❌ Database operation failed: {str(e)}")
        st.write("Error details:", str(e))

else:
    st.error(f"❌ Database file not found at: {os.path.abspath(db_path)}")

st.write("---")
st.info("✅ Dashboard with filters and IntP vs PK plot complete!")