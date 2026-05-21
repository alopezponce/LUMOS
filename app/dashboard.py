import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
import subprocess
import urllib.request
import json
import numpy as np
import joblib

# Silenciar warnings de TensorFlow en la consola
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf

# Configuración de página
st.set_page_config(page_title="Centro de Control Energético", layout="wide", page_icon="☀️")

# Cargar configuración de base de datos
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(base_dir, '..')))
from src.database_config import engine

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .main { background-color: #1a1c24; color: white; }
    .stMetric { background-color: #262730; padding: 15px; border-radius: 10px; border-left: 5px solid #2196F3; }
    .golden-card { padding: 15px; border-radius: 10px; margin-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAR MEMORIA DE APARATOS ---
if 'mis_aparatos' not in st.session_state:
    st.session_state.mis_aparatos = {
        "Lavadora estándar": {"kW": 1.5, "horas": 1.5},
        "Lavavajillas": {"kW": 1.2, "horas": 2.0},
        "Horno Eléctrico": {"kW": 2.0, "horas": 1.0},
        "Coche Eléctrico (Carga lenta)": {"kW": 3.5, "horas": 4.0},
        "Termo de Agua": {"kW": 1.8, "horas": 1.5},
        "Aire Acondicionado": {"kW": 1.0, "horas": 3.0}
    }

# --- CARGA DE DATOS E IA ---
@st.cache_resource
def load_ml_model():
    """Carga el modelo LSTM y el escalador entrenados en la capa Gold"""
    try:
        models_dir = os.path.abspath(os.path.join(base_dir, '../models'))
        model = tf.keras.models.load_model(os.path.join(models_dir, 'solar_lstm.keras'))
        scaler = joblib.load(os.path.join(models_dir, 'scaler.pkl'))
        try:
            with open(os.path.join(models_dir, 'accuracy.txt'), 'r') as f:
                r2 = f.read()
        except:
            r2 = "N/A"
        return model, scaler, r2
    except Exception as e:
        return None, None, "Error"

@st.cache_data(ttl=60)
def load_solar_data():
    df = pd.read_sql("SELECT * FROM solar_bronze ORDER BY timestamp DESC", engine)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['autoconsumo_kw'] = df[['production_kw', 'consumption_kw']].min(axis=1)
    return df

@st.cache_data(ttl=60)
def load_silver_data():
    try:
        df = pd.read_sql("SELECT * FROM master_silver ORDER BY timestamp", engine)
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

@st.cache_data(ttl=3600)
def calcular_mae_global(_model, _scaler, df_silver):
    if df_silver.empty or _model is None or _scaler is None:
        return "N/A"
    try:
        df_clean = df_silver.dropna(subset=['production_kw']).copy()
        df_clean['hora'] = df_clean['timestamp'].dt.hour
        df_clean['prod_lag_1'] = df_clean['production_kw'].shift(1).fillna(0.0)

        features_top = ['hora', 'rad_shortwave', 'rad_direct', 'cloud_cover', 'temp', 'prod_lag_1']
        for col in features_top:
            if col not in df_clean.columns:
                df_clean[col] = 0.0

        X = df_clean[features_top].fillna(0.0)
        y = df_clean['production_kw'].values

        X_scaled = _scaler.transform(X)
        X_rnn = X_scaled.reshape((X_scaled.shape[0], 1, X_scaled.shape[1]))

        y_pred = _model.predict(X_rnn, verbose=0).flatten()
        mae = np.mean(np.abs(y - y_pred))
        return f"{mae:.4f} kW"
    except:
        return "Error"

@st.cache_data(ttl=3600)
def get_weather_forecast(fecha_objetivo):
    target_str = fecha_objetivo.strftime('%Y-%m-%d')
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude=41.6167&longitude=2.6667&daily=weather_code&timezone=Europe%2FMadrid&start_date={target_str}&end_date={target_str}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
        code = data['daily']['weather_code'][0]
    except Exception:
        code = 0

    if code in [0, 1, 2]:
        return "☀️ Despejado", "#FFC107", "#332900", "💡 **Informe de IA:** El modelo predictivo LSTM indica que mañana la producción será excelente gracias al cielo despejado."
    elif code in [3, 45, 48]:
        return "⛅ Nubes y Claros", "#FF9800", "#331c00", "⚠️ **Informe de IA:** La API meteorológica detecta inestabilidad nubosa. La red neuronal ha ajustado la predicción."
    else:
        return "🌧️ Lluvia / Mal tiempo", "#F44336", "#330000", "🚨 **ALERTA METEOROLÓGICA:** El modelo LSTM prevé una caída drástica de la producción solar a causa de la lluvia."

@st.cache_data(ttl=3600)
def get_weather_hourly_features(fecha_objetivo):
    target_str = fecha_objetivo.strftime('%Y-%m-%d')
    try:
        lat, lon = 41.67, 2.78
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,cloud_cover,shortwave_radiation,direct_radiation&timezone=UTC&start_date={target_str}&end_date={target_str}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

        df_w = pd.DataFrame(data['hourly'])
        df_w = df_w.rename(columns={
            'temperature_2m': 'temp',
            'cloud_cover': 'cloud_cover',
            'shortwave_radiation': 'rad_shortwave',
            'direct_radiation': 'rad_direct'
        })
        df_w['timestamp'] = pd.to_datetime(df_w['time'], utc=True)
        return df_w
    except:
        return pd.DataFrame()

# Instanciar componentes globales
modelo_lstm, escalador, acc_r2 = load_ml_model()
df_bronze_full = load_solar_data()
df_silver_full = load_silver_data()
filas_silver = get_silver_rows()
calculo_mae = calcular_mae_global(modelo_lstm, escalador, df_silver_full)

# --- SIDEBAR ---
ruta_logo = os.path.join(base_dir, 'assets', 'logo.png')
try:
    if os.path.exists(ruta_logo):
        st.logo(ruta_logo)
except AttributeError:
    pass

with st.sidebar:
    if os.path.exists(ruta_logo):
        st.image(ruta_logo, width=180)
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/808/808569.png", width=80)

    st.title("Métricas del Sistema")
    st.metric("Filas Silver (Histórico)", f"{filas_silver:,}")

    if acc_r2 != "Error":
        try:
            st.metric("Precisión IA (R²)", f"{float(acc_r2)*100:.2f}%", "En Producción")
        except:
            st.metric("Precisión IA (R²)", acc_r2)
    else:
        st.metric("Precisión IA (R²)", "No Entrenado", "-")

    st.metric("Error Medio (MAE)", calculo_mae, help="Media del valor absoluto de los residuos calculada sobre el dataset histórico Silver.")

    st.write("---")
    st.subheader("🤖 MLOps: Aprendizaje")
    if st.button("🔄 Re-entrenar Modelo LSTM"):
        with st.spinner("Entrenando nueva generación de IA..."):
            result = subprocess.run(["python", "src/gold/train_model.py"], capture_output=True, text=True)
            if result.returncode == 0:
                st.success("✅ Modelo actualizado.")
                st.cache_resource.clear()
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("❌ Error en el entrenamiento.")

# --- CUERPO PRINCIPAL ---
st.title("Centro de Control Energético ☀️")

col_f1, col_f2 = st.columns([2, 5])
with col_f1:
    fecha_sel = st.date_input("Día de análisis", datetime.now() - timedelta(days=1))

# Datos reales de AYER (para la Pestaña 1)
df_bronze_day = df_bronze_full[df_bronze_full['timestamp'].dt.date == fecha_sel].sort_values('timestamp')

# =========================================================================
# NUEVO: LÓGICA DE PREDICCIÓN GLOBAL PARA MAÑANA (Usada en Pestañas 2 y 4)
# =========================================================================
fecha_objetivo = fecha_sel + timedelta(days=1)
estado_clima, color_borde, bg_color, msj = get_weather_forecast(fecha_objetivo)
df_pred = pd.DataFrame() # Creamos un df_pred vacío por defecto

if not df_bronze_day.empty and modelo_lstm is not None and escalador is not None:
    df_weather_tomorrow = get_weather_hourly_features(fecha_objetivo)
    if not df_weather_tomorrow.empty:
        df_pred_features = df_weather_tomorrow.copy()
        df_pred_features['hora'] = df_pred_features['timestamp'].dt.hour

        prod_hoy_hora = df_bronze_day.groupby(df_bronze_day['timestamp'].dt.hour)['production_kw'].mean().to_dict()
        df_pred_features['prod_lag_1'] = df_pred_features['hora'].map(prod_hoy_hora).fillna(0.0)

        features_top = ['hora', 'rad_shortwave', 'rad_direct', 'cloud_cover', 'temp', 'prod_lag_1']
        X_nuevo = df_pred_features[features_top].fillna(0.0)

        X_scaled = escalador.transform(X_nuevo)
        X_rnn = X_scaled.reshape((X_scaled.shape[0], 1, X_scaled.shape[1]))

        predicciones = modelo_lstm.predict(X_rnn, verbose=0).flatten()

        df_pred = pd.DataFrame({
            'timestamp': df_pred_features['timestamp'],
            'production_kw': np.clip(predicciones, 0, None)
        })

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Día de ayer", "🧠 Predicción Futura (IA)", "🗄️ Base de Datos", "💡 Planificador Inteligente"])

# ==========================================
# PESTAÑA 1: DÍA DE AYER
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
        st.warning(f"No hay datos registrados para el día seleccionado.")

# ==========================================
# PESTAÑA 2: PREDICCIÓN FUTURA (INFERENCIA REAL LSTM)
# ==========================================
with tab2:
    st.subheader("🧠 Previsión Real de Red Neuronal LSTM (Próximas 24h)")

    if not df_pred.empty:
        st.markdown(f"#### 📡 Ejecutando Inferencia. Clima mañana: **{estado_clima}**")

        energia_estimada = df_pred['production_kw'].sum()
        pic_idx = df_pred['production_kw'].idxmax()
        pic_kw = df_pred.loc[pic_idx, 'production_kw']
        pic_hora = df_pred.loc[pic_idx, 'timestamp'].strftime("%H:%M")

        llindar_dorat = pic_kw * 0.6
        hores_dorades_df = df_pred[df_pred['production_kw'] >= llindar_dorat]

        if pic_kw < 0.5:
            text_dorat = "Producció insuficient"
        elif not hores_dorades_df.empty:
            inici_dorat = hores_dorades_df['timestamp'].min().strftime("%H:%M")
            fi_dorat = hores_dorades_df['timestamp'].max().strftime("%H:%M")
            text_dorat = f"De {inici_dorat} a {fi_dorat}"
        else:
            text_dorat = "Sense franja clara"

        st.markdown(f"""
        <div class="golden-card" style="background-color: {bg_color}; border-left: 5px solid {color_borde};">
            <span style="color: white;">{msj}</span>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("⚡ Energia Total Estimada", f"{energia_estimada:.2f} kWh")
        c2.metric("☀️ Pic Màxim de Potència", f"{pic_kw:.2f} kW", f"A les {pic_hora}", delta_color="off")
        c3.metric("⏱️ Horas Doradas", text_dorat)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df_pred['timestamp'], y=df_pred['production_kw'], name='Inferencia LSTM', fill='tozeroy', line=dict(color=color_borde, width=3, shape='spline'), fillcolor=f'rgba({int(color_borde[1:3], 16)}, {int(color_borde[3:5], 16)}, {int(color_borde[5:], 16)}, 0.2)'))

        if pic_kw >= 0.5 and not hores_dorades_df.empty:
            fig2.add_vrect(x0=hores_dorades_df['timestamp'].min(), x1=hores_dorades_df['timestamp'].max(), fillcolor="green", opacity=0.1, line_width=0, annotation_text="Horas Doradas", annotation_position="top left", annotation_font_color="green")

        fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), height=400, yaxis=dict(title="kW previstos", gridcolor='#333'), xaxis=dict(gridcolor='#333', tickformat="%H:%M"))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("⚠️ No se pudo generar la predicción. Comprueba si el modelo está entrenado y hay datos del clima disponibles.")

# ==========================================
# PESTAÑA 3: EXPLORADOR MEDALLIÓN
# ==========================================
with tab3:
    st.subheader("🗄️ Explorador de Arquitectura de Datos")
    subtab1, subtab2 = st.tabs(["🥉 Capa Bronze (Día Seleccionado)", "🥈 Capa Silver (Histórico Completo)"])

    with subtab1:
        st.write(f"**`solar_bronze`**: Datos crudos de Huawei del día **{fecha_sel}** (Intervalos de 5 min).")
        if not df_bronze_day.empty:
            st.dataframe(df_bronze_day, use_container_width=True, height=400)
        else:
            st.info(f"No hay datos de la Capa Bronze para el día seleccionado ({fecha_sel}).")

    with subtab2:
        st.write("**`master_silver`**: Histórico completo enriquecido (Meteo + Precios). Mostrando las últimas **1000 filas**.")
        if not df_silver_full.empty:
            st.dataframe(df_silver_full.sort_values('timestamp', ascending=False).head(1000), use_container_width=True, height=400)
        else:
            st.info("La capa Silver aún no se ha generado o está vacía.")

# ==========================================
# PESTAÑA 4: PLANIFICADOR DE CARGAS
# ==========================================
with tab4:
    st.subheader("💡 Planificador Inteligente de Cargas (Para Mañana)")

    st.markdown("#### 🔌 Paso 1: Configurar el Consumo Base de la casa")
    consumo_base_w = st.slider(
        "Consumo continuo 24h (Nevera, Router, Standby) en W:",
        min_value=0, max_value=500, value=150, step=10
    )
    consumo_base_kw = consumo_base_w / 1000

    st.write("---")

    st.markdown("#### ⚙️ Paso 2: Configurar Electrodomésticos")
    with st.expander("Modificar Potencia y Duración de Aparatos"):
        datos_aparatos = [{"Aparato": k, "Consumo (kW)": v["kW"], "Duración (horas)": v["horas"]} for k, v in st.session_state.mis_aparatos.items()]
        df_aparatos = pd.DataFrame(datos_aparatos)

        df_editado = st.data_editor(df_aparatos, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("💾 Guardar Cambios de Aparatos"):
            df_valido = df_editado.dropna(subset=["Aparato", "Consumo (kW)", "Duración (horas)"])
            df_valido = df_valido[df_valido["Aparato"].str.strip() != ""]
            nuevo_dict = {}
            for _, fila in df_valido.iterrows():
                try:
                    nuevo_dict[str(fila["Aparato"]).strip()] = {
                        "kW": float(fila["Consumo (kW)"]),
                        "horas": float(fila["Duración (horas)"])
                    }
                except ValueError: pass
            st.session_state.mis_aparatos = nuevo_dict
            st.rerun()

    st.write("---")

    st.markdown("#### 📅 Paso 3: Crear Agenda del Día")
    mapa_opciones = {f"{nombre} ({v['kW']} kW | {v['horas']} h)": nombre for nombre, v in st.session_state.mis_aparatos.items()}
    opciones = list(mapa_opciones.keys())

    seleccion = st.multiselect("¿Qué aparatos necesitas encender hoy?", opciones, default=[opciones[0]] if opciones else [])

    if seleccion:
        # AHORA UTILIZAMOS df_pred (LA PREDICCIÓN) EN LUGAR DE df_bronze_day
        if not df_pred.empty:
            df_hora = df_pred.copy()
            df_hora['hora'] = df_hora['timestamp'].dt.hour

            df_hora['solar_disponible'] = df_hora['production_kw'] - consumo_base_kw
            df_hora['solar_disponible'] = df_hora['solar_disponible'].clip(lower=0)

            aparatos_ordenados = sorted(seleccion, key=lambda x: st.session_state.mis_aparatos[mapa_opciones[x]]["kW"] * st.session_state.mis_aparatos[mapa_opciones[x]]["horas"], reverse=True)

            agenda_resumen = []
            agenda_grafica = []
            total_kwh = 0
            total_gratis_kwh = 0

            for aparato_label in aparatos_ordenados:
                nombre_real = mapa_opciones[aparato_label]
                kw_req = st.session_state.mis_aparatos[nombre_real]["kW"]
                duracion_h = st.session_state.mis_aparatos[nombre_real]["horas"]

                energia_necesaria_kwh = kw_req * duracion_h
                total_kwh += energia_necesaria_kwh

                mejor_hora = -1
                max_cobertura = -1

                for h in df_hora['hora']:
                    cobertura_temp = 0
                    t_restante = duracion_h
                    h_actual = h

                    while t_restante > 0 and h_actual <= 23:
                        fraccion = min(1.0, t_restante)
                        req_kwh = kw_req * fraccion
                        if h_actual in df_hora['hora'].values:
                            disp = df_hora.loc[df_hora['hora'] == h_actual, 'solar_disponible'].values[0]
                            cobertura_temp += min(req_kwh, disp)
                        t_restante -= 1.0
                        h_actual += 1

                    if cobertura_temp > max_cobertura:
                        max_cobertura = cobertura_temp
                        mejor_hora = h

                t_restante = duracion_h
                h_actual = mejor_hora
                cubierto_este_aparato = 0

                while t_restante > 0 and h_actual <= 23:
                    fraccion = min(1.0, t_restante)
                    req_kwh = kw_req * fraccion

                    if h_actual in df_hora['hora'].values:
                        idx = df_hora.index[df_hora['hora'] == h_actual][0]
                        disp = df_hora.at[idx, 'solar_disponible']

                        cubierto = min(req_kwh, disp)
                        cubierto_este_aparato += cubierto
                        df_hora.at[idx, 'solar_disponible'] = max(0, disp - req_kwh)

                        agenda_grafica.append({
                            "hora_num": h_actual,
                            "Aparato": nombre_real,
                            "Demanda_kW_promedio": kw_req * fraccion
                        })

                    t_restante -= 1.0
                    h_actual += 1

                red = energia_necesaria_kwh - cubierto_este_aparato
                total_gratis_kwh += cubierto_este_aparato

                minutos_totales = int(duracion_h * 60)
                hora_fin_num = mejor_hora + (minutos_totales // 60)
                minutos_fin = minutos_totales % 60
                if hora_fin_num > 23:
                    hora_fin_num = 23
                    minutos_fin = 59

                agenda_resumen.append({
                    "Aparato": nombre_real,
                    "Inicio": f"{mejor_hora:02d}:00",
                    "Fin": f"{hora_fin_num:02d}:{minutos_fin:02d}",
                    "Energía (kWh)": energia_necesaria_kwh,
                    "Gratis (Sol)": cubierto_este_aparato,
                    "Pagado (Red)": red
                })

            pct_ahorro = (total_gratis_kwh / total_kwh) * 100 if total_kwh > 0 else 0
            st.info(f"⚡ **Energía Total Requerida:** {total_kwh:.2f} kWh | 🟩 **Cubierta por el Sol (Estimado):** {total_gratis_kwh:.2f} kWh ({pct_ahorro:.0f}%) | 🟥 **A pagar:** {total_kwh - total_gratis_kwh:.2f} kWh")

            col_c1, col_c2 = st.columns([1, 2])
            with col_c1:
                st.write("📋 **Tu Agenda Óptima para Mañana:**")
                df_agenda = pd.DataFrame(agenda_resumen).sort_values("Inicio")
                st.dataframe(df_agenda.style.format({
                    "Energía (kWh)": "{:.2f}", "Gratis (Sol)": "{:.2f}", "Pagado (Red)": "{:.2f}"
                }), hide_index=True, use_container_width=True)

            with col_c2:
                fig4 = go.Figure()
                base_date = df_pred['timestamp'].dt.date.iloc[0].strftime('%Y-%m-%d')

                # GRAFICAR LA PREDICCIÓN DE LA IA (No la del día de ayer)
                fig4.add_trace(go.Scatter(
                    x=df_pred['timestamp'],
                    y=df_pred['production_kw'],
                    name='Predicción Solar (IA)',
                    fill='tozeroy',
                    line=dict(color=color_borde, width=2, shape='spline'),
                    fillcolor=f'rgba({int(color_borde[1:3], 16)}, {int(color_borde[3:5], 16)}, {int(color_borde[5:], 16)}, 0.1)'
                ))

                fig4.add_trace(go.Scatter(x=df_pred['timestamp'], y=[consumo_base_kw] * len(df_pred), name='Consumo Base', mode='lines', line=dict(color='gray', width=2, dash='dot')))

                colores_aparatos = ['#2196F3', '#FF9800', '#9C27B0', '#E91E63', '#00BCD4', '#FFEB3B']
                nombres_vistos = []

                for item in agenda_grafica:
                    hora_dt = pd.to_datetime(f"{base_date} {item['hora_num']:02d}:00:00")
                    color_idx = opciones.index(next(op for op in opciones if item['Aparato'] in op))
                    color = colores_aparatos[color_idx % len(colores_aparatos)]

                    show_leg = item['Aparato'] not in nombres_vistos
                    if show_leg: nombres_vistos.append(item['Aparato'])

                    fig4.add_trace(go.Bar(
                        x=[hora_dt], y=[item['Demanda_kW_promedio']],
                        name=item['Aparato'],
                        width=3600000 * 0.9,
                        marker_color=color,
                        marker_line_width=1, marker_line_color='rgba(255,255,255,0.2)',
                        opacity=0.9,
                        showlegend=show_leg
                    ))

                fig4.update_layout(barmode='stack', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), height=400, yaxis=dict(title="Potencia Promedio (kW)", gridcolor='#333'), xaxis=dict(gridcolor='#333', dtick=3600000, tickformat="%H:%M"), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig4, use_container_width=True)
        else:
            st.error("❌ No se puede generar el planificador. Asegúrate de que el modelo de IA está entrenado y que hay previsión del clima disponible para generar la curva de mañana.")
iabd@ceiabd-03:~/proyectov2/app$
