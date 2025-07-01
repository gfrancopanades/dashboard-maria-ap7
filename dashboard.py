import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
import os
import folium
from streamlit_folium import st_folium

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
        unique_months = con.execute("SELECT DISTINCT mes FROM predictions ORDER BY mes").fetchdf()['mes'].tolist()
        unique_days = con.execute("SELECT DISTINCT dia FROM predictions ORDER BY dia").fetchdf()['dia'].tolist()
        unique_hours = con.execute("SELECT DISTINCT hor FROM predictions ORDER BY hor").fetchdf()['hor'].tolist()
        unique_vias = con.execute("SELECT DISTINCT via FROM predictions ORDER BY via").fetchdf()['via'].tolist()

        # Sidebar filters
        st.sidebar.header("📅 Filtres")
        default_year = 2023
        default_month = 10
        default_day = 6
        default_hour = 8

        selected_year = st.sidebar.selectbox("Selecciona Any", options=unique_years,
                                             index=unique_years.index(default_year) if default_year in unique_years else 0)
        selected_month = st.sidebar.selectbox("Selecciona Mes", options=unique_months,
                                               index=unique_months.index(default_month) if default_month in unique_months else 0)
        selected_day = st.sidebar.selectbox("Selecciona Dia", options=unique_days,
                                             index=unique_days.index(default_day) if default_day in unique_days else 0)
        selected_hour = st.sidebar.selectbox("Selecciona Hora (pels gràfics per PK)", options=unique_hours,
                                              index=unique_hours.index(default_hour) if default_hour in unique_hours else 0)
        selected_via = st.sidebar.selectbox("Selecciona Via", options=unique_vias, index=0)

        # Query filtered data with real values joined
        print("🐛 DEBUG: Preparing query with selected filters and joining real values")
        query = """
        WITH ranked_predictions AS (
            SELECT 
                p.Anyo as Anyo,
                p.pk,
                p.hor,
                p.intP_pred,
                p.intTot_pred,
                p.mean_speed_pred,
                g.intP as intP_real,
                g.intTot as intTot_real,
                g.mean_speed as mean_speed_real,
                ABS(p.mean_speed_pred - COALESCE(g.mean_speed, 0)) as speed_residual,
                ABS(p.intP_pred - COALESCE(g.intP, 0)) as intP_residual,
                ABS(p.intTot_pred - COALESCE(g.intTot, 0)) as intTot_residual,
                ROW_NUMBER() OVER (
                    PARTITION BY p.Anyo, p.mes, p.dia, p.hor, p.via, p.pk 
                    ORDER BY (
                        ABS(p.mean_speed_pred - COALESCE(g.mean_speed, 0)) +
                        ABS(p.intP_pred - COALESCE(g.intP, 0)) +
                        ABS(p.intTot_pred - COALESCE(g.intTot, 0))
                    ) ASC
                ) as rn
            FROM predictions p
            LEFT JOIN geo_cal_vel g ON 
                p.pk = g.pk AND 
                p.Anyo = g.Any AND 
                p.mes = g.mes AND 
                p.dia = g.dia AND 
                p.hor = g.hor AND
                g.via = 'AP-7'
            WHERE p.Anyo = ? AND p.mes = ? AND p.dia = ? AND p.via = ?
        )
        SELECT 
            pk,
            intP_pred,
            intTot_pred,
            mean_speed_pred,
            intP_real,
            intTot_real,
            mean_speed_real,
            hor
        FROM ranked_predictions 
        WHERE rn = 1
        ORDER BY pk, hor
        """

        filtered_data = con.execute(query, [selected_year, selected_month, selected_day, selected_via]).fetchdf()

        if len(filtered_data) > 0:
            pk_list = filtered_data['pk'].tolist()

            tab1, tab2, tab3, tab4 = st.tabs([
                "🗺️ Dades en Mapa per pk",
                "📈 Gràfic de linies per pk",
                "🕒 Gràfic de linies per hores",
                "⚠️ Prediccions de velocitat ≤ 85 km/h"
            ])

            with tab1:
                st.header("Dades en Mapa per pk")
                hour_filtered = filtered_data[filtered_data['hor'] == selected_hour]
                hour_pk_list = hour_filtered['pk'].tolist()

                variables = [
                    ('mean_speed_pred', 'Velocitat Mitjana Predita (km/h)', ['red', 'yellow', 'green']),
                    ('intP_pred', 'Intensitat Vehicles Pesats Predita', ['green', 'yellow', 'red']),
                    ('intTot_pred', 'Intensitat Total Predita', ['green', 'yellow', 'red'])
                ]

                for var_name, var_title, colors in variables:
                    st.subheader(var_title)
                    if len(hour_pk_list) > 0:
                        pk_tuple = tuple(hour_pk_list)
                        if len(pk_tuple) == 1:
                            pk_tuple = f"({pk_tuple[0]})"

                        lonlat_query = f"""
                            SELECT pk, lon, lat FROM lonlat_pks_ap7 WHERE pk IN {pk_tuple}
                        """
                        lonlat_df = con.execute(lonlat_query).fetchdf()
                        map_df = pd.merge(hour_filtered, lonlat_df, on='pk', how='inner')

                        if len(map_df) > 0:
                            map_center = [map_df['lat'].mean(), map_df['lon'].mean()]
                            m = folium.Map(location=map_center, zoom_start=8, tiles='cartodbpositron')
                            min_val = map_df[var_name].min()
                            max_val = map_df[var_name].max()
                            colormap = folium.LinearColormap(colors=colors, vmin=min_val, vmax=max_val)
                            colormap.caption = var_title
                            colormap.add_to(m)

                            for _, row in map_df.iterrows():
                                folium.CircleMarker(
                                    location=[row['lat'], row['lon']],
                                    radius=4,
                                    color=colormap(row[var_name]),
                                    fill=True,
                                    fill_color=colormap(row[var_name]),
                                    fill_opacity=0.7,
                                    popup=f"PK: {row['pk']}<br>{var_title}: {row[var_name]:.2f}"
                                ).add_to(m)

                            st_folium(m, width=1200, height=500)
                        else:
                            st.warning("No dades disponibles")
                    else:
                        st.warning("No dades disponibles")

            with tab2:
                st.header("Gràfic de linies per pk")
                hour_filtered = filtered_data[filtered_data['hor'] == selected_hour]
                plot_variables = [
                    ('mean_speed_pred', 'mean_speed_real', 'Velocitat Mitjana', 'blue', 'lightblue'),
                    ('intP_pred', 'intP_real', 'Intensitat Vehicles Pesats', 'purple', 'mediumpurple'),
                    ('intTot_pred', 'intTot_real', 'Intensitat Total', 'orange', 'moccasin')
                ]

                for pred_col, real_col, title, pred_color, real_color in plot_variables:
                    st.subheader(title)
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=hour_filtered['pk'],
                        y=hour_filtered[pred_col],
                        mode='lines+markers',
                        name=f'{title} Predita',
                        line=dict(color=pred_color, width=3),
                        marker=dict(size=6)
                    ))
                    real_data = hour_filtered[hour_filtered[real_col].notna()]
                    if len(real_data) > 0:
                        fig.add_trace(go.Scatter(
                            x=real_data['pk'],
                            y=real_data[real_col],
                            mode='lines+markers',
                            name=f'{title} Real',
                            line=dict(color=real_color, width=2, dash='dot'),
                            marker=dict(size=4),
                            opacity=0.7
                        ))
                    fig.update_layout(
                        title=f'{title} per PK (Hora {selected_hour})',
                        xaxis_title='PK (Punt Quilomètric)',
                        yaxis_title=title,
                        hovermode='x unified',
                        height=400,
                        legend=dict(x=0.02, y=0.98)
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with tab3:
                st.header("Gràfic de linies per hores")
                unique_pks = sorted(filtered_data['pk'].unique())
                selected_pk = st.sidebar.selectbox(
                    "Selecciona PK (pels gràfics per hores)", options=unique_pks, key="pk_for_hourly_tab")
                pk_filtered = filtered_data[filtered_data['pk'] == selected_pk]

                hourly_vars = [
                    ('mean_speed_pred', 'mean_speed_real', 'Velocitat Mitjana', 'blue', 'lightblue'),
                    ('intP_pred', 'intP_real', 'Intensitat Vehicles Pesats', 'purple', 'mediumpurple'),
                    ('intTot_pred', 'intTot_real', 'Intensitat Total', 'orange', 'moccasin')
                ]

                for pred_col, real_col, title, pred_color, real_color in hourly_vars:
                    st.subheader(title)
                    hourly_df = pk_filtered.groupby('hor').agg({pred_col: 'mean', real_col: 'mean'}).reset_index()
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=hourly_df['hor'],
                        y=hourly_df[pred_col],
                        mode='lines+markers',
                        name=f'{title} Predita',
                        line=dict(color=pred_color, width=3),
                        marker=dict(size=6)
                    ))
                    if hourly_df[real_col].notna().sum() > 0:
                        fig.add_trace(go.Scatter(
                            x=hourly_df['hor'],
                            y=hourly_df[real_col],
                            mode='lines+markers',
                            name=f'{title} Real',
                            line=dict(color=real_color, width=2, dash='dot'),
                            marker=dict(size=4),
                            opacity=0.7
                        ))
                    fig.update_layout(
                        title=f'{title} per Hora (PK {selected_pk})',
                        xaxis_title='Hora',
                        yaxis_title=title,
                        hovermode='x unified',
                        height=400,
                        legend=dict(x=0.02, y=0.98)
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with tab4:
                st.header("Taula de prediccions de velocitat ≤ 85 km/h")
                all_low_speed_query = """
                    SELECT Anyo, mes, dia, hor, via, pk, mean_speed_pred
                    FROM predictions
                    WHERE mean_speed_pred <= 85
                    ORDER BY Anyo, mes, dia, hor, via, pk
                """
                all_low_speed_df = con.execute(all_low_speed_query).fetchdf()
                if not all_low_speed_df.empty:
                    st.dataframe(all_low_speed_df)
                else:
                    st.info("No hi ha prediccions de velocitat ≤ 85 km/h en tota la base de dades.")

        con.close()
        print("🐛 DEBUG: Database connection closed")

    except Exception as e:
        print(f"🐛 DEBUG: Database operation failed with error: {str(e)}")
        st.error(f"❌ Ha fallat l'operació de base de dades: {str(e)}")
else:
    print("🐛 DEBUG: Database file not found")
    st.error(f"❌ No s'ha trobat el fitxer de base de dades")

print("🐛 DEBUG: Dashboard execution completed")
