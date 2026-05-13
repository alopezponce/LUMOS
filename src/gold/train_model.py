import os
import sys
import warnings

# 1. Silenciar los molestos warnings de TensorFlow y Sklearn ANTES de importar nada
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import joblib
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score

# 2. Configuración de rutas (Subimos un nivel para encontrar database_config)
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(base_dir, '..')))
from database_config import engine

def train_solar_model():
    # Subimos dos niveles (../../) porque estamos en src/gold y queremos ir a models/
    models_dir = os.path.abspath(os.path.join(base_dir, '../../models'))
    os.makedirs(models_dir, exist_ok=True)

    print(" Extrayendo datos de la tabla master_silver...")
    df = pd.read_sql("SELECT * FROM master_silver ORDER BY timestamp", engine)
    
    print("⚙️Ingeniería de Características y Limpieza...")
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df['hora'] = df['timestamp'].dt.hour
    df['prod_lag_1'] = df['production_kw'].shift(1)
    
    # Nos aseguramos de que existan las variables, si la API falló las creamos con 0
    for col in ['rad_direct', 'cloud_cover', 'rad_shortwave', 'temp']:
        if col not in df.columns:
            df[col] = 0.0

    features_top = ['hora', 'rad_shortwave', 'rad_direct', 'cloud_cover', 'temp', 'prod_lag_1']
    
    # Rellenar los nulos (NaN) con 0 para que la IA no explote
    df_clean = df.fillna(0.0).copy()
    df_clean = df_clean[df_clean['production_kw'] >= 0]
    
    X = df_clean[features_top]
    y = df_clean['production_kw']
    
    print(" Escalando datos...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_rnn = X_scaled.reshape((X_scaled.shape[0], 1, X_scaled.shape[1]))
    
    print("Entrenando red neuronal LSTM...")
    model = tf.keras.models.Sequential([
        tf.keras.layers.LSTM(32, activation='relu', input_shape=(1, len(features_top))),
        tf.keras.layers.Dropout(0.1),
        tf.keras.layers.Dense(1)
    ])
    
    model.compile(optimizer='adam', loss='mae')
    model.fit(X_rnn, y, epochs=40, batch_size=16, verbose=0, validation_split=0.1)
    
    print("Guardando el modelo...")
    model.save(os.path.join(models_dir, 'solar_lstm.keras'))
    joblib.dump(scaler, os.path.join(models_dir, 'scaler.pkl'))
    
    # Calcular la precisión y guardarla en un TXT para el Dashboard
    y_pred = model.predict(X_rnn, verbose=0).flatten()
    r2 = r2_score(y, y_pred)
    
    with open(os.path.join(models_dir, 'accuracy.txt'), 'w') as f:
        f.write(str(r2))
        
    print(f"Entrenamiento completado. R2 score: {r2:.4f}")

if __name__ == "__main__":
    train_solar_model()
