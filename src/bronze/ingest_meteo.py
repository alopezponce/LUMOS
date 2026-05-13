import requests
import pandas as pd
import sys
import os
from datetime import datetime

# Añadimos la ruta para encontrar database_config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database_config import engine

def ingest_meteo():
    print(f"[{datetime.now()}]  Iniciando ingesta de Meteo en DB...")

    # Coordenadas de Calella
    lat, lon = 41.67, 2.78
    # AQUÍ ESTÁ LA MAGIA: Hemos añadido humedad, precipitación, difusa y presión
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,precipitation,cloud_cover,shortwave_radiation,direct_radiation,diffuse_radiation,surface_pressure&timezone=UTC&forecast_days=1"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        if 'hourly' in data:
            df = pd.DataFrame(data['hourly'])

            # Renombramos para que coincida EXACTAMENTE con las columnas de tu DB
            df = df.rename(columns={
                'time': 'timestamp',
                'temperature_2m': 'temp',
                'relative_humidity_2m': 'hum',
                'precipitation': 'precip',
                'direct_radiation': 'rad_direct',
                'shortwave_radiation': 'rad_shortwave',
                'diffuse_radiation': 'rad_diffuse',
                'surface_pressure': 'pressure'
            })

            # Convertir timestamp a formato fecha
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

            # --- GUARDADO EN POSTGRESQL ---
            df.to_sql('meteo_bronze', engine, if_exists='append', index=False)

            print(f" ¡Éxito! Se han guardado {len(df)} horas completas en la tabla 'meteo_bronze'.")
        else:
            print(" La API no devolvió datos horarios.")

    except Exception as e:
        print(f" Error crítico en la ingesta de Meteo: {e}")

if __name__ == "__main__":
    ingest_meteo()
