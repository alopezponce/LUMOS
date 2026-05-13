import requests
import pandas as pd
import sys
import os
from datetime import datetime

# Encontrar database_config.py
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from database_config import engine

def rellenar_abril():
    print(f"[{datetime.now()}] 🕳️ Parcheando el hueco del mes de Abril...")
    lat, lon = 41.67, 2.78
    
    # Le pedimos a la API exactamente el rango de fechas que falta
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&start_date=2026-03-29&end_date=2026-04-29&hourly=temperature_2m,relative_humidity_2m,precipitation,cloud_cover,shortwave_radiation,direct_radiation,diffuse_radiation,surface_pressure&timezone=UTC"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        if 'hourly' in data:
            df = pd.DataFrame(data['hourly'])
            
            # Renombramos para encajar en el esquema
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
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

            # Inyectamos en la capa Bronze
            df.to_sql('meteo_bronze', engine, if_exists='append', index=False)
            print(f"✅ ¡Agujero de Meteo tapado! Se han inyectado {len(df)} horas.")
        else:
            print("⚠️ La API no devolvió datos para este rango.")

    except Exception as e:
        print(f"❌ Error al parchear: {e}")

if __name__ == "__main__":
    rellenar_abril()
