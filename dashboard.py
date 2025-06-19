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
        
        # Get unique values for filters from predictions table
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
        st.sidebar.header("📅 Filtres")
        print("🐛 DEBUG: Setting up sidebar filters")
        
        # Set default filter values
        default_year = 2023
        default_month = 10
        default_day = 6
        default_hour = 8

        selected_year = st.sidebar.selectbox(
            "Selecciona Any",
            options=unique_years,
            index=unique_years.index(default_year) if default_year in unique_years else 0
        )
        print(f"🐛 DEBUG: Selected year: {selected_year}")
        
        selected_month = st.sidebar.selectbox(
            "Selecciona Mes",
            options=unique_months,
            index=unique_months.index(default_month) if default_month in unique_months else 0
        )
        print(f"🐛 DEBUG: Selected month: {selected_month}")
        
        selected_day = st.sidebar.selectbox(
            "Selecciona Dia",
            options=unique_days,
            index=unique_days.index(default_day) if default_day in unique_days else 0
        )
        print(f"🐛 DEBUG: Selected day: {selected_day}")
        
        selected_hour = st.sidebar.selectbox(
            "Selecciona Hora",
            options=unique_hours,
            index=unique_hours.index(default_hour) if default_hour in unique_hours else 0
        )
        print(f"🐛 DEBUG: Selected hour: {selected_hour}")
        
        selected_via = st.sidebar.selectbox(
            "Selecciona Via",
            options=unique_vias,
            index=0
        )
        print(f"🐛 DEBUG: Selected via: {selected_via}")
        
        # Query filtered data with real values joined
        print("🐛 DEBUG: Preparing query with selected filters and joining real values")
        query = """
        SELECT 
            p.pk,
            p.intP_pred,
            p.intTot_pred,
            p.mean_speed_pred,
            g.intP as intP_real,
            g.intTot as intTot_real,
            g.mean_speed as mean_speed_real
        FROM predictions p
        LEFT JOIN geo_cal_vel g ON 
            p.pk = g.pk AND 
            p.Anyo = g.Any AND 
            p.mes = g.mes AND 
            p.dia = g.dia AND 
            p.hor = g.hor AND
            g.via = 'AP-7'
        WHERE p.Anyo = ? AND p.mes = ? AND p.dia = ? AND p.hor = ? AND p.via = ?
        ORDER BY p.pk
        """
        
        print(f"🐛 DEBUG: Executing query with parameters: [{selected_year}, {selected_month}, {selected_day}, {selected_hour}, {selected_via}]")
        
        filtered_data = con.execute(query, [selected_year, selected_month, selected_day, selected_hour, selected_via]).fetchdf()
        
        print(f"🐛 DEBUG: Query returned {len(filtered_data)} records")
        if len(filtered_data) > 0:
            print(f"🐛 DEBUG: Data shape: {filtered_data.shape}")
            print(f"🐛 DEBUG: PK range: {filtered_data['pk'].min()} to {filtered_data['pk'].max()}")
            print(f"🐛 DEBUG: HWV Intensity pred range: {filtered_data['intP_pred'].min()} to {filtered_data['intP_pred'].max()}")
            print(f"🐛 DEBUG: HWV Intensity real range: {filtered_data['intP_real'].min()} to {filtered_data['intP_real'].max()}")
            print(f"🐛 DEBUG: Real data availability: {filtered_data['intP_real'].notna().sum()} of {len(filtered_data)} records")
        
        if len(filtered_data) > 0:
            # Mean Speed Prediction by PK plot (moved to first position)
            st.header("Predicció de Velocitat Mitjana per PK")
            print("🐛 DEBUG: Creating Mean Speed plot with real vs predicted values")
            
            fig3 = go.Figure()
            
            # Add predicted values
            fig3.add_trace(go.Scatter(
                x=filtered_data['pk'],
                y=filtered_data['mean_speed_pred'],
                mode='lines+markers',
                name='Velocitat Mitjana Predita',
                line=dict(color='blue', width=3),
                marker=dict(size=6)
            ))
            
            # Add real values if available
            real_data = filtered_data[filtered_data['intP_real'].notna()]
            if len(real_data) > 0:
                fig3.add_trace(go.Scatter(
                    x=real_data['pk'],
                    y=real_data['mean_speed_real'],
                    mode='lines+markers',
                    name='Velocitat Mitjana Real',
                    line=dict(color='lightblue', width=2, dash='dot'),
                    marker=dict(size=4),
                    opacity=0.7
                ))
            
            fig3.update_layout(
                title=f'Predicció de Velocitat Mitjana per PK (Any: {selected_year}, Mes: {selected_month}, Dia: {selected_day}, Hora: {selected_hour}, Via: {selected_via})',
                xaxis_title='PK (Punt Quilomètric)',
                yaxis_title='Velocitat mitjana (km/h)',
                hovermode='x unified',
                height=500,
                legend=dict(x=0.02, y=0.98)
            )
            
            print("🐛 DEBUG: Displaying Mean Speed plot")
            st.plotly_chart(fig3, use_container_width=True)
            print("🐛 DEBUG: Mean Speed plot displayed successfully")
            
            # HWV Intensity Prediction by PK plot (moved to second position)
            st.header("Predicció Intensitat de Vehicles Pesats per PK")
            print("🐛 DEBUG: Creating HWV Intensity plot with real vs predicted values")
            
            fig1 = go.Figure()
            
            # Add predicted values
            fig1.add_trace(go.Scatter(
                x=filtered_data['pk'],
                y=filtered_data['intP_pred'],
                mode='lines+markers',
                name='Intensitat Vehicles Pesats Predita',
                line=dict(color='purple', width=3),
                marker=dict(size=6)
            ))
            
            # Add real values if available
            if len(real_data) > 0:
                fig1.add_trace(go.Scatter(
                    x=real_data['pk'],
                    y=real_data['intP_real'],
                    mode='lines+markers',
                    name='Intensitat Vehicles Pesats Real',
                    line=dict(color='mediumpurple', width=2, dash='dot'),
                    marker=dict(size=4),
                    opacity=0.7
                ))
            
            fig1.update_layout(
                title=f'Predicció Intensitat de Vehicles Pesats per PK (Any: {selected_year}, Mes: {selected_month}, Dia: {selected_day}, Hora: {selected_hour}, Via: {selected_via})',
                xaxis_title='PK (Punt Quilomètric)',
                yaxis_title='Intensitat de Vehicles Pesats',
                hovermode='x unified',
                height=500,
                legend=dict(x=0.02, y=0.98)
            )
            
            print("🐛 DEBUG: Displaying HWV Intensity plot")
            st.plotly_chart(fig1, use_container_width=True)
            print("🐛 DEBUG: HWV Intensity plot displayed successfully")
            
            # Total Intensity Prediction by PK plot (moved to third position)
            st.header("Predicció Intensitat Total per PK")
            print("🐛 DEBUG: Creating Total Intensity plot with real vs predicted values")
            
            fig2 = go.Figure()
            
            # Add predicted values
            fig2.add_trace(go.Scatter(
                x=filtered_data['pk'],
                y=filtered_data['intTot_pred'],
                mode='lines+markers',
                name='Intensitat Total Predita',
                line=dict(color='orange', width=3),
                marker=dict(size=6)
            ))
            
            # Add real values if available
            if len(real_data) > 0:
                fig2.add_trace(go.Scatter(
                    x=real_data['pk'],
                    y=real_data['intTot_real'],
                    mode='lines+markers',
                    name='Intensitat Total Real',
                    line=dict(color='moccasin', width=2, dash='dot'),
                    marker=dict(size=4),
                    opacity=0.7
                ))
            
            fig2.update_layout(
                title=f'Predicció Intensitat Total per PK (Any: {selected_year}, Mes: {selected_month}, Dia: {selected_day}, Hora: {selected_hour}, Via: {selected_via})',
                xaxis_title='PK (Punt Quilomètric)',
                yaxis_title='Intensitat Total',
                hovermode='x unified',
                height=500,
                legend=dict(x=0.02, y=0.98)
            )
            
            print("🐛 DEBUG: Displaying Total Intensity plot")
            st.plotly_chart(fig2, use_container_width=True)
            print("🐛 DEBUG: Total Intensity plot displayed successfully")
            
            # Display data availability info
            if len(real_data) > 0:
                st.info(f"📊 Dades reals disponibles per {len(real_data)} de {len(filtered_data)} punts quilomètrics.")
            else:
                st.warning("⚠️ No hi ha dades reals disponibles per als filtres seleccionats.")
        
        # Close connection
        con.close()
        print("🐛 DEBUG: Database connection closed")
    
    except Exception as e:
        print(f"🐛 DEBUG: Database operation failed with error: {str(e)}")
        st.error(f"❌ Ha fallat l'operació de base de dades: {str(e)}")

else:
    print("🐛 DEBUG: Database file not found")
    st.error(f"❌ No s'ha trobat el fitxer de base de dades")

print("🐛 DEBUG: Dashboard execution completed")