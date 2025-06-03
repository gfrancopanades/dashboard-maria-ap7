import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
import os

# Page config
st.set_page_config(
    page_title="MARIA AP7",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Predicció de Trànsit - MARIA AP7")

print("🐛 DEBUG: Starting dashboard application")

# Database connection
db_path = 'maria_ap7.duckdb'
print(f"🐛 DEBUG: Looking for database at: {db_path}")
print(f"🐛 DEBUG: Database exists: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    print("🐛 DEBUG: Database file found, attempting connection")
    try:
        con = duckdb.connect(db_path)
        print("🐛 DEBUG: Database connection successful")
        
        # Get unique values for filters
        print("🐛 DEBUG: Querying unique values for filters...")
        
        unique_years = con.execute("SELECT DISTINCT Anyo FROM predictions ORDER BY Anyo").fetchdf()['Anyo'].tolist()
        print(f"🐛 DEBUG: Found {len(unique_years)} unique years: {unique_years}")
        
        unique_months = con.execute("SELECT DISTINCT mes FROM predictions ORDER BY mes").fetchdf()['mes'].tolist()
        print(f"🐛 DEBUG: Found {len(unique_months)} unique months: {unique_months}")
        
        unique_days = con.execute("SELECT DISTINCT dia FROM predictions ORDER BY dia").fetchdf()['dia'].tolist()
        print(f"🐛 DEBUG: Found {len(unique_days)} unique days: {unique_days}")
        
        unique_hours = con.execute("SELECT DISTINCT hor FROM predictions ORDER BY hor").fetchdf()['hor'].tolist()
        print(f"🐛 DEBUG: Found {len(unique_hours)} unique hours: {unique_hours}")
        
        unique_vias = con.execute("SELECT DISTINCT via FROM predictions ORDER BY via").fetchdf()['via'].tolist()
        print(f"🐛 DEBUG: Found {len(unique_vias)} unique vias: {unique_vias}")
        
        # Sidebar filters
        st.sidebar.header("📅 Filters")
        print("🐛 DEBUG: Setting up sidebar filters")
        
        selected_year = st.sidebar.selectbox(
            "Select Year (Anyo)",
            options=unique_years,
            index=0
        )
        print(f"🐛 DEBUG: Selected year: {selected_year}")
        
        selected_month = st.sidebar.selectbox(
            "Select Month (mes)",
            options=unique_months,
            index=0
        )
        print(f"🐛 DEBUG: Selected month: {selected_month}")
        
        selected_day = st.sidebar.selectbox(
            "Select Day (dia)",
            options=unique_days,
            index=0
        )
        print(f"🐛 DEBUG: Selected day: {selected_day}")
        
        selected_hour = st.sidebar.selectbox(
            "Select Hour (hor)",
            options=unique_hours,
            index=0
        )
        print(f"🐛 DEBUG: Selected hour: {selected_hour}")
        
        selected_via = st.sidebar.selectbox(
            "Select Via",
            options=unique_vias,
            index=0
        )
        print(f"🐛 DEBUG: Selected via: {selected_via}")
        
        # Query filtered data
        print("🐛 DEBUG: Preparing query with selected filters")
        query = """
        SELECT 
            pk,
            intP_pred,
            intTot_pred,
            mean_speed_pred
        FROM predictions
        WHERE Anyo = ? AND mes = ? AND dia = ? AND hor = ? AND via = ?
        ORDER BY pk
        """
        
        print(f"🐛 DEBUG: Executing query with parameters: [{selected_year}, {selected_month}, {selected_day}, {selected_hour}, {selected_via}]")
        
        filtered_data = con.execute(query, [selected_year, selected_month, selected_day, selected_hour, selected_via]).fetchdf()
        
        print(f"🐛 DEBUG: Query returned {len(filtered_data)} records")
        if len(filtered_data) > 0:
            print(f"🐛 DEBUG: Data shape: {filtered_data.shape}")
            print(f"🐛 DEBUG: PK range: {filtered_data['pk'].min()} to {filtered_data['pk'].max()}")
            print(f"🐛 DEBUG: HWV Intensity range: {filtered_data['intP_pred'].min()} to {filtered_data['intP_pred'].max()}")
            print(f"🐛 DEBUG: Total Intensity range: {filtered_data['intTot_pred'].min()} to {filtered_data['intTot_pred'].max()}")
            print(f"🐛 DEBUG: Mean Speed range: {filtered_data['mean_speed_pred'].min()} to {filtered_data['mean_speed_pred'].max()}")
        
        if len(filtered_data) > 0:
            # HWV Intensity Prediction by PK plot
            st.header("HWV Intensity Prediction by PK")
            print("🐛 DEBUG: Creating HWV Intensity plot")
            
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=filtered_data['pk'],
                y=filtered_data['intP_pred'],
                mode='lines+markers',
                name='HWV Intensity Predicted',
                line=dict(color='purple', width=2),
                marker=dict(size=4)
            ))
            
            fig1.update_layout(
                title=f'HWV Intensity Prediction by PK (Year: {selected_year}, Month: {selected_month}, Day: {selected_day}, Hour: {selected_hour}, Via: {selected_via})',
                xaxis_title='PK (Punto Kilométrico)',
                yaxis_title='HWV Intensity Predicted (Heavy Vehicle Intensity)',
                hovermode='x unified',
                height=500
            )
            
            print("🐛 DEBUG: Displaying HWV Intensity plot")
            st.plotly_chart(fig1, use_container_width=True)
            print("🐛 DEBUG: HWV Intensity plot displayed successfully")
            
            # Total Intensity Prediction by PK plot
            st.header("Total Intensity Prediction by PK")
            print("🐛 DEBUG: Creating Total Intensity plot")
            
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=filtered_data['pk'],
                y=filtered_data['intTot_pred'],
                mode='lines+markers',
                name='Total Intensity Predicted',
                line=dict(color='orange', width=2),
                marker=dict(size=4)
            ))
            
            fig2.update_layout(
                title=f'Total Intensity Prediction by PK (Year: {selected_year}, Month: {selected_month}, Day: {selected_day}, Hour: {selected_hour}, Via: {selected_via})',
                xaxis_title='PK (Punto Kilométrico)',
                yaxis_title='Total Intensity Predicted (Total Vehicle Intensity)',
                hovermode='x unified',
                height=500
            )
            
            print("🐛 DEBUG: Displaying Total Intensity plot")
            st.plotly_chart(fig2, use_container_width=True)
            print("🐛 DEBUG: Total Intensity plot displayed successfully")
            
            # Mean Speed Prediction by PK plot
            st.header("Mean Speed Prediction by PK")
            print("🐛 DEBUG: Creating Mean Speed plot")
            
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=filtered_data['pk'],
                y=filtered_data['mean_speed_pred'],
                mode='lines+markers',
                name='Mean Speed Predicted',
                line=dict(color='blue', width=2),
                marker=dict(size=4)
            ))
            
            fig3.update_layout(
                title=f'Mean Speed Prediction by PK (Year: {selected_year}, Month: {selected_month}, Day: {selected_day}, Hour: {selected_hour}, Via: {selected_via})',
                xaxis_title='PK (Punto Kilométrico)',
                yaxis_title='Mean Speed Predicted (km/h)',
                hovermode='x unified',
                height=500
            )
            
            print("🐛 DEBUG: Displaying Mean Speed plot")
            st.plotly_chart(fig3, use_container_width=True)
            print("🐛 DEBUG: Mean Speed plot displayed successfully")
                
        else:
            print("🐛 DEBUG: No data found for selected filters")
            st.warning("⚠️ No data found for the selected filters. Try different values.")
        
        # Close connection
        con.close()
        print("🐛 DEBUG: Database connection closed")
    
    except Exception as e:
        print(f"🐛 DEBUG: Database operation failed with error: {str(e)}")
        st.error(f"❌ Database operation failed: {str(e)}")

else:
    print("🐛 DEBUG: Database file not found")
    st.error(f"❌ Database file not found")

print("🐛 DEBUG: Dashboard execution completed")