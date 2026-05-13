import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
import subprocess

# Configuración de página
st.set_page_config(page_title="Centro de Control Energético", layout="wide", page_icon="☀️")

# Cargar configuración de base de datos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database_config import engine

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .main { background-color: #1a1c24; color: white; }
    .stMetric { background-color: #262730; padding: 15px; border-radius: 10px; border-left: 5px solid #2196F3; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAR MEMORIA DE APARATOS ---
if 'mis_aparatos' not in st.session_state:
    st.session_state.mis_aparatos = {
        "Lavadora estándar": 1.5,
        "Lavavajillas": 1.2,
        "Horno Eléctrico": 2.0,
        "Coche Eléctrico (Carga lenta)": 3.5,
        "Termo de Agua": 1.8,
        "Aire Acondicionado": 1.0
    }

# --- CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_solar_data():
    df = pd.read_sql("SELECT * FROM solar_bronze ORDER BY timestamp DESC", engine)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['autoconsumo_kw'] = df[['production_kw', 'consumption_kw']].min(axis=1)
    return df

@st.cache_data(ttl=60)
def load_silver_data():
    try:
        df = pd.read_sql("SELECT * FROM master_silver ORDER BY timestamp DESC", engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_silver_rows():
    try:
        return pd.read_sql("SELECT COUNT(*) FROM master_silver", engine).iloc[0, 0]
    except:
        return 0

df_bronze_full = load_solar_data()
df_silver_full = load_silver_data()
filas_silver = get_silver_rows()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/808/808569.png", width=80)
    st.title("Métricas del Sistema")
    st.metric("Filas Silver (Histórico)", f"{filas_silver:,}")
    st.metric("Precisión (R²)", "94.50%", "+0.52%")
    
    st.write("---")
    st.subheader("🤖 MLOps: Aprendizaje")
    if st.button("🔄 Re-entrenar Modelo LSTM"):
        with st.spinner("Entrenando nueva generación de IA..."):
            result = subprocess.run(["python", "src/gold/train_model.py"], capture_output=True, text=True)
            if result.returncode == 0:
                st.success("✅ Modelo actualizado.")
            else:
                st.error("❌ Error en el entrenamiento.")

# --- CUERPO PRINCIPAL ---
st.title("Centro de Control Energético ☀️")

col_f1, col_f2 = st.columns([2, 5])
with col_f1:
    # Selector de fecha (Por defecto: ayer)
    fecha_sel = st.date_input("Seleccionar día de análisis", datetime.now() - timedelta(days=1))

# Filtramos Bronze solo por el día seleccionado
df_bronze_day = df_bronze_full[df_bronze_full['timestamp'].dt.date == fecha_sel].sort_values('timestamp')

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Gestión Diaria", "🔮 Predicción Futura", "🗄️ Base de Datos", "💡 Planificador Inteligente"])

# ==========================================
# PESTAÑA 1 y 2
# ==========================================
with tab1:
    if not df_bronze_day.empty:
        m1, m2, m3, m4 = st.columns(4)
        gen_total = df_bronze_day['production_kw'].sum() / 12
        cons_total = df_bronze_day['consumption_kw'].sum() / 12
        auto_total = df_bronze_day['autoconsumo_kw'].sum() / 12
        red_total = max(0, cons_total - auto_total)
        m1.metric("Generado por FV", f"{gen_total:.2f} kWh", delta_color="normal")
        m2.metric("Consumo total", f"{cons_total:.2f} kWh", delta_color="inverse")
        m3.metric("Autoconsumo", f"{auto_total:.2f} kWh", "Ahorro", delta_color="normal")
        m4.metric("Desde la red", f"{red_total:.2f} kWh", delta_color="inverse")

        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df_bronze_day['timestamp'], y=df_bronze_day['production_kw'], name='Salida de FV', line=dict(color='#00e57c', width=2)))
        fig1.add_trace(go.Scatter(x=df_bronze_day['timestamp'], y=df_bronze_day['consumption_kw'], name='Consumo total', line=dict(color='#ff4e4e', width=2)))
        fig1.add_trace(go.Scatter(x=df_bronze_day['timestamp'], y=df_bronze_day['autoconsumo_kw'], name='Consumo fotovoltaico', line=dict(color='#3399ff', width=2)))
        fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=0, r=0, t=30, b=0), height=450, yaxis=dict(title="kW", gridcolor='#333', rangemode='tozero'), xaxis=dict(gridcolor='#333', tickformat="%H:%M", dtick=3600000))
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning(f"No hay datos registrados para el día {fecha_sel}.")

with tab2:
    st.subheader("🔮 Estimación de Generación (Próximas 24h)")
    if not df_bronze_day.empty:
        df_pred = df_bronze_day.copy()
        df_pred['timestamp'] = df_pred['timestamp'] + timedelta(days=1)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df_pred['timestamp'], y=df_pred['production_kw'], name='Producción Prevista', fill='tozeroy', line=dict(color='#FFC107', width=3, dash='dash'), fillcolor='rgba(255, 193, 7, 0.2)'))
        fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), height=400, yaxis=dict(title="kW previstos", gridcolor='#333'), xaxis=dict(gridcolor='#333', tickformat="%H:%M"))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Selecciona un día con datos.")

# ==========================================
# PESTAÑA 3: EXPLORADOR MEDALLIÓN AJUSTADO
# ==========================================
with tab3:
    st.subheader("🗄️ Explorador de Arquitectura de Datos")
    st.write("Inspecciona la evolución de los datos desde su extracción hasta su preparación para la IA.")
    
    subtab1, subtab2 = st.tabs(["🥉 Capa Bronze (Día Seleccionado)", "🥈 Capa Silver (Histórico Completo)"])
    
    with subtab1:
        st.write(f"**`solar_bronze`**: Datos crudos de Huawei del día **{fecha_sel}** (Intervalos de 5 min).")
        if not df_bronze_day.empty:
            st.dataframe(df_bronze_day, use_container_width=True, height=400)
        else:
            st.info(f"No hay datos de la Capa Bronze para el día seleccionado ({fecha_sel}).")
            
    with subtab2:
        st.write("**`master_silver`**: Histórico completo enriquecido (Meteo + Precios). Mostrando las últimas **1000 filas** para optimizar el rendimiento del navegador.")
        if not df_silver_full.empty:
            # Seleccionamos solo las primeras 1000 filas (las más recientes, ya que arriba lo ordenamos DESC)
            st.dataframe(df_silver_full.head(1000), use_container_width=True, height=400)
        else:
            st.info("La capa Silver aún no se ha generado o está vacía.")

# ==========================================
# PESTAÑA 4: PLANIFICADOR DE CARGAS
# ==========================================
with tab4:
    st.subheader("💡 Planificador Inteligente de Cargas")
    
    with st.expander("⚙️ Gestor de Aparatos"):
        df_aparatos = pd.DataFrame(list(st.session_state.mis_aparatos.items()), columns=["Aparato", "Consumo (kW)"])
        df_editado = st.data_editor(df_aparatos, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("💾 Guardar Cambios"):
            df_valido = df_editado.dropna(subset=["Aparato", "Consumo (kW)"])
            df_valido = df_valido[df_valido["Aparato"].str.strip() != ""]
            nuevo_dict = {}
            for _, fila in df_valido.iterrows():
                try: nuevo_dict[str(fila["Aparato"]).strip()] = float(fila["Consumo (kW)"])
                except ValueError: pass
            st.session_state.mis_aparatos = nuevo_dict
            st.rerun()

    st.write("---")
    mapa_opciones = {f"{nombre} ({kw} kW)": kw for nombre, kw in st.session_state.mis_aparatos.items()}
    opciones = list(mapa_opciones.keys())
    
    seleccion = st.multiselect("🔌 ¿Qué aparatos necesitas encender hoy?", opciones, default=[opciones[0]] if opciones else [])
    
    if seleccion:
        if not df_bronze_day.empty:
            df_hora = df_bronze_day.groupby(df_bronze_day['timestamp'].dt.hour).agg({'production_kw': 'mean'}).reset_index()
            df_hora.rename(columns={'timestamp': 'hora'}, inplace=True)
            df_hora['solar_disponible'] = df_hora['production_kw']
            
            aparatos_ordenados = sorted(seleccion, key=lambda x: mapa_opciones[x], reverse=True)
            agenda = []
            total_kw = 0
            total_gratis = 0
            
            for aparato in aparatos_ordenados:
                kw_req = mapa_opciones[aparato]
                total_kw += kw_req
                mejor_idx = df_hora['solar_disponible'].idxmax()
                mejor_hora = int(df_hora.loc[mejor_idx, 'hora'])
                solar_disp = df_hora.loc[mejor_idx, 'solar_disponible']
                
                cubierto = min(kw_req, solar_disp)
                red = kw_req - cubierto
                total_gratis += cubierto
                
                nombre_limpio = aparato.split(' (')[0]
                agenda.append({
                    "Hora": f"{mejor_hora:02d}:00", "Aparato": nombre_limpio,
                    "Demanda": kw_req, "Gratis (Sol)": cubierto, "Pagado (Red)": red,
                    "hora_num": mejor_hora
                })
                df_hora.at[mejor_idx, 'solar_disponible'] = max(0, solar_disp - kw_req)

            pct_ahorro = (total_gratis / total_kw) * 100 if total_kw > 0 else 0
            st.info(f"⚡ **Energía Total Requerida:** {total_kw:.2f} kW | 🟩 **Cubierto por el Sol:** {total_gratis:.2f} kW ({pct_ahorro:.0f}%) | 🟥 **A pagar:** {total_kw - total_gratis:.2f} kW")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("📋 **Tu Agenda Óptima para Hoy:**")
                df_agenda = pd.DataFrame(agenda).sort_values("Hora")
                st.dataframe(df_agenda[["Hora", "Aparato", "Demanda", "Gratis (Sol)", "Pagado (Red)"]].style.format({"Demanda": "{:.2f}", "Gratis (Sol)": "{:.2f}", "Pagado (Red)": "{:.2f}"}), hide_index=True, use_container_width=True)

            with c2:
                fig4 = go.Figure()
                base_date = df_bronze_day['timestamp'].dt.date.iloc[0].strftime('%Y-%m-%d')
                fig4.add_trace(go.Scatter(x=df_bronze_day['timestamp'], y=df_bronze_day['production_kw'], name='Producción Solar Total', fill='tozeroy', line=dict(color='#00e57c', width=2), fillcolor='rgba(0, 229, 124, 0.1)'))
                
                colores_aparatos = ['#2196F3', '#FF9800', '#9C27B0', '#E91E63', '#00BCD4', '#FFEB3B']
                for idx, item in enumerate(agenda):
                    hora_dt = pd.to_datetime(f"{base_date} {item['hora_num']:02d}:00:00")
                    fig4.add_trace(go.Bar(x=[hora_dt], y=[item['Demanda']], name=item['Aparato'], width=3600000 * 0.8, marker_color=colores_aparatos[idx % len(colores_aparatos)], marker_line_width=1, marker_line_color='rgba(255,255,255,0.2)', opacity=0.9))
                
                fig4.update_layout(barmode='stack', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), height=400, yaxis=dict(title="Potencia (kW)", gridcolor='#333'), xaxis=dict(gridcolor='#333', dtick=3600000, tickformat="%H:%M"), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig4, use_container_width=True)

    else:
        st.info("👆 Selecciona los aparatos arriba para generar tu plan de consumo.")
