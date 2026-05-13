import os
import sys
import warnings

# Silenciar logs de TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import subprocess
import requests
import joblib
import numpy as np

# Ajustar rutas (Subimos un nivel hacia /src para la DB)
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(base_dir, '../src')))
from database_config import engine

st.set_page_config(page_title="MLOps Solar CEIABD-03", layout="wide")
st.title("☀️ Panel de Control de Inteligencia Artificial")

# ----------------- MÉTRICAS DEL MENÚ LATERAL -----------------
st.sidebar.header("📊 Métricas del Sistema")

try:
    total_rows = pd.read_sql("SELECT COUNT(*) FROM master_silver", engine).iloc[0, 0]
except:
    total_rows = 0

models_dir = os.path.abspath(os.path.join(base_dir, '../models'))
acc_file = os.path.join(models_dir, 'accuracy.txt')
accuracy_str = "No entrenado"

if os.path.exists(acc_file):
    try:
        with open(acc_file, 'r') as f:
            r2_val = float(f.read().strip())
            accuracy_str = f"{r2_val * 100:.2f}%"
    except:
        pass

col1, col2 = st.sidebar.columns(2)
col1.metric("Filas Silver", total_rows)
col2.metric("Precisión (R²)", accuracy_str)

st.sidebar.divider()

# ----------------- ZONA DE RE-ENTRENAMIENTO -----------------
st.sidebar.header("🤖 MLOps: Aprendizaje Continuo")
st.sidebar.write("Actualiza el 'cerebro' de la IA con los datos acumulados.")

if st.sidebar.button("🔄 Re-entrenar Modelo LSTM", use_container_width=True):
    with st.spinner("Entrenando red neuronal... Por favor, espera."):
        script_path = os.path.abspath(os.path.join(base_dir, '../src/gold/train_model.py'))
        result = subprocess.run(["python", script_path], capture_output=True, text=True)
        
        if result.returncode == 0:
            st.sidebar.success("✅ Modelo actualizado con éxito.")
            with st.expander("Ver Log de Entrenamiento"):
                st.text(result.stdout)
            st.rerun() 
        else:
            st.sidebar.error("❌ Error durante el entrenamiento.")
            st.error(result.stderr)

# ----------------- CARGA DE IA Y CÁLCULO DE PREDICCIÓN -----------------
st.subheader("👀 Explorador Predictivo y Prescriptivo")

@st.cache_resource
def load_ai_models():
    import tensorflow as tf
    model_path = os.path.join(models_dir, 'solar_lstm.keras')
    scaler_path = os.path.join(models_dir, 'scaler.pkl')
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        return tf.keras.models.load_model(model_path), joblib.load(scaler_path)
    return None, None

# Traer datos históricos
try:
    df_data = pd.read_sql("SELECT * FROM master_silver ORDER BY timestamp DESC LIMIT 1000", engine)
    df_data['timestamp'] = pd.to_datetime(df_data['timestamp'], utc=True)
except Exception as e:
    st.warning(f"Error al leer la base de datos: {e}")
    df_data = pd.DataFrame()

# Generar la predicción maestra
df_prediccion = None
model, scaler = load_ai_models()

if model and scaler and not df_data.empty:
    lat, lon = 41.67, 2.78
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,direct_radiation,shortwave_radiation,cloud_cover&timezone=UTC&forecast_days=3"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()['hourly']
            df_f = pd.DataFrame(data)
            df_f['timestamp'] = pd.to_datetime(df_f['time'], utc=True)
            df_f['hora'] = df_f['timestamp'].dt.hour
            
            df_f = df_f.rename(columns={
                'temperature_2m': 'temp',
                'direct_radiation': 'rad_direct',
                'shortwave_radiation': 'rad_shortwave',
                'cloud_cover': 'cloud_cover'
            })

            for col in ['rad_direct', 'cloud_cover']:
                if col in df_data.columns and df_data[col].fillna(0).sum() == 0:
                    df_f[col] = 0.0

            features_top = ['hora', 'rad_shortwave', 'rad_direct', 'cloud_cover', 'temp', 'prod_lag_1']
            predicciones = []
            valor_anterior = df_data['production_kw'].iloc[0]

            for i in range(len(df_f)):
                fila = df_f.iloc[i:i+1].copy()
                fila['prod_lag_1'] = valor_anterior
                
                X_val = fila[features_top].values.astype('float32')
                X_scaled = scaler.transform(X_val)
                X_rnn = X_scaled.reshape((1, 1, 6))
                
                p = model.predict(X_rnn, verbose=0)[0][0]
                if df_f.iloc[i]['rad_shortwave'] <= 0:
                    p = 0.0
                    
                p = max(0, float(p))
                predicciones.append(p)
                valor_anterior = p
            
            df_f['Predicción (kW)'] = predicciones
            df_f['Hora Local'] = df_f['timestamp'].dt.tz_convert('Europe/Madrid')
            
            # Borramos el día de hoy
            df_prediccion = df_f.iloc[24:].copy().reset_index(drop=True)
    except Exception as e:
        st.error(f"Error generando predicción: {e}")

# ----------------- SISTEMA DE PESTAÑAS -----------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🌤️ Último Día Real", 
    "🔮 Predicción IA", 
    "📚 Tabla de Datos", 
    "💡 Ahorro Inteligente"
])

# --- PESTAÑA 1: ÚLTIMO DÍA ---
with tab1:
    if not df_data.empty:
        ultimo_dia = df_data['timestamp'].dt.date.max()
        st.write(f"Producción exacta por hora del día **{ultimo_dia}**:")
        
        df_recent = df_data[df_data['timestamp'].dt.date == ultimo_dia].copy()
        df_recent = df_recent.sort_values('timestamp')
        df_recent['production_kw'] = df_recent['production_kw'].clip(lower=0)
        
        df_recent['Hora'] = df_recent['timestamp'].dt.tz_convert('Europe/Madrid').dt.strftime('%H:%M')
        st.bar_chart(df_recent.set_index('Hora')['production_kw'], color="#ffaa00")

# --- PESTAÑA 2: PREDICCIÓN ---
with tab2:
    st.write("Generación de energía estimada para los próximos 2 días:")
    if df_prediccion is not None:
        df_plot = df_prediccion.copy()
        df_plot['Día-Hora'] = df_plot['Hora Local'].dt.strftime('%d %b - %H:%M')
        st.bar_chart(df_plot.set_index('Día-Hora')['Predicción (kW)'], color="#00ff88")
    else:
        st.info("⚠️ Necesitas entrenar la IA o esperar a tener datos.")

# --- PESTAÑA 3: TABLA DE DATOS CRUDOS ---
with tab3:
    st.write("Registros crudos extraídos de la tabla maestra (Capa Silver):")
    st.dataframe(df_data, use_container_width=True)

# --- PESTAÑA 4: RECOMENDADOR PRESCRIPTIVO (SIN BLOQUEOS + MEDIAS HORAS) ---
with tab4:
    st.markdown("### 🔌 Planificador Inteligente de Consumo")
    st.write("Escribe los aparatos que necesitas encender mañana y cuánto tiempo tardan. La IA organizará tu día.")
    
    # Datos por defecto al abrir la página (con decimales)
    df_default = pd.DataFrame([
        {"Aparato": "Lavadora", "Horas": 2.0},
        {"Aparato": "Lavavajillas", "Horas": 2.5}
    ])
    
    # Hemos quitado el required=True para que no de errores si la dejas vacía
    edited_df = st.data_editor(
        df_default,
        num_rows="dynamic",
        column_config={
            "Aparato": st.column_config.TextColumn(
                "Nombre del Aparato",
                help="Ejemplo: Lavadora, Horno, Depuradora..."
            ),
            "Horas": st.column_config.NumberColumn(
                "Duración Estimada (Horas)",
                min_value=0.5,
                max_value=24.0,
                step=0.5,
                format="%.1f"
            )
        },
        use_container_width=True
    )
    
    # Algoritmo de planificación con medias horas
    if st.button("✨ Organizar mi día (Mañana)", type="primary"):
        if df_prediccion is not None and not df_prediccion.empty:
            
            manana = (pd.Timestamp.now(tz='Europe/Madrid') + pd.Timedelta(days=1)).date()
            df_manana = df_prediccion[df_prediccion['Hora Local'].dt.date == manana].reset_index(drop=True)
            
            if len(df_manana) > 0:
                # Limpiar filas vacías para que no de error si el usuario las deja en blanco
                df_limpio = edited_df.dropna(subset=['Aparato', 'Horas']).copy()
                df_limpio = df_limpio[df_limpio['Aparato'].astype(str).str.strip() != ""]
                df_limpio = df_limpio[df_limpio['Horas'] > 0]
                
                tareas = df_limpio.to_dict('records')
                
                if not tareas:
                    st.warning("⚠️ La tabla está vacía o incompleta. Añade al menos un aparato y sus horas.")
                else:
                    # Ordenar por duración (los más largos primero)
                    tareas.sort(key=lambda x: float(x['Horas']), reverse=True)
                    
                    ocupadas = set()
                    resultados = []
                    
                    for tarea in tareas:
                        aparato = tarea['Aparato']
                        duracion_h = float(tarea['Horas'])
                        
                        # Cuantos bloques de 1 hora necesitamos reservar en la agenda (ej: 1.5h = 2 bloques)
                        duracion_slots = int(np.ceil(duracion_h)) 
                        
                        max_energia = -1
                        mejor_indice = -1
                        
                        # Buscamos huecos libres
                        for i in range(len(df_manana) - duracion_slots + 1):
                            bloque_libre = True
                            for j in range(duracion_slots):
                                if (i + j) in ocupadas:
                                    bloque_libre = False
                                    break
                            
                            if bloque_libre:
                                energia_ventana = df_manana['Predicción (kW)'].iloc[i:i+duracion_slots].sum()
                                if energia_ventana > max_energia:
                                    max_energia = energia_ventana
                                    mejor_indice = i
                        
                        # Si encontramos hueco
                        if mejor_indice != -1:
                            for j in range(duracion_slots):
                                ocupadas.add(mejor_indice + j)
                            
                            hora_inicio = df_manana['Hora Local'].iloc[mejor_indice]
                            # Calculamos la hora de fin exacta sumando la duración en horas (incluso si es 1.5)
                            hora_fin = hora_inicio + pd.Timedelta(hours=duracion_h)
                            
                            resultados.append({
                                "Aparato": aparato,
                                "Inicio": hora_inicio,
                                "Fin": hora_fin
                            })
                        else:
                            st.error(f"❌ No ha sido posible encontrar hueco libre para: **{aparato}**")
                    
                    # Mostrar los resultados cronológicamente
                    if resultados:
                        resultados.sort(key=lambda x: x['Inicio'])
                        
                        st.subheader("📅 Tu Horario Solar Optimizado")
                        st.write("Tu plan de ahorro sin solapar electrodomésticos:")
                        for res in resultados:
                            st.success(f"**{res['Inicio'].strftime('%H:%M')} a {res['Fin'].strftime('%H:%M')}** ➔ 🔌 {res['Aparato']}")
            else:
                st.warning("No hay suficientes datos predichos para el día de mañana todavía.")
        else:
            st.error("La IA aún no ha generado predicciones. Comprueba la pestaña de predicción.")
